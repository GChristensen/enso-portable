##### 14.07.2022 (v.0.9.1)

* Sped up `learn as open` and `unlearn as open` commands.
* Fixed delayed Shift key state when localized input is enabled.
* Fixed web-search commands.

##### 24.12.2021 (v.0.9.0)
* Added experimental support of internationalized command input. Non-latin characters such as спасибо are allowed when
  the current input language is not English. Set LOCALIZED_INPUT = False in the settings configuration block to disable
  this feature. Due to limitations of Windows, it will not work when a console window is in the foreground. Deadkeys are
  not supported.

##### 06.10.2021 (v.0.8.0)
* Migrated to Python 3.10.

##### 22.06.2021 (v.0.7.0)
* Migrated to x86_64 platform, which allows to bypass some shortcut-related operating system bugs inherent 
  to 32-bit applications on 64-bit Windows. v0.6.1 is the last 32-bit version of the application.
* Updated Enso Retreat to version 0.6.
* Enso now can properly work with elevated processes when digitally signed. See the readme file for more details.

##### 20.10.2020 (v.0.6.1)
* Fixed opening of .URL shortcuts.

##### 07.10.2020 (v.0.6.0)
* Migrated to Python 3.9.

##### 06.08.2020 (v.0.5.1)
* Fixed invalid shortcut path variable bug on Windows 10.

##### 15.10.2019 (v.0.5.0)
* Migrated to Python 3.8
* Updated Cairo graphics library to the recent version (1.16.0)
* Dropped support of "~/.ensocommands" file

##### 11.10.2019 (v.0.4.6)
* Fixed command editor undo history.

##### 24.08.2019 (v.0.4.5)
* Optimized 'open' command shortcut reloading (should seed up command editing/testing cycle).
* Added 'enso refresh' command option.

##### 21.08.2019 (v.0.4.4)

* Fixed Google command.
* Improved quasimode performance through smart command change tracking.

##### 14.03.2019 (v.0.4.3)

* Added UWP application support (based on the commit by Mark Wiseman).
* Added some common initialization variables to settings page configuration block.

##### 13.09.2018 (v.0.4.2)

* Added APPEAR_OVER_TASKBAR custom initialization option.

##### 09.09.2018 (v.0.4.1)

* Restored web search commands.

##### 07.09.2018 (v.0.4.0)

* Added UbiquityWE-styled settings pages.
* Added ability to disable separate commands.
* Added 'Tasks' feature.
* The most actual information on command authoring is moved to the tutorial at the Enso settings page. 

##### 04.09.2018 (v.0.3.0)

* Angelic Retreat is now Enso Retreat (an optional Enso module).
* Added installer which allows to selectively install only necessary packages of commands.

##### 28.09.2018 (v.0.2.1)

* Added `mpc' command (send commands to Media Player Classic). See the command description for details.
* Added mediaprobes.
* DD-WRT configuration has changed.
* Removed mount.py.
* Fixed `enso restart' command.

##### 24.09.2018 (v.0.2.0)

* Migrated to Python 3.7
* Added `enso userhome' command
* Added `enso install' command
* 'kill' command is renamed to 'terminate'
* Learn as open commands moved to `~/.enso/learned-commands'

##### 06.09.2018

* Fixed `go' command
* CapsLock key works instantly after start
* Removed resource-consuming currency conversion from the calculate command
* Removed web-search commands

##### 01.09.2018

* Added new color theme (amethyst)
* A color theme may be specified in config.py (e.g. COLOR_THEME="amethyst"),
see `enso theme' command suggested arguments for the list of available themes

##### 21.07.2017

* Added .ensorc support
* Added systay icon graceful removal after exit or restart
* Added Angelic Retreat integration
* Rebuilt the launcher with VC++2017 to address some AV false-positive alerts

##### 15.07.2017

* Added platform code into the repository
* Added `capslock toggle' command (always dreamed of)
* Fixed `enso quit' command

##### 28.05.2015

* Added Python 2.7 support

##### 05.01.2015

* Additional symbols in calc command (+, -, etc.) [thodan]
* Fixed `close' command [Caleb John]
* Fixed `website' command (by adding `simplejson' library)

##### 15.10.2012

* Fixed `help' command, internal fixes [Brian Peiris]