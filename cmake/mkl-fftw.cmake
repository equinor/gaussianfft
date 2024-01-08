# Configure Intel MKL & FFTW (for Apple M-series)
if (USE_FFT3)
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
    if (EXISTS ${CMAKE_BINARY_DIR}/venv/lib/cmake/mkl/MKLConfig.cmake)
        include(${CMAKE_BINARY_DIR}/venv/lib/cmake/mkl/MKLConfig.cmake)
    endif ()
    set(MKL_LINK "static")
    set(MKL_ILP64 ON)
    find_package(MKL CONFIG REQUIRED PATHS $ENV${MKLROOT})
    include_directories(SYSTEM ${MKL_ROOT}/include/fftw)
    link_directories(${MKL_ROOT}/lib)
endif ()
