<#
.SYNOPSIS
    Sign an executable with a single-use self-signed certificate so it can
    obtain UIAccess, then destroy the signing key.

.DESCRIPTION
    Windows grants UIAccess -- the ability to draw above elevated windows such
    as Task Manager -- only when all three of these hold:

      1. the binary carries a valid Authenticode signature whose chain
         terminates in a root this machine trusts,
      2. the binary sits in a secure location (%ProgramFiles% or System32),
      3. its embedded manifest declares uiAccess="true".

    This script provides (1) without a commercial certificate. It generates a
    code-signing certificate, signs the target, installs the *public* half as a
    trust anchor, and then deletes the private key.

    The key is generated here, used once, and destroyed, so nothing that could
    sign new code survives. The trust anchor left in the Root store is inert:
    no key exists that can issue anything it would vouch for. That is the whole
    point of the design -- do not "simplify" it by reusing a stored key.

    The certificate must REMAIN in the Root store afterwards. Authenticode
    revalidates the chain on every process launch, so removing it silently
    revokes UIAccess. Use -Remove only when uninstalling.

    Requires administrator: writing to the machine Root store and to
    %ProgramFiles% both demand it. Needs no Windows SDK -- everything here is
    in-box PowerShell.

.PARAMETER Path
    Executables to sign. Defaults to the installed pythonu.exe.

.PARAMETER Years
    Certificate lifetime. Deliberately long: an expired certificate makes the
    signature invalid, which silently revokes UIAccess. The usual reason to
    keep certificates short-lived is limiting exposure if the key leaks, and
    that cannot happen here because the key is destroyed before this script
    returns.

.PARAMETER TimestampServer
    Optional RFC3161 server. Unnecessary given the long lifetime above, and it
    makes signing depend on network reachability, so it is off by default.

.PARAMETER Force
    Re-sign even if the target already carries a valid signature.

.PARAMETER List
    Show trust anchors this script has previously installed.

.PARAMETER Remove
    Remove a previously installed trust anchor. This revokes UIAccess for
    anything signed with it.

.EXAMPLE
    .\sign-uiaccess.ps1
    Sign the installed pythonu.exe and install the trust anchor.

.EXAMPLE
    .\sign-uiaccess.ps1 -Path 'C:\Program Files\Enso Launcher\python\pythonu.exe' -Verbose

.EXAMPLE
    .\sign-uiaccess.ps1 -List

.EXAMPLE
    .\sign-uiaccess.ps1 -Remove -Thumbprint ABC123...
#>

