# Rebuild + deploy the voicecmd native module (voicecmd.pyd) into Enso's contrib.
#
# Usage (from this directory):
#   .\build.ps1                 # incremental build of the module + auto-deploy
#   .\build.ps1 -Configure      # re-run cmake configure first (after CMakeLists edits)
#   .\build.ps1 -StopEnso       # close a running Enso first so the .pyd isn't locked
#   .\build.ps1 -Tests          # build and run the core unit tests instead
#   .\build.ps1 -Config Debug   # build the Debug config instead of Release
#
# Nothing here is hard-coded to one machine:
#   * Visual Studio (and its bundled CMake) is located with vswhere, so any
#     edition/install path works; a CMake on PATH is used as a fallback.
#   * The module is built against Enso's own bundled Python, found relative to
#     this script -- so the .pyd targets exactly the interpreter that will load
#     it. Override with -Python if you need a different one.
#   * nanobind only has to be importable by SOME Python (it is a build-time
#     tool; we just need the source + CMake package dir it ships). Candidates
#     are probed in turn, and if no interpreter has it a pinned copy is
#     provisioned into build-msvc\.tools automatically -- so a fresh checkout
#     needs no manual setup. Changing the target interpreter never requires
#     reinstalling it.
#
# NOTE: the deploy step copies voicecmd.pyd into Enso's contrib package. A
# running Enso holds that file open, so either close Enso or pass -StopEnso; the
# build itself still succeeds (the deploy just warns) if it's locked.
param(
    [switch]$Configure,
    [switch]$StopEnso,
    [switch]$Tests,
    [string]$Config = "Release",
    [string]$Python,
    [string]$NanobindPython
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Repo root: <repo>\platform\win32\VoiceCmd -> <repo>
$repo = (Resolve-Path (Join-Path $root "..\..\..")).Path

# ---- Visual Studio / CMake -------------------------------------------------
# vswhere ships with every VS 2017+ installer and lives at a fixed location, so
# it is the one path worth hard-coding.
function Find-CMake {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsPath = & $vswhere -latest -products * `
            -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
            -property installationPath
        if ($vsPath) {
            $bundled = Join-Path $vsPath "Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
            if (Test-Path $bundled) { return $bundled }
        }
    }
    $onPath = (Get-Command cmake -ErrorAction SilentlyContinue).Source
    if ($onPath) { return $onPath }
    throw "cmake not found: no Visual Studio with C++ tools (via vswhere) and no cmake on PATH."
}

# ---- Python ----------------------------------------------------------------
# The interpreter the module is built against. Enso's bundled Python ships the
# headers and the stable-ABI lib (include\Python.h, libs\python3.lib), so it is
# both a valid build target and the one that actually loads the .pyd.
function Find-TargetPython {
    if ($Python) {
        if (-not (Test-Path $Python)) { throw "-Python '$Python' does not exist." }
        return (Resolve-Path $Python).Path
    }
    $bundled = Join-Path $repo "enso\python\python.exe"
    if (Test-Path $bundled) { return (Resolve-Path $bundled).Path }
    $onPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($onPath) {
        Write-Warning "Enso's bundled Python not found under '$repo'; falling back to '$onPath'."
        return $onPath
    }
    throw "No Python found. Expected Enso's bundled interpreter at $bundled, or pass -Python."
}

# Pinned deliberately. nanobind is here because pybind11 under Py_LIMITED_API
# hits an MSVC 14.44 internal compiler error, so a silent upgrade into an
# untested version is exactly what we do not want from an automatic install.
$NanobindVersion = "2.13.0"

# Asks an interpreter where nanobind's CMake package lives, optionally with an
# extra directory on sys.path. Returns $null if nanobind isn't importable.
function Resolve-NanobindDir([string]$python, [string]$extraPath) {
    $saved = $env:PYTHONPATH
    if ($extraPath) { $env:PYTHONPATH = $extraPath }
    try {
        $dir = & $python -c "import nanobind; print(nanobind.cmake_dir())" 2>$null
        if ($LASTEXITCODE -eq 0 -and $dir) { return $dir.Trim() }
    } catch {
    } finally { $env:PYTHONPATH = $saved }
    return $null
}

function Get-NanobindDir([string]$targetPython, [string]$toolDir) {
    # nanobind is a build-time tool: it need not live in the target interpreter,
    # we only need the source + CMake package it ships. Prefer any copy already
    # installed, so an existing setup keeps working and costs no network.
    $candidates = @()
    if ($NanobindPython) { $candidates += $NanobindPython }
    $candidates += $targetPython
    $candidates += (Get-Command python -ErrorAction SilentlyContinue).Source
    $pyLauncher = (Get-Command py -ErrorAction SilentlyContinue).Source
    if ($pyLauncher) { $candidates += $pyLauncher }

    foreach ($c in ($candidates | Where-Object { $_ } | Select-Object -Unique)) {
        $dir = Resolve-NanobindDir $c $null
        if ($dir) {
            if ($c -ne $targetPython) { Write-Host "nanobind: using the copy installed in $c" }
            return $dir
        }
    }

    # Nothing installed anywhere: provision a private copy into the build tree.
    # `pip install --target` is a plain file drop -- no venv to manage, and it
    # touches neither your dev interpreter nor Enso's shipped runtime.
    $dir = Resolve-NanobindDir $targetPython $toolDir
    if ($dir) { return $dir }

    Write-Host "nanobind: not installed anywhere; provisioning $NanobindVersion into $toolDir"
    # Out-Host, not bare invocation: inside a function a native command's stdout
    # would join this function's return value and corrupt the path we hand back.
    & $targetPython -m pip install --disable-pip-version-check --no-warn-script-location `
        --target $toolDir "nanobind==$NanobindVersion" | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Could not provision nanobind (pip failed; offline?). Install it manually with " +
              "'pip install nanobind' into any interpreter, or pass -NanobindPython <python.exe>."
    }

    $dir = Resolve-NanobindDir $targetPython $toolDir
    if (-not $dir) { throw "nanobind was installed into $toolDir but is still not importable." }
    return $dir
}

