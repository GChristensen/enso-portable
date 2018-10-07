## Enso open-source

A feature-rich descendant of Enso Community Edition (win32). 

This is a development page. Please visit the main site at: https://gchristensen.github.io/enso-portable/


![screen](screen.jpg?raw=true)

SEE ALSO: [Ubiquity WebExtension](https://github.com/GChristensen/ubiquitywe#readme)

Enso Launcher allows to launch programs found in the Windows Start menu (or picked manually using the 
`learn as open' command) and perform many other operations with a text command line 
triggered by the CAPSLOCK key. It's possible to create your own commands using Python 
programming language.

Find more information on command authoring in the tutorial available at Enso settings pages
(use the tray menu or 'enso settings' command to reach them).


#### History

At first there was a propietary closed-source Enso Launcher from Humanized [[web archive](https://web.archive.org/web/20140701081042/http://humanized.com/)]
(the guys who also created Ubiquity). This version was extensible by many programming languages, but someday it went open
([Enso Community Edition](https://web.archive.org/web/20110128205130/http://www.ensowiki.com/wiki/index.php?title=Main_Page)) and became extensible only by python.
By some reasons it has also ceased.

At the moment <b>Enso open-source</b> is the most feature-rich descendant of <b>Enso Community Edition</b>.

#### Notes

* There is no need to hold down the CAPSLOCK key as in the original version (it's only necessary to hit it once.

* Use `help' command to get the list of all available commands.

#### Background

The original source code of **Enso Community Edition** could be found here:
[https://launchpad.net/enso/community-enso](https://launchpad.net/enso/community-enso) (you can download the full original source without installing bazaar by using [this](https://bazaar.launchpad.net/%7Ecommunityenso/enso/community-enso/tarball/145?start_revid=145) link).

#### Additional functionality not found in the original Enso

* Python 3 support.
* Option pages with built-in command editor.
* Ability to disable commands.
* It is possible to execute user-supplied code in a separate thread on Enso start (useful for scheduling).
* Mediaprobes.
* Ability to restart using tray menu or 'enso restart' command.
* [Enso Retreat](https://gchristensen.github.io/retreat) - a work regime control utility. 

#### Known Issues

* The trigger key will not show the command line if any privileged (adminstrator) process is under the focus (use the `capslock toggle' command to flip CAPSLOCK state if it's wrong). 
Enso also may spontaneously stuck if some system event that grabs input is triggered.
* &#x1F534; Some security tools may consider `run-enso.exe' as a potentially unwanted program. These are false-positive claims since the launcher uses API needed to run other programs.


#### Change Log
[full changelog](changelog.md)

##### 07.09.2018 (v.0.4.0)

* Added UbiquityWE-styled settings pages.
* Added ability to disable separate commands.
* Added 'Tasks' feature.
* The most actual information on command authoring is moved to the tutorial at Enso settings. 

#### Contributors

* [Brian Peiris](https://github.com/brianpeiris)
* [thdoan](https://github.com/thdoan)
* [Caleb John](https://github.com/CalebJohn)