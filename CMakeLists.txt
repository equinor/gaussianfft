cmake_minimum_required(VERSION 3.23)
set(CMAKE_CXX_STANDARD 20)

#include(cmake/prelude.cmake)

# TODO: Generate automatically?

project(
    gaussianfft
    VERSION 1.1.1
    DESCRIPTION "GaussianFFT"
    HOMEPAGE_URL "https://github.com/equinor/gaussianfft"
    LANGUAGES CXX
)

if(NOT DEFINED SKBUILD)
  # TODO: Ensure Python is set up correctly
  message(WARNING "Not building with scikit-build")

  execute_process(
          COMMAND_ERROR_IS_FATAL ANY
          OUTPUT_VARIABLE Gaussianfft_ERROR
          COMMAND python3 -c "
import sys

if sys.prefix == sys.base_prefix:
    sys.stdout.write('Not in a virtual environment. Please create one')
")
  if(Gaussianfft_ERROR)
    if (NOT EXISTS ${CMAKE_BINARY_DIR}/venv)
      message(STATUS "Creating a new venv in ${CMAKE_BINARY_DIR}/venv")
      find_package(Python3 ${Python3_VERSION} REQUIRED COMPONENTS Interpreter)
      execute_process(COMMAND ${Python3_EXECUTABLE} "-m" "venv" "venv"
              WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
              COMMAND_ERROR_IS_FATAL ANY
      )
      unset(${Python3_EXECUTABLE})
    endif ()
    set(Python3_EXECUTABLE "${CMAKE_BINARY_DIR}/venv/bin/python")
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    message(STATUS ${Python3_EXECUTABLE})

    execute_process(
            COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_SOURCE_DIR}/pyproject.toml pyproject.toml
            COMMAND ${Python3_EXECUTABLE} -c "import tomllib" || ${Python3_EXECUTABLE} -m pip install toml
            COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/bin/install-build-requirements.py
            COMMAND_ERROR_IS_FATAL ANY
    )
  endif ()
endif()
find_package(Python3 REQUIRED COMPONENTS Development.Module NumPy)


# Configure Intel MKL & FFTW (for Apple M-series)
if (APPLE AND ${CMAKE_HOST_SYSTEM_PROCESSOR} STREQUAL "arm64")
  message(FATAL_ERROR "Apple Silicon is not yet supported")
else ()
  # MKL
  set(MKL_LINK "static")
  find_package(MKL CONFIG REQUIRED PATHS $ENV${MKLROOT})
  include_directories(SYSTEM ${MKL_ROOT}/include/fftw)
  link_directories(${MKL_ROOT}/lib)
endif ()

# Compile Boost
option(BOOST_VERSION "Configure the specific version of Boost gaussianfft wil be statically linked against")
if (NOT BOOST_VERSION)
  execute_process(COMMAND ${CMAKE_SOURCE_DIR}/bin/find_boost_version.py OUTPUT_VARIABLE BOOST_VERSION)
endif()
message(VERBOSE "Using version ${BOOST_VERSION} of Boost")

if (DEFINED ${SKBUILD_STATE} AND ${SKBUILD_STATE} STREQUAL "sdist" AND NOT EXISTS ${CMAKE_SOURCE_DIR}/sources/boost/${BOOST_VERSION})
  execute_process(
          COMMAND_ERROR_IS_FATAL ANY
          COMMAND ${CMAKE_SOURCE_DIR}/bin/fetch-boost.sh ${BOOST_VERSION}
  )
endif ()

# TODO: Work in CMAKE_BINARY_DIR
set(ENV{PYTHON} ${Python3_EXECUTABLE})
execute_process(COMMAND ${CMAKE_SOURCE_DIR}/bin/compile-boost.sh ${BOOST_VERSION} COMMAND_ERROR_IS_FATAL ANY)

#include(cmake/project-is-top-level.cmake)
#include(cmake/variables.cmake)

set(Boost_DIR ${CMAKE_SOURCE_DIR}/sources/boost/${BOOST_VERSION})
set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)
set(Boost_LIBRARY_DIR ${Boost_DIR}/stage/lib)

execute_process(COMMAND python -c "import sysconfig, sys; sys.stdout.write(sysconfig.get_paths()['include'])" OUTPUT_VARIABLE Python3_LIBRARIES)
include_directories(SYSTEM ${Boost_DIR})
include_directories(SYSTEM ${Python3_LIBRARIES})

