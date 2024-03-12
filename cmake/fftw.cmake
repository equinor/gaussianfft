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
    if (EXISTS ${CMAKE_BINARY_DIR}/venv/lib/cmake/mkl/MKLConfig.cmake)
        include(${CMAKE_BINARY_DIR}/venv/lib/cmake/mkl/MKLConfig.cmake)
    endif ()
    set(MKL_LINK "static")
    set(MKL_ILP64 ON)
    find_package(MKL CONFIG REQUIRED PATHS $ENV${MKLROOT})
    include_directories(SYSTEM ${MKL_ROOT}/include/fftw)
    link_directories(${MKL_ROOT}/lib)
endif ()
