import os
import re
import SCons.Builder
import SCons.Scanner

from Helpers import addInstanceMethodToEnv

def buildSwigExtension( env,
                        swigInterfaceFile,
                        source = None,
                        isCpp = True,
                        **kwargs ):
    """
    Builds a SWIG extension by calling a SwigC/SwigCpp builder
    method and then a SharedLibrary builder method.
    """

    if isCpp:
        # We need to dynamically determine swigWrapper and pyFile
        # because the returned targets may contain a variable
        # number of files--if directors are enabled.
        files = env.SwigCpp( source=swigInterfaceFile )
        swigWrapper = [ f for f in files
                        if f.path.endswith( ".cxx" ) ][0]
        pyFile = [ f for f in files
                   if f.path.endswith( ".py" ) ][0]
    else:
        swigWrapper, pyFile = env.SwigC( source=swigInterfaceFile )

    sourceList = [swigWrapper]

    if source:
        sourceList.append( source )

    # If our SWIG interface file is "foo.i", our target file will
    # be "_foo".
    fileName = os.path.basename( swigInterfaceFile )
    targetFileName = "_%s" % os.path.splitext( fileName )[0]

    pydFile, libFile, expFile = env.SharedLibrary(
        target=targetFileName,
        source=sourceList,
        SHLIBSUFFIX = ".pyd",
        **kwargs
        )

    return [pydFile, pyFile]


# ----------------------------------------------------------------------------
# SWIG Builders and Scanner
# ----------------------------------------------------------------------------

# SWIG Builders

def swigBuilderModifyTargets( target, source, env ):
    """
    Emitter for the Swig Builder.
    """

    # Assign param to dummy variable to ensure that pychecker
    # doesn't complain.
    _ = env

    for i in source:
        name = str( i )[:-2]

        # If directors are enabled, then add the "*_wrap.h" file as a
        # target.
        text = i.get_contents()
        if text.find( b"\"director\"" ) != -1:
            target.append( "%s_wrap.h" % name )

        # Add the "*.py" file as a target.
        target.append( "%s.py" % name )
    return target, source

def swigBuilderGenerator( source, target, env, for_signature ):
    """
    Generator for the Swig Builder.
    """

    # Assign param to dummy variable to ensure that pychecker
    # doesn't complain.
    _ = for_signature
    
    import os.path
    sourceFile = str(source[0])
    targetFile = str(target[0])
    dirName = os.path.dirname( sourceFile )
    if len( dirName ) == 0:
        dirName = "."
    if targetFile.endswith( ".cxx" ):
        cmdStr = "\"${SWIG}\" -c++"
    else:
        cmdStr = "\"${SWIG}\""

    # Read the environment's CPPPATH and turn that into the Swig
    # include path.

    if env.has_key( "CPPPATH" ):
        for includeDirName in env["CPPPATH"]:
            # Expand out those variables and "#" characters.
            includeDirName = env.Dir( env.subst(includeDirName) ).path
            cmdStr += ' "-I%s"' % includeDirName

    cmdStr += " -Werror -outdir %s -python %s"
    finalCmd = cmdStr % ( dirName, sourceFile )
    return finalCmd

swigCBuilder = SCons.Builder.Builder(
    generator = swigBuilderGenerator,
    suffix = "_wrap.c",
    src_suffix = ".i",
    emitter = swigBuilderModifyTargets
    )

swigCppBuilder = SCons.Builder.Builder(
    generator = swigBuilderGenerator,
    suffix = "_wrap.cxx",
    src_suffix = ".i",
    emitter = swigBuilderModifyTargets
    )

# SWIG Scanner

swigInterfaceFileRe = re.compile( r'%include\s+"(.*)"' )

def swigInterfaceFileScan( node, env, path, arg = None ):
    """
    Main function for Swig interface (.i) file Scanner.
    """
    
    # Assign param to dummy variable to ensure that pychecker
    # doesn't complain.
    _ = arg

    contents = node.get_contents()
    includedFiles = swigInterfaceFileRe.findall( contents )
    implicitDependencies = [ fileName for fileName in includedFiles
                             if fileName.endswith( ".h" ) ]

    theFiles = []

    for fileName in implicitDependencies:
        pathFound = False
        for dirName in path:
            relPath = env.Dir( dirName ).abspath
            filePath = os.path.join( relPath, fileName )
            if os.path.exists( filePath ):
                theFiles.append( filePath )
                pathFound = True
                break
        if not pathFound:
            raise Exception( "Dependency '%s' mentioned in '%s' not found." %
                             (fileName, node.path) )

    return theFiles

def swigInterfaceFilePath( env, node, unknown1, unknown2 ):
    """
    Path function for Swig interface (.i) file Scanner.
    """

    # Assign params to dummy variables to ensure that pychecker
    # doesn't complain.
    _, _ = unknown1, unknown2

    return tuple( [node.path] + env["CPPPATH"] )

swigInterfaceFileScanner = SCons.Scanner.Scanner(
    function = swigInterfaceFileScan,
    path_function = swigInterfaceFilePath,
    skeys = [".i"]
    )

def generate( env ):
    # Add the Builders and Scanner to the environment.

    env.Append(
        BUILDERS = { "SwigC" : swigCBuilder,
                     "SwigCpp" : swigCppBuilder, },
        SCANNERS = swigInterfaceFileScanner,
        )
    addInstanceMethodToEnv( env, buildSwigExtension )

def exists( env ):
    if env.has_key( "SWIG" ):
        return 1
    else:
        return 0
