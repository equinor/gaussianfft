import glob
import os
import platform
import re
import sys
from distutils.command.register import register as register_orig
from distutils.command.upload import upload as upload_orig
from pathlib import Path
from typing import Iterable, List
import logging

from setuptools import Distribution, Extension, find_packages, setup
from warnings import warn

MINIMUM_SUPPORTED_PYTHON = "3.6"


try:
    from bin.find_lowest_supported_numpy import get_minimum_supported_numpy_version
    MINIMUM_SUPPORTED_NUMPY = get_minimum_supported_numpy_version(MINIMUM_SUPPORTED_PYTHON)
except ImportError:
    # The earliest version of numpy whit a wheel for Python 3.6
    MINIMUM_SUPPORTED_NUMPY = "1.11.3"


if os.getenv('VERBOSE', '').lower() in ['1', 'yes', 'y']:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


with open('README.md') as f:
    long_description = f.read()


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
extension_name = '_gaussianfft'

# Log file of all compilations. If this file is not present, it has no effect. If it is, then the revision number of
# NRLib is appended to the file, along with a time and date stamp. This is for development only and should be removed
# later.
compilation_logs = 'compiles.log'

"""**********************"""


def _get_code_dir():
    return os.environ.get('CODE_DIR', '.')


def _get_pypirc_file():
    return os.path.join(_get_code_dir(), '.pypirc')


class register(register_orig):

    def _get_rc_file(self):
        return _get_pypirc_file()


class upload(upload_orig):

    def _get_rc_file(self):
        return _get_pypirc_file()


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
        logging.info('Could not determine svn version. Error was: ' + str(e))
        logging.info('Continuing to compilation')

if os.getenv('BOOST_ROOT'):
    boost_root = os.getenv('BOOST_ROOT')
    logging.info('Using Boost directory determined by BOOST_ROOT env variable: ' + boost_root)
else:
    boost_root = os.getcwd()
    logging.info('Using current directory as Boost root: ' + boost_root)


# Platform specific definitions
linker_args = []


def get_library_extension(linking):
    if linking == 'static':
        return 'a'
    elif linking == 'shared':
        if platform.system() == 'Darwin':
            return 'dylib'
        elif platform.system() == 'Linux':
            return 'so'
        elif platform.system() == 'Windows':
            return 'dll'
        else:
            raise ValueError("Invalid platform")
    else:
        raise ValueError("Invalid linking argument")


_python_version = sys.version_info
_python_version = "{}{}".format(_python_version.major, _python_version.minor)
boost_libraries = ['boost_python' + _python_version, 'boost_numpy' + _python_version, 'boost_filesystem', 'boost_system']


def is_compiling() -> bool:
    try:
        _, argument, *rest = sys.argv
        return argument in ['install', 'bdist_wheel']
    except ValueError:
        return False


