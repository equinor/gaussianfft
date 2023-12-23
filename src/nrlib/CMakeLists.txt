cmake_minimum_required(VERSION 3.28)
project(nrlib)

list(APPEND nrlib_HEADERS
${CMAKE_CURRENT_LIST_DIR}/exception/exception.hpp
${CMAKE_CURRENT_LIST_DIR}/fft/fft.hpp
${CMAKE_CURRENT_LIST_DIR}/fft/fftgrid2d.hpp
${CMAKE_CURRENT_LIST_DIR}/fft/fftgrid3d.hpp
${CMAKE_CURRENT_LIST_DIR}/flens/nrlib_flens.hpp
${CMAKE_CURRENT_LIST_DIR}/grid/grid.hpp
${CMAKE_CURRENT_LIST_DIR}/grid/grid2d.hpp
${CMAKE_CURRENT_LIST_DIR}/grid/grid2dgeneral.hpp
${CMAKE_CURRENT_LIST_DIR}/grid/grid4d.hpp
${CMAKE_CURRENT_LIST_DIR}/grid/grid5d.hpp
${CMAKE_CURRENT_LIST_DIR}/iotools/bigfile.hpp
${CMAKE_CURRENT_LIST_DIR}/iotools/fileio.hpp
${CMAKE_CURRENT_LIST_DIR}/iotools/logkit.hpp
${CMAKE_CURRENT_LIST_DIR}/iotools/logstream.hpp
${CMAKE_CURRENT_LIST_DIR}/iotools/serialize.hpp
${CMAKE_CURRENT_LIST_DIR}/iotools/stringtools.hpp
${CMAKE_CURRENT_LIST_DIR}/iotools/tabularfile.hpp
${CMAKE_CURRENT_LIST_DIR}/math/constants.hpp
${CMAKE_CURRENT_LIST_DIR}/math/mathutility.hpp
${CMAKE_CURRENT_LIST_DIR}/random/beta.hpp
${CMAKE_CURRENT_LIST_DIR}/random/betawithendmass.hpp
${CMAKE_CURRENT_LIST_DIR}/random/binomial.hpp
${CMAKE_CURRENT_LIST_DIR}/random/chisquared.hpp
${CMAKE_CURRENT_LIST_DIR}/random/delta.hpp
${CMAKE_CURRENT_LIST_DIR}/random/distribution.hpp
${CMAKE_CURRENT_LIST_DIR}/random/fractal.hpp
${CMAKE_CURRENT_LIST_DIR}/random/functions.hpp
${CMAKE_CURRENT_LIST_DIR}/random/gamma.hpp
${CMAKE_CURRENT_LIST_DIR}/random/generaldiscrete.hpp
${CMAKE_CURRENT_LIST_DIR}/random/lognormal.hpp
${CMAKE_CURRENT_LIST_DIR}/random/normal.hpp
${CMAKE_CURRENT_LIST_DIR}/random/poisson.hpp
${CMAKE_CURRENT_LIST_DIR}/random/random.hpp
${CMAKE_CURRENT_LIST_DIR}/random/randomgenerator.hpp
${CMAKE_CURRENT_LIST_DIR}/random/splituniform.hpp
${CMAKE_CURRENT_LIST_DIR}/random/triangular.hpp
${CMAKE_CURRENT_LIST_DIR}/random/uniform.hpp
${CMAKE_CURRENT_LIST_DIR}/variogram/covgrid2d.hpp
${CMAKE_CURRENT_LIST_DIR}/variogram/fftcovgrid.hpp
${CMAKE_CURRENT_LIST_DIR}/variogram/gaussianfield.hpp
${CMAKE_CURRENT_LIST_DIR}/variogram/variogram.hpp
${CMAKE_CURRENT_LIST_DIR}/variogram/variogramtypes.hpp)

