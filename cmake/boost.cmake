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
if (NOT EXISTS ${CMAKE_BINARY_DIR}/sources/boost/${BOOST_VERSION})
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
    execute_process(COMMAND ${Boost_COMPILE_SCRIPT} ${BOOST_VERSION} COMMAND_ERROR_IS_FATAL ANY)
else ()
    message(STATUS "Reusing compiled boost libraries at ${Boost_LIBRARY_DIR}")
endif ()

include_directories(SYSTEM ${Boost_DIR})

find_package(Boost
        ${BOOST_VERSION} EXACT
        REQUIRED
        COMPONENTS python numpy filesystem system
        PATHS ${Boost_LIBRARY_DIR}/cmake
)
