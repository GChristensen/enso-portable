# Best-effort deploy of the built module into Enso's contrib dir. Never fails the
# build: if the destination .pyd is locked (Enso running with it loaded), just
# warn so the developer knows to close Enso and rebuild/redeploy.
execute_process(
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${SRC}" "${DST}"
    RESULT_VARIABLE _rc)
if (_rc EQUAL 0)
    message(STATUS "voicecmd: deployed -> ${DST}")
else()
    message(WARNING
        "voicecmd: could not deploy to ${DST} (is Enso running and holding the "
        ".pyd? close it and rebuild). Build itself is unaffected.")
endif()