if platform.system() in ['Linux', 'Darwin']:
    compiling = is_compiling()
    if compiling:
        logging.info("Preparing to compile. MKL must be available")

    if compiling:
        logging.info("Looking for MKL_ROOT / MKLROOT in environment variable")
        mkl_root = os.getenv('MKL_ROOT') or os.getenv('MKLROOT')
    else:
        mkl_root = None

    if compiling and mkl_root is None:
        logging.info(
            "No environment variable set. "
            "Attempting to look for MKL, assuming it was installed from pip"
        )

    if mkl_root is None:
        # Attempt to find it
        # Assuming it was install through pip
        from sysconfig import get_paths

        site_packages = Path(get_paths()['purelib'])
        for package in site_packages.glob('mkl_include*'):
            mkl_root = str(package.parent.parent.parent.parent.absolute().resolve())

    if compiling and mkl_root is None:
        logging.info(
            'MKL does not seem to be installed through pip. '
            "Attempting to look for MKL, assuming it was installed through Intel's installer"
        )

    if mkl_root is None:
        default = '/opt/intel/oneapi/mkl/latest'
        if Path(default).exists():
            mkl_root = default

    if compiling:
        if mkl_root is None:
            logging.info('MKL does not seem to be installed on this system')
        else:
            logging.info(f"Using the MKL libraries located in '{mkl_root}'")

    if mkl_root is None and compiling:
        raise RuntimeError(
            "The environment variables MKL_ROOT, or MKLROOT is not defined. "
            "MKL headers and libraries are required for compilation"
            "\nSee "
            "https://software.intel.com/content/www/us/en/develop/documentation/"
            "installation-guide-for-intel-oneapi-toolkits-linux/top/installation.html"
            " for instructions on how to install Intel's OneAPI, which includes MKL."
        )
    if mkl_root is None:
        mkl_root = "DUMMY-VALUE"
    linking = os.getenv('NRLIB_LINKING')
    if linking not in ['static', 'shared']:
        linking = 'static'
        warn("The environment variable NRLIB_LINKING is unset. It must be 'static' or 'shared'. Setting it to 'static'.")
    link_libraries = []
    compile_args = [
        # Necessary for some C++11 compilers:
        '-D_GLIBCXX_USE_CXX11_ABI=0',
        '-DBOOST_PYTHON_STATIC_LIB',
        '-DBOOST_NUMPY_STATIC_LIB',
        '-DMKL_ILP64',
        '-m64',
        '-I${0}/include'.format(mkl_root),
    ]
    library_extension = get_library_extension(linking)
    # Standard Intel MKL installation (static linking):
    library_dir = mkl_root + '/lib'
    if os.path.isdir(library_dir + '/intel64'):
        library_dir += '/intel64'
    mkl_libraries = ['mkl_core', 'mkl_intel_ilp64', 'mkl_sequential']
    if linking == 'static':
        mkl_libraries = [library_dir + '/lib' + mkl_library + '.' + library_extension for mkl_library in mkl_libraries]
    else:
        link_libraries += mkl_libraries
    if platform.system() == 'Darwin':
        linker_args += ['-I' + mkl_root + '/include', '-L' + library_dir]
        linker_args += mkl_libraries
        linker_args += ' -lpthread -lm -ldl'.format(mkl_root, library_dir).split()
    else:
        linker_args += ['-Wl,--start-group']
        linker_args += mkl_libraries
        linker_args += ['-Wl,--end-group']
    linker_args += ['-lpthread', '-lm', '-ldl']
    boost_library_path = os.path.dirname(os.path.realpath(__file__)) + '/stage/lib'
    if linking == 'shared':
        link_libraries += [boost_library_path + '/' + lib_name for lib_name in boost_libraries]
    elif linking == 'static':
        # Force static linking with Boost (requires Boost compiled with fPIC flag)
        linker_args += ['-L' + boost_library_path, '-Bstatic', '-static-libstdc++']
        linker_args += [boost_library_path + '/lib' + lib_name + '.' + library_extension for lib_name in boost_libraries]
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

type_hint_files = [str(file) for file in Path('gaussianfft').glob('**/*.pyi')]

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

open('source_files.txt', 'w').writelines([file + '\n' for file in all_source_files])

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
                     os.path.abspath('src'),
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


def collect_sources(from_source_files: Iterable[str]) -> List[str]:
    files = set()

    src = Path('src')
    root = Path('.').absolute()
    files_to_be_inspected = set(Path(file) for file in from_source_files)

    def add_if_necessary(file):
        if file not in files and file not in files_to_be_inspected:
            files_to_be_inspected.add(file)

    while len(files_to_be_inspected) > 0:
        file = files_to_be_inspected.pop().resolve().relative_to(root)
        name = str(file)
        if name in files:
            continue

        pattern = re.compile(r'^ *# *include *[<"](?P<name>.*)[">]', re.IGNORECASE)

        try:
            with file.open(encoding='utf8') as f:
                for line in f.readlines():
                    match = pattern.search(line)
                    if match:
                        item = Path(match.group('name'))
                        if (file.parent / item).is_file():
                            add_if_necessary(file.parent / item)
                        elif item.is_file():
                            add_if_necessary(item)
                        elif (src / item).is_file():
                            add_if_necessary(src / item)
                        else:
                            pass
                            # logging.info(file, item)
        except UnicodeDecodeError:
            logging.info(f"'{name}' could not be opened / decoded as a text file. It's been ignored")

        files.add(name)

    return list(files)


