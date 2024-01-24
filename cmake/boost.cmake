if (NOT DEFINED BOOST_VERSION)
    message(FATAL_ERROR "Boost was requested, but no version was set. Use -DBOOST_VERSION")
endif ()
if (NOT ${BOOST_VERSION} MATCHES "^[0-9]\.[0-9]+\.[0-9]$")
    message(FATAL_ERROR "BOOST_VERSION does not match a sematic version;\n got '${BOOST_VERSION}', expect \\d.\\d.\\d")
endif ()

message(STATUS "Using version ${BOOST_VERSION} of Boost")

if (DEFINED ${SKBUILD_STATE} AND ${SKBUILD_STATE} STREQUAL "sdist" AND NOT EXISTS ${CMAKE_SOURCE_DIR}/sources/boost/${BOOST_VERSION})
    execute_process(
            COMMAND_ERROR_IS_FATAL ANY
            COMMAND ${CMAKE_SOURCE_DIR}/bin/fetch-boost.sh ${BOOST_VERSION}
    )
endif ()

message(STATUS "Prepare Boost")
set(ENV{PYTHON} ${Python3_EXECUTABLE})
file(COPY_FILE ${CMAKE_SOURCE_DIR}/bin/compile-boost.sh ${CMAKE_BINARY_DIR}/bin/compile-boost.sh ONLY_IF_DIFFERENT)
file(COPY_FILE ${CMAKE_SOURCE_DIR}/bin/fetch-boost.sh ${CMAKE_BINARY_DIR}/bin/fetch-boost.sh ONLY_IF_DIFFERENT)
file(COPY_FILE ${CMAKE_SOURCE_DIR}/utils.py ${CMAKE_BINARY_DIR}/utils.py ONLY_IF_DIFFERENT)
if (NOT EXISTS ${CMAKE_BINARY_DIR}/sources/boost/${BOOST_VERSION} AND EXISTS ${CMAKE_SOURCE_DIR}/sources/boost/${BOOST_VERSION})
    message(STATUS "Copying Boost source to build directory")
    file(
            COPY ${CMAKE_SOURCE_DIR}/sources/boost/${BOOST_VERSION}
            DESTINATION ${CMAKE_BINARY_DIR}/sources/boost/
            USE_SOURCE_PERMISSIONS
            FOLLOW_SYMLINK_CHAIN
    )
endif ()
set(Boost_COMPILE_SCRIPT ${CMAKE_BINARY_DIR}/bin/compile-boost.sh)
set(Boost_DIR ${CMAKE_BINARY_DIR}/sources/boost/${BOOST_VERSION})


set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)
set(BUILD_PYTHON_SUPPORT ON)
set(Boost_LIBRARY_DIR ${Boost_DIR}/stage/lib)
if (NOT EXISTS ${Boost_LIBRARY_DIR})
    message(STATUS "Compiling Boost")
    if (DEFINED APPLE AND "${APPLE}" AND ${BOOST_VERSION} STRLESS "1.76.0")
        message(WARNING "There are known problems compiling Boost prior to 1.76.0 on newer versions of macOS")
        # There is a problem with the C++11 check in tools/build/src/engine/build.sh
        # for Boost 1.74.0 on macOS; the script does not add the necessary include directories for clang
        # causing check_cxx11.cpp to fail by not finding <wchar.h>
        # This is not a problem in Boost 1.76.0 and newer
        set(ENV{NO_CXX11_CHECK} "1")
    endif ()
    execute_process(COMMAND ${Boost_COMPILE_SCRIPT} ${BOOST_VERSION} COMMAND_ERROR_IS_FATAL ANY)
else ()
    message(STATUS "Reusing compiled boost libraries at ${Boost_LIBRARY_DIR}")
endif ()

include_directories(SYSTEM ${Boost_DIR})

find_package(Boost
        ${BOOST_VERSION} EXACT
        REQUIRED
        COMPONENTS filesystem
        PATHS ${Boost_LIBRARY_DIR}/cmake
)
# Helper-macro to toggle whether boost is intentionally requested.
# When building on GitHub Action runners, boost is available and added to the system path
# It is used by boost-filesystem.hpp
add_compile_definitions(USE_BOOST)
