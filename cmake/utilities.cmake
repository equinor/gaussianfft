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
    list(APPEND include_directories ${Python3_INCLUDE_DIRS} ${pybind11_INCLUDE_DIR})
    if (MSVC)
        # MSVC's cl.exe requires system include directories when invoked directly
        # (outside of MSBuild). Derive them from the compiler path and SDK version.
        get_filename_component(_msvc_bin_hostarch "${CMAKE_CXX_COMPILER}" DIRECTORY)   # .../Hostx64/x64
        get_filename_component(_msvc_bin_host "${_msvc_bin_hostarch}" DIRECTORY)        # .../Hostx64
        get_filename_component(_msvc_bin "${_msvc_bin_host}" DIRECTORY)                 # .../bin
        get_filename_component(_msvc_version_dir "${_msvc_bin}" DIRECTORY)              # .../MSVC/<version>
        if (EXISTS "${_msvc_version_dir}/include")
            list(APPEND include_directories "${_msvc_version_dir}/include")
        endif ()
        # Add Windows SDK ucrt include directory
        set(_winsdk_base "C:/Program Files (x86)/Windows Kits/10")
        if (DEFINED CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION AND EXISTS "${_winsdk_base}/Include/${CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION}")
            set(_winsdk_inc "${_winsdk_base}/Include/${CMAKE_VS_WINDOWS_TARGET_PLATFORM_VERSION}")
            foreach(_subdir ucrt shared um)
                if (EXISTS "${_winsdk_inc}/${_subdir}")
                    list(APPEND include_directories "${_winsdk_inc}/${_subdir}")
                endif ()
            endforeach()
        endif ()
    endif ()
    execute_process(
            COMMAND_ERROR_IS_FATAL ANY
            COMMAND ${Python3_EXECUTABLE} ${CMAKE_BINARY_DIR}/bin/find_dependants.py --include-directories "${include_directories}" ${ARGN}
            OUTPUT_VARIABLE _FILES
    )
    message(STATUS "Found dependants: ${_FILES}")
    separate_arguments(_FILES_LIST NATIVE_COMMAND PROGRAM SEPARATE_ARGS ${_FILES})
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
