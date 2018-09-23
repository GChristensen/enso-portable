# Creating Enso Commands

To create a command for the portable distribution of Enso put the code of your command 
into a python file under the ``commands`` directory at the root of the distribution.

Hello World: Displaying Transparent Messages
--------------------------------------------

A simple command called "hello world" can be created by entering the
following into your command source code file:
```python
  def cmd_hello_world(ensoapi):
    ensoapi.display_message("Hello World!")
```
As soon as the the file is saved, the Enso quasimode can
be entered and the command used: Enso scans this file and its
dependencies whenever the quasimode is entered, and if the contents
have changed, Enso reloads them, so there is never a need to restart
Enso itself when developing commands.

From the source code of the command, a number of things can be
observed:

  * A command is a function that starts with the prefix ``cmd_``.
  * The name of a command is everything following the prefix,
    with underscores converted to spaces.
  * A command takes an ``ensoapi`` object as a parameter, which can
    be used to access Enso-specific functionality.

You may want to take the time to play around with the "hello world"
example; try raising an exception in the function body; try adding a
syntax error in the file and see what happens.  It should be apparent
that such human errors have been accounted for and are handled in a
way that is considerate of one's frailties, allowing the programmer to
write and test code with minimal interruptions to their train of
thought.

One may wonder why the ``ensoapi`` object has to be explicitly
   passed-in rather than being imported.  The reasons for this are
   manifold: firstly, importing a specific module, e.g. ``enso.api``,
   would tie the command to a particular implementation of the Enso
   API.  Yet it should be possible for the command to run in different
   kinds of contexts - for instance, one where Enso itself is in a
   separate process or even on a separate computer, and ``ensoapi`` is
   just a proxy object.  Secondly, explicitly passing in the object
   makes the unit testing of commands easier.

Adding Help Text
----------------

When using the "hello world" command, you may notice that the help
text displayed above the command entry display isn't very helpful.
You can set it to something nicer by adding a docstring to your
command function, like so:
```python
  def cmd_hello_world(ensoapi):
    "Displays a friendly greeting."

    ensoapi.display_message("Hello World!")
```
If you add anything past a first line in the docstring, it will be
rendered as HTML in the documentation for the command when the user
runs the "help" command:
```python
  def cmd_hello_world(ensoapi):
    """
    Displays a friendly greeting.

    This command can be used in any application, at any time,
    providing you with a hearty salutation at a moment's notice.
    """

    ensoapi.display_message("Hello World!")
```
Interacting with The Current Selection
--------------------------------------

To obtain the current selection, use ``ensoapi.get_selection()``.
This method returns a *selection dictionary*, or seldict for short.  A
seldict is simply a dictionary that maps a data format identifier to
selection data in that format.

Some valid data formats in a seldict are:

  * ``text``: Plain unicode text of the current selection.
  * ``files``: A list of filenames representing the current selection.

Setting the current selection works similarly: just pass
``ensoapi.set_selection()`` a seldict containing the selection data to
set.

The following is an implementation of an "upper case" command that
converts the user's current selection to upper case:
```python
  def cmd_upper_case(ensoapi):
    text = ensoapi.get_selection().get("text")
    if text:
      ensoapi.set_selection({"text" : text.upper()})
    else:
      ensoapi.display_message("No selection!")
```
Command Arguments
-----------------

It's possible for a command to take arbitrary arguments; an example of
this is the "google" command, which allows you to optionally specify a
search term following the command name.  To create a command like
this, just add a parameter to the command function:
```python
  def cmd_boogle(ensoapi, query):
    ensoapi.display_message("You said: %s" % query)
```
Unless you specify a default for your argument, however, a friendly
error message will be displayed when the user runs the command without
specifying one.  If you don't want this to be the case, just add a
default argument to the command function:
```python
  def cmd_boogle(ensoapi, query="pants"):
    ensoapi.display_message("You said: %s" % query)
```
If you want the argument to be bounded to a particular set of options,
you can specify them by attaching a ``valid_args`` property to your
command function.  For instance:
```python
  def cmd_vote_for(ensoapi, candidate):
    ensoapi.display_message("You voted for: %s" % candidate)
  cmd_vote_for.valid_args = ["barack obama", "john mccain"]
```
Prolonged Execution
-------------------

It's expected that some commands, such as ones that need to fetch
resources from the internet, may take some time to execute.  If this
is the case, a command function may use Python's ``yield`` statement
to return control back to Enso when it needs to wait for something to
finish.  For example:
```python
  def cmd_rest_awhile(ensoapi):
    import time, threading

    def do_something():
      time.sleep(3)
    t = threading.Thread(target = do_something)
    t.start()
    ensoapi.display_message("Please wait...")
    while t.isAlive():
      yield
    ensoapi.display_message("Done!")
```
Returning control back to Enso is highly encouraged - without it, your
command will monopolize Enso's resources and you won't be able to use
Enso until your command has finished executing!

Class-based Commands
--------------------

More complex commands can be encapsulated into classes and
instantiated as objects; in fact, all Enso really looks for when
importing commands are callables that start with ``cmd_``.  This means
that the following works:
```python
  class VoteCommand(object):
    def __init__(self, candidates):
      self.valid_args = candidates

    def __call__(self, ensoapi, candidate):
      ensoapi.display_message("You voted for: %s" % candidate)

  cmd_vote_for = VoteCommand(["barack obama", "john mccain"])
```
Command Updating
----------------

Some commands may need to do processing while not being executed; for
instance, an ``open`` command that allows the user to open an
application installed on their computer may want to update its
``valid_args`` property whenever a new application is installed or
uninstalled.

If a command object has an ``on_quasimode_start()`` function attached
to it, it will be called whenever the command quasimode is entered.
This allows the command to do any processing it may need to do.  As
with the command execution call itself, ``on_quasimode_start()`` may
use ``yield`` to relegate control back to Enso when it knows that some
operation will take a while to finish.

Including Other Files
---------------------

Python's standard ``import`` statement can be used from command
scripts, of course, but the disadvantage of doing this with evolving
code is that - at present, at least - imported modules won't be reloaded
if their contents change.
