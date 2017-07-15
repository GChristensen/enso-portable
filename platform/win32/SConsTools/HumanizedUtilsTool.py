import os

from Helpers import addInstanceMethodToEnv

def makeRootRelativePath( env, path ):
    """
    Takes a path relative to the current working directory and
    converts it to a root-relative path (e.g., a path beginning
    with a hash symbol).
    """

    return "#%s" % env.Dir( path ).path

def addLib( env,
            basePath = None,
            libPath = None,
            includePath = None,
            **additionalVars ):
    """
    Adds the library and include paths for a library, as well as any
    other additional environment variables needed by the library.

    This provides us with a way to encapsulate all environment
    modifications needed by a library into a single method call.
    """

    if not basePath:
        basePath = ""
    if not libPath:
        libPath = ""
    if not includePath:
        includePath = ""

    libPath = os.path.join( basePath, libPath )
    includePath = os.path.join( basePath, includePath )

    if includePath != "" and not env["CPPPATH"].count( includePath ):
        env["CPPPATH"].append( includePath )

    if libPath != "" and not env["LIBPATH"].count( libPath ):
        env["LIBPATH"].append( libPath )

    for key in additionalVars.keys():
        env[key] = additionalVars[key]

def generate( env ):
    addInstanceMethodToEnv( env, makeRootRelativePath )
    addInstanceMethodToEnv( env, addLib )

def exists( env ):
    return 1
