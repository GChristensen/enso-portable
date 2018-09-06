## Enso Portable

A portable distribution of the *community* version of Humanized Enso Launcher for Windows with some additional commands

[DOWNLOAD](https://github.com/GChristensen/enso-portable/releases/download/v1.0.10/enso-portable-0.1.10-py27.zip) :: [VIDEO MANUAL](https://youtu.be/QFXBp2vuEEA)

![screen](screen.jpg?raw=true)

Description: the Enso Launcher application allows to launch programs found in the Windows Start menu (or picked manually using the `learn as open' command) and perform many other operations with text command line 
triggered by pressing the CAPSLOCK key. It's possible to create your own commands using Python programming language.

SEE ALSO: [Ubiquity WebExtension](https://github.com/GChristensen/ubichr#readme)

#### History

At first there was a propietary closed-source Enso Launcher from Humanized [[web archive](https://web.archive.org/web/20140701081042/http://humanized.com/)]
(the guys who also created [Ubiquity](https://youtu.be/9hXU1GAm_Qg)). This version was extensible by many programming languages, but someday it went open-source 
and became extensible only by python [[web archive of community enso](https://web.archive.org/web/20110128205130/http://www.ensowiki.com/wiki/index.php?title=Main_Page)].
By some reasons it has also ceased.

#### Notes

* There is no need to hold down the CAPSLOCK key as in the original version (it's only necessary to hit it once, the settings could be adjusted at the enso/config.py file).

* Use the `help' command to get the list of available commands.

* The GIT repository contains only the Enso source code without a Python interpreter, it's more convenient to use the binary package above (which includes a trimmed down Python interpreter) to develop your own commands, so you need only the Notepad to do this.

* To add a new command you need to put a Python file with its source code into the `commands' folder under the Enso root directory (see the [docs](commands.md) on command authoring).

* It's possible to put any custom python code needed to initialize Enso into the file named `.ensorc' under the Enso root folder.

* A color theme may be specified in config.py (e.g. COLOR_THEME="amethyst") 

#### Background

The source code of the original community Enso application could be found here:
[https://launchpad.net/enso/community-enso](https://launchpad.net/enso/community-enso) (also probably orphaned, you can download the full original source without installing bazaar by using [this](https://bazaar.launchpad.net/%7Ecommunityenso/enso/community-enso/tarball/145?start_revid=145) link).

#### Additional functionality not found in the original Enso

* Ability to restart using a tray menu item or the `enso restart' command

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

>>>* kill [process name or id] - kills a process using its executable name
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
>>>* quit lingvo - close Lingvo

>>**mount.py** <font color="red">warning: does not work out of the box, hacking required</font>

>>>A set of shortcuts to [un]mount TrueCrypt volumes:

>>>* truecrypt mount [letter] - mount a truecrypt volume assigned to the specified letter 
>>>* truecrypt umount - unmount all mounted volumes

>>**dd_wrt.py** <font color="red">warning: does not work out of the box, hacking required</font>

>>>A set of dd-wrt shortcut commands (requires terminal access to a [dd-wrt](http://www.dd-wrt.com) router):

>>>* wake slave - send a magic packet to a workstation with MAC address hardcoded in the command file

>>>* switch wireless - turn wireless radio on/off

>>>* wan reconnect - reconnect the ppoe daemon (may be useful to get a new IP from a dynamic pool)

#### Dependencies

* Abbyy Lingvo dictionary software (optional)

#### Known Issues

* The trigger key will not show the command line if Windows Taskbar or Windows Task Manager is under the focus (use the `capslock toggle' command to flip CAPSLOCK state if it's wrong). 
Enso also may spontaneously stuck if some system event that grabs focus is triggered.
* Some AV tools may consider `run-enso.exe' as a potentially unwanted program. These are false-positive claims since the launcher uses API needed to run other programs.

#### Change Log
[full changelog](changelog.txt)

##### 01.09.2018

* Added new color theme (amethyst)
* A color theme may be specified in config.py (e.g. COLOR_THEME="amethyst"), 
see `enso theme' command suggested arguments for the list of available themes

##### 06.09.2018

* Fixed `go' command
* CapsLock key works instantly after start
* Removed resource-consuming currency conversion from calculate command
* Removed web-search commands

#### Contributors

* [Brian Peiris](https://github.com/brianpeiris)
* [thdoan](https://github.com/thdoan)
* [Caleb John](https://github.com/CalebJohn)