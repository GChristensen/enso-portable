import os, configparser
from ast import literal_eval

# the following files also can redefine variables in config.py
# ~/.ensorc file which is not available from WebUI (more secure option)
# ~/.enso/ensorc.py (can be got/set from WebUI)


CONFIG_VARS = None
CONFIG_SECTION = "General"


def storeValue(key, value):
    """
    stores values in ~/.enso/enso.cfg file
    """
    parser = configparser.ConfigParser()
    parser.optionxform = str

    if os.path.exists(CONFIG_VARS["CONFIG_FILE"]):
        parser.read(CONFIG_VARS["CONFIG_FILE"])
    else:
        parser.add_section(CONFIG_SECTION)

    if key == "DISABLED_COMMANDS":
        parser[CONFIG_SECTION][key] = ",".join(value)
    else:
        parser[CONFIG_SECTION][key] = str(value)

        try:
            CONFIG_VARS[key] = literal_eval(value)
        except:
            CONFIG_VARS[key] = value

    with open(CONFIG_VARS["CONFIG_FILE"], 'w') as stream:
        parser.write(stream)


def init(vars):
    """
    sets variables in config.py from ~/.enso/enso.cfg file
    """
    global CONFIG_VARS
    CONFIG_VARS = vars

    configFile = CONFIG_VARS["CONFIG_FILE"]

    if os.path.exists(configFile):
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(configFile)

        for key in parser[CONFIG_SECTION].keys():
            if key == "DISABLED_COMMANDS":
                if parser[CONFIG_SECTION][key]:
                    CONFIG_VARS[key] = parser[CONFIG_SECTION][key].split(",")
            else:
                try:
                    CONFIG_VARS[key] = literal_eval(parser[CONFIG_SECTION][key])
                except:
                    CONFIG_VARS[key] = parser[CONFIG_SECTION][key]
