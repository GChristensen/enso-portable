import enso.providers

__cairoImpl = enso.providers.getInterface( "cairo" )

globals().update( __cairoImpl.__dict__ )
