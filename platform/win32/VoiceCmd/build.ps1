# Rebuild + deploy the voicecmd native module (voicecmd.pyd) into Enso's contrib.
#
# Usage (from this directory):
#   .\build.ps1                 # incremental build of the module + auto-deploy
#   .\build.ps1 -Configure      # re-run cmake configure first (after CMakeLists edits)
#   .\build.ps1 -StopEnso       # close a running Enso first so the .pyd isn't locked
#   .\build.ps1 -Config Debug   # build the Debug config instead of Release
#
# NOTE: the deploy step copies voicecmd.pyd into ..\..\..\enso\enso\contrib. A
# running Enso holds that file open, so either close Enso or pass -StopEnso; the
# build itself still succeeds (the deploy just warns) if it's locked.
param(
    [switch]$Configure,
    [switch]$StopEnso,
    [string]$Config = "Release"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Locate the VS-bundled CMake (cmake is not on PATH here); fall back to PATH.
$cmake = "C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
if (-not (Test-Path $cmake)) {
    $cmake = (Get-Command cmake -ErrorAction SilentlyContinue).Source
    if (-not $cmake) { throw "cmake not found; set the path in build.ps1" }
}

# Python that owns nanobind (the build links against its stable-ABI Python).
$py = "D:\software\dev\python\python.exe"

if ($StopEnso) {
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -match "^(run-enso|enso-portable|enso-open-source)" } |
        ForEach-Object { Write-Host "stopping $($_.ProcessName) (pid $($_.Id))"; Stop-Process $_.Id -Force }
    Start-Sleep -Milliseconds 400
}

if ($Configure -or -not (Test-Path "$root\build-msvc\CMakeCache.txt")) {
    $nb = & $py -c "import nanobind; print(nanobind.cmake_dir())"
    & $cmake -S $root -B "$root\build-msvc" -G "Visual Studio 17 2022" -A x64 `
        -DVOICECMD_BUILD_PYTHON=ON -DPython_EXECUTABLE="$py" -Dnanobind_DIR="$nb"
}

& $cmake --build "$root\build-msvc" --config $Config --target voicecmd
Write-Host "`nDone. If deploy warned about a locked file, close Enso and re-run (or use -StopEnso)."
