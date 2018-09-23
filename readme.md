## Enso Portable

A portable distribution of the *community* version of Humanized Enso Launcher for Windows with some additional commands.

[DOWNLOAD v0.2.0 (Python 3.7)](https://github.com/GChristensen/enso-portable/releases/download/v1.0.11/enso-portable-0.1.11-py27.zip) :: [VIDEO MANUAL](https://youtu.be/QFXBp2vuEEA)

[DOWNLOAD v0.1.11 (Python 2.7, WinXP support)](https://github.com/GChristensen/enso-portable/releases/download/v1.0.11/enso-portable-0.1.11-py27.zip)

![screen](screen.jpg?raw=true)

SEE ALSO: [Ubiquity WebExtension](https://github.com/GChristensen/ubichr#readme)

Enso Launcher allows to launch programs found in the Windows Start menu (or picked manually using the `learn as open' command) and perform many other operations with text command line 
triggered by the CAPSLOCK key. It's possible to [create](commands.md) your own commands using Python programming language.


#### History

At first there was a propietary closed-source Enso Launcher from Humanized [[web archive](https://web.archive.org/web/20140701081042/http://humanized.com/)]
(the guys who also created Ubiquity). This version was extensible by many programming languages, but someday it went open-source 
and became extensible only by python [[web archive of community enso](https://web.archive.org/web/20110128205130/http://www.ensowiki.com/wiki/index.php?title=Main_Page)].
By some reasons it has also ceased.

#### Notes

* There is no need to hold down the CAPSLOCK key as in the original version (it's only necessary to hit it once, the settings could be adjusted at the enso/config.py file).

* Use the `help' command to get the list of available commands.

* The GIT repository contains only the Enso source code without a Python interpreter, it's more convenient to use the binary package above (which includes a portable Python interpreter) to develop your own commands, so you need only the Notepad to do this.

* It's possible to put any custom Python code needed to initialize Enso into the file named '.ensorc' under your HOME folder (issue `enso userhome' command to find what is it).
Use '--portable' option of run-enso.exe (for example, from a Windows Shortcut) to set Enso distribution directory as Enso home directory.

* To add a new command you need to put a Python file with its source code into the `commands' folder under the Enso root directory (see the [docs](commands.md) on command authoring). 
You also can place Python command code at '~/.ensocommands' file.

* A color theme may be specified in config.py or .ensorc (e.g. COLOR_THEME="amethyst").
 
* Any variables you declare in .ensorc file are added to the `config' module, so you can access them in your commands later (e.g. config.MY_VARIABLE).

* Install necessary Python packages with the `enso install &lt;package name&gt;' command. 

#### Background

The source code of the original community Enso application could be found here:
[https://launchpad.net/enso/community-enso](https://launchpad.net/enso/community-enso) (you can download the full original source without installing bazaar by using [this](https://bazaar.launchpad.net/%7Ecommunityenso/enso/community-enso/tarball/145?start_revid=145) link).

#### Additional functionality not found in the original Enso

* Ability to restart using a tray menu item or the `enso restart' command

#### Known Issues

* The trigger key will not show the command line if any privileged (adminstrator) process is under the focus (use the `capslock toggle' command to flip CAPSLOCK state if it's wrong). 
Enso also may spontaneously stuck if some system event that grabs input is triggered.
* &#x1F534; Some security tools may consider `run-enso.exe' as a potentially unwanted program. These are false-positive claims since the launcher uses API needed to run other programs.

#### Additional Commands 

>>**enso.py**

>>>Toggle CAPSLOCK state:

>>>* capslock toggle

>>**session.py**

>>>Session/Power management commands (self explanatory):
      
>>>* log off
>>>* shut down
>>>* reboot
>>>* suspend
>>>* hibernate

>>**system.py**

>>>System commands:

>>>* terminate [process name or id] - terminates a process using its executable name
                                   (without extension) or id

>>**dial.py**

>>>Dial-up network related commands:
  
>>>* dial [connection name] - connect to the Internet using a dialup connection
>>>* hangup [connection name] - close an Internet connection

>>**idgen.py**

>>>Generate a UUID in several formats (upper/lower case, numeric):

>>>* guid [format]

>>>Generate a random number in the Int32 positive range [0, 2147483646].
    It's possible to narrow the range using command arguments:

>>>* random [from num to num]

>>**retreat.py**

>>>Delay or skip [Angelic Retreat](http://retreat.sourceforge.net) breaks:

>>>* delay break
>>>* skip break

>>**lingvo.py**

>>>Control Abbyy Lingvo dictionary software with Enso Launcher. It's possible to specify translation direction attributes, see command help for the details.
     
>>>* lingvo [word from lang to lang] - translate a word

>>**mount.py** <font color="red">warning: does not work out of the box, see the command file for details</font>

>>>A set of shortcuts to [un]mount TrueCrypt volumes:

>>>* truecrypt mount [letter] - mount a truecrypt volume assigned to the specified letter 
>>>* truecrypt umount - unmount all mounted volumes

>>**dd_wrt.py** <font color="red">warning: does not work out of the box, see the command file for details</font>

>>>A set of dd-wrt shortcut commands (requires terminal access to a [dd-wrt](http://www.dd-wrt.com) router):

>>>* wake slave - send a magic packet to a workstation with MAC address hardcoded in the command file

>>>* switch wireless - turn wireless radio on/off

>>>* wan reconnect - reconnect the ppoe daemon (may be useful to get a new IP from a dynamic pool)

#### Change Log
[full changelog](changelog.txt)

##### 24.09.2018 (v.0.2.0)

* Migrated to Python 3.7
* Added `enso userhome' command
* Added `enso install' command
* Learn as open commands moved to `~/.enso/learned-commands'
* `--portable' launcher command line option added

#### Contributors

* [Brian Peiris](https://github.com/brianpeiris)
* [thdoan](https://github.com/thdoan)
* [Caleb John](https://github.com/CalebJohn)