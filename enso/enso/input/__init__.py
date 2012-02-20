import enso.providers

_input = enso.providers.getInterface( "input" )

for attrName in _input.__dict__.keys():
    if not attrName.startswith( "_" ) and attrName.upper() == attrName:
        # It's a public, all-uppercase constant; import it into our
        # namespace.
        globals()[attrName] = getattr( _input, attrName )

# Import the InputManager class into our namespace.
InputManager = _input.InputManager
