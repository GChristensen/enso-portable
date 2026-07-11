import enso.providers

_input = enso.providers.getInterface( "input" )

for attrName in list(_input.__dict__.keys()):
    if not attrName.startswith( "_" ) and attrName.upper() == attrName:
        # It's a public, all-uppercase constant; import it into our
        # namespace.
        globals()[attrName] = getattr( _input, attrName )

# Import the InputManager class into our namespace.
InputManager = _input.InputManager

# Platform-specific key state query with win32 GetKeyState() semantics:
# negative return means the key is currently held down, low bit set means
# the key's toggle state (Caps Lock/Num Lock) is on.  Providers that don't
# implement it degrade to "not pressed / not toggled".
getKeyState = getattr( _input, "getKeyState", lambda keyCode: 0 )