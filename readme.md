## Enso Open-Source

A feature-rich descendant of Enso Community Edition (Microsoft Windows only). 

This is a development page. Please visit the main site at: https://gchristensen.github.io/enso-portable/

#### Digitally signing Python binary to make Enso work properly with elevated processes

**Prerequisites**

* Installed [Microsoft Visual Studio](https://visualstudio.microsoft.com) with Windows Platform SDK.
Available for free on [virtual machines](https://developer.microsoft.com/en-us/windows/downloads/virtual-machines/) from Microsoft.

**Signing Python**

1. Install Enso to `C:\Program Files\Enso`
2. Launch Visual Studio Developer Command Prompt *as Administrator*.
3. Change the current directory to where you want to store the copy of the certificate file (appcert.cer).
4. Execute the following command to create a self-issued digital certificate:

`makecert -r -pe -n "CN=Application Certificate - For Use on This Machine Only" -ss PrivateCertStore appcert.cer`

5. Import the certificate to the trusted root store with the following command:

`certmgr.exe -add appcert.cer -s -r localMachine root`

NOTE: if you are signing on a virtual machine, you also need to import the certificate you have created 
to the real machine. If you have no Visual Studio installed, launch the Certificate Manager (certmgr.msc),
open and select `Trusted Root Certificate Authorities/Certificates`, and choose Actions -> All Tasks -> Import... menu item.

6. Issue the command below to sign the Python binary:

`SignTool sign /v /s PrivateCertStore /n "Application Certificate - For Use on This Machine Only" "C:\Program Files\Enso\python\pythonu.exe"`

NOTE: pythonu.exe is a Python binary with the application manifest option `UIAccess` set to `ture`. 
Because Enso is a modeless application, it needs this option to get input when elevated processes are in the foreground.
This version of Python is launched only if it is properly signed and Enso is installed at `C:\Program Files\Enso`. 

#### Bringing the source snapshot back to life

Enso source snapshot does not contain a Python interpreter and can not be run as is. 
If you have Python installed at your system, you may launch Enso by executing
the following command at the repository root: 
<pre>
python enso/scripts/run_enso.py -l INFO
</pre>
You need to place a Python interpreter (with all required dependencies preinstalled)
under /enso/python to use `/enso/debug.bat`, `/enso/run-enso.exe` or `/enso/enso-portable.exe`. 

#### Required dependencies

* [pywin32](https://github.com/mhammond/pywin32)
* [flask](http://flask.pocoo.org/)
* [requests](http://docs.python-requests.org/en/master/)

#### Building platform code

Follow the [platform build instructions](platform/README.win32) and use the makefile 
(compatible with [Mingw](http://www.mingw.org) or [Mingw-w64](https://mingw-w64.org)
mingw32-make) to build and copy binaries to the proper destination. 

#### The original source code

The original source code of **Enso Community Edition** could be found here:
[https://launchpad.net/enso/community-enso](https://launchpad.net/enso/community-enso) (you can download the original source without installing bazaar by using [this](https://bazaar.launchpad.net/%7Ecommunityenso/enso/community-enso/tarball/145?start_revid=145) link).

#### Mediaprobes

Mediaprobes allow to create commands that automatically pass items found in filesystem 
(or listed in a dictionary) to the specified program. Let's assume that you have a directory 
named 'd:/tv-shows', which contains subdirectories: 'columbo', 'the octopus' and 'inspector gadget'.
Let's create a command named 'show' that has the names of all subdirectories under 'd:/tv-shows'
as arguments (the argument will be named "series") and opens the given directory (or file) in 
Media Player Classic.

```python
# place the following into command editor

from enso.user import mediaprobe

cmd_show = mediaprobe.directory_probe("series", "d:/tv-shows", "<absolute path to MPC-HC>")
```
That's all. The command will have the following additional arguments:

    what - lists available arguments.
    next - open the next show in the player.
    prev - open the previous show in the player.
    all - pass 'd:/tv-shows' to the player.

It is possible to create probe commands based on a dictionary:

```python
what_to_watch = {"formula 1": "<a link to my favorite formula 1 stream>",
                 "formula e": "<a link to my favorite formula e stream>"}
cmd_watch = mediaprobe.dictionary_probe("stream", what_to_watch, "<absolute path to my network player>")
```

If player does not accept directories (as, for example, ACD See does), it is possible to pass a first file in the directory specified at a dictionary:

```python
what_to_stare_at = {'nature': 'd:/images/nature',
                    'cosmos': 'd:/images/cosmos'}

# if player is not specified, the command will use the default system application 
# associated with the encountered file type
cmd_stare = mediaprobe.findfirst_probe("at", what_to_stare_at)
```

Of course, you may construct dictionaries in various ways.

#### Change log
[full changelog](changelog.md)

##### 24.12.2021 (v.0.9.0)

* Added experimental support of internationalized command input. Non-latin characters such as спасибо are allowed when
  the current input language is not English. Set LOCALIZED_INPUT = False in the settings configuration block to disable
  this feature. Due to limitations of Windows, it will not work when a console window is in the foreground. Deadkeys are
  not supported.

#### Contributors

* [Brian Peiris](https://github.com/brianpeiris)
* [thdoan](https://github.com/thdoan)
* [Caleb John](https://github.com/CalebJohn)
* [Mark Wiseman](https://github.com/mawiseman)