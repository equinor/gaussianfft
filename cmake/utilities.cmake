# macOS and Linux report different processors "arm64" and "aarch64" respectively
# when they use the ARM instruction set
# This is intended as a convenient check when we need to treat ARM differently
# particularly when using Intel MKL / FFTW3
if (${CMAKE_SYSTEM_PROCESSOR} STREQUAL "arm64" OR ${CMAKE_SYSTEM_PROCESSOR} STREQUAL "aarch64")
    set (IS_AARCH64 ON)
else ()
    set(IS_AARCH64 OFF)
endif ()