# ---- build -----------------------------------------------------------------
$cmake = Find-CMake
$py = Find-TargetPython
Write-Host "cmake : $cmake"
Write-Host "python: $py ($(& $py -c 'import sys; print(sys.version.split()[0])'))"

if ($StopEnso) {
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -match "^(run-enso|enso-portable|enso-open-source)" } |
        ForEach-Object { Write-Host "stopping $($_.ProcessName) (pid $($_.Id))"; Stop-Process $_.Id -Force }
    Start-Sleep -Milliseconds 400
}

$build = Join-Path $root "build-msvc"
if ($Configure -or -not (Test-Path "$build\CMakeCache.txt")) {
    $nb = Get-NanobindDir $py (Join-Path $build ".tools")
    # Python_ROOT_DIR is required, not merely a hint: Enso's Python is an
    # embedded distribution with no registry entry, so FindPython can locate
    # the interpreter but not the headers / stable-ABI lib without being told
    # where the install root is.
    $pyRoot = Split-Path -Parent $py
    & $cmake -S $root -B $build -G "Visual Studio 17 2022" -A x64 `
        -DVOICECMD_BUILD_PYTHON=ON -DPython_EXECUTABLE="$py" `
        -DPython_ROOT_DIR="$pyRoot" -Dnanobind_DIR="$nb"
    if ($LASTEXITCODE -ne 0) { throw "cmake configure failed." }
}

$target = if ($Tests) { "voicecmd_tests" } else { "voicecmd" }
& $cmake --build $build --config $Config --target $target
if ($LASTEXITCODE -ne 0) { throw "build failed." }

if ($Tests) {
    & (Join-Path $build "$Config\voicecmd_tests.exe")
    if ($LASTEXITCODE -ne 0) { throw "tests failed." }
} else {
    Write-Host "`nDone. If deploy warned about a locked file, close Enso and re-run (or use -StopEnso)."
}
