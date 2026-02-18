# CMakeLists.txt for nrlib C++ unit tests
cmake_minimum_required(VERSION 3.20)
project(nrlib_tests CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set project root directory
get_filename_component(PROJECT_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)

find_package(Boost 1.74 CONFIG COMPONENTS filesystem unit_test_framework QUIET)

if(NOT Boost_FOUND)
    if(POLICY CMP0167)
        cmake_policy(SET CMP0167 OLD)
    endif()
    find_package(Boost 1.74 REQUIRED COMPONENTS filesystem unit_test_framework)
endif()

message(STATUS "Using Boost ${Boost_VERSION}")

# Collect all nrlib source files (excluding unittests)
file(GLOB_RECURSE NRLIB_SOURCES
    "${PROJECT_ROOT}/src/nrlib/*.cpp"
)

# Filter out test files and pchheader from main sources
list(FILTER NRLIB_SOURCES EXCLUDE REGEX ".*/unittests/.*")
list(FILTER NRLIB_SOURCES EXCLUDE REGEX ".*pchheader\\.cpp$")
set(EXCLUDED_NRLIB_MODULES backup experimentation flens statistics segy well)
foreach(module IN LISTS EXCLUDED_NRLIB_MODULES)
    list(FILTER NRLIB_SOURCES EXCLUDE REGEX ".*/${module}/.*")
endforeach()

# Collect all test source files
file(GLOB_RECURSE TEST_SOURCES
    "${PROJECT_ROOT}/src/nrlib/*/unittests/*.cpp"
)
# Filter out tests for excluded modules
set(EXCLUDED_TEST_MODULES flens statistics segy well)
foreach(module IN LISTS EXCLUDED_TEST_MODULES)
    list(FILTER TEST_SOURCES EXCLUDE REGEX ".*/${module}/.*")
endforeach()

# Create test executable
add_executable(nrlib_tests
    test_runner.cpp
    ${NRLIB_SOURCES}
    ${TEST_SOURCES}
)

# Find FFTW3 (required for FFT module)
find_package(PkgConfig REQUIRED)
pkg_check_modules(FFTW3 REQUIRED fftw3)
pkg_check_modules(FFTW3F REQUIRED fftw3f)

# Include directories
target_include_directories(nrlib_tests PRIVATE
    ${PROJECT_ROOT}/src
    ${Boost_INCLUDE_DIRS}
    ${FFTW3_INCLUDE_DIRS}
)

# Link against Boost libraries and FFTW
target_link_libraries(nrlib_tests PRIVATE
    Boost::filesystem
    Boost::unit_test_framework
    ${FFTW3_LIBRARIES}
    ${FFTW3F_LIBRARIES}
)

target_link_directories(nrlib_tests PRIVATE
    ${FFTW3_LIBRARY_DIRS}
)

# Define HAS_BOOST_FILESYSTEM for the tests
target_compile_definitions(nrlib_tests PRIVATE
    HAS_BOOST_FILESYSTEM
    USE_BOOST
)

# Enable testing
enable_testing()
add_test(NAME nrlib_unit_tests COMMAND nrlib_tests)

message(STATUS "nrlib C++ tests configured with ${CMAKE_CXX_COMPILER}")
list(LENGTH TEST_SOURCES TEST_SOURCE_COUNT)
message(STATUS "Found ${TEST_SOURCE_COUNT} test source files")
