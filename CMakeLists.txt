cmake_minimum_required(VERSION 3.23)
set(CMAKE_CXX_STANDARD 20)

include(cmake/prelude.cmake)

project(
    gaussianfft
    VERSION 1.1.1
    DESCRIPTION "GaussianFFT"
    HOMEPAGE_URL "https://github.com/equinor/gaussianfft"
    LANGUAGES CXX
)

include(cmake/project-is-top-level.cmake)
include(cmake/variables.cmake)

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
endif ()
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
message(STATUS "Using version ${BOOST_VERSION} of Boost")

if (DEFINED ${SKBUILD_STATE} AND ${SKBUILD_STATE} STREQUAL "sdist" AND NOT EXISTS ${CMAKE_SOURCE_DIR}/sources/boost/${BOOST_VERSION})
  execute_process(
          COMMAND_ERROR_IS_FATAL ANY
          COMMAND ${CMAKE_SOURCE_DIR}/bin/fetch-boost.sh ${BOOST_VERSION}
  )
endif ()

message(STATUS "Prepare Boost")
set(ENV{PYTHON} ${Python3_EXECUTABLE})
if (NOT EXISTS ${CMAKE_BINARY_DIR}/bin/compile-boost.sh)
  file(COPY ${CMAKE_SOURCE_DIR}/bin/compile-boost.sh DESTINATION ${CMAKE_BINARY_DIR}/bin/)
  file(COPY ${CMAKE_SOURCE_DIR}/bin/fetch-boost.sh DESTINATION ${CMAKE_BINARY_DIR}/bin/)
  file(COPY ${CMAKE_SOURCE_DIR}/utils.py DESTINATION ${CMAKE_BINARY_DIR}/)
endif ()
if (NOT EXISTS ${CMAKE_BINARY_DIR}/src)
  file(COPY ${CMAKE_SOURCE_DIR}/src DESTINATION ${CMAKE_BINARY_DIR}/)
endif ()
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

message(STATUS "Compiling Boost")
execute_process(COMMAND ${Boost_COMPILE_SCRIPT} ${BOOST_VERSION} COMMAND_ERROR_IS_FATAL ANY)

set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)
set(Boost_LIBRARY_DIR ${Boost_DIR}/stage/lib)

execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import sysconfig, sys; sys.stdout.write(sysconfig.get_paths()['include'])"
        OUTPUT_VARIABLE Python3_LIBRARIES
)
include_directories(SYSTEM ${Boost_DIR})
include_directories(SYSTEM ${Python3_LIBRARIES})

find_package(Boost
        ${BOOST_VERSION} EXACT
        REQUIRED
        COMPONENTS python NumPy filesystem system
        PATHS ${Boost_LIBRARY_DIR}/cmake
)

# ---- Declare library ----
set(CMAKE_SHARED_LIBRARY_PREFIX "")

add_compile_definitions(FLENS_FIRST_INDEX="0")
add_compile_definitions(VECLIB)
add_compile_definitions(ACCELERATE_NEW_LAPACK="1")
add_compile_definitions(ACCELERATE_LAPACK_ILP64="1")

add_library(
    gaussianfft_gaussianfft
    SHARED
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
    EXPORT_NAME _gaussianfft
    OUTPUT_NAME _gaussianfft
)

target_compile_features(gaussianfft_gaussianfft PUBLIC cxx_std_17)
target_link_libraries(
        gaussianfft_gaussianfft
        PRIVATE
        Boost::boost Boost::python Boost::numpy Boost::filesystem Boost::system
)
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

# ---- Install rules ----

if(DEFINED SKBUILD)
install(
        TARGETS gaussianfft_gaussianfft
        DESTINATION ${SKBUILD_PLATLIB_DIR}
)
endif ()

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
