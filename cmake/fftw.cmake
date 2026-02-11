# Configure Intel MKL & FFTW (for Apple M-series)
if (${IS_AARCH64})
    if (${APPLE})
        set(RUNNER_OS "macOS")
    else ()
        message(FATAL_ERROR "Currently, ARM is only supported macOS")
    endif ()
    message(STATUS "Using version ${ARMPL_VERSION} of ARM Performance Libraries")

    set(BUILD_ENVIRONMENT ${pybind11_INCLUDE_DIR}/../../../../..)
    find_library(
        ARMPL_STATIC_LIB
        NAMES libarmpl_lp64.a armpl_lp64.a
        PATHS ${BUILD_ENVIRONMENT}/lib
        NO_DEFAULT_PATH NO_CMAKE_FIND_ROOT_PATH
    )

    include_directories(SYSTEM ${BUILD_ENVIRONMENT}/include)
    link_directories(${BUILD_ENVIRONMENT}/lib)
else ()
    # MKL
    file(COPY_FILE ${CMAKE_SOURCE_DIR}/bin/find-mkl-config.py ${CMAKE_BINARY_DIR}/bin/find-mkl-config.py ONLY_IF_DIFFERENT)
    execute_process(
            COMMAND ${Python3_EXECUTABLE} ${CMAKE_BINARY_DIR}/bin/find-mkl-config.py ${pybind11_INCLUDE_DIR}/../../../..
            OUTPUT_VARIABLE MKL_CONFIG
    )
    if (DEFINED MKL_CONFIG)
        get_filename_component(MKL_CONFIG ${MKL_CONFIG}/.. REALPATH)
        list(APPEND CMAKE_MODULE_PATH ${MKL_CONFIG})
        message(STATUS "Found Intel MKL: ${MKL_CONFIG}")
    endif ()
    set(MKL_LINK "static")
    set(MKL_ILP64 ON)
    find_package(MKL CONFIG REQUIRED PATHS $ENV${MKLROOT} ${MKL_CONFIG})
    include_directories(SYSTEM ${MKL_ROOT}/include/fftw)
    link_directories(${MKL_ROOT}/lib)

    if (WIN32)
        link_directories(${MKL_ROOT}/../../compiler/latest/lib)
    endif ()
endif ()
