import logging
import os
import re
import subprocess
import sysconfig
from pathlib import Path
from typing import Iterable, Optional, List


def preprocess(file: Path, include_directories: Optional[List[str]] = None) -> Optional[List[str]]:
    cxx = os.environ.get("CXX")
    if cxx:
        # GCC, and older versions of clang may fail if it cannot find references to the #include directives
        # Additionally, the result will not be annotated with -E -dI
        # Clang does not require it, though
        if include_directories is None:
            additional_include_directories = []
        else:
            additional_include_directories = [f"-I{directory}" for directory in include_directories]
            additional_include_directories.append(f"-I{sysconfig.get_path('data')}/include")
        cxx_flags = os.environ.get("CXXFLAGS") or ""
        res = subprocess.run(" ".join([
            cxx,
            *cxx_flags.split(" "),
            "-E",
            "-dI",
            *additional_include_directories,
            str(file),
        ]),
            check=False,
            capture_output=True,
            shell=True,
        )
        if res.returncode > 0:
            raise SystemError(res.stderr)
        if b'-E -dI' in res.stdout:
            return [
                line.decode("utf-8")
                for line in re.findall(b'^.*-E -dI.*$', res.stdout + res.stderr, re.MULTILINE)
            ]
        else:
            return [
                line.decode("utf-8")
                for line in re.findall(b'^# *1 +.*$', res.stdout + res.stderr, re.MULTILINE)
            ]


def collect_sources(
        from_source_files: Iterable[str],
        ignore: Optional[List[str]] = None,
        source_dir: str = 'src',
        use_absolute: bool = False,
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

    include_pattern = re.compile(r'^ *# *include *[<"](?P<name>[a-z0-9/._]*)[">]', re.IGNORECASE)
    define_pattern = re.compile(r'^ *# *define \w+ *(\\\n)? *[<"](?P<name>[\w/.]+)[>"]', re.IGNORECASE | re.MULTILINE)
    completely_preprocessed_pattern = re.compile(r'^ *# *\d+ *[<"](?P<name>[\w/.]+)[>"]', re.IGNORECASE)
    while len(files_to_be_inspected) > 0:

        file = files_to_be_inspected.pop().resolve()
        try:
            file = file.relative_to(root)
        except ValueError:
            if not use_absolute:
                raise
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
                previous_line = line
        except UnicodeDecodeError:
            logging.info(f"'{name}' could not be opened / decoded as a text file. It's been ignored")

        files.append(name)

    return files
