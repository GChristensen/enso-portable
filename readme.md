## Enso open-source

A feature-rich descendant of Enso Community Edition (win32). 

This is a development page. Please visit the main site at: https://gchristensen.github.io/enso-portable/

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

##### 24.08.2019 (v.0.4.5)
* Optimized 'open' command shortcut reloading (should seed up command editing/testing cycle).
* Added 'enso refresh' command option.

##### 21.08.2019 (v.0.4.4)

* Fixed Google command.
* Improved quasimode performance through smart command change tracking.

#### Contributors

* [Brian Peiris](https://github.com/brianpeiris)
* [thdoan](https://github.com/thdoan)
* [Caleb John](https://github.com/CalebJohn)
* [Mark Wiseman](https://github.com/mawiseman)