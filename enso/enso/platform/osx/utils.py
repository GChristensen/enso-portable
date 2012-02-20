# Miscellaneous OS X helper utilities

def sendMsg( receiver, *args ):
    """
    Sends a message to a PyObjC Objective-C receiver object.

    For instance, assume an Objective-C object called 'person', which
    can be sent a message of the following form:

      [person eatFood: @"spam" withSideDish: @"eggs"]

    When wrapped by PyObjC, 'person' would be represented as an object
    like this:

      >>> class MockPerson( object ):
      ...   def eatFood_withSideDish_( self, food, sideDish ):
      ...     print "Eating %s with %s." % (food, sideDish)
    
      >>> person = MockPerson()

    So the identical way to send a message to 'person' using PyObjC would
    be as follows:

      >>> person.eatFood_withSideDish_( 'spam', 'eggs' )
      Eating spam with eggs.

    However, this calling convention has a number of problems:

      * It impairs readability by making it difficult to match message
        parameters with their values.

      * When there are lots of parameters, it makes for function calls
        that are longer than PEP 8's maximum line length of 79
        characters.

      * It doesn't look much at all like the original Objective-C message.

    The sendMsg() function allows you to send a message to 'person' in a
    way that resolves most of these issues:

      >>> sendMsg( person, 'eatFood:', 'spam', 'withSideDish:', 'eggs' )
      Eating spam with eggs.
    """

    funcName, funcArgs = _split( *args )
    func = getattr( receiver, funcName )
    return func( *funcArgs )

def _split( *args ):
    """
    Takes the given sequence of alternating Objective-C parameter
    names and parameter values for a message and returns a tuple of
    the form (funcName, funcArgs), where funcName is the "munged"
    PyObjC function name for the Objective-C parameters and funcArgs
    is a tuple of arguments for the function.

    For example:

      >>> _split( 'nextEventMatchingMask:', 5,
      ...         'untilDate:', 0 )
      ('nextEventMatchingMask_untilDate_', (5, 0))

      >>> _split( "bad" )
      Traceback (most recent call last):
      ...
      AssertionError: Length of args must be a multiple of 2.
    """

    assert len( args ) / 2 == len(args) / 2.0, \
        "Length of args must be a multiple of 2."

    funcNameParts = []
    funcArgs = []

    for i in range( 0, len(args), 2 ):
        namePart = args[i].replace( ":", "_" )
        funcNameParts.append( namePart )
        funcArgs.append( args[i+1] )

    return ( "".join( funcNameParts ),
             tuple( funcArgs ) )

if __name__ == "__main__":
    import doctest

    doctest.testmod()