# MKL stuff

find_package(Boost
        ${BOOST_VERSION} EXACT
        REQUIRED
        COMPONENTS python NumPy filesystem system
        PATHS ${Boost_LIBRARY_DIR}/cmake
)

# ---- Declare library ----
set(CMAKE_SHARED_MODULE_PREFIX "")


add_library(
    gaussianfft_gaussianfft
    MODULE
    src/gaussfftinterface.cpp
    src/gaussfft.cpp
    src/gaussfft.hpp
    src/nrlib/exception/exception.hpp
    src/nrlib/fft/fft.cpp
    src/nrlib/fft/fft.hpp
    src/nrlib/fft/fftgrid2d.cpp
    src/nrlib/fft/fftgrid2d.hpp
    src/nrlib/fft/fftgrid3d.cpp
    src/nrlib/fft/fftgrid3d.hpp
    src/nrlib/grid/grid.hpp
    src/nrlib/grid/grid2d.hpp
    src/nrlib/iotools/fileio.cpp
    src/nrlib/iotools/fileio.hpp
    src/nrlib/iotools/stringtools.cpp
    src/nrlib/iotools/stringtools.hpp
    src/nrlib/math/constants.cpp
    src/nrlib/math/constants.hpp
    src/nrlib/random/dSFMT.cpp
    src/nrlib/random/dSFMT.h
    src/nrlib/random/random.cpp
    src/nrlib/random/random.hpp
    src/nrlib/random/randomgenerator.cpp
    src/nrlib/random/randomgenerator.hpp
    src/nrlib/surface/regularsurface.hpp
    src/nrlib/surface/regularsurfacerotated.hpp
    src/nrlib/surface/surface.hpp
    src/nrlib/surface/surfaceio.cpp
    src/nrlib/surface/surfaceio.hpp
    src/nrlib/variogram/fftcovgrid.cpp
    src/nrlib/variogram/fftcovgrid.hpp
    src/nrlib/variogram/gaussianfield.cpp
    src/nrlib/variogram/gaussianfield.hpp
    src/nrlib/variogram/variogram.cpp
    src/nrlib/variogram/variogram.hpp
    src/nrlib/variogram/variogramtypes.cpp
    src/nrlib/variogram/variogramtypes.hpp
)
add_library(gaussianfft::gaussianfft ALIAS gaussianfft_gaussianfft)

if(NOT BUILD_SHARED_LIBS)
  target_compile_definitions(gaussianfft_gaussianfft PUBLIC GAUSSIANFFT_STATIC_DEFINE)
endif()

set_target_properties(
    gaussianfft_gaussianfft PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
    VERSION "${PROJECT_VERSION}"
    SOVERSION "${PROJECT_VERSION_MAJOR}"
    EXPORT_NAME _gaussianfft
    OUTPUT_NAME _gaussianfft
)

target_include_directories(
    gaussianfft_gaussianfft ${warning_guard}
    PUBLIC
    "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>"
)

target_include_directories(
    gaussianfft_gaussianfft SYSTEM
    PUBLIC
    "$<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/export>"
)

target_compile_features(gaussianfft_gaussianfft PUBLIC cxx_std_17)
target_link_libraries(
        gaussianfft_gaussianfft
        PRIVATE
        Boost::boost Boost::python Boost::numpy Boost::filesystem
)
# TODO: It seems this linking is only necessary if we are building 'manually'
#       tht is; mkdir build; cd build; cmake ..
target_link_libraries(gaussianfft_gaussianfft PRIVATE
        -Wl,--start-group
        mkl_intel_ilp64
        mkl_gnu_thread
        mkl_core
        -Wl,--end-group
        gomp
        pthread
        m
        dl
)
#target_link_libraries(gaussianfft_gaussianfft PRIVATE

# ---- Install rules ----

if(DEFINED SKBUILD)
install(
        TARGETS gaussianfft_gaussianfft
        DESTINATION ${SKBUILD_PLATLIB_DIR}
)
endif ()

#if(NOT CMAKE_SKIP_INSTALL_RULES)
#  include(cmake/install-rules.cmake)
#endif()

# ---- Developer mode ----

if(NOT gaussianfft_DEVELOPER_MODE)
  return()
elseif(NOT PROJECT_IS_TOP_LEVEL)
  message(
      AUTHOR_WARNING
      "Developer mode is intended for developers of gaussianfft"
  )
endif()

#include(cmake/dev-mode.cmake)
