cmake_minimum_required(VERSION 3.23)
set(CMAKE_CXX_STANDARD 20)
#set(CMAKE_TOOLCHAIN_FILE vcpkg/scripts/buildsystems/vcpkg.cmake)

#include(cmake/prelude.cmake)

#include(build/Release/generators/conan_toolchain.cmake)

# TODO: Generate automatically?

project(
    gaussianfft
    VERSION 1.1.1
    DESCRIPTION "GaussianFFT"
    HOMEPAGE_URL "https://github.com/equinor/gaussianfft"
    LANGUAGES CXX
)


# Compile Boost
option(BOOST_VERSION "Configure the specific version of Boost gaussianfft wil be statically linked against")
if (NOT BOOST_VERSION)
  execute_process(COMMAND ${CMAKE_SOURCE_DIR}/bin/find_boost_version.py OUTPUT_VARIABLE BOOST_VERSION)
endif()
message(VERBOSE "Using version ${BOOST_VERSION} of Boost")

execute_process(COMMAND ${CMAKE_SOURCE_DIR}/bin/compile-boost.sh ${BOOST_VERSION} COMMAND_ERROR_IS_FATAL ANY)

#include(src/nrlib/CMakeLists.txt)
#include(src/flens/CMakeLists.txt)


#include(cmake/project-is-top-level.cmake)
#include(cmake/variables.cmake)

#set(Boost_DIR sources/boost/1.81.0)
set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)
set(Boost_LIBRARY_DIR stage/lib)
#include(sources/boost/1.81.0/stage/lib/cmake/Boost-1.81.0/BoostConfig.cmake)

execute_process(COMMAND python -c "import sysconfig, sys; sys.stdout.write(sysconfig.get_paths()['include'])" OUTPUT_VARIABLE Python3_LIBRARIES)
include_directories(SYSTEM sources/boost/${BOOST_VERSION})
include_directories(SYSTEM ${Python3_LIBRARIES})

# MKL stuff
#include_directories(${Python3_LIBRARIES}/fftw)
#link_directories(venv/lib)

#include_directories(SYSTEM sources/boost/1.76.0)
#include_directories(SYSTEM ~/.asdf/installs/python/3.11.7/include/python3.11/)
# TODO: Set appropriate path to Python header files
#set(Python3_EXECUTABLE  venv/bin/python)
#set(Python3_NumPy_INCLUDE_DIRS venv/lib/python3.11/site-packages/numpy/core/include)
find_package(Python3 REQUIRED COMPONENTS Development.Module NumPy )
find_package(Boost
        ${BOOST_VERSION} EXACT
        REQUIRED
        COMPONENTS python NumPy filesystem system
        PATHS stage/lib/cmake
)
# These need to fetched / populated automatically
#include_directories(
#        ~/.conan2/p/b/boost8d6067e3ac3b9/p/include/
#        ~/.asdf/installs/python/3.11.7/include/python3.11/
#)

#message(Boost_LIBRARIES="${Boost_LIBRARIES}")

# TODO: Build it (if necessary)
#include(sources/fftw/3.3.10/CMakeLists.txt)

# MKL
# TODO: Make this 'optional' for macOS (Apple Silicon)
#include(${CMAKE_INSTALL_LIBDIR}/cmake/mkl/MKLConfig.cmake)
set(MKL_LINK "static")
find_package(MKL CONFIG REQUIRED PATHS $ENV${MKLROOT})
#set(MKL_LIBRARY_FLAGS "-Wl,--start-group ${MKL_ROOT}/lib/libmkl_intel_ilp64.a ${MKL_ROOT}/lib/libmkl_intel_thread.a ${MKL_ROOT}/lib/libmkl_core.a -Wl,--end-group -lgomp -lpthread -lm -ldl")
include_directories(SYSTEM ${MKL_ROOT}/include)
link_directories(${MKL_ROOT}/lib)

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

