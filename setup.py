import glob
import platform
import os

from setuptools import setup, Extension, find_packages, Distribution

""" Installation Instructions """
# Linux:
#   [Conditional] export MKL_ROOT=/nr/prog/intel/Compiler/mkl
#   [Conditional] /nr/prog/smedvig/rms/versions/10.1.1/linux-amd64-gcc_4_4-release/bin/roxenv
# Make sure the correct version of pip is being used:
#   which pip
#   pip install --user -e .
# Alternatively
#   python -m pip install --user -e .
# Note: The option -e is optional, but it is convenient to use during development.
#
# Mac:
#   as for Linux, however, some other variables must likely be set:
#   >>>source /opt/intel/bin/compilervars.sh intel64
#   If MKL has not been installed prior, see https://software.intel.com/en-us/mkl
#   After the compilation you may need to run
#   >>>install_name_tool -add_rpath /opt/intel/mkl/lib nrlib.cpython-36m-darwin.so
#
# Windows:
#   pip install --user -e .

# If the installation fails, some additional information may be printed if the following environment variable is defined
#   DISTUTILS_DEBUG=1

""" Installation settings """

# Must correspond to the name within BOOST_PYTHON_MODULE in the cpp code:
extension_name = 'nrlib'

# Log file of all compilations. If this file is not present, it has no effect. If it is, then the revision number of
# NRLib is appended to the file, along with a time and date stamp. This is for development only and should be removed
# later.
compilation_logs = 'compiles.log'

"""**********************"""


class BinaryDistribution(Distribution):
    def is_pure(self):
        return False


if os.path.isfile(compilation_logs):
    import subprocess
    import datetime


    def get_revision(text):
        lines = text.decode().replace('\r', '').split('\n')
        revision_line = [li for li in lines if "Revision" in li]
        assert len(revision_line) == 1
        return revision_line[0].split()[-1]

    try:
        process = subprocess.Popen(['svn', 'info', 'src/nrlib'], stdout=subprocess.PIPE)
        out, err = process.communicate()
        nr_rev = get_revision(out)
        process = subprocess.Popen(['svn', 'info', 'src/flens'], stdout=subprocess.PIPE)
        out, err = process.communicate()
        fl_rev = get_revision(out)
        line = str(datetime.datetime.now()) + ": nrlib r{}, flens r{}\n".format(nr_rev, fl_rev)
        open(compilation_logs, 'a').write(line)
    except AssertionError as e:
        print('Could not determine svn version. Error was: ' + str(e))
        print('Continuing to compilation')

if os.getenv('BOOST_ROOT'):
    boost_root = os.getenv('BOOST_ROOT')
    print('Using Boost directory determined by BOOST_ROOT env variable: ' + boost_root)
else:
    boost_root = os.getcwd()
    print('Using current directory as Boost root: ' + boost_root)


# Platform specific definitions
linker_args = []
if platform.system() in ['Linux', 'Darwin']:
    mkl_root = os.getenv('MKL_ROOT') or os.getenv('MKLROOT')
    if mkl_root is None:
        raise RuntimeError(
            "The environment variables MKL_ROOT, or MKLROOT is not defined. "
            "MKL headers and libraries are required."
        )
    boost_linking = os.getenv('BOOST_LINKING')
    if boost_linking not in ['static', 'shared']:
        raise RuntimeError("The environment variable BOOST_LINKING must be set to either 'static' or 'shared'.")
    link_libraries = []
    compile_args = [
        # Necessary for some C++11 compilers:
        '-D_GLIBCXX_USE_CXX11_ABI=0',
        '-DBOOST_PYTHON_STATIC_LIB',
        '-DBOOST_NUMPY_STATIC_LIB',
    ]
    # Standard Intel MKL installation (static linking):
    library_dir = mkl_root + '/lib'
    if os.path.isdir(library_dir + '/intel64'):
        library_dir += '/intel64'
    if platform.system() == 'Darwin':
        library_extension = 'dylib'
        linker_args += '-I{0}/include -L{1} -lpthread -lm -ldl'.format(mkl_root, library_dir).split()
        link_libraries += [
            'mkl_core',
            'mkl_intel_lp64',
            'mkl_sequential',
        ]
    else:
        library_extension = 'a'
        linker_args += '-Wl,--start-group {0}/libmkl_intel_lp64.a {0}/libmkl_sequential.a {0}/libmkl_core.a -Wl,--end-group -lpthread -lm -ldl'.format(library_dir).split()
    boost_libraries = ['boost_python3', 'boost_numpy3', 'boost_filesystem', 'boost_system']
    if boost_linking == 'shared':
        link_libraries += ['stage/lib/' + lib_name for lib_name in boost_libraries]
    elif boost_linking == 'static':
        # Force static linking with Boost (requires Boost compiled with fPIC flag)
        linker_args += ['-l:lib' + lib_name + '.' + library_extension for lib_name in boost_libraries]
    # RMS develop Intel MKL (static linking):
    # linker_args += '-Wl,--start-group {0}/em64t/lib/libmkl_intel_lp64.a {0}/em64t/lib/libmkl_sequential.a {0}/em64t/lib/libmkl_core.a -Wl,--end-group -lpthread -lm -ldl'.format(mkl_root).split()
    library_dirs = [
        # To support different folder structures, a variety of MKL directories are added:
        library_dir,
        os.path.join(boost_root, 'lib'),
    ]
    include_dirs = []
