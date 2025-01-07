# Configure Intel MKL & FFTW (for Apple M-series)
if (${IS_AARCH64})
    if (${APPLE})
        set(RUNNER_OS "macOS")
    else ()
        message(FATAL_ERROR "Currently, ARM is only supported macOS")
    endif ()
    message(STATUS "Using version ${ARMPL_VERSION} of ARM Performance Libraries")

    file(COPY_FILE ${CMAKE_SOURCE_DIR}/bin/fetch-ArmPL.sh ${CMAKE_BINARY_DIR}/bin/fetch-ArmPL.sh ONLY_IF_DIFFERENT)
    set(ARMPL_DIR "sources/arm-performance-libraries/${ARMPL_VERSION}/${RUNNER_OS}")
    if (
            NOT EXISTS ${CMAKE_BINARY_DIR}/${ARMPL_DIR}
            AND EXISTS ${CMAKE_SOURCE_DIR}/${ARMPL_DIR}
    )
        message(STATUS "Copy ArmPL files to build directory")
        file(
                COPY ${CMAKE_SOURCE_DIR}/${ARMPL_DIR}
                DESTINATION ${CMAKE_BINARY_DIR}/sources/arm-performance-libraries/${ARMPL_VERSION}/
                USE_SOURCE_PERMISSIONS
                FOLLOW_SYMLINK_CHAIN
        )
    else ()
        message(STATUS "Downloading ARM performance library")
        execute_process(
                COMMAND_ERROR_IS_FATAL ANY
                COMMAND ${CMAKE_BINARY_DIR}/bin/fetch-ArmPL.sh ${ARMPL_VERSION}
        )
    endif ()

    include_directories(SYSTEM ${CMAKE_BINARY_DIR}/${ARMPL_DIR}/include_lp64)
    link_directories(${CMAKE_BINARY_DIR}/${ARMPL_DIR}/lib)
else ()
    # MKL
    execute_process(
            COMMAND find ${Python3_SITELIB}/../../ -name "MKLConfig.cmake"
            OUTPUT_VARIABLE MKL_CONFIG
    )
    if (NOT DEFINED MKL_CONFIG AND WIN32)
        execute_process(
                COMMAND find "C:/Program Files (x86)/Intel/oneAPI/mkl" -name "MKLConfig.cmake"
                OUTPUT_VARIABLE MKL_CONFIG
        )
    endif ()
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
