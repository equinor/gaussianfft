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

option(FFTW_DEBUG "Flag to add methods for writing the FFT grid to file. Requires Boost" OFF)
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(FFTW_DEBUG ON)
    # TODO: Move this logic into CMakePresets.json
endif ()
set(FFTW_DEBUG OFF)
if (FFTW_DEBUG)
    set(BOOST_VERSION "1.81.0" CACHE STRING "Configure the specific version of Boost gaussianfft wil be statically linked against")
endif ()

option(USE_ARM_PERFORMANCE_LIBRARY "Use ARM Performance Library's FFT functionality on ARM-based builds" ON)
if (${USE_ARM_PERFORMANCE_LIBRARY})
    set(ARMPL_VERSION "23.10" CACHE STRING "Which version of ARM Performance Libraries to Use")
endif ()

if (NOT DEFINED SKBUILD)
    message(STATUS "Not building with scikit-build; using a local virtual environment instead")
    include(cmake/python-venv.cmake)
endif ()
set(Python3_USE_STATIC_LIBS ON)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED PATHS ${Python3_SITELIB}/pybind11)
include_directories(SYSTEM ${Python3_INCLUDE_DIRS})


include(cmake/fftw.cmake)

# ---- Copy source files ----
file(COPY ${CMAKE_SOURCE_DIR}/src DESTINATION ${CMAKE_BINARY_DIR}/)

if (FFTW_DEBUG)
    add_compile_definitions(FFTW_DEBUG)
    find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
    # ./bin/fetch-boost.sh requires access to the source code when it searches through src/gaussfftinterface.cpp
    include(cmake/boost.cmake)
endif ()

# ---- Declare library ----
set(CMAKE_SHARED_LIBRARY_PREFIX "")
set(CMAKE_POSITION_INDEPENDENT_CODE ON)  # equivalent to -fPIC

add_compile_definitions(FLENS_FIRST_INDEX="0")
add_compile_definitions(VECLIB)
add_compile_definitions(ACCELERATE_NEW_LAPACK="1")
add_compile_definitions(ACCELERATE_LAPACK_ILP64="1")

if (APPLE)
    set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")
endif ()

message(STATUS "Finding used source files")
dependants(SOURCE_FILES_LIST --use-preprocessor src/gaussfftinterface.cpp)

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
        pybind11::headers
        ${Boost_LIBRARIES}
)
if (${IS_AARCH64})
    if (USE_ARM_PERFORMANCE_LIBRARY)
        target_link_libraries(gaussianfft_gaussianfft PRIVATE
                # TODO: Make work with OpenMP / parallel
                armpl_lp64.a
                FortranDecimal
                FortranRuntime
                m
                c++
        )
    else ()
        message(WARNING "ARM based architectures are not yet supported")
    endif ()
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
