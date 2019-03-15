.PHONY: platform
platform:
	cd platform; scons.bat
	cp -f platform/enso/platform/win32/cairo/_cairo.pyd enso/enso/platform/win32/cairo/_cairo.pyd
	cp -f platform/enso/platform/win32/graphics/_TransparentWindow.pyd enso/enso/platform/win32/graphics/_TransparentWindow.pyd
	cp -f platform/enso/platform/win32/input/_AsyncEventThread.pyd enso/enso/platform/win32/input/_AsyncEventThread.pyd
	cp -f platform/enso/platform/win32/input/_InputManager.pyd enso/enso/platform/win32/input/_InputManager.pyd
	cp -f platform/enso/platform/win32/selection/_ClipboardBackend.pyd enso/enso/platform/win32/selection/_ClipboardBackend.pyd
	cp -f platform/enso/platform/win32/AsyncEventProcessorRegistry.dll enso/enso/platform/win32/AsyncEventProcessorRegistry.dll
	cp -f platform/enso/platform/win32/CLogging.dll enso/enso/platform/win32/CLogging.dll
	cp -f platform/enso/platform/win32/Keyhook.dll enso/enso/platform/win32/Keyhook.dll
	cp -f platform/enso/platform/win32/freetype2.dll enso/enso/platform/win32/freetype2.dll
	cp -f platform/enso/platform/win32/libcairo-2.dll enso/enso/platform/win32/libcairo-2.dll

.PHONY: clean-platform
clean-platform:
	cd platform; scons.bat -c
	rm -r -f platform/enso
	find platform -name "*.ilk" -type f -delete
	find platform -name "*.pdb" -type f -delete
	find platform -name "*.dblite" -type f -delete