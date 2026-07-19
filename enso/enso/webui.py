import threading, uuid, platform, logging, os, random, string, re, hmac
import shutil, tempfile
import enso.messages

import enso
from enso import config
from enso.contrib import retreat
from enso.quasimode import layout
from enso.commands.manager import CommandManager
from enso.contrib.scriptotron.tracker import ScriptTracker

from flask import Flask, request, send_from_directory, abort, jsonify, redirect
from functools import wraps
from urllib.parse import quote, unquote
from werkzeug.serving import make_server
from werkzeug.utils import safe_join

HOST = "localhost"
PORT = 31750
AUTH_TOKEN = str(uuid.uuid4())

# Client-side routes of the single-page UI. A request for one of these is
# answered with index.html so that deep links and refreshes work.
SPA_ROUTES = frozenset((
    "settings", "commands", "tasks", "editor", "api-ref", "tutorial", "about",
))

# The pages this UI used to be. Kept so existing bookmarks, and any link in
# the wild, still land somewhere sensible.
LEGACY_PAGES = {
    "options.html": "/settings",
    "commands.html": "/commands",
    "tasks.html": "/tasks",
    "edit.html": "/editor",
    "api.html": "/api-ref",
    "tutorial.html": "/tutorial",
    "about.html": "/about",
    "changes.html": "/about",
    "index.html": "/settings",
}

# Command category names become filenames. Allow word characters, spaces,
# dots, and dashes -- but the pattern as a whole rejects "." and ".." and
# anything containing a path separator.
_SAFE_CATEGORY = re.compile(r"\A[\w \-.]{1,64}\Z", re.UNICODE)

webui_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(webui_dir, "webui")

app = Flask(__name__, static_url_path='', static_folder=None)

#app.debug = True

config.WEBUI_APP = app

log = logging.getLogger('werkzeug')
log.disabled = True # False
app.logger.disabled = True # False


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if config.ENABLE_WEB_UI_CSRF:
            auth = request.authorization
            password = auth.password if auth else None
            # compare_digest rather than != so the check does not leak the
            # token a character at a time through its timing.
            if not password or not hmac.compare_digest(password, AUTH_TOKEN):
                return abort(401)
        return f(*args, **kwargs)
    return decorated


def _allowed_origins():
    server_host = getattr(config, "WEBUI_HOST", None) or HOST
    return {"http://%s:%d" % (h, PORT)
            for h in (server_host, "localhost", "127.0.0.1")}


def _is_same_origin():
    """True only for requests originating from a page we served ourselves.

    Fails closed: a request carrying none of the three headers is rejected.
    """
    # Sec-Fetch-Site is a forbidden header name, so page script cannot forge
    # it. Where the browser sends it, it is decisive.
    site = request.headers.get("Sec-Fetch-Site")
    if site is not None:
        return site == "same-origin"

    # Older browser. Origin is sent on cross-origin requests, so its presence
    # is decisive when it is there.
    origin = request.headers.get("Origin")
    if origin is not None:
        return origin in _allowed_origins()

    # Neither header: fall back to Referer. A cross-site <script src> or <img>
    # carries the attacker's Referer, and no Referer at all is rejected.
    referer = request.headers.get("Referer", "")
    return any(referer.startswith(o + "/") for o in _allowed_origins())


@app.route('/api/enso/token')
def get_enso_token():
    """Hand the auth token to our own pages.

    Deliberately not @requires_auth -- this is how the client bootstraps, and
    how it recovers after an Enso restart mints a new token (the process is
    replaced, so the token an open tab holds goes stale). Gated on origin
    instead. NEVER serve CORS headers from this app: without them a foreign
    page cannot read this response even if it manages to issue the request.
    """
    if not _is_same_origin():
        abort(403)

    r = jsonify({"token": AUTH_TOKEN})
    r.headers["Cache-Control"] = "no-store"
    r.headers["Vary"] = "Origin, Sec-Fetch-Site"
    return r


def _send_index():
    r = send_from_directory(static_dir, "index.html")
    r.headers["Cache-Control"] = "no-store"
    return r


@app.route('/')
def index():
    return _send_index()


