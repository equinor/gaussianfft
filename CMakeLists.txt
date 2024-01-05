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
  message(WARNING "Not building with scikit-build")

  if (NOT EXISTS ${CMAKE_BINARY_DIR}/venv)
    message(STATUS "Creating a new venv in ${CMAKE_BINARY_DIR}/venv")
    find_package(Python3 ${Python3_VERSION} EXACT REQUIRED COMPONENTS Interpreter)
    execute_process(COMMAND ${Python3_EXECUTABLE} "-m" "venv" "venv"
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
            COMMAND_ERROR_IS_FATAL ANY
    )
    unset(${Python3_EXECUTABLE})
  endif ()
  message(STATUS "Installing necessary dependencies in ${CMAKE_BINARY_DIR}/venv")
  set(Python3_EXECUTABLE "${CMAKE_BINARY_DIR}/venv/bin/python")
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  message(STATUS ${Python3_EXECUTABLE})

  # Ensure pip ins up do date
  execute_process(
          COMMAND ${Python3_EXECUTABLE} -m pip install --upgrade pip
          COMMAND_ERROR_IS_FATAL ANY
  )
  # For very old version of pip, we may need to update it twice (e.g. Python 3.6)
  execute_process(
          COMMAND ${Python3_EXECUTABLE} -m pip install --upgrade pip
          COMMAND_ERROR_IS_FATAL ANY
  )
  execute_process(
  # Ensure toml / tomllib is installed
          COMMAND ${Python3_EXECUTABLE} -c "
try:
    # Newer versions of Python come with tomllib preinstalled
    import tomllib
except ImportError:
    try:
        import toml
    except ImportError:
        # Fall back on installing it
        import subprocess
        import sys
        subprocess.run(' '.join([
                sys.executable,
                '-m',
                'pip',
                'install',
                'toml',
            ]),
            shell=True,
            check=True,
        )
"
          COMMAND_ERROR_IS_FATAL ANY
  )
  execute_process(
          COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_SOURCE_DIR}/pyproject.toml pyproject.toml
          COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/bin/install-build-requirements.py
          COMMAND_ERROR_IS_FATAL ANY
  )
  if (EXISTS ${CMAKE_BINARY_DIR}/venv/lib/cmake/mkl/MKLConfig.cmake)
    include(${CMAKE_BINARY_DIR}/venv/lib/cmake/mkl/MKLConfig.cmake)
  endif ()
endif ()
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module NumPy)


# Configure Intel MKL & FFTW (for Apple M-series)
if (APPLE AND ${CMAKE_HOST_SYSTEM_PROCESSOR} STREQUAL "arm64")
  message(WARNING "Intel MKL is not supported on Apple Silicon; using FFTW3 instead")
  # Compiling for Apple silicone, which does not support Intel MKL
  option(FFTW_VERSION "Which version of FFTW to compile against")
  if(NOT FFTW_VERSION)
    set(FFTW_VERSION "3.3.10")
  endif ()
  if (DEFINED ${SKBUILD_STATE} AND ${SKBUILD_STATE} STREQUAL "sdist")
    execute_process(
            COMMAND_ERROR_IS_FATAL ANY
            COMMAND ${CMAKE_SOURCE_DIR}/bin/fetch-fftw.sh ${FFTW_VERSION}
    )
  endif ()
  if (EXISTS ${CMAKE_SOURCE_DIR}/sources/fftw/${FFTW_VERSION})
    message(STATUS "Copy FFTW source to build directory")
    file(COPY ${CMAKE_SOURCE_DIR}/sources/fftw/${FFTW_VERSION} DESTINATION ${CMAKE_BINARY_DIR}/sources/fftw/)
  endif ()

  if (NOT EXISTS ${CMAKE_BINARY_DIR}/bin/compile-fftw.sh)
    file(COPY ${CMAKE_SOURCE_DIR}/bin/compile-fftw.sh DESTINATION ${CMAKE_BINARY_DIR}/bin)
    file(COPY ${CMAKE_SOURCE_DIR}/bin/fetch-fftw.sh DESTINATION ${CMAKE_BINARY_DIR}/bin)
  endif ()
    if (NOT EXISTS ${CMAKE_BINARY_DIR}/vendor AND EXISTS ${CMAKE_SOURCE_DIR}/vendor)
      message(STATUS "Reusing pre-compiled FFTW")
      file(COPY ${CMAKE_SOURCE_DIR}/vendor DESTINATION ${CMAKE_BINARY_DIR})
    endif ()
  if (NOT EXISTS ${CMAKE_BINARY_DIR}/vendor/include/fftw3.h OR NOT EXISTS ${CMAKE_BINARY_DIR}/vendor/lib/libfftw3.a)
    message(STATUS "Compiling FFTW")
    set(ENV{CMAKE} "${CMAKE_COMMAND}")
    execute_process(
            COMMAND_ERROR_IS_FATAL ANY
            COMMAND ${CMAKE_BINARY_DIR}/bin/compile-fftw.sh ${FFTW_VERSION}
    )
  unset(ENV{CMAKE})
  endif ()
  include_directories(SYSTEM ${CMAKE_BINARY_DIR}/vendor/include)
  link_directories(${CMAKE_BINARY_DIR}/vendor/lib)
  # TODO: Use these when fftw properly uses CMAKE
  #find_package(FFTW3 CONFIG REQUIRED PATHS ${CMAKE_BINARY_DIR}/vendor/lib/cmake/fftw3)
  #find_package(FFTW3f CONFIG REQUIRED PATHS ${CMAKE_BINARY_DIR}/vendor/lib/cmake/fftw3f)
