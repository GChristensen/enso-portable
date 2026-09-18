# Digitally signing the Python binary to make Enso work properly with elevated processes

TL;DR

1. Install into `C:\Program Files\Enso Launcher`.
2. Execute Run [`tools/sign-uiaccess.ps1`](tools/sign-uiaccess.ps1) from an **elevated** PowerShell prompt.

Currently, this is done by an installer check. Read below only if you need the theory behind.

Because Enso has no traditional input components, it needs Windows **UIAccess** to receive input while an
elevated process is in the foreground (e.g. Windows Task Manager). `pythonu.exe` is a Python binary whose application manifest
sets `uiAccess="true"`, and Enso launches it in place of the regular interpreter - but only when
Windows actually grants UIAccess, which requires all three of the following:

1. The binary carries a valid digital signature that chains to a certificate this machine trusts.
2. The binary sits in a **secure location** - a directory only an administrator can write to.
3. Its manifest declares `uiAccess="true"` (already the case for the bundled `pythonu.exe`).

Point 2 is why **Enso must be installed to `C:\Program Files`** for this to work. The default
installation directory is under `%APPDATA%`, which is user-writable, and Windows refuses UIAccess
to a binary there no matter how it is signed. Install to `C:\Program Files` first; signing an
`%APPDATA%` installation has no effect.

**Signing**

Run [`tools/sign-uiaccess.ps1`](tools/sign-uiaccess.ps1) from an **elevated** PowerShell prompt:

```powershell
.\tools\sign-uiaccess.ps1
```

That is the whole procedure. The script creates a single-use self-issued code-signing certificate,
signs `C:\Program Files\Enso Launcher\python\pythonu.exe`, installs the certificate's public half
as a trust anchor, and then destroys the private key - so no key remains that could sign anything
else against that anchor. Restart Enso afterwards so Windows re-evaluates UIAccess.

Pass `-Path` to sign an executable elsewhere, `-Force` to re-sign one that is already signed, and
`-Verbose` to see each step. The script warns if the target is outside a secure location or appears
to lack the `uiAccess` manifest, since neither can be fixed by signing.

The certificate is added to the local **Trusted Root** store and must remain there: Windows
revalidates the signature every time the process starts, so removing it silently revokes UIAccess.
