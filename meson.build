project(
    'gaussianfft',
    'cpp',
    version: run_command('setuptools-scm', check: true).stdout().strip(),
    default_options: [
        'cpp_std=c++20',
    ],
)

py = import('python').find_installation(pure: false)
pybind11_dep = dependency('pybind11')
boost_dep = dependency('boost', modules: ['filesystem'])

cpp = meson.get_compiler('cpp')
armpl = cpp.find_library(
    'armpl_lp64_mp',
    dirs:  meson.current_source_dir() / 'sources/arm-performance-libraries/23.10/arm64/lib',
    required: true,
)

#fftw = dependency('ArmPL', required: true, method: 'pkg-config')
#library(
#    '_gaussianfft',
#    'src/gaussfftinterface.cpp',
#    dependencies: [pybind11_dep],
#
#)

_gaussianfft = py.extension_module('_gaussianfft',
    'src/gaussfftinterface.cpp',
        'src/gaussfft.cpp',
            'src/nrlib/math/constants.cpp',
#            'src/nrlib/iotools/stringtools.cpp',
#        'src/nrlib/variogram/variogram.cpp',
#        'src/nrlib/random/random.cpp',
#            'src/nrlib/random/dSFMT.cpp',
    'src/gaussfftinterface.cpp',
    'src/nrlib/random/random.cpp',
    'src/nrlib/exception/exception.hpp',
    'src/nrlib/random/random.hpp',
    'src/nrlib/random/dSFMT.cpp',
    'src/nrlib/random/dSFMT-common.h',
    'src/nrlib/random/dSFMT-params.h',
    'src/nrlib/random/dSFMT-params19937.h',
    'src/nrlib/random/dSFMT.h',
    'src/nrlib/variogram/variogram.cpp',
    'src/nrlib/variogram/variogramtypes.cpp',
    'src/nrlib/variogram/variogramtypes.hpp',
    'src/nrlib/variogram/variogram.hpp',
    'src/gaussfft.cpp',
    'src/nrlib/variogram/gaussianfield.cpp',
    'src/nrlib/variogram/fftcovgrid.cpp',
    'src/nrlib/variogram/fftcovgrid.hpp',
    'src/nrlib/fft/fft.cpp',
    'src/nrlib/fft/fft.hpp',
    'src/nrlib/fft/fftgrid3d.cpp',
    'src/nrlib/fft/fftgrid3d.hpp',
    'src/nrlib/grid/grid.hpp',
#    'src/nrlib/iotools/fileio.cpp',
#    'src/nrlib/iotools/boost-filesystem.hpp',
#    'src/nrlib/iotools/fileio.hpp',
    'src/nrlib/fft/fftgrid2d.cpp',
    'src/nrlib/fft/fftgrid2d.hpp',
    'src/nrlib/iotools/stringtools.cpp',
    'src/nrlib/iotools/stringtools.hpp',
#    'src/nrlib/surface/surfaceio.cpp',
    'src/nrlib/surface/surface.hpp',
    'src/nrlib/surface/regularsurfacerotated.hpp',
    'src/nrlib/grid/grid2d.hpp',
    'src/nrlib/surface/regularsurface.hpp',
#    'src/nrlib/surface/surfaceio.hpp',
    'src/nrlib/math/constants.cpp',
    'src/nrlib/math/constants.hpp',
    'src/nrlib/variogram/gaussianfield.hpp',
    'src/nrlib/random/randomgenerator.cpp',
    'src/nrlib/random/randomgenerator.hpp',
    'src/gaussfft.hpp',
    install: true,
    dependencies: [pybind11_dep, boost_dep, armpl],
    include_directories: [
        'src',
    'sources/arm-performance-libraries/23.10/arm64/include_lp64',
    ],
)

#unittest = dependency('boost', modules: ['unit_test_framework'])
#
## Unit tests
#e = executable(
#    'fftcovgrid',
#    'src/nrlib/variogram/unittests/fftcovgrid_test.cpp',
#    include_directories: 'src',
#    dependencies: [unittest],
#    link_with: _gaussianfft,
#)
#test(
#    'fftcovgrid',
#    e,
#)