include(GenerateExportHeader)
generate_export_header(
    gaussianfft_gaussianfft
    BASE_NAME gaussianfft
    EXPORT_FILE_NAME export/gaussianfft/gaussianfft_export.hpp
    CUSTOM_CONTENT_FROM_VARIABLE pragma_suppress_c4251
)

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

#set(MKL_LIBRARY_FLAGS "-Wl,--start-group ${MKL_ROOT}/lib/libmkl_intel_ilp64.a ${MKL_ROOT}/lib/libmkl_intel_thread.a ${MKL_ROOT}/lib/libmkl_core.a -Wl,--end-group -lgomp -lpthread -lm -ldl")
#target_link_libraries(gaussianfft_gaussianfft PUBLIC MKL::fftw)
#target_link_libraries(gaussianfft_gaussianfft PRIVATE MKL::MKL)
#target_link_libraries(gaussianfft_gaussianfft PRIVATE MKL::MKL gomp pthread m dl)
#target_link_libraries(
#        gaussianfft_gaussianfft PRIVATE
#        -Wl,--start-group
#        mkl_intel_ilp64
#        mkl_intel_thread
#        mkl_core
#        -Wl,--end-group
##        iomp5
##        -openmp
#        gomp
#        pthread
#        m
#        dl
#)
#mkl-static-lp64-iomp


# ../venv/lib/libmkl_gnu_thread.a
#  0000000000000000 T mkl_dft_commit_node_d_c2c_md_omp
# ../venv/lib/libmkl_intel_thread.a
# 0000000000000000 T mkl_dft_commit_node_d_c2c_md_omp
# ../venv/lib/libmkl_pgi_thread.a
# 0000000000000000 T mkl_dft_commit_node_d_c2c_md_omp
# ../venv/lib/libmkl_sequential.a
# 0000000000000000 T mkl_dft_commit_node_d_c2c_md_omp
# ../venv/lib/libmkl_tbb_thread.a
# 0000000000000000 T mkl_dft_commit_node_d_c2c_md_omp
#target_link_libraries(gaussianfft_gaussianfft PUBLIC
#        gomp
#
#        mkl_gnu_thread
#        mkl_intel_thread
#        mkl_pgi_thread
#        mkl_sequential
#        mkl_tbb_thread
#)

# Follow the recommendations from Intel's linking advisor
# https://www.intel.com/content/www/us/en/developer/tools/oneapi/onemkl-link-line-advisor.html

## Linking the symbol mkl_dft_commit_node_d_c2c_md_omp
# TODO: It seems this linking is only necessary if we are building 'manually'
#       tht is; mkdir build; cd build; cmake ..
target_link_libraries(gaussianfft_gaussianfft PRIVATE
        -Wl,--start-group
        ${MKL_ROOT}/lib/libmkl_intel_ilp64.a
        ${MKL_ROOT}/lib/libmkl_gnu_thread.a
        ${MKL_ROOT}/lib/libmkl_core.a
        -Wl,--end-group
        -lgomp
        -lpthread
        -lm
        -ldl
)
#target_link_libraries(gaussianfft_gaussianfft PRIVATE
#        mkl_intel_ilp64
#        mkl_gnu_thread
#        mkl_core
#
#        gomp pthread m dl
#)

# Linking the symbol mkl_dft_compute_forward_dz_out_par
#target_link_libraries(gaussianfft_gaussianfft PRIVATE
#        # One or more of these MAY be unnecessary
#        # I've tried removing one at the time, bo it seems
#        # importing gaussianfft fails if one of them is removed
#        mkl_gnu_thread
#        mkl_intel_thread
#        mkl_pgi_thread
#        mkl_sequential
#        mkl_tbb_thread
#)
#
## Linking the symbol mkl_dft_xdzforward_out
#target_link_libraries(gaussianfft_gaussianfft PRIVATE
#  mkl_core
#  mkl_gf_ilp64
#  libmkl_gf_ilp64.a
#)

# ---- Install rules ----

install(
        TARGETS gaussianfft_gaussianfft
        DESTINATION ${SKBUILD_PLATLIB_DIR}
)

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
