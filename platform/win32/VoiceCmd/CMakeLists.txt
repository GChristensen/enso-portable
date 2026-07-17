cmake_minimum_required(VERSION 3.24)
project(voicecmd LANGUAGES CXX)

# C++20 is the floor the core needs (std::variant / future / optional).
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(VOICECMD_BUILD_TESTS  "Build core unit tests"              ON)
option(VOICECMD_BUILD_SAPI   "Build the SAPI backend (Windows)"   OFF)
option(VOICECMD_BUILD_PYTHON "Build the pybind11 abi3 module"     OFF)
option(VOICECMD_PY_ABI3      "Python module: single portable abi3 binary" ON)

find_package(Threads REQUIRED)

# ---- core (backend-agnostic, Python-free, COM-free) ----
add_library(voicecmd_core STATIC
    src/core/engine.cpp)
target_include_directories(voicecmd_core PUBLIC include)
target_link_libraries(voicecmd_core PUBLIC Threads::Threads)
if (MSVC)
    target_compile_options(voicecmd_core PRIVATE /W4 /permissive-)
endif()

# The Python module needs the real backend, so building it implies SAPI on Win32.
set(_build_sapi ${VOICECMD_BUILD_SAPI})
if (VOICECMD_BUILD_PYTHON AND WIN32)
    set(_build_sapi ON)
endif()

# ---- SAPI backend (M2) ----
if (_build_sapi AND WIN32)
    add_library(voicecmd_sapi STATIC
        src/backend/sapi/sapi_backend.cpp)
    target_include_directories(voicecmd_sapi PUBLIC include src/backend/sapi)
    # SAPI GUIDs come from initguid.h in the .cpp, so no sapi.lib needed.
    target_link_libraries(voicecmd_sapi PUBLIC voicecmd_core ole32 oleaut32)
    if (MSVC)
        target_compile_options(voicecmd_sapi PRIVATE /permissive-)
    endif()

    # Link + runtime smoke check for the SAPI backend.
    add_executable(voicecmd_sapi_smoke tests/sapi_smoke.cpp)
    target_link_libraries(voicecmd_sapi_smoke PRIVATE voicecmd_sapi voicecmd_core)
endif()

# ---- nanobind module (M3) ----
# nanobind (not pybind11) because pybind11 under Py_LIMITED_API triggers an MSVC
# 14.44 internal compiler error. Default: STABLE_ABI => a single portable abi3
# binary importable on any CPython >= 3.10. nanobind_add_module handles the
# stable-ABI define, python3.lib linkage, MSVC conformance flags, bigobj and the
# extension suffix. Fallback (VOICECMD_PY_ABI3=OFF): a version-specific module.
if (VOICECMD_BUILD_PYTHON)
    set(_py_components Interpreter Development.Module)
    if (VOICECMD_PY_ABI3)
        list(APPEND _py_components Development.SABIModule)
    endif()
    find_package(Python 3.10 REQUIRED COMPONENTS ${_py_components})
    find_package(nanobind CONFIG REQUIRED)

    if (VOICECMD_PY_ABI3)
        nanobind_add_module(voicecmd STABLE_ABI NB_STATIC src/python/module.cpp)
    else()
        nanobind_add_module(voicecmd NB_STATIC src/python/module.cpp)
    endif()

    target_link_libraries(voicecmd PRIVATE voicecmd_core)
    # Fake backend is header-only; SAPI is the real one on Windows.
    target_include_directories(voicecmd PRIVATE src/backend/fake)
    if (_build_sapi AND WIN32)
        target_link_libraries(voicecmd PRIVATE voicecmd_sapi)
        target_include_directories(voicecmd PRIVATE src/backend/sapi)
        target_compile_definitions(voicecmd PRIVATE VOICECMD_HAS_SAPI=1)
    endif()

    # Optional deploy: drop the built voicecmd.pyd into Enso's contrib package
    # (shadowing the renamed voicecmd_mock.py). Defaults to the sibling checkout.
    set(VOICECMD_ENSO_CONTRIB_DIR "${CMAKE_SOURCE_DIR}/../../../enso/enso/contrib"
        CACHE PATH "Enso contrib dir to copy voicecmd.pyd into (empty to skip)")
    if (VOICECMD_ENSO_CONTRIB_DIR AND EXISTS "${VOICECMD_ENSO_CONTRIB_DIR}")
        # Non-fatal: a running Enso holds the .pyd, which must not break the build.
        add_custom_command(TARGET voicecmd POST_BUILD
            COMMAND ${CMAKE_COMMAND}
                    -DSRC=$<TARGET_FILE:voicecmd>
                    -DDST=${VOICECMD_ENSO_CONTRIB_DIR}/voicecmd.pyd
                    -P ${CMAKE_SOURCE_DIR}/cmake/deploy_pyd.cmake
            COMMENT "Deploying voicecmd.pyd -> ${VOICECMD_ENSO_CONTRIB_DIR}")
    endif()
endif()

# ---- tests (M1) ----
if (VOICECMD_BUILD_TESTS)
    enable_testing()
    add_executable(voicecmd_tests tests/test_core.cpp)
    target_include_directories(voicecmd_tests PRIVATE
        include tests src/backend/fake)
    target_link_libraries(voicecmd_tests PRIVATE voicecmd_core)
    if (MSVC)
        target_compile_options(voicecmd_tests PRIVATE /W4 /permissive-)
    endif()
    add_test(NAME core COMMAND voicecmd_tests)
endif()