list(APPEND nrlib_SOURCES
${CMAKE_CURRENT_LIST_DIR}/fft/fft.cpp
${CMAKE_CURRENT_LIST_DIR}/fft/fftgrid2d.cpp
${CMAKE_CURRENT_LIST_DIR}/fft/fftgrid3d.cpp
${CMAKE_CURRENT_LIST_DIR}/flens/nrlib_flens.cpp
${CMAKE_CURRENT_LIST_DIR}/iotools/bigfile.cpp
${CMAKE_CURRENT_LIST_DIR}/iotools/fileio.cpp
${CMAKE_CURRENT_LIST_DIR}/iotools/logkit.cpp
${CMAKE_CURRENT_LIST_DIR}/iotools/logstream.cpp
${CMAKE_CURRENT_LIST_DIR}/iotools/serialize.cpp
${CMAKE_CURRENT_LIST_DIR}/iotools/stringtools.cpp
${CMAKE_CURRENT_LIST_DIR}/iotools/tabularfile.cpp
${CMAKE_CURRENT_LIST_DIR}/math/constants.cpp
${CMAKE_CURRENT_LIST_DIR}/random/beta.cpp
${CMAKE_CURRENT_LIST_DIR}/random/betawithendmass.cpp
${CMAKE_CURRENT_LIST_DIR}/random/binomial.cpp
${CMAKE_CURRENT_LIST_DIR}/random/chisquared.cpp
${CMAKE_CURRENT_LIST_DIR}/random/delta.cpp
${CMAKE_CURRENT_LIST_DIR}/random/dSFMT.cpp
${CMAKE_CURRENT_LIST_DIR}/random/fractal.cpp
${CMAKE_CURRENT_LIST_DIR}/random/functions.cpp
${CMAKE_CURRENT_LIST_DIR}/random/gamma.cpp
${CMAKE_CURRENT_LIST_DIR}/random/generaldiscrete.cpp
${CMAKE_CURRENT_LIST_DIR}/random/lognormal.cpp
${CMAKE_CURRENT_LIST_DIR}/random/normal.cpp
${CMAKE_CURRENT_LIST_DIR}/random/poisson.cpp
${CMAKE_CURRENT_LIST_DIR}/random/random.cpp
${CMAKE_CURRENT_LIST_DIR}/random/randomgenerator.cpp
${CMAKE_CURRENT_LIST_DIR}/random/splituniform.cpp
${CMAKE_CURRENT_LIST_DIR}/random/triangular.cpp
${CMAKE_CURRENT_LIST_DIR}/random/uniform.cpp
${CMAKE_CURRENT_LIST_DIR}/variogram/covgrid2d.cpp
${CMAKE_CURRENT_LIST_DIR}/variogram/fftcovgrid.cpp
${CMAKE_CURRENT_LIST_DIR}/variogram/gaussianfield.cpp
${CMAKE_CURRENT_LIST_DIR}/variogram/variogram.cpp
${CMAKE_CURRENT_LIST_DIR}/variogram/variogramtypes.cpp)

set(BOOST_ROOT "/usr/local/Homebrew/Cellar/boost@1.76/1.76.0_4")
set(Boost_LIBRARY_DIR "${BOOST_ROOT}/lib")
set(Boost_USE_STATIC_LIBS ON)
find_package(Boost 1.76 EXACT REQUIRED COMPONENTS unit_test_framework)
include_directories(${Boost_INCLUDE_DIRS})

set(FFTW_INCLUDE_DIR "/usr/local/Homebrew/Cellar/fftw/3.3.10_1/include")
set(FFTW_DOUBLE_LIB "/usr/local/Homebrew/Cellar/fftw/3.3.10_1/lib/libfftw3.a")
set(FFTW_SINGLE_LIB "/usr/local/Homebrew/Cellar/fftw/3.3.10_1/lib/libfftw3f.a")
include_directories(${FFTW_INCLUDE_DIR})

if (APPLE)
include_directories("/opt/homebrew/opt/openblas/include")
endif (APPLE)

# Assuming nrlib should be compiled as a static library
add_library(nrlib STATIC ${nrlib_SOURCES})

target_include_directories(nrlib PUBLIC
${CMAKE_CURRENT_SOURCE_DIR}  # for nrlib's own headers
${CMAKE_CURRENT_SOURCE_DIR}/..  # for the flens headers
)

add_executable(nrlib_tests
variogram/unittests/test.cpp
variogram/unittests/fftcovgrid_test.cpp
variogram/unittests/gaussianfield_test.cpp)

target_link_libraries(nrlib ${FFTW_LIBRARIES} ${FFTW_DOUBLE_LIB} ${FFTW_SINGLE_LIB})

target_link_libraries(nrlib_tests ${Boost_UNIT_TEST_FRAMEWORK_LIBRARY} nrlib)

target_include_directories(nrlib_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