else ()
  # MKL
  set(MKL_LINK "static")
  set(MKL_ILP64 ON)
  find_package(MKL CONFIG REQUIRED PATHS $ENV${MKLROOT})
  include_directories(SYSTEM ${MKL_ROOT}/include/fftw)
  link_directories(${MKL_ROOT}/lib)
endif ()

# Compile Boost
option(BOOST_VERSION "Configure the specific version of Boost gaussianfft wil be statically linked against")
if (NOT BOOST_VERSION)
  execute_process(COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/bin/find_boost_version.py OUTPUT_VARIABLE BOOST_VERSION)
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


set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)
set(Boost_LIBRARY_DIR ${Boost_DIR}/stage/lib)
if (NOT EXISTS ${Boost_LIBRARY_DIR})
  message(STATUS "Compiling Boost")
  execute_process(COMMAND ${Boost_COMPILE_SCRIPT} ${BOOST_VERSION} COMMAND_ERROR_IS_FATAL ANY)
else ()
  message(STATUS "Reusing compiled boost libraries at ${Boost_LIBRARY_DIR}")
endif ()

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

if (APPLE)
  set(CMAKE_SHARED_LIBRARY_SUFFIX ".so")
endif ()
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

if (APPLE)
  # We need to explicitly link with libpython.dylib on macOS
  execute_process(
          COMMAND_ERROR_IS_FATAL ANY
          COMMAND ${Python3_EXECUTABLE} -m find_libpython
          OUTPUT_VARIABLE Python3_LIBPYTHON
  )
  target_link_options(gaussianfft_gaussianfft PRIVATE ${Python3_LIBPYTHON})
endif ()

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
if (${CMAKE_HOST_SYSTEM_PROCESSOR} STREQUAL "arm64")
  target_link_libraries(gaussianfft_gaussianfft PRIVATE fftw3 fftw3f)
else ()
  if (APPLE)
    target_link_libraries(gaussianfft_gaussianfft PRIVATE
            mkl_intel_ilp64
            mkl_core
    )
    target_link_libraries(gaussianfft_gaussianfft PRIVATE
            # TODO: Make @rpath/libiomp.dylib work as expected
            #       with the version installed on the target system, and
            #       not the one it was built with (absolute path)
            #       Until then, we use `mkl_sequential`
#            mkl_intel_thread
            mkl_sequential
#            iomp5
    )
  else ()
    # Presumably Linux x86
    target_link_libraries(gaussianfft_gaussianfft PRIVATE
            mkl_gnu_thread
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
