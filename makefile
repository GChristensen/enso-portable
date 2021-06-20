.DEFAULT_GOAL := all

# this target should be made from msys2 shell invoked through msys2_shell.cmd -use-full-path
# from the appropriate (x86/x64) Visual Studio Developer Command Prompt
# it is not required to build platform binaries
cairo:
	#cd platform/win32/graphics/cairo; sh build.sh
	cd platform/win32/graphics/cairo; sh build.sh x64

.PHONY: platform
platform:
	cd platform; scons
	cp -f platform/enso/platform/win32/cairo/_cairo.pyd enso/enso/platform/win32/cairo/_cairo.pyd
	cp -f platform/enso/platform/win32/graphics/_TransparentWindow.pyd enso/enso/platform/win32/graphics/_TransparentWindow.pyd
	cp -f platform/enso/platform/win32/input/_AsyncEventThread.pyd enso/enso/platform/win32/input/_AsyncEventThread.pyd
	cp -f platform/enso/platform/win32/input/_InputManager.pyd enso/enso/platform/win32/input/_InputManager.pyd
	cp -f platform/enso/platform/win32/selection/_ClipboardBackend.pyd enso/enso/platform/win32/selection/_ClipboardBackend.pyd
	cp -f platform/enso/platform/win32/AsyncEventProcessorRegistry.dll enso/enso/platform/win32/AsyncEventProcessorRegistry.dll
	cp -f platform/enso/platform/win32/CLogging.dll enso/enso/platform/win32/CLogging.dll
	cp -f platform/enso/platform/win32/Keyhook.dll enso/enso/platform/win32/Keyhook.dll

.PHONY: all
all:
	#mingw32-make cairo
	mingw32-make platform

.PHONY: clean-platform
clean-platform:
	cd platform; scons -c
	rm -r -f platform/enso
	find platform -name "*.ilk" -type f -delete
	find platform -name "*.pdb" -type f -delete
	find platform -name "*.dblite" -type f -delete