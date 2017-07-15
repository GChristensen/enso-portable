import os
import types

def addInstanceMethodToEnv( env, function ):
    """
    Adds the given function as an instance method to the given SCons
    environment.
    """

    envClass = env.__class__
    methodName = function.__name__

    # Make sure the class doesn't already have a method by the same
    # name--at least, not one that we didn't create. (We may be asked
    # to install the same method into the same class more than once,
    # if the Tool that calls us is added to more than one SCons
    # Environment.)
    wrappedFuncAttr = "wrappedFunction"
    if hasattr( envClass, methodName ):
        method = getattr( envClass, methodName )
        isMethodOurs = False
        if hasattr( method, "im_func" ):
            if hasattr( method.im_func, wrappedFuncAttr ):
                wrappedFunc = getattr( method.im_func, wrappedFuncAttr )
                if wrappedFunc == function:
                    isMethodOurs = True
        if not isMethodOurs:
            raise AssertionError(
                "A method by the name %s must not already exist" % methodName
            )

    # This part is weird because we're actually adding an unbound
    # method into the instance's class.  Because the method is being
    # added by a Tool that may not be installed in all Environments,
    # we need to add a flag to the environment saying "yes, the method
    # is supposed to exist in this environment", and have our method
    # wrapper check for this flag on its Environment instance whenever
    # it's called.  If the flag's not there, then the Tool that called
    # us wasn't actually installed in this Environment instance, so we
    # need to throw an AttributeError.
    addedMethodFlag = "ADDED_METHOD_%s" % methodName

    def methodWrapper( self, *args, **kwargs ):
        if not self.has_key( addedMethodFlag ):
            raise AttributeError(
                "%s instance has no attribute '%s'" % ( envClass.__name__,
                                                        methodName )
                )
        else:
            return function( self, *args, **kwargs )

    # Add the signature that tells us what function our method wraps.
    setattr( methodWrapper, wrappedFuncAttr, function )

    # Add the flag that identifies this particular environment
    # instance as having this method installed.
    env[addedMethodFlag] = True

    # Now create the unbound method object and add it to the
    # Environment's class.
    method = types.MethodType( methodWrapper, None, envClass )
    setattr( envClass, methodName, method )

def findFileWithExtensionInNodeList( nodeList,
                                     possibleExtensions ):
    """
    Returns the SCons Node in the given SCons NodeList that has an
    extension in the given list.  There can only be at most one
    such file, or else a RuntimeError will be raised.
    """

    filteredList = []
    for node in nodeList:
        nodeFileExt = os.path.splitext( str(node) )[1].lower()
        if nodeFileExt in possibleExtensions:
            filteredList.append( node )
    if len( filteredList ) == 0:
        raise RuntimeError( "No files with extension %s found in "
                            "node list." % possibleExtensions )
    elif len( filteredList ) > 1:
        raise RuntimeError( "Multiple files with extension %s found in "
                            "node list." % possibleExtensions )
    return filteredList[0]
