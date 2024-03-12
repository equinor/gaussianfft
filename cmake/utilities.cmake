# A utility function for finding all source / header files a particular file depend on
# including itself
if (NOT EXISTS ${CMAKE_BINARY_DIR}/bin)
    file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
endif ()
file(
        COPY_FILE ${CMAKE_SOURCE_DIR}/bin/find_dependants.py
        ${CMAKE_BINARY_DIR}/bin/find_dependants.py
        ONLY_IF_DIFFERENT
)
file(
        COPY_FILE ${CMAKE_SOURCE_DIR}/utils.py
        ${CMAKE_BINARY_DIR}/utils.py
        ONLY_IF_DIFFERENT
)
function(dependants output_variables)
    set(ENV{PYTHONPATH} ${CMAKE_BINARY_DIR})
    set(ENV{CXX} ${CMAKE_CXX_COMPILER})
    set(ENV{CXXFLAGS} ${CMAKE_CXX_FLAGS})
    get_property(include_directories DIRECTORY ${CMAKE_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
    list(APPEND include_directories ${CMAKE_CXX_STANDARD_INCLUDE_DIRECTORIES} ${CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES})
#    message(FATAL_ERROR ${include_directories})
#    list(APPEND include_directories "/Users/SNIS/Projects/APS/gaussianfft/sources/arm-performance-libraries/armpl_23.10_flang-new_clang_17/include_int64_mp")
    execute_process(
            COMMAND_ERROR_IS_FATAL ANY
            COMMAND ${Python3_EXECUTABLE} ${CMAKE_BINARY_DIR}/bin/find_dependants.py --include-directories "${include_directories}" ${ARGN}
            OUTPUT_VARIABLE _FILES
    )
    separate_arguments(_FILES_LIST UNIX_COMMAND PROGRAM SEPARATE_ARGS ${_FILES})
    set(${output_variables} ${_FILES_LIST} PARENT_SCOPE)
endfunction()

# macOS and Linux report different processors "arm64" and "aarch64" respectively
# when they use the ARM instruction set
# This is intended as a convenient check when we need to treat ARM differently
# particularly when using Intel MKL / FFTW3
if (${CMAKE_SYSTEM_PROCESSOR} STREQUAL "arm64" OR ${CMAKE_SYSTEM_PROCESSOR} STREQUAL "aarch64")
    set (IS_AARCH64 ON)
else ()
    set(IS_AARCH64 OFF)
endif ()
