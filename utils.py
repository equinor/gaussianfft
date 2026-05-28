import logging
import os
import re
import subprocess
import sysconfig
import tempfile
from pathlib import Path
from typing import Iterable, Optional, List, Union


def preprocess(file: Path, include_directories: Optional[List[str]] = None) -> Optional[List[str]]:
    cxx = os.environ.get("CXX")
    if cxx:
        # GCC, and older versions of clang may fail if it cannot find references to the #include directives
        # Additionally, the result will not be annotated with -E -dI
        # Clang does not require it, though
        if include_directories is None:
            additional_include_directories = []
        else:
            additional_include_directories = [Path(directory) for directory in include_directories]
        # MSVC uses different arguments and notation than gcc / llvm
        is_msvc = bool(re.search(r"^[a-z]:[\\/].*[\\/]Microsoft Visual Studio[\\/].*[\\/]cl.exe", cxx, re.IGNORECASE))
        if is_msvc:
            preprocessor_args = ("/P", "/showIncludes")
            include_arg = "/I"
        else:
            preprocessor_args = ("-E", "-dI")
            include_arg = "-I"
        include_arguments = []
        for directory in additional_include_directories:
            include_arguments.extend([include_arg, directory])
        cxx_flags = os.environ.get("CXXFLAGS") or ""

        # MSVC cannot preprocess header files directly; wrap them in a temp .cpp
        tmp_file = None
        preprocess_file = file
        if is_msvc and file.suffix in ('.h', '.hpp', '.tcc'):
            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.cpp', dir=str(file.parent))
            try:
                os.write(tmp_fd, f'#include "{file.name}"\n'.encode())
            finally:
                os.close(tmp_fd)
            tmp_file = Path(tmp_path)
            preprocess_file = tmp_file

        try:
            res = subprocess.run([
                cxx,
                *[flag for flag in cxx_flags.split(" ") if flag],
                *preprocessor_args,
                *include_arguments,
                str(preprocess_file),
            ],
                check=False,
                capture_output=True,
                cwd=tempfile.gettempdir() if is_msvc else None,
            )
        finally:
            if tmp_file is not None:
                tmp_file.unlink(missing_ok=True)
                # MSVC /P creates a .i file next to the source
                i_file = tmp_file.with_suffix('.i')
                if i_file.exists():
                    i_file.unlink()
            if is_msvc:
                # Clean up .i file MSVC /P may create in cwd
                i_file = Path(tempfile.gettempdir()) / preprocess_file.with_suffix('.i').name
                if i_file.exists():
                    i_file.unlink()

        if res.returncode != 0:
            return None
        return [
            line[0].decode("utf-8").strip()
            for line in re.findall(b'^((# *[0-9]+ +|Note: including file: +|.*-E -dI).*$)', res.stdout + res.stderr, re.MULTILINE)
        ]


def is_relative_to(path: Path, other: Union[Path, str]) -> bool:
    try:
        return path.is_relative_to(other)
    except AttributeError:
        # Backport for Python < 3.9
        try:
            path.relative_to(other)
            return True
        except ValueError:
            return False


def collect_sources(
        from_source_files: Iterable[str],
        ignore: Optional[List[str]] = None,
        source_dir: str = 'src',
        use_preprocessor: bool = True,
        include_directories: Optional[List[str]] = None,
) -> List[str]:
    if ignore is None:
        ignore = []
    files = []

    src = Path(source_dir)
    root = Path('.').absolute()
    _files_to_be_inspected = [Path(file) for file in from_source_files]
    files_to_be_inspected = []
    for file in _files_to_be_inspected:  # type: Path
        if file.is_dir():
            for child in file.glob('*'):
                if child.is_file():
                    files_to_be_inspected.append(child)
        else:
            files_to_be_inspected.append(file)

    header_regex = re.compile(r'\.h(pp)?$')
    source_regex = re.compile(r'\.c(pp)?$')

    def add_if_necessary(file):
        if any(str(file).startswith(ignore_folder) for ignore_folder in ignore):
            return
        if file not in files and file not in files_to_be_inspected:

            def _add_file(repl: str, file_regex):
                target_file = file.parent / file_regex.sub(repl, file.name)
                if target_file.exists():
                    files_to_be_inspected.append(target_file)

            files_to_be_inspected.append(file)
            # TODO: Deal with dSFT.cpp has a .h file
            if file.suffix in ['.hpp', '.h']:
                _add_file(r'.c\1', header_regex)
                _add_file(r'.cpp', header_regex)
            if file.suffix in ['.cpp', '.c']:
                _add_file(r'.h\1', source_regex)

    _name_group = r'(?P<name>([a-z]:[\\/])?[\w\\/._-]+)'
    _name_pattern = r'[<"]' + _name_group + '[>"]'
    include_pattern = re.compile(r'^ *# *include *' + _name_pattern, re.IGNORECASE)
    define_pattern = re.compile(r'^ *# *define \w+ *(\\\n)? *' + _name_pattern, re.IGNORECASE | re.MULTILINE)
    completely_preprocessed_pattern = re.compile(r'^ *# *\d+ *' + _name_pattern + r'( \d+)*', re.IGNORECASE)
    msvc_include_pattern = re.compile(r'^Note: including file: +' + _name_group, re.IGNORECASE)
    while len(files_to_be_inspected) > 0:

        file = files_to_be_inspected.pop().resolve()
        try:
            file = file.relative_to(root)
        except ValueError:
            # Skip files from the system
            continue
        if use_preprocessor and is_relative_to(file, sysconfig.get_path("include")):
            # We are not interested in these files, and some of them should not be used directly
            # which we'll be doing here
            continue
        name = str(file)
        if name in files:
            continue

        with file.open(encoding='utf8') as f:
            if use_preprocessor:
                source_lines = preprocess(file, include_directories)
            if not use_preprocessor or source_lines is None:
                source_lines = f.readlines()
        try:
            previous_line = ''
            for line in source_lines:
                match = include_pattern.search(line)
                if not match:
                    match = define_pattern.search(line)
                if not match:
                    if not previous_line.endswith('\n'):
                        previous_line += '\n'
                    match = define_pattern.search(previous_line + line)
                if not match:
                    match = completely_preprocessed_pattern.search(line)
                if not match:
                    match = msvc_include_pattern.search(line)
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
                previous_line = line
        except UnicodeDecodeError:
            logging.info(f"'{name}' could not be opened / decoded as a text file. It's been ignored")

        files.append(name)

    # CMake expects UNIX style paths even on Windows
    files = [str(file).replace('\\', '/') for file in files]
    return files