[CmdletBinding(SupportsShouldProcess = $true, DefaultParameterSetName = 'Sign')]
param(
    [Parameter(ParameterSetName = 'Sign', Position = 0)]
    [string[]] $Path = @("$env:ProgramFiles\Enso Launcher\python\pythonu.exe"),

    [Parameter(ParameterSetName = 'Sign')]
    [string] $Subject = 'CN=Enso Launcher UIAccess (self-signed, single use)',

    [Parameter(ParameterSetName = 'Sign')]
    [ValidateRange(1, 100)]
    [int] $Years = 30,

    [Parameter(ParameterSetName = 'Sign')]
    [string] $TimestampServer,

    [Parameter(ParameterSetName = 'Sign')]
    [switch] $Force,

    [Parameter(ParameterSetName = 'List', Mandatory = $true)]
    [switch] $List,

    [Parameter(ParameterSetName = 'Remove', Mandatory = $true)]
    [switch] $Remove,

    [Parameter(ParameterSetName = 'Remove')]
    [string] $Thumbprint
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Marks the certificates this script owns, so -List and -Remove can find them
# again without the caller having recorded a thumbprint.
$MARKER = 'Enso Launcher UIAccess'

# Stores the anchor goes into. Root satisfies the chain requirement;
# TrustedPublisher suppresses the "unknown publisher" prompt for the same
# signature elsewhere in Windows.
$ANCHOR_STORES = @('Root', 'TrustedPublisher')


function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-PublicOnly {
    # A copy carrying no private key, which is all a trust anchor needs. The
    # unary comma keeps PowerShell from splatting the byte array across the
    # constructor's parameters.
    param([Security.Cryptography.X509Certificates.X509Certificate2] $Certificate)
    return New-Object Security.Cryptography.X509Certificates.X509Certificate2 (, $Certificate.RawData)
}

function Add-Anchor {
    param([Security.Cryptography.X509Certificates.X509Certificate2] $Certificate)

    $public = Get-PublicOnly -Certificate $Certificate
    foreach ($name in $ANCHOR_STORES) {
        $store = New-Object Security.Cryptography.X509Certificates.X509Store($name, 'LocalMachine')
        $store.Open('ReadWrite')
        try {
            $store.Add($public)
            Write-Verbose "Installed anchor into LocalMachine\$name."
        }
        finally {
            $store.Close()
        }
    }
}

function Get-Anchors {
    $found = @()
    foreach ($name in $ANCHOR_STORES) {
        $store = New-Object Security.Cryptography.X509Certificates.X509Store($name, 'LocalMachine')
        $store.Open('ReadOnly')
        try {
            foreach ($c in $store.Certificates) {
                if ($c.Subject -like "*$MARKER*") {
                    $found += [pscustomobject]@{
                        Store      = $name
                        Thumbprint = $c.Thumbprint
                        Subject    = $c.Subject
                        NotAfter   = $c.NotAfter
                    }
                }
            }
        }
        finally {
            $store.Close()
        }
    }
    return $found
}

function Remove-Anchor {
    param([string] $CertThumbprint)

    $removed = 0
    foreach ($name in $ANCHOR_STORES) {
        $store = New-Object Security.Cryptography.X509Certificates.X509Store($name, 'LocalMachine')
        $store.Open('ReadWrite')
        try {
            foreach ($c in @($store.Certificates)) {
                $matchesThumb = $CertThumbprint -and ($c.Thumbprint -eq $CertThumbprint)
                $matchesMark = (-not $CertThumbprint) -and ($c.Subject -like "*$MARKER*")
                if ($matchesThumb -or $matchesMark) {
                    if ($PSCmdlet.ShouldProcess("LocalMachine\$name\$($c.Thumbprint)", 'Remove certificate')) {
                        $store.Remove($c)
                        $removed++
                        Write-Verbose "Removed $($c.Thumbprint) from LocalMachine\$name."
                    }
                }
            }
        }
        finally {
            $store.Close()
        }
    }
    return $removed
}

function Remove-SigningKey {
    # Deleting an exported .pfx does NOT destroy the key -- the material lives
    # in the store (and under %ProgramData%\Microsoft\Crypto). Removing the
    # certificate from LocalMachine\My is what actually takes the private key
    # with it. Getting this wrong leaves a live signing key on a machine that
    # now trusts it, which is worse than not running this script at all.
    param([string] $CertThumbprint)

    $store = New-Object Security.Cryptography.X509Certificates.X509Store('My', 'LocalMachine')
    $store.Open('ReadWrite')
    try {
        foreach ($c in @($store.Certificates)) {
            if ($c.Thumbprint -eq $CertThumbprint) {
                $store.Remove($c)
                Write-Verbose "Removed signing key $CertThumbprint from LocalMachine\My."
            }
        }
    }
    finally {
        $store.Close()
    }

    # Confirm, rather than trust that the removal worked.
    $store = New-Object Security.Cryptography.X509Certificates.X509Store('My', 'LocalMachine')
    $store.Open('ReadOnly')
    try {
        foreach ($c in $store.Certificates) {
            if ($c.Thumbprint -eq $CertThumbprint) {
                throw ("The signing key $CertThumbprint is STILL PRESENT in " +
                       "LocalMachine\My. Remove it by hand before using this " +
                       "machine further: a usable key plus an installed trust " +
                       "anchor lets any administrator sign trusted code.")
            }
        }
    }
    finally {
        $store.Close()
    }
}

function Test-SecureLocation {
    param([string] $File)

    $secure = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, "$env:SystemRoot\System32") |
        Where-Object { $_ }
    $full = [IO.Path]::GetFullPath($File)
    foreach ($dir in $secure) {
        if ($full.StartsWith(([IO.Path]::GetFullPath($dir) + [IO.Path]::DirectorySeparatorChar),
                             [StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Test-UIAccessManifest {
    # Crude but useful: the embedded manifest is plain XML inside the PE, so
    # the attribute is findable without SDK tooling. Only ever a warning --
    # a false negative here should not block signing.
    param([string] $File)

    try {
        $bytes = [IO.File]::ReadAllBytes($File)
        $text = [Text.Encoding]::ASCII.GetString($bytes)
        return $text -match 'uiAccess\s*=\s*"true"'
    }
    catch {
        Write-Verbose "Could not scan manifest of ${File}: $_"
        return $true   # unknown: do not warn
    }
}


# --------------------------------------------------------------------- main

if ($PSCmdlet.ParameterSetName -eq 'List') {
    $anchors = Get-Anchors
    if (-not $anchors) {
        Write-Host 'No UIAccess trust anchors installed by this script.'
    }
    else {
        $anchors | Format-Table -AutoSize
        Write-Host 'These are inert: the keys that could sign for them were destroyed.'
    }
    return
}

if (-not (Test-Admin)) {
    throw ('Administrator required: this writes to the machine certificate ' +
           'store and to %ProgramFiles%. Re-run from an elevated prompt.')
}

if ($PSCmdlet.ParameterSetName -eq 'Remove') {
    $count = Remove-Anchor -CertThumbprint $Thumbprint
    Write-Host "Removed $count certificate(s)."
    Write-Warning ('Anything signed against this anchor has lost UIAccess. ' +
                   'Windows revalidates the chain on every launch, so the ' +
                   'change takes effect the next time the program starts.')
    return
}

# ---- Sign

foreach ($file in $Path) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Not found: $file"
    }
}

$targets = @()
foreach ($file in $Path) {
    $full = (Resolve-Path -LiteralPath $file).Path

    if (-not $Force) {
        $existing = Get-AuthenticodeSignature -LiteralPath $full
        if ($existing.Status -eq 'Valid') {
            Write-Host "Already validly signed, skipping: $full"
            Write-Host '  (use -Force to re-sign)'
            continue
        }
    }

    if (-not (Test-SecureLocation -File $full)) {
        Write-Warning ("$full is not under %ProgramFiles% or System32. " +
                       'Windows will refuse UIAccess regardless of the ' +
                       'signature. Signing anyway.')
    }

    if (-not (Test-UIAccessManifest -File $full)) {
        Write-Warning ("$full does not appear to declare uiAccess=`"true`" in " +
                       'its manifest. Signing is necessary but not sufficient ' +
                       '-- without the manifest the overlay still will not ' +
                       'appear above elevated windows.')
    }

    $targets += $full
}

if (-not $targets) {
    Write-Host 'Nothing to do.'
    return
}

if (-not $PSCmdlet.ShouldProcess(($targets -join ', '), 'Sign with a single-use certificate')) {
    return
}

Write-Host "Generating single-use code-signing certificate ($Years year lifetime)..."
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject $Subject `
    -CertStoreLocation 'Cert:\LocalMachine\My' `
    -KeyExportPolicy NonExportable `
    -KeyUsage DigitalSignature `
    -HashAlgorithm SHA256 `
    -NotAfter (Get-Date).AddYears($Years)

Write-Host "  thumbprint: $($cert.Thumbprint)"

# From here the key exists on disk, so every path out of this block must
# destroy it -- including failures. Hence try/finally rather than tidy-up at
# the end.
try {
    # The anchor must be in place before verification, or the chain has
    # nowhere to terminate and every signature reads as untrusted.
    Add-Anchor -Certificate $cert

    foreach ($file in $targets) {
        Write-Host "Signing $file"

        $signArgs = @{
            LiteralPath   = $file
            Certificate   = $cert
            HashAlgorithm = 'SHA256'
        }
        if ($TimestampServer) {
            $signArgs['TimestampServer'] = $TimestampServer
        }

        $result = Set-AuthenticodeSignature @signArgs
        if ($result.Status -ne 'Valid') {
            throw "Signing failed for ${file}: $($result.Status) - $($result.StatusMessage)"
        }
    }
}
finally {
    Write-Host 'Destroying signing key...'
    Remove-SigningKey -CertThumbprint $cert.Thumbprint
}

# Verify against the real trust chain, after the key is gone, which is the
# state the machine will actually be in at launch time.
$failed = @()
foreach ($file in $targets) {
    $sig = Get-AuthenticodeSignature -LiteralPath $file
    if ($sig.Status -eq 'Valid') {
        Write-Host "  verified: $file"
    }
    else {
        Write-Warning "  NOT valid: $file -> $($sig.Status) - $($sig.StatusMessage)"
        $failed += $file
    }
}

if ($failed) {
    throw "Signature verification failed for: $($failed -join ', ')"
}

Write-Host ''
Write-Host 'Done. The signing key no longer exists; the trust anchor remains.'
Write-Host "Anchor thumbprint: $($cert.Thumbprint)"
Write-Host 'Remove it on uninstall with:'
Write-Host "  .\sign-uiaccess.ps1 -Remove -Thumbprint $($cert.Thumbprint)"
Write-Host ''
Write-Host 'Restart the signed program for Windows to re-evaluate UIAccess.'