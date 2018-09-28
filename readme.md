## Enso Portable

A portable distribution of the *community* version of Humanized Enso Launcher for Windows with some additional commands.

![Windows](https://github.com/GChristensen/gchristensen.github.io/blob/master/windows.png?raw=true)
[v0.2.1 (Python 3.7, Win7+)](https://github.com/GChristensen/enso-portable/releases/download/v0.2.1/enso-portable-0.2.1-py37.zip)
:: ![Windows](https://github.com/GChristensen/gchristensen.github.io/blob/master/windows.png?raw=true)
[v0.1.11 (Python 2.7, WinXP+)](https://github.com/GChristensen/enso-portable/releases/download/v0.2.0/enso-portable-0.1.11-py27.zip) 
::&nbsp;![Youtube](https://github.com/GChristensen/gchristensen.github.io/blob/master/youtube.png?raw=true)&nbsp;[Video Manual](https://youtu.be/QFXBp2vuEEA)


![screen](screen.jpg?raw=true)

SEE ALSO: [Ubiquity WebExtension](https://github.com/GChristensen/ubichr#readme)

Enso Launcher allows to launch programs found in the Windows Start menu (or picked manually using the 
`learn as open' command) and perform many other operations with text command line 
triggered by the CAPSLOCK key. It's possible to [create](commands.md) your own commands using Python 
programming language.


#### History

At first there was a propietary closed-source Enso Launcher from Humanized [[web archive](https://web.archive.org/web/20140701081042/http://humanized.com/)]
(the guys who also created Ubiquity). This version was extensible by many programming languages, but someday it went open-source 
and became extensible only by python [[web archive of community enso](https://web.archive.org/web/20110128205130/http://www.ensowiki.com/wiki/index.php?title=Main_Page)].
By some reasons it has also ceased.

#### Notes

* There is no need to hold down the CAPSLOCK key as in the original version (it's only necessary to hit it once, the settings could be adjusted at the enso/config.py file).

* Use `help' command to get the list of available commands.


* It is possible to put any custom Python code needed to initialize Enso into the file named '.ensorc' under your HOME folder (issue `enso userhome' command to find what is it).
Use '--portable' option of run-enso.exe (for example, from a Windows shortcut) to set Enso distribution directory as the HOME home directory.

* To add a new command you need to put a Python file with its source code into the `commands' folder under the Enso root directory (see the [docs](commands.md) on command authoring). 
You also can place Python commands at '~/.ensocommands' file ('.ensocommands' file located at the HOME directory).

* A color theme may be specified in '~/.ensorc' (e.g. COLOR_THEME="amethyst").
 
* Any variables you declare in '~/.ensorc' file are added to the `config' module, so you can access them in your commands later (e.g. config.MY_VARIABLE).

* Install necessary Python packages with the `enso install &lt;package name&gt;' command. 

#### Mediaprobes

Mediaprobes allow to create commands that automatically pass items found in the filesystem (or specified
in a dictionary) to a media player, which may be useful, for example, at a media-center. Let's assume that
you have a directory named 'd:/tv-shows', which contains subdirectories named: 'columbo', 'the octopus', 'inspector gadget'. Let's create a command named 'show' that will have the names of all subdirectories
under 'd:/tv-shows' as arguments ("name" in the code below) and open selected directory in Media Player Classic. 

```python
# contents of ~/.ensocommands

from enso.user import mediaprobe

cmd_show = mediaprobe.directory_probe("name", "d:/tv-shows", "<absolute path to MPC-HC>")
```

That is all. The command will have the following additional arguments:
* what - lists available arguments.
* next - open the next show in the player.
* prev - open the previous show in the player. 
* all - pass 'd:/tv-shows' to the player.

It is possible to create media commands based on a dictionary:

```python
what_to_watch = {"formula 1": "<a link to my favorite formula 1 stream>",
                 "formula e": "<a link to my favorite formula e stream>"}
cmd_watch = mediaprobe.dictionary_probe("name", what_to_watch, "<absolute path to my network player>")
```

If player does not accept directories (as, for example, ACD See), it is possible to pass a first file in the directory specified at
a dictionary:

```
what_to_stare_at = {'nature': 'd:/images/nature',
                    'cosmos': 'd:/images/cosmos'}
                    
# if player is not specified, the command will use the default system application 
# associated with the encountered file type
cmd_stare = mediaprobe.findfirst_probe("at", what_to_stare_at)
```

Remember, that you may construct dictionaries by various ways.

#### Background

Source code of the original community Enso application could be found here:
[https://launchpad.net/enso/community-enso](https://launchpad.net/enso/community-enso) (you can download the full original source without installing bazaar by using [this](https://bazaar.launchpad.net/%7Ecommunityenso/enso/community-enso/tarball/145?start_revid=145) link).

#### Additional functionality not found in the original Enso

* Mediaprobes.
* Python 3 support.
* Ability to restart using a tray menu item or `enso restart' command.

#### Known Issues

* The trigger key will not show the command line if any privileged (adminstrator) process is under the focus (use the `capslock toggle' command to flip CAPSLOCK state if it's wrong). 
Enso also may spontaneously stuck if some system event that grabs input is triggered.
* &#x1F534; Some security tools may consider `run-enso.exe' as a potentially unwanted program. These are false-positive claims since the launcher uses API needed to run other programs.

#### Additional Commands 

>>**enso.py**

>>>Enso-related commands:

>>>* capslock toggle - toggle CAPSLOCK state.
>>>* enso userhome - get user home directory used by Enso.
>>>* enso install - install a python package.
>>>* enso restart - restart enso.
>>>* enso theme - preview color themes.

>>**mpc.py** 

>>>Control Media Player Classic with Enso.

>>> IMPORTANT: Web Interface should be enabled in MPC settings.

>>>* mpc - send a command to MPC. Based on [mpcapi](https://github.com/Grokzen/mpcapi/). Due to the vast
list of arguments 'mpc' command should be enabled before the first usage by issuing `mpc enable'.
May be enabled by default if MPC_ENABLED=True is set in ~/.ensorc file.


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

>>**dd_wrt.py**

>>>A set of dd-wrt shortcut commands (requires terminal access to a [dd-wrt](http://www.dd-wrt.com) router):

>>>Requires the following variables in '~/.ensorc':

>>>>DD_WRT_HOST = ... #default: "192.168.1.1"

>>>>DD_WRT_USER = ... #default: "root"

>>>>DD_WRT_PASSWORD = "my_dd_wrt_password"

>>>* wake - send a magic packet to a workstation with the specified MAC Address. 
Configured by DD_WRT_MACHINES in '~/.ensorc', for example:

>>>>DD_WRT_MACHINES = {'shell': "AA:BB:CC:DD:EE:FF"}

>>>* switch wireless - turn wireless radio on/off

>>>* wan reconnect - reconnect the ppoe daemon (may be useful to get a new IP from a dynamic pool)


#### Change Log
[full changelog](changelog.md)

##### 24.09.2018 (v.0.2.0)

* Migrated to Python 3.7
* Added `enso userhome' command
* Added `enso install' command
* Learn as open commands moved to `~/.enso/learned-commands'
* `--portable' launcher command line option added

##### 28.09.2018 (v.0.2.1)

* Added `mpc' command (send commands to Media Player Classic). See the command description above for details.
* Added mediaprobes.
* DD-WRT configuration has changed.
* Removed mount.py.
* Fixed `enso restart' command.

#### Contributors

* [Brian Peiris](https://github.com/brianpeiris)
* [thdoan](https://github.com/thdoan)
* [Caleb John](https://github.com/CalebJohn)