@app.route('/<path:filename>')
def my_static(filename):
    # An unknown /api/... path is a bug in a caller, not a page. Answer 404
    # rather than letting it fall through to the SPA and come back as a 200
    # full of HTML.
    if filename == "api" or filename.startswith("api/"):
        abort(404)

    legacy = LEGACY_PAGES.get(filename.lower())
    if legacy:
        # A fragment (tutorial.html#voice-recognition) never reaches the
        # server; the browser re-applies it to the redirect target itself.
        # The query string does need carrying across by hand.
        query = request.query_string.decode("utf-8", "replace")
        if query:
            if filename.lower() == "edit.html":
                # edit.html took the category as a bare query string.
                legacy += "?category=" + quote(unquote(query), safe="")
            else:
                legacy += "?" + query
        return redirect(legacy, 302)

    # safe_join returns None rather than raising when the path escapes.
    full = safe_join(static_dir, filename)
    if full is not None and os.path.isfile(full):
        return send_from_directory(static_dir, filename)

    if filename.split("/", 1)[0] in SPA_ROUTES:
        return _send_index()

    abort(404)


@app.after_request
def add_header(r):
    # Asset filenames are content-hashed, so they can be cached hard: an Enso
    # upgrade produces new names. Everything else must not be cached at all.
    #
    # Never add Access-Control-Allow-* here. The token endpoint's protection
    # rests on a foreign page being unable to read our responses.
    if request.path.startswith("/assets/"):
        r.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        r.headers["Cache-Control"] = "no-store"
    return r


@app.route('/api/python/version')
@requires_auth
def get_python_version():
    return platform.python_version()


@app.route('/api/enso/version')
@requires_auth
def get_enso_version():
    return config.ENSO_VERSION


@app.route('/api/retreat/installed')
@requires_auth
def get_retreat_installed():
    if retreat.installed():
        return "True"
    return ""


@app.route('/api/retreat/show_options', methods=["POST"])
@requires_auth
def post_retreat_show_settings():
    retreat.settings()
    return ""


@app.route('/api/enso/color_themes')
@requires_auth
def get_enso_themes():
    return jsonify({"current": config.COLOR_THEME, "all": layout.COLOR_THEMES})


@app.route('/api/enso/get/config/<key>')
@requires_auth
def get_enso_get_config(key):
    config_vars = vars(config)
    if key in config_vars:
        return str(config_vars[key])
    else:
        return ""


@app.route('/api/enso/set/config/<key>', methods=["POST"])
@requires_auth
def post_enso_set_config(key):
    # The value travels in the body, not the path: a value containing "/"
    # would otherwise change which route matched.
    config.storeValue(key.upper(), request.form["value"])
    return ""


@app.route('/api/enso/get/config_dir')
@requires_auth
def get_enso_get_config_dir():
    return config.ENSO_USER_DIR.replace("\\", "/")


@app.route('/api/enso/open/config_dir', methods=["POST"])
@requires_auth
def post_enso_open_config_dir():
    os.startfile(config.ENSO_USER_DIR, "open")
    return ""


@app.route('/api/enso/get/ensorc')
@requires_auth
def get_enso_get_ensorc():
    return send_from_directory(config.ENSO_USER_DIR, "ensorc.py")


@app.route('/api/enso/set/ensorc', methods=["POST"])
@requires_auth
def post_enso_set_ensorc():
    ensorc_file = os.path.join(config.ENSO_USER_DIR, "ensorc.py")
    allow_empty = request.form.get("allow_empty") == "1"
    if not _write_user_file(ensorc_file, request.form["ensorc"], allow_empty):
        return "refused: empty payload would overwrite existing content", 409
    return ""


@app.route('/api/enso/get/commands')
@requires_auth
def get_enso_get_commands():
    cmdman = CommandManager.get()
    commands = cmdman.getCommands()
    output = []

    for name, command in commands.items():
        desc = command.getDescription()
        helpText = command.getHelp()

        category = "other"
        if hasattr(command, "func") and hasattr(command.func, "category"):
            category = command.func.category

        file = ""
        if hasattr(command, "func") and hasattr(command.func, "cmdFile"):
            file = command.func.cmdFile

        cmdJSON = {"name": name, "description": desc, "help": helpText,
                   "category": category, "file": file}

        if name in config.DISABLED_COMMANDS:
            cmdJSON["disabled"] = "true"

        if name in config.VOICE_COMMANDS:
            cmdJSON["voice"] = "true"

        if name in config.VOICE_ONLY_COMMANDS:
            cmdJSON["voiceOnly"] = "true"

        if name in config.VOICE_CONFIRM_COMMANDS:
            cmdJSON["voiceConfirm"] = "true"

        output = output + [cmdJSON]
    return jsonify(output)


