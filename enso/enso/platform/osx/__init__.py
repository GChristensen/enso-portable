import sys

import enso.platform

if sys.platform != "darwin":
    raise enso.platform.PlatformUnsupportedError()



def provideInterface( name ):
    if name == "input":
        import enso.platform.osx.input
        return enso.platform.osx.input
    elif name == "graphics":
        import enso.platform.osx.graphics
        return enso.platform.osx.graphics
    elif name == "cairo":
        import enso.platform.osx.cairo
        return enso.platform.osx.cairo
    elif name == "selection":
        import enso.platform.osx.selection
        return enso.platform.osx.selection
    elif name == "scripts_folder":
        from enso.platform.osx.scriptfolder import get_script_folder_name
        return get_script_folder_name
    else:
        return None
