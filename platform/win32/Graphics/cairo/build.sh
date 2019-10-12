#! bash
set -e
trap 'previous_command=$this_command; this_command=$BASH_COMMAND' DEBUG
trap 'echo FAILED COMMAND: $previous_command' EXIT

# Versions used
USE_FREETYPE=1

# Set variables according to command line argument
if [ ${1:-x86} = x64 ]; then
    MSVC_PLATFORM_NAME=x64
    OUTPUT_PLATFORM_NAME=x64
else
    MSVC_PLATFORM_NAME=Win32
    OUTPUT_PLATFORM_NAME=x86
fi

# Make sure the MSVC linker appears first in the path
MSVC_LINK_PATH=`whereis link | sed "s| /usr/bin/link.exe||" | sed "s|.*\(/c.*\)link.exe.*|\1|"`
export PATH="$MSVC_LINK_PATH:$PATH"

# Build libpng and zlib
cd libpng
sed s/zlib-1.2.8/zlib/ projects/vstudio/zlib.props > zlib.props.fixed
sed "s/<TreatWarningAsError>true<\/TreatWarningAsError>/<TreatWarningAsError>false<\/TreatWarningAsError>/" zlib.props.fixed > zlib.props.fixed2
mv zlib.props.fixed2 projects/vstudio/zlib.props
if [ ! -d "projects\vstudio\Backup" ]; then
    # Upgrade solution if not already
    devenv.com "projects\vstudio\vstudio.sln" -upgrade
fi
devenv.com "projects\vstudio\vstudio.sln" -build "Release Library|$MSVC_PLATFORM_NAME" -project libpng
cd ..
if [ $MSVC_PLATFORM_NAME = x64 ]; then
    cp "libpng/projects/vstudio/x64/Release Library/libpng16.lib" libpng/libpng.lib
    cp "libpng/projects/vstudio/x64/Release Library/zlib.lib" zlib/zlib.lib
else
    cp "libpng/projects/vstudio/Release Library/libpng16.lib" libpng/libpng.lib
    cp "libpng/projects/vstudio/Release Library/zlib.lib" zlib/zlib.lib
fi

# Build pixman
cd pixman
sed s/-MD/-MT/ Makefile.win32.common > Makefile.win32.common.fixed
mv Makefile.win32.common.fixed Makefile.win32.common
if [ $MSVC_PLATFORM_NAME = x64 ]; then
    # pass -B for switching between x86/x64
    make pixman -B -f Makefile.win32 "CFG=release" "MMX=off"
else
    make pixman -B -f Makefile.win32 "CFG=release"
fi
cd ..

if [ $USE_FREETYPE -ne 0 ]; then
    cd freetype
    # Build freetype
    if [ ! -d "builds/windows/vc2010/Backup" ]; then
        # Upgrade solution if not already
        devenv.com "builds/windows/vc2010/freetype.sln" -upgrade
    fi
    devenv.com "builds/windows/vc2010/freetype.sln" -build "Release Static|$MSVC_PLATFORM_NAME"
    cp "`ls -1d "objs/$MSVC_PLATFORM_NAME/Release Static/freetype.lib"`" .
    cd ..
fi

# Build cairo
cd cairo
sed 's/-MD/-MT/;s/zdll.lib/zlib.lib/' build/Makefile.win32.common > Makefile.win32.common.fixed
mv Makefile.win32.common.fixed build/Makefile.win32.common
if [ $USE_FREETYPE -ne 0 ]; then
    sed '/^CAIRO_LIBS =/s/$/ $(top_builddir)\/..\/freetype\/freetype.lib/;/^DEFAULT_CFLAGS =/s/$/ -I$(top_srcdir)\/..\/freetype\/include/' build/Makefile.win32.common > Makefile.win32.common.fixed
else
    sed '/^CAIRO_LIBS =/s/ $(top_builddir)\/..\/freetype\/freetype.lib//;/^DEFAULT_CFLAGS =/s/ -I$(top_srcdir)\/..\/freetype\/include//' build/Makefile.win32.common > Makefile.win32.common.fixed
fi
mv Makefile.win32.common.fixed build/Makefile.win32.common
sed "s/CAIRO_HAS_FT_FONT=./CAIRO_HAS_FT_FONT=$USE_FREETYPE/" build/Makefile.win32.features > Makefile.win32.features.fixed
mv Makefile.win32.features.fixed build/Makefile.win32.features
# pass -B for switching between x86/x64
make -B -f Makefile.win32 cairo "CFG=release"
cd ..

# Package headers with DLL
OUTPUT_FOLDER=output/${CAIRO_VERSION/cairo-/cairo-windows-}
mkdir -p $OUTPUT_FOLDER/include
for file in cairo/cairo-version.h \
            cairo/src/cairo-features.h \
            cairo/src/cairo.h \
            cairo/src/cairo-deprecated.h \
            cairo/src/cairo-win32.h \
            cairo/src/cairo-script.h \
            cairo/src/cairo-ps.h \
            cairo/src/cairo-pdf.h \
            cairo/src/cairo-svg.h; do
    cp $file $OUTPUT_FOLDER/include
done
if [ $USE_FREETYPE -ne 0 ]; then
    cp cairo/src/cairo-ft.h $OUTPUT_FOLDER/include
fi
mkdir -p $OUTPUT_FOLDER/lib/$OUTPUT_PLATFORM_NAME
cp cairo/src/release/cairo.lib $OUTPUT_FOLDER/lib/$OUTPUT_PLATFORM_NAME
cp cairo/src/release/cairo.dll $OUTPUT_FOLDER/lib/$OUTPUT_PLATFORM_NAME
cp cairo/COPYING* $OUTPUT_FOLDER

trap - EXIT
echo 'Success!'