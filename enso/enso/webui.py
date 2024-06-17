import threading, uuid, platform, logging, os, random, string, json, mimetypes
import enso.messages

import enso
from enso import config
from enso.contrib import retreat
from enso.quasimode import layout
from enso.commands.manager import CommandManager
from enso.contrib.scriptotron.tracker import ScriptTracker

from flask import Flask, request, send_from_directory, abort
from functools import wraps
from werkzeug.serving import make_server

HOST = "localhost"
PORT = 31750
AUTH_TOKEN = str(uuid.uuid4())

webui_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(webui_dir, "webui")

app = Flask(__name__, static_url_path='', static_folder=None)

log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if config.ENABLE_WEB_UI_CSRF and (not request.authorization or request.authorization["password"] != AUTH_TOKEN):
            return abort(401)
        return f(*args, **kwargs)
    return decorated


@app.route('/<path:filename>')
def my_static(filename):
    if filename.endswith(".html"):
        return inject_enso_token(filename)
    else:
        return send_from_directory("webui", filename)


def inject_enso_token(filename):
    filename = os.path.join(app.root_path, "webui", filename)

    with open(filename, encoding="utf-8") as file:
        content = file.read()
        content = content.replace("%%ENSO_TOKEN%%", AUTH_TOKEN)
        return content


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
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


@app.route('/api/retreat/show_options')
@requires_auth
def get_retreat_show_settings():
    retreat.options()
    return ""


@app.route('/api/enso/color_themes')
@requires_auth
def get_enso_themes():
    return json.dumps({"current": config.COLOR_THEME, "all": layout.COLOR_THEMES})


@app.route('/api/enso/get/config/<key>')
@requires_auth
def get_enso_get_config(key):
    config_vars = vars(config)
    if key in config_vars:
        return str(config_vars[key])
    else:
        return ""


@app.route('/api/enso/set/config/<key>/<value>')
@requires_auth
def get_enso_set_config(key, value):
    config.storeValue(key.upper(), value)
    return ""


@app.route('/api/enso/get/config_dir')
@requires_auth
def get_enso_get_config_dir():
    return config.ENSO_USER_DIR.replace("\\", "/")


@app.route('/api/enso/open/config_dir')
@requires_auth
def get_enso_open_config_dir():
    os.startfile(config.ENSO_USER_DIR, "open")
    return ""


@app.route('/api/enso/get/ensorc')
@requires_auth
def get_enso_get_ensorc():
    return send_from_directory(config.ENSO_USER_DIR, "ensorc.py")


@app.route('/api/enso/set/ensorc', methods=["POST"])
@requires_auth
def post_enso_set_ensorc():
    with open(os.path.join(config.ENSO_USER_DIR, "ensorc.py"), "wb") as ensorc:
        ensorc.write(request.form["ensorc"].encode("utf-8"))
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

        output = output + [cmdJSON]
    return json.dumps(output)


@app.route('/api/enso/get/user_command_categories')
@requires_auth
def get_enso_commands_categories():
    commands_dir = os.path.join(config.ENSO_USER_DIR, "commands")
    categories = []
    for f in os.listdir(commands_dir):
        if f.endswith(".py"):
            categories = categories + [os.path.splitext(f)[0]]
    return json.dumps(categories)


@app.route('/api/enso/commands/delete_category/<value>')
@requires_auth
def get_enso_commands_create_category(value):
    category_file = os.path.join(config.ENSO_USER_DIR, "commands", value + ".py")
    if os.path.exists(category_file):
        os.remove(category_file)
    return ""


@app.route('/api/enso/commands/write_category/<value>', methods=["POST"])
@requires_auth
def post_enso_commands_write_category(value):
    category_file = os.path.join(config.ENSO_USER_DIR, "commands", value + ".py")

    with open(category_file, "wb") as cat:
        cat.write(request.form["code"].encode("utf-8"))

    ScriptTracker.get().setPendingChanges()

    return ""


@app.route('/api/enso/commands/read_category/<value>')
@requires_auth
def get_enso_commands_read_category(value):
    return send_from_directory(os.path.join(config.ENSO_USER_DIR, "commands"), value + ".py")


@app.route('/api/enso/commands/disable/<command>')
@requires_auth
def get_enso_commands_disable(command):
    if command not in config.DISABLED_COMMANDS:
        config.DISABLED_COMMANDS += [command]
        config.COMMAND_STATE_CHANGED = True
        config.storeValue("DISABLED_COMMANDS", config.DISABLED_COMMANDS)
    return ""


@app.route('/api/enso/commands/enable/<command>')
@requires_auth
def get_enso_commands_enable(command):
    if command in config.DISABLED_COMMANDS:
        config.DISABLED_COMMANDS.remove(command)
        config.COMMAND_STATE_CHANGED = True
        config.storeValue("DISABLED_COMMANDS", config.DISABLED_COMMANDS)
    return ""


@app.route('/api/enso/write_tasks', methods=["POST"])
@requires_auth
def post_enso_commands_write_tasks():
    category_file = os.path.join(config.ENSO_USER_DIR, "tasks.py")

    with open(category_file, "wb") as tasks:
        tasks.write(request.form["code"].encode("utf-8"))
    return ""


@app.route('/api/enso/read_tasks')
@requires_auth
def get_enso_commands_read_tasks():
    return send_from_directory(config.ENSO_USER_DIR, "tasks.py")


class Httpd(threading.Thread):

    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server(HOST, PORT, app, True)
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
