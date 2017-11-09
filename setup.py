import glob
import os
import platform

from setuptools import Extension, setup

""" Installation Instructions """
# Linux:
#   [Conditional] export MKL_ROOT=/nr/prog/intel/Compiler/mkl
#   [Conditional] /nr/prog/smedvig/rms/versions/10.1.1/linux-amd64-gcc_4_4-release/bin/roxenv
# Make sure the correct version of pip is being used:
#   which pip
#   pip install --user -e .
# Note: The option -e is optional, but it is convenient to use during development.
#
#
# Windows:
#   python setup.py install [--user]
# or (preferrably)
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

if os.path.isfile(compilation_logs):
    import subprocess
    import datetime

    def get_revision(text):
        lines = text.decode().replace('\r', '').split('\n')
        revision_line = [li for li in lines if "Revision" in li]
        assert len(revision_line) == 1
        return revision_line[0].split()[-1]

    process = subprocess.Popen(['svn', 'info', 'src/nrlib'], stdout=subprocess.PIPE)
    out, err = process.communicate()
    nr_rev = get_revision(out)
    process = subprocess.Popen(['svn', 'info', 'src/flens'], stdout=subprocess.PIPE)
    out, err = process.communicate()
    fl_rev = get_revision(out)
    line = str(datetime.datetime.now()) + ": nrlib r{}, flens r{}\n".format(nr_rev, fl_rev)
    open(compilation_logs, 'a').write(line)

# Platform specific definitions
linker_args = []
if platform.system() == 'Linux':
    mkl_root = os.getenv('MKL_ROOT')
    if mkl_root is None:
        raise RuntimeError(
            "Environment variable MKL_ROOT is not defined. "
            "MKL headers and libraries are required."
        )
    link_libraries = [
        'mkl_intel_lp64',
        'mkl_sequential',
        'mkl_core',
        'mkl_mc3',
        'mkl_def',
        'boost_python3',
        'boost_filesystem',
        'boost_system',
    ]
    compile_args = []
    linker_args += [
        # mkl_root + '/lib/intel64/libmkl_core.a',
        # mkl_root + '/lib/intel64/libmkl_intel_lp64.a',
        # mkl_root + '/lib/intel64/libmkl_sequential.a',
    ]
    library_dirs = [
        # boost_root + '/lib/',
        mkl_root + '/lib/intel64/',
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
        # '/showIncludes'  # Debug
    ]
    library_dirs = [r'libs\win64vc11']

fftw_dirs = [
    os.path.join(mkl_root, "include", "fftw"),
    os.path.join(mkl_root, "include"),
]

# Define all nrlib source files to compile. Globbing may not be recommended,
# but it is convenient and compact.
nrlib_source_files = glob.glob('src/nrlib/*/*.cpp')
nrlib_source_files += glob.glob('src/flens/*.cc')
source_files = [
    'src/gaussfft.cpp',
    'src/gaussfftinterface.cpp',
]
all_source_files = source_files + nrlib_source_files

# We do not need entire NRLib. Exclude unused files.
all_source_files = [
    a
    for a in all_source_files
    if not a.startswith('src/nrlib\\eclipsegrid')
       and not a.startswith('src/nrlib\\geometry')
       and not a.startswith('src/nrlib\\pointset')
       and (not a.startswith('src/nrlib\\random') or a.count('random') == 2 or 'dSFMT' in a)
       and not a.startswith('src/nrlib\\segy')
       and not a.startswith('src/nrlib\\statistics')
       and not a.startswith('src/nrlib\\stormgrid')
       and not a.startswith('src/nrlib\\surface')
       and not a.startswith('src/nrlib\\tinyxml')
       and not a.startswith('src/nrlib\\trend')
       and not a.startswith('src/nrlib\\volume')
       and not a.startswith('src/nrlib\\wavelet')
       and not a.startswith('src/nrlib\\well')
]

""" Python module setup """

bp_module = Extension(
    extension_name,
    sources=all_source_files,
    define_macros=[
        ('FLENS_FIRST_INDEX', '0'),
        ('MKL', None),
    ],
    include_dirs=[
        os.path.abspath('.'),  # For Boost
        os.path.abspath('./src'),
    ]
    + fftw_dirs,
    library_dirs=library_dirs,
    libraries=link_libraries,
    extra_compile_args=compile_args,
    extra_link_args=[
        # '/VERBOSE:lib'    # For Debug
    ]
    + linker_args,
    language='c++'
)

setup(
    name=extension_name,
    version="0.2",
    packages=[],  # find_packages()
    ext_modules=[bp_module]
)
