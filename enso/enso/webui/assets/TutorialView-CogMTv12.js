import{_ as n}from"./AppHeader.vue_vue_type_style_index_0_lang-B41ULFtW.js";import{_ as e}from"./StaticDoc.vue_vue_type_script_setup_true_lang-DnAe-d6T.js";import{d as a,c as o,a as s,u as t,F as r,k as i}from"./index-BfbyZTJC.js";const p=`<div class="doc-body">\r
    <nav id="mw-mf-page-left" class="navigation-drawer view-border-box">\r
\r
    </nav>\r
    <div id="mw-mf-page-center">\r
\r
            <div id="toc" class="toc-mobile"><h2>Contents</h2></div>\r
            <ul data-toc>\r
\r
            </ul>\r
        </div>\r
\r
    <h1><a id="user-content-configuring-enso" class="anchor" aria-hidden="true" href="#configuring-enso"></a>Configuring Enso</h1>\r
\r
    <p>'Custom Initialization' block at the Enso <a href="/settings">settings</a> page allows specifying any\r
        Python code needed to initialize Enso. By using it, you may override variables from config.py or provide\r
        values required by some commands. You can access variables declared at this block in your own commands through\r
        the 'config' module. For example, you can obtain <code>MY_VARIABLE</code> defined at the configuration block:\r
        <p><pre><code>MY_VARIABLE = "my value"</code></pre></p>\r
        <p>in the following way at your command code:</p>\r
        <p><pre><code>from enso import config<br>my_value = config.MY_VARIABLE</code></pre></p></p>\r
\r
    <h1><a id="user-content-creating-enso-commands" class="anchor" aria-hidden="true" href="#creating-enso-commands"></a>Creating Enso Commands</h1>\r
    <h2><a id="user-content-hello-world-displaying-transparent-messages" class="anchor" aria-hidden="true" href="#hello-world-displaying-transparent-messages"></a>Hello World: Displaying Transparent Messages</h2>\r
    <p>A simple command called "hello world" can be created by entering the\r
        following into the command editor:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_hello_world</span>(<span class="pl-smi">ensoapi</span>):\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>Hello World!<span class="pl-pds">"</span></span>)</pre></div>\r
    <p>As soon as the command is typed, the Enso quasimode can\r
        be entered and the command used. Enso scans command files whenever the command line is shown,\r
        and if there are changes, Enso reloads them, so there is no need to restart\r
        Enso itself when developing commands. But restart is always required after a new\r
        command category has been created.</p>\r
    <p>From the source code of the command, a number of things can be\r
        observed:</p>\r
    <ul>\r
        <li>A command is a function that starts with the prefix <code>cmd_</code>.</li>\r
        <li>The name of a command is everything following the prefix,\r
            with underscores converted to spaces.</li>\r
        <li>A command takes an <code>ensoapi</code> object as a parameter, which can\r
            be used to access Enso-specific functionality.</li>\r
    </ul>\r
    <p>You may want to take the time to play around with the "hello world"\r
        example; try raising an exception in the function body; try adding a\r
        syntax error in the file and see what happens.  It should be apparent\r
        that such human errors have been accounted for and are handled in a\r
        way that is considerate of one's frailties, allowing the programmer to\r
        write and test code with minimal interruptions to their train of\r
        thought.</p>\r
    <p>One may wonder why the <code>ensoapi</code> object has to be explicitly\r
        passed-in rather than imported.  The reasons for this are\r
        manifold: firstly, importing a specific module, e.g. <code>enso.api</code>,\r
        would tie the command to a particular implementation of the Enso\r
        API.  Yet it should be possible for the command to run in different\r
        kinds of contexts - for instance, one where Enso itself is in a\r
        separate process or even on a separate computer, and <code>ensoapi</code> is\r
        just a proxy object.  Secondly, explicitly passing in the object\r
        makes the unit testing of commands easier.</p>\r
    <h2><a id="user-content-adding-help-text" class="anchor" aria-hidden="true" href="#adding-help-text"></a>Adding Help Text</h2>\r
    <p>When using the "hello world" command, you may notice that the help\r
        text displayed above the command entry display isn't very helpful.\r
        You can set it to something nicer by adding a docstring to your\r
        command function, like so:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_hello_world</span>(<span class="pl-smi">ensoapi</span>):\r
    <span class="pl-s"><span class="pl-pds">"</span>Displays a friendly greeting.<span class="pl-pds">"</span></span>\r
\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>Hello World!<span class="pl-pds">"</span></span>)</pre></div>\r
    <p>If you add anything past a first line in the docstring, it will be\r
        rendered as HTML in the documentation for the command when the user\r
        runs the "help" command:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_hello_world</span>(<span class="pl-smi">ensoapi</span>):\r
    <span class="pl-s"><span class="pl-pds">"""</span></span>\r
<span class="pl-s">    Displays a friendly greeting.</span>\r
<span class="pl-s"></span>\r
<span class="pl-s">    This command can be used in any application, at any time,</span>\r
<span class="pl-s">    providing you with a hearty salutation at a moment's notice.</span>\r
<span class="pl-s">    <span class="pl-pds">"""</span></span>\r
\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>Hello World!<span\r
                class="pl-pds">"</span></span>)</pre>\r
    </div>\r
    <h2><a id="user-content-interacting-with-the-current-selection" class="anchor"\r
           aria-hidden="true" href="#interacting-with-the-current-selection"></a>Interacting with\r
        The Current Selection</h2>\r
    <p>Interacting with the selection is the primary method to get values in and out of Enso\r
        commands. To obtain the current selection, use <code>ensoapi.get_selection()</code>. This\r
        method returns a <em>selection dictionary</em>, or seldict for short. A seldict is simply a\r
        dictionary that maps a data format identifier to selection data in that format.</p>\r
    <p>Some valid data formats in a seldict are:</p>\r
    <ul>\r
        <li><code>text</code>: Plain unicode text of the current selection.</li>\r
        <li><code>files</code>: A list of filenames representing the current selection.</li>\r
    </ul>\r
    <p>Setting the current selection works similarly: just pass\r
        <code>ensoapi.set_selection()</code> a seldict containing the selection data to\r
        set.</p>\r
    <p>The following is an implementation of an "upper case" command that\r
        converts the user's current selection to upper case:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_upper_case</span>(<span class="pl-smi">ensoapi</span>):\r
    text <span class="pl-k">=</span> ensoapi.get_selection().get(<span class="pl-s"><span class="pl-pds">"</span>text<span class="pl-pds">"</span></span>)\r
    <span class="pl-k">if</span> text:\r
      ensoapi.set_selection({<span class="pl-s"><span class="pl-pds">"</span>text<span class="pl-pds">"</span></span> : text.upper()})\r
    <span class="pl-k">else</span>:\r
      ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>No selection!<span class="pl-pds">"</span></span>)</pre></div>\r
    <h2><a id="user-content-command-arguments" class="anchor" aria-hidden="true" href="#command-arguments"></a>Command Arguments</h2>\r
    <p>It's possible for a command to take arbitrary arguments; an example of\r
        this is the "google" command, which allows you to optionally specify a\r
        search term following the command name.  To create a command like\r
        this, just add a parameter to the command function:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_boogle</span>(<span class="pl-smi">ensoapi</span>, <span class="pl-smi">query</span>):\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>You said: <span class="pl-c1">%s</span><span class="pl-pds">"</span></span> <span class="pl-k">%</span> query)</pre></div>\r
    <p>Unless you specify a default for your argument, however, a friendly\r
        error message will be displayed when the user runs the command without\r
        specifying one.  If you don't want this to be the case, just add a\r
        default argument to the command function:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_boogle</span>(<span class="pl-smi">ensoapi</span>, <span class="pl-smi">query</span><span class="pl-k">=</span><span class="pl-s"><span class="pl-pds">"</span>pants<span class="pl-pds">"</span></span>):\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>You said: <span class="pl-c1">%s</span><span class="pl-pds">"</span></span> <span class="pl-k">%</span> query)</pre></div>\r
    <p>If you want the argument to be bounded to a particular set of options,\r
        you can specify them by attaching a <code>valid_args</code> property to your\r
        command function.  For instance:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_vote_for</span>(<span class="pl-smi">ensoapi</span>, <span class="pl-smi">candidate</span>):\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>You voted for: <span class="pl-c1">%s</span><span class="pl-pds">"</span></span> <span class="pl-k">%</span> candidate)\r
  cmd_vote_for.valid_args <span class="pl-k">=</span> [<span class="pl-s"><span class="pl-pds">"</span>barack obama<span class="pl-pds">"</span></span>, <span class="pl-s"><span class="pl-pds">"</span>john mccain<span class="pl-pds">"</span></span>]</pre></div>\r
    <h2><a id="user-content-prolonged-execution" class="anchor" aria-hidden="true" href="#prolonged-execution"></a>Prolonged Execution</h2>\r
    <p>It's expected that some commands, such as ones that need to fetch\r
        resources from the internet, may take some time to execute.  If this\r
        is the case, a command function may use Python's <code>yield</code> statement\r
        to return control back to Enso when it needs to wait for something to\r
        finish.  For example:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">def</span> <span class="pl-en">cmd_rest_awhile</span>(<span class="pl-smi">ensoapi</span>):\r
    <span class="pl-k">import</span> time, threading\r
\r
    <span class="pl-k">def</span> <span class="pl-en">do_something</span>():\r
      time.sleep(<span class="pl-c1">3</span>)\r
    t <span class="pl-k">=</span> threading.Thread(<span class="pl-v">target</span> <span class="pl-k">=</span> do_something)\r
    t.start()\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>Please wait...<span class="pl-pds">"</span></span>)\r
    <span class="pl-k">while</span> t.is_alive():\r
      <span class="pl-k">yield</span>\r
    ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>Done!<span class="pl-pds">"</span></span>)</pre></div>\r
    <p>Returning control back to Enso is highly encouraged - without it, your\r
        command will monopolize Enso's resources and you won't be able to use\r
        Enso until your command has finished executing!</p>\r
    <h2><a id="user-content-class-based-commands" class="anchor" aria-hidden="true" href="#class-based-commands"></a>Class-based Commands</h2>\r
    <p>More complex commands can be encapsulated into classes and\r
        instantiated as objects; in fact, all Enso really looks for when\r
        importing commands are callables that start with <code>cmd_</code>.  This means\r
        that the following works:</p>\r
    <div class="highlight highlight-source-python"><pre>  <span class="pl-k">class</span> <span class="pl-en">VoteCommand</span>(<span class="pl-c1">object</span>):\r
    <span class="pl-k">def</span> <span class="pl-c1">__init__</span>(<span class="pl-smi"><span class="pl-smi">self</span></span>, <span class="pl-smi">candidates</span>):\r
      <span class="pl-c1">self</span>.valid_args <span class="pl-k">=</span> candidates\r
\r
    <span class="pl-k">def</span> <span class="pl-c1">__call__</span>(<span class="pl-smi"><span class="pl-smi">self</span></span>, <span class="pl-smi">ensoapi</span>, <span class="pl-smi">candidate</span>):\r
      ensoapi.display_message(<span class="pl-s"><span class="pl-pds">"</span>You voted for: <span class="pl-c1">%s</span><span class="pl-pds">"</span></span> <span class="pl-k">%</span> candidate)\r
  cmd_vote_for <span class="pl-k">=</span> VoteCommand([<span class="pl-s"><span class="pl-pds">"</span>barack obama<span class="pl-pds">"</span></span>, <span class="pl-s"><span class="pl-pds">"</span>john mccain<span class="pl-pds">"</span></span>])</pre></div>\r
\r
    <h2><a id="user-content-multiline-messages" class="anchor" aria-hidden="true" href="#multiline-messages"></a>Multiline messages</h2>\r
    <p>Messages displayed with <code></code>ensoapi.display_message()</code> can contain only one line.\r
        If you need to display more than one line in your message, use the <code>displayMessage</code> function:</p>\r
\r
    <div class="highlight highlight-source-python">\r
            <pre>\r
  from enso.messages import displayMessage\r
\r
  MESSAGE_TEXT_XML = "&lt;p&gt;&lt;command&gt;Colored text&lt;/command&gt; white text.&lt;/p&gt;" \\\r
                     "&lt;p&gt;Another line entirely in white.&lt;/p&gt;" \\\r
                     "&lt;caption&gt;Small right-aligned caption&lt;/caption&gt;"\r
\r
  displayMessage(MESSAGE_TEXT_XML)\r
            </pre>\r
    </div>\r
    \r
    <h2><a id="user-content-command-updating" class="anchor" aria-hidden="true" href="#command-updating"></a>Command Updating</h2>\r
    <p>Some commands may need to do processing while not being executed; for\r
        instance, an <code>open</code> command that allows the user to open an\r
        application installed on their computer may want to update its\r
        <code>valid_args</code> property whenever a new application is installed or\r
        uninstalled.</p>\r
    <p>If a command object has an <code>on_quasimode_start()</code> function attached\r
        to it, it will be called whenever the command quasimode is entered.\r
        This allows the command to do any processing it may need to do.  As\r
        with the command execution call itself, <code>on_quasimode_start()</code> may\r
        use <code>yield</code> to relegate control back to Enso when it knows that some\r
        operation will take a while to finish.</p>\r
\r
    <pre>\r
from enso.messages import displayMessage\r
\r
def cmd_test(ensoapi):\r
    ensoapi.display_message("demo")\r
\r
def my_func():\r
    displayMessage("&lt;p&gt;On quasimode start&lt;/p&gt;")\r
\r
cmd_test.on_quasimode_start = my_func\r
    </pre>\r
\r
    <h2><a id="user-content-including-other-files" class="anchor" aria-hidden="true" href="#including-other-files"></a>Including Other Files</h2>\r
    <p>It is possible to install or uninstall Python libraries from <a href="https://pypi.org/">PyPi</a>\r
        using 'enso install' and 'enso uninstall' commands respectively.<br>\r
        If you need to import some code that is not installable as a Python module,\r
        place it under the 'lib' folder in your Enso configuration directory. The 'lib' directory is added to Enso <code>PYTHONPATH</code>.\r
        The path of the Enso configuration folder could be found on the Enso <a href="/settings">settings</a> page.\r
        <br>\r
        If there is an __init__.py file in the 'lib' directory it will be imported as a module before Enso initialization.\r
        This may be used to create complex Enso-based applications, for example, using Flask Blueprints.\r
        <br>\r
        Python's standard <code>import</code> statement can be used from command\r
        scripts. But the disadvantage of doing this with evolving\r
        code is that imported modules won't be reloaded\r
        if their contents change.</p>\r
\r
    <h1><a id="user-content-mediaprobes" class="anchor" aria-hidden="true" href="#mediaprobes"></a>Mediaprobes</h1>\r
    <p>Mediaprobes allow to create commands that automatically pass items found in the filesystem (or listed\r
        in a dictionary) to the specified program. Let's assume that\r
        you have a directory named 'd:/tv-shows', which contains subdirectories: 'columbo', 'the octopus', and 'inspector gadget'.\r
        Let's create a command named 'show' that has the names of all subdirectories\r
        under 'd:/tv-shows' as suggestions for its argument (the argument will be named "series") and opens the given directory (or file) in Media Player Classic.</p>\r
    <div class="highlight highlight-source-python"><pre><span class="pl-c"><span class="pl-c">#</span> place the following into the command editor</span>\r
\r
<span class="pl-k">from</span> enso.user <span class="pl-k">import</span> mediaprobe\r
\r
cmd_show <span class="pl-k">=</span> mediaprobe.directory_probe(<span class="pl-s"><span\r
                class="pl-pds">"</span>show<span class="pl-pds">"</span></span>, <span\r
                class="pl-s"><span class="pl-pds">"</span>d:/tv-shows<span\r
                class="pl-pds">"</span></span>, <span class="pl-s"><span class="pl-pds">"</span>&lt;absolute path to MPC-HC&gt;<span\r
                class="pl-pds">"</span></span>)</pre>\r
    </div>\r
    <p>That's all. The command will have the following additional arguments:</p>\r
    <ul>\r
        <li>what - lists available arguments.</li>\r
        <li>next - open the next show in the player.</li>\r
        <li>prev - open the previous show in the player.</li>\r
        <li>all - pass 'd:/tv-shows' to the player.</li>\r
    </ul>\r
    <p><code>mediaprobe.dictionary_probe</code> allows to create probe commands based on a\r
        dictionary:</p>\r
    <div class="highlight highlight-source-python"><pre>what_to_watch <span class="pl-k">=</span> {<span class="pl-s"><span class="pl-pds">"</span>formula 1<span class="pl-pds">"</span></span>: <span class="pl-s"><span class="pl-pds">"</span>&lt;a link to my favorite formula 1 stream&gt;<span class="pl-pds">"</span></span>,\r
                 <span class="pl-s"><span class="pl-pds">"</span>formula e<span class="pl-pds">"</span></span>: <span class="pl-s"><span class="pl-pds">"</span>&lt;a link to my favorite formula e stream&gt;<span class="pl-pds">"</span></span>}\r
cmd_watch <span class="pl-k">=</span> mediaprobe.dictionary_probe(<span class="pl-s"><span class="pl-pds">"</span>stream<span class="pl-pds">"</span></span>, what_to_watch, <span class="pl-s"><span class="pl-pds">"</span>&lt;absolute path to my network player&gt;<span class="pl-pds">"</span></span>)</pre></div>\r
    <p>If player does not accept directories (as, for example, ACD See does), use <code>mediaprobe.findfirst_probe</code> to pass a first file in a directory (one of the specified at\r
        a dictionary):</p>\r
    <pre><code>what_to_stare_at = {'nature': 'd:/images/nature',\r
                    'cosmos': 'd:/images/cosmos'}\r
                    \r
# if player is not specified, the command will use the default system application \r
# associated with the encountered file type\r
cmd_stare = mediaprobe.findfirst_probe("at", what_to_stare_at)\r
</code></pre>\r
    <p>Of course, you may construct dictionaries in various ways.</p>\r
\r
    <h1 id="voice-recognition"><a id="user-content-voice-recognition" class="anchor" aria-hidden="true"\r
                                  href="#voice-recognition"></a>Voice Recognition</h1>\r
    <p>Enso can listen for your commands and run them without the quasimode. This requires the\r
        <code>voicecmd</code> module to be installed; if it is missing, the voice controls simply\r
        do not appear on the <a href="/commands">Your Commands</a> page and everything else\r
        works as usual.</p>\r
\r
    <h2><a id="user-content-speaking-commands" class="anchor" aria-hidden="true"\r
           href="#speaking-commands"></a>Speaking Commands</h2>\r
    <p>Spoken commands are prefixed with a keyword, <code>computer</code> by default. Saying</p>\r
    <pre><code>computer open notepad</code></pre>\r
    <p>runs the same command as typing <code>open notepad</code> in the quasimode. The keyword is\r
        what keeps ordinary conversation from triggering commands, so leaving it enabled is\r
        recommended.</p>\r
    <p>Only the commands you have explicitly enabled for voice are listened for - everything\r
        else is deaf. For commands that take an argument, the available arguments become part of\r
        what can be said, so <code>open</code> with its list of applications lets you say\r
        <code>computer open google chrome</code> as one phrase. Commands whose argument is\r
        arbitrary text (a search query, an expression) are recognized by name only.</p>\r
    <p>Listening can be suspended and resumed by voice:</p>\r
    <ul>\r
        <li><code>computer stop listening</code> - ignore everything but the resume phrase.</li>\r
        <li><code>computer resume listening</code> - start listening again.</li>\r
    </ul>\r
    <p>Recognition also stops by itself while the workstation is locked, and resumes when you log\r
        back in, so nothing is listening at the lock screen.</p>\r
\r
    <h2><a id="user-content-the-command-checks" class="anchor" aria-hidden="true"\r
           href="#the-command-checks"></a>The Command Checks</h2>\r
    <p>Each command on the <a href="/commands">Your Commands</a> page carries a row of\r
        checkboxes:</p>\r
    <ul>\r
        <li><b>&#9211;</b> - the command is enabled at all. Unchecking it hides the command\r
            everywhere.\r
        </li>\r
        <li><b>&#127897;</b> - <b>voice command</b>. The command is added to the voice\r
            grammar and can be spoken. Off by default: a smaller grammar recognizes far more\r
            accurately, so enable only the commands you actually intend to say.\r
        </li>\r
        <li><b>&#128066;</b> - <b>voice&#8209;only</b>. The command is spoken but hidden from\r
            the quasimode suggestion list. Useful for commands you never want to type.\r
        </li>\r
        <li><b>&#127383;</b> - <b>confirm before running</b>. The command asks before it\r
            runs. See below.\r
        </li>\r
    </ul>\r
    <p>The last two describe <em>how</em> a voice command behaves, so checking either one checks\r
        the voice command box for you.</p>\r
\r
    <h2><a id="user-content-confirmations" class="anchor" aria-hidden="true"\r
           href="#confirmations"></a>Confirmations</h2>\r
    <p>Speech recognition is never perfect, and some commands are worth a second question before\r
        they run - anything that shuts a machine down, sends something, or cannot be undone.\r
        Checking the confirm box holds such a command back until you approve it.</p>\r
    <p>When a command that requires confirmation is recognized, a message appears naming what was\r
        heard, and Enso waits. Answer with a bare</p>\r
    <ul>\r
        <li><code>yes</code> - run the command.</li>\r
        <li><code>no</code> - drop it.</li>\r
    </ul>\r
    <p>The keyword is not needed for the answer. While Enso is waiting it listens for nothing but\r
        <code>yes</code> and <code>no</code>, so a misheard word cannot start another command. If\r
        you say nothing, the request times out after ten seconds and is treated as\r
        <code>no</code> - silence never runs a command.</p>\r
\r
    <h2><a id="user-content-voice-settings" class="anchor" aria-hidden="true"\r
           href="#voice-settings"></a>Settings</h2>\r
    <p>Voice behavior is tuned from the custom initialization block on the\r
        <a href="/settings">settings</a> page:</p>\r
    <ul>\r
        <li><code>VOICE_ENABLED</code> - set to <code>False</code> to turn off the voice recognition entirely.</li>\r
        <li><code>VOICE_KEYWORD</code> - the prefix word, <code>"computer"</code> by default.</li>\r
        <li><code>VOICE_KEYWORD_REQUIRED</code> - set to <code>False</code> to speak commands\r
            with no prefix at all. Expect false triggers.\r
        </li>\r
        <li><code>VOICE_LANGUAGE</code> - recognizer language, <code>"en-US"</code> by default.</li>\r
        <li><code>VOICE_DEBUG</code> - print what the recognizer hears, including rejected\r
            phrases and their confidence. Useful when a command is not being picked up.\r
        </li>\r
    </ul>\r
\r
    <p>See more at the config.py in the enso source directory.</p>\r
</div>
`,g=a({__name:"TutorialView",setup(l){return(c,d)=>(i(),o(r,null,[s(n,{title:"Tutorial"}),s(e,{html:t(p)},null,8,["html"])],64))}});export{g as default};