else:
    mkl_root = r"C:\Program Files (x86)\IntelSWTools\compilers_and_libraries_2016.0.110\windows\mkl"
    link_libraries = [
        mkl_root + r'\lib\intel64\mkl_intel_lp64_dll',
        mkl_root + r'\lib\intel64\mkl_sequential_dll',
        mkl_root + r'\lib\intel64\mkl_core_dll',
    ]
    compile_args = [
        '/EHsc',
        '/MT',
        '/DBOOST_PYTHON_STATIC_LIB',
        '/DBOOST_NUMPY_STATIC_LIB',
        # '/showIncludes'  # Debug
    ]
    library_dirs = [
        os.path.join(boost_root, 'lib')
    ]

fftw_dirs = [
    os.path.join(mkl_root, "include", "fftw"),
    os.path.join(mkl_root, "include"),
]


# Define all nrlib source files to compile. Globbing may not be recommended,
# but it is convenient and compact.
nrlib_source_files = glob.glob(
    os.path.join('src', 'nrlib', '*', '*.cpp')
)
nrlib_source_files += glob.glob(
    os.path.join('src', 'flens', '*.cc')
)
source_files = [
    os.path.join('src', 'gaussfft.cpp'),
    os.path.join('src', 'gaussfftinterface.cpp'),
]
all_source_files = source_files + nrlib_source_files

# We do not need entire NRLib. Exclude unused files.

all_source_files = [
    a
    for a in all_source_files
    # @formatter:off
    if not a.startswith(  os.path.join('src', 'nrlib', 'eclipsegrid'))
    and not a.startswith( os.path.join('src', 'nrlib', 'geometry'   ))
    and not a.startswith( os.path.join('src', 'nrlib', 'pointset'   ))
    and (not a.startswith(os.path.join('src', 'nrlib', 'random'     )) or a.count('random') == 2 or 'dSFMT' in a)
    and not a.startswith( os.path.join('src', 'nrlib', 'segy'       ))
    and not a.startswith( os.path.join('src', 'nrlib', 'statistics' ))
    and not a.startswith( os.path.join('src', 'nrlib', 'stormgrid'  ))
    and not a.startswith( os.path.join('src', 'nrlib', 'surface'    ))
    and not a.startswith( os.path.join('src', 'nrlib', 'tinyxml'    ))
    and not a.startswith( os.path.join('src', 'nrlib', 'trend'      ))
    and not a.startswith( os.path.join('src', 'nrlib', 'volume'     ))
    and not a.startswith( os.path.join('src', 'nrlib', 'wavelet'    ))
    and not a.startswith( os.path.join('src', 'nrlib', 'well'       ))
    # @formatter:on
]

open('source_files.txt', 'w').writelines(all_source_files)

""" Python module setup """

bp_module = Extension(
    extension_name,
    sources=all_source_files,
    define_macros=[
      ('FLENS_FIRST_INDEX', '0'),
      ('MKL', None),
    ],
    include_dirs=[
      boost_root,
      os.path.join(boost_root, 'include'),
      os.path.abspath('./src'),
    ]
    + fftw_dirs,
    library_dirs=library_dirs,
    libraries=link_libraries,
    extra_compile_args=compile_args,
    extra_link_args=[
      # '/VERBOSE:lib'    # For Debug on Windows
    ]
    + linker_args,
    language='c++'
)


setup(
    name=extension_name,
    version="0.6",
    packages=find_packages(),
    ext_modules=[bp_module],
    include_package_data=True,
    distclass=BinaryDistribution,
    package_data={
        'stage/lib': ['*.so', '*.dll', '*.dylib', '*.a'],
    },
)
