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


#### Change log
[full changelog](changelog.md)

##### 21.08.2019 (v.0.4.4)

* Fixed Google command.
* Improved quasimode performance through smart command change tracking.

#### Contributors

* [Brian Peiris](https://github.com/brianpeiris)
* [thdoan](https://github.com/thdoan)
* [Caleb John](https://github.com/CalebJohn)
* [Mark Wiseman](https://github.com/mawiseman)