def _voicecmd_available():
    """True if the native voicecmdlib module is importable. Governs whether
    the voice checkbox columns are shown in the commands web UI."""
    try:
        import enso.contrib.voicecmdlib  # noqa: F401
        return True
    except ImportError:
        return False


@app.route('/api/enso/voice/available')
@requires_auth
def get_enso_voice_available():
    return jsonify(_voicecmd_available())


@app.route('/api/enso/get/user_command_categories')
@requires_auth
def get_enso_commands_categories():
    commands_dir = os.path.join(config.ENSO_USER_DIR, "commands")
    categories = []
    for f in os.listdir(commands_dir):
        if f.endswith(".py"):
            categories = categories + [os.path.splitext(f)[0]]
    return jsonify(categories)


def _write_user_file(path, text, allow_empty=False):
    """Replace `path` with `text`, refusing to destroy content by accident.

    These files are scripts the user typed by hand, and the editor autosaves
    them on a debounce and on blur -- so a save fires at moments the user never
    consciously chose. Three ways that used to lose work, all closed here:

      * The old code opened the destination "wb" (which truncates) and only
        then evaluated the payload. Anything failing in between -- a missing
        form field, a dropped connection -- left a 0-byte file where the
        script had been. The bytes are now materialized first, and the
        destination is touched only once we hold them.

      * An empty payload silently overwrote real content. The editor posts its
        buffer, and its buffer is empty whenever a read failed (Enso
        restarting, say), so a blur right after a failed load wiped the file.
        An empty write over a non-empty file is now refused.

      * A crash mid-write left a partial file. The write goes to a temp file in
        the same directory, is flushed to disk, and is swapped in with
        os.replace(), which is atomic -- readers see either the old file or
        the new one, never a half-written one.

    Returns True if written, False if refused as an empty overwrite.
    """
    data = text.encode("utf-8")

    if not data and not allow_empty:
        try:
            if os.path.getsize(path) > 0:
                logging.warning(
                    "enso.webui: refused to overwrite %s with an empty "
                    "payload (%d bytes on disk)", path, os.path.getsize(path))
                return False
        except OSError:
            pass  # absent or unreadable: nothing to protect

    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    # Same directory as the destination, so the os.replace() below is a true
    # atomic rename (renaming across volumes is not).
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".enso-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

        # One generation of undo, for the case this whole function exists for:
        # the user's own script being replaced by something they did not mean
        # to save. Best-effort -- a backup we cannot write must not block a
        # save the user did ask for.
        try:
            if os.path.getsize(path) > 0:
                shutil.copy2(path, path + ".bak")
        except OSError:
            pass

        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return True


def _commands_dir():
    return os.path.join(config.ENSO_USER_DIR, "commands")


def _category_path(value):
    """Resolve a category name to its .py file, refusing to leave the dir.

    The name arrives from the network and is turned into a filename, so it is
    checked twice: the pattern rejects separators and the relative names up
    front, and safe_join backstops whatever the pattern lets through.
    """
    if value in (".", "..") or not _SAFE_CATEGORY.match(value):
        abort(400)

    path = safe_join(_commands_dir(), value + ".py")
    if path is None:
        abort(400)
    return path


@app.route('/api/enso/commands/delete_category/<value>', methods=["POST"])
@requires_auth
def post_enso_commands_delete_category(value):
    category_file = _category_path(value)
    if os.path.exists(category_file):
        os.remove(category_file)
    return ""


@app.route('/api/enso/commands/write_category/<value>', methods=["POST"])
@requires_auth
def post_enso_commands_write_category(value):
    category_file = _category_path(value)

    # An explicitly created, still-empty category is a legitimate empty write;
    # a save of an empty buffer over an existing script is not. The client
    # marks the former.
    allow_empty = request.form.get("allow_empty") == "1"
    if not _write_user_file(category_file, request.form["code"], allow_empty):
        # 409: the request was understood and deliberately not applied. The
        # editor turns this back into "reload, your file is intact".
        return "refused: empty payload would overwrite existing content", 409

    ScriptTracker.get().setPendingChanges()

    return ""


