cmake_minimum_required(VERSION 3.19)
set(CMAKE_CXX_STANDARD 20)

include(cmake/prelude.cmake)

project(
        gaussianfft
        DESCRIPTION "GaussianFFT"
        HOMEPAGE_URL "https://github.com/equinor/gaussianfft"
        LANGUAGES CXX
)

include(cmake/project-is-top-level.cmake)
include(cmake/variables.cmake)
include(cmake/utilities.cmake)

# Which versions of dependencies to use
option(USE_FFTW3 "Use FFTW3 instead of Intel MKL (default on Apple Silicon)")
if (APPLE AND ${CMAKE_HOST_SYSTEM_PROCESSOR} STREQUAL "arm64")
    message(WARNING "Intel MKL is not supported on Apple Silicon; using FFTW3 instead")
    set(USE_FFT3 ON)
endif ()
if (USE_FFT3)
    option(FFTW_VERSION "Which version of FFTW to compile against")
    if (NOT FFTW_VERSION)
        set(FFTW_VERSION "3.3.10")
    endif ()
endif ()

option(BOOST_VERSION "Configure the specific version of Boost gaussianfft wil be statically linked against")
if (NOT BOOST_VERSION)
    execute_process(COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/bin/find_boost_version.py OUTPUT_VARIABLE BOOST_VERSION)
endif ()


if (NOT DEFINED SKBUILD)
    message(WARNING "Not building with scikit-build")
    include(cmake/python-venv.cmake)
endif ()
set(Python3_USE_STATIC_LIBS ON)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module NumPy)
include_directories(SYSTEM ${Python3_INCLUDE_DIRS})


include(cmake/mkl-fftw.cmake)

include(cmake/boost.cmake)

# ---- Copy source files ----
if (NOT EXISTS ${CMAKE_BINARY_DIR}/src)
    file(COPY ${CMAKE_SOURCE_DIR}/src DESTINATION ${CMAKE_BINARY_DIR}/)
endif ()

# ---- Declare library ----
set(CMAKE_SHARED_LIBRARY_PREFIX "")

add_compile_definitions(FLENS_FIRST_INDEX="0")
add_compile_definitions(VECLIB)
add_compile_definitions(ACCELERATE_NEW_LAPACK="1")
add_compile_definitions(ACCELERATE_LAPACK_ILP64="1")

if (APPLE)
    set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")
endif ()

dependants(SOURCE_FILES_LIST src/gaussfftinterface.cpp)

add_library(
        gaussianfft_gaussianfft
        SHARED
        ${SOURCE_FILES_LIST}
)
add_library(gaussianfft::gaussianfft ALIAS gaussianfft_gaussianfft)

if (NOT BUILD_SHARED_LIBS)
    target_compile_definitions(gaussianfft_gaussianfft PUBLIC GAUSSIANFFT_STATIC_DEFINE)
endif ()

if (APPLE)
    # We need to explicitly link with libpython.dylib on macOS
    target_link_libraries(gaussianfft_gaussianfft PRIVATE Python3::Module)
endif ()

set_target_properties(
        gaussianfft_gaussianfft PROPERTIES
        CXX_VISIBILITY_PRESET hidden
        CXX_STANDARD 17
        VISIBILITY_INLINES_HIDDEN YES
        EXPORT_NAME _gaussianfft
        OUTPUT_NAME _gaussianfft
)

target_link_libraries(
        gaussianfft_gaussianfft
        PRIVATE
        ${Boost_LIBRARIES}
)
if (${CMAKE_HOST_SYSTEM_PROCESSOR} STREQUAL "arm64")
    target_link_libraries(gaussianfft_gaussianfft PRIVATE fftw3 fftw3f)
else ()
    if (APPLE)
        target_link_libraries(gaussianfft_gaussianfft PRIVATE
                # TODO: Make @rpath/libiomp.dylib work as expected
                #       with the version installed on the target system, and
                #       not the one it was built with (absolute path)
                #       Until then, we use `mkl_sequential`
                mkl_intel_ilp64
                #mkl_intel_thread
                mkl_sequential
                mkl_core
                #iomp5
        )
    else ()
        # Presumably Linux x86
        target_link_libraries(gaussianfft_gaussianfft PRIVATE
                -Wl,--start-group
                mkl_intel_ilp64
                mkl_gnu_thread
                mkl_core
                -Wl,--end-group
                gomp
        )
    endif ()
    target_link_libraries(gaussianfft_gaussianfft PRIVATE
            pthread
            m
            dl
    )
endif ()

# ---- Install rules ----

if (DEFINED SKBUILD)
    install(
            TARGETS gaussianfft_gaussianfft
            DESTINATION ${SKBUILD_PLATLIB_DIR}
    )
endif ()

# ---- Developer mode ----

if (NOT gaussianfft_DEVELOPER_MODE)
    return()
elseif (NOT PROJECT_IS_TOP_LEVEL)
    message(
            AUTHOR_WARNING
            "Developer mode is intended for developers of gaussianfft"
    )
endif ()

#include(cmake/dev-mode.cmake)