def get_source_files_in(directory: str) -> List[str]:
    return [str(file) for file in Path(directory).glob('**/*') if file.is_file()]


def cache_to_disk(func):

    def hash_of_function() -> str:
        # The function may have change, in which case, the cache should be invalidated
        import inspect
        from hashlib import blake2b  # Optimized for 64bit architectures, while the s variant is used for other architectures

        src = inspect.getsource(func)
        return blake2b(src.encode()).hexdigest()

    def decorator(*args, **kwargs):
        sources = Path('boost_source_files.txt')
        if sources.exists():
            with sources.open() as f:
                _hash = f.readline().strip()
                if _hash == hash_of_function():
                    files = f.readlines()
                    return [file.strip() for file in files]
            # Invalidate cache
            os.remove(sources)
            return decorator(*args, **kwargs)
        else:
            files = func(*args, **kwargs)
            with sources.open('w') as f:
                f.write(hash_of_function() + '\n')
                f.writelines([file + '\n' for file in files])
            return files
    return decorator


@cache_to_disk
def get_boost_source_files() -> List[str]:
    return (
            collect_sources(all_source_files)
            # Needed for compiling the boost modules
            + [
                'bootstrap.sh',
                'Makefile',
                'boost-build.jam',
                'Jamroot',
                'boostcpp.jam',
            ]
            + get_source_files_in('tools')
            + collect_sources(get_source_files_in('libs'))
            # Some files seem to be defined dynamically, and thus not reachable to the `get_source_files_in` method
            + get_source_files_in('boost/preprocessor/iteration/detail')
            + get_source_files_in('boost/preprocessor')
            + get_source_files_in('boost/function/detail')
            + get_source_files_in('boost/mpl/aux_/preprocessed')
            + get_source_files_in('boost/mpl/vector/aux_/preprocessed')
            + get_source_files_in('boost/python')
            + get_source_files_in('boost/graph')
            + get_source_files_in('boost/config/no_tr1')
            # Auxiliary files, not related to Boost
            + type_hint_files
    )


boost_module = Extension(
    extension_name,
    sources=get_boost_source_files(),
    include_dirs=[
        'libs',
        'boost',
        'boost/filesystem',
        'boost/detail',
        'boost/python',
        'boost/python/suite/indexing',
        'boost/test',
        'boost/endian',
        'boost/math/special_functions',
    ],
    libraries=boost_libraries,
)


def compile_boost_modules_if_necessary():
    stage = Path('stage/lib')
    if is_compiling() and (
            not stage.exists()
            or not all((stage / f"lib{library}.a").exists() for library in boost_libraries)
    ):
        import subprocess

        subprocess.run(
            ['make _build-boost-python'],
            env=dict(
                os.environ,
                **{
                    'PYTHON': sys.executable,
                    'VIRTUAL_PYTHON': sys.executable,
                    'LC_ALL': 'en_US.utf8',
                }
            ),
            shell=True,
            check=True,
        )


compile_boost_modules_if_necessary()


setup(
    name=extension_name.lstrip('_'),
    version="1.1.0",
    packages=find_packages(),
    ext_modules=[bp_module, boost_module],
    install_requires=[
        f'numpy>={MINIMUM_SUPPORTED_NUMPY}',
    ],
    extras_require={
        "util": ["scipy"]
    },
    include_package_data=True,
    license='LICENSE.txt',
    long_description=long_description,
    long_description_content_type='text/markdown',
    distclass=BinaryDistribution,
    package_data={
        'stage/lib': ['*.so', '*.dll', '*.dylib', '*.a'],
        extension_name: ['py.typed'] + type_hint_files,
    },
    cmdclass={
        'register': register,
        'upload': upload,
    },
    zip_safe=False,
)