@app.route('/api/enso/commands/read_category/<value>')
@requires_auth
def get_enso_commands_read_category(value):
    _category_path(value)  # validate before handing the name to Flask
    return send_from_directory(_commands_dir(), value + ".py")


@app.route('/api/enso/commands/disable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_disable(command):
    if command not in config.DISABLED_COMMANDS:
        config.DISABLED_COMMANDS += [command]
        config.COMMAND_STATE_CHANGED = True
        config.storeValue("DISABLED_COMMANDS", config.DISABLED_COMMANDS)
    return ""


@app.route('/api/enso/commands/enable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_enable(command):
    if command in config.DISABLED_COMMANDS:
        config.DISABLED_COMMANDS.remove(command)
        config.COMMAND_STATE_CHANGED = True
        config.storeValue("DISABLED_COMMANDS", config.DISABLED_COMMANDS)
    return ""


@app.route('/api/enso/commands/voice/disable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_voice_disable(command):
    if command in config.VOICE_COMMANDS:
        config.VOICE_COMMANDS.remove(command)
        config.VOICE_COMMANDS_CHANGED = True
        config.storeValue("VOICE_COMMANDS", config.VOICE_COMMANDS)
    return ""


@app.route('/api/enso/commands/voice/enable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_voice_enable(command):
    if command not in config.VOICE_COMMANDS:
        config.VOICE_COMMANDS += [command]
        config.VOICE_COMMANDS_CHANGED = True
        config.storeValue("VOICE_COMMANDS", config.VOICE_COMMANDS)
    return ""


@app.route('/api/enso/commands/voice_only/disable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_voice_only_disable(command):
    if command in config.VOICE_ONLY_COMMANDS:
        config.VOICE_ONLY_COMMANDS.remove(command)
        config.storeValue("VOICE_ONLY_COMMANDS", config.VOICE_ONLY_COMMANDS)
    return ""


@app.route('/api/enso/commands/voice_only/enable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_voice_only_enable(command):
    if command not in config.VOICE_ONLY_COMMANDS:
        config.VOICE_ONLY_COMMANDS += [command]
        config.storeValue("VOICE_ONLY_COMMANDS", config.VOICE_ONLY_COMMANDS)
    return ""


@app.route('/api/enso/commands/voice_confirm/disable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_voice_confirm_disable(command):
    if command in config.VOICE_CONFIRM_COMMANDS:
        config.VOICE_CONFIRM_COMMANDS.remove(command)
        # Unlike voice_only (a quasimode-display concern), this one is baked
        # into the grammar as Verb.confirm, so the engine must be rebuilt.
        config.VOICE_COMMANDS_CHANGED = True
        config.storeValue("VOICE_CONFIRM_COMMANDS", config.VOICE_CONFIRM_COMMANDS)
    return ""


@app.route('/api/enso/commands/voice_confirm/enable/<command>', methods=["POST"])
@requires_auth
def post_enso_commands_voice_confirm_enable(command):
    if command not in config.VOICE_CONFIRM_COMMANDS:
        config.VOICE_CONFIRM_COMMANDS += [command]
        config.VOICE_COMMANDS_CHANGED = True
        config.storeValue("VOICE_CONFIRM_COMMANDS", config.VOICE_CONFIRM_COMMANDS)
    return ""


@app.route('/api/enso/write_tasks', methods=["POST"])
@requires_auth
def post_enso_commands_write_tasks():
    category_file = os.path.join(config.ENSO_USER_DIR, "tasks.py")

    allow_empty = request.form.get("allow_empty") == "1"
    if not _write_user_file(category_file, request.form["code"], allow_empty):
        return "refused: empty payload would overwrite existing content", 409
    return ""


@app.route('/api/enso/read_tasks')
@requires_auth
def get_enso_commands_read_tasks():
    return send_from_directory(config.ENSO_USER_DIR, "tasks.py")


class Httpd(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        server_host = getattr(config, "WEBUI_HOST", None) or HOST
        self.srv = make_server(server_host, PORT, app, True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()


def displayMessage(msg):
    enso.messages.displayMessage("<p>%s</p>" % msg)


httpd = None


def start():
    global httpd
    httpd = Httpd(app)
    httpd.daemon = True
    httpd.start()


def stop():
    global httpd
    httpd.shutdown()
