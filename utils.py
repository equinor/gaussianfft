import logging
import os
import re
import subprocess
import sysconfig
from collections.abc import Iterable
from pathlib import Path


def preprocess(file: Path, include_directories: list[str] | None = None) -> list[str] | None:
    cxx = os.environ.get('CXX')
    if cxx:
        # GCC, and older versions of clang may fail if it cannot find references to the #include directives
        # Additionally, the result will not be annotated with -E -dI
        # Clang does not require it, though
        if include_directories is None:
            additional_include_directories = []
        else:
            additional_include_directories = [Path(directory) for directory in include_directories]
        # MSVC uses different arguments and notation than gcc / llvm
        if re.search(
            r'^[a-z]:[\\/].*[\\/]Microsoft Visual Studio[\\/].*[\\/]cl.exe',
            cxx,
            re.IGNORECASE,
        ):
            preprocessor_args = ('/P', '/showIncludes')
            include_arg = '/I'
        else:
            preprocessor_args = ('-E', '-dI')
            include_arg = '-I'
        cxx_flags = os.environ.get('CXXFLAGS') or ''
        res = subprocess.run(  # noqa: S602
            ' '.join(
                [
                    f'"{cxx}"',
                    *cxx_flags.split(' '),
                    *preprocessor_args,
                    *[f'{include_arg}"{include}"' for include in additional_include_directories],
                    str(file),
                ]
            ),
            check=False,
            capture_output=True,
            shell=True,
        )
        return [
            line[0].decode('utf-8').strip()
            for line in re.findall(
                b'^((# *[0-9]+ +|Note: including file: +|.*-E -dI).*$)',
                res.stdout + res.stderr,
                re.MULTILINE,
            )
        ]


def is_relative_to(path: Path, other: Path | str) -> bool:
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
    ignore: list[str] | None = None,
    source_dir: str = 'src',
    use_preprocessor: bool = True,
    include_directories: list[str] | None = None,
) -> list[str]:
    collector = SourceCollector(from_source_files, ignore, source_dir, use_preprocessor, include_directories)
    return collector.collect_files()


class SourceCollector:
    header_regex = re.compile(r'\.h(pp)?$')
    source_regex = re.compile(r'\.c(pp)?$')

    _name_group = r'(?P<name>([a-z]:[\\/])?[\w\\/._-]+)'
    _name_pattern = r'[<"]' + _name_group + '[>"]'
    include_pattern = re.compile(r'^ *# *include *' + _name_pattern, re.IGNORECASE)
    define_pattern = re.compile(r'^ *# *define \w+ *(\\\n)? *' + _name_pattern, re.IGNORECASE | re.MULTILINE)
    completely_preprocessed_pattern = re.compile(r'^ *# *\d+ *' + _name_pattern + r'( \d+)*', re.IGNORECASE)
    msvc_include_pattern = re.compile(r'^Note: including file: +' + _name_group, re.IGNORECASE)

    def __init__(
        self,
        from_source_files: Iterable[str],
        ignore: list[str] | None = None,
        source_dir: str = 'src',
        use_preprocessor: bool = True,
        include_directories: list[str] | None = None,
    ):
        if ignore is None:
            ignore = []
        self.files = []
        self.files_to_be_inspected = []

        self.from_source_files = from_source_files
        self.ignore = ignore
        self.source_dir = source_dir
        self.use_preprocessor = use_preprocessor
        self.include_directories = include_directories
        self.src = Path(self.source_dir)

    def collect_files(self) -> list[str]:
        root = Path('.').absolute()
        _files_to_be_inspected = [Path(file) for file in self.from_source_files]
        for file in _files_to_be_inspected:  # type: Path
            if file.is_dir():
                for child in file.glob('*'):
                    if child.is_file():
                        self.files_to_be_inspected.append(child)
            else:
                self.files_to_be_inspected.append(file)

        while len(self.files_to_be_inspected) > 0:
            file = self.files_to_be_inspected.pop().resolve()
            try:
                file = file.relative_to(root)
            except ValueError:
                # Skip files from the system
                continue
            if self.use_preprocessor and is_relative_to(file, sysconfig.get_path('include')):
                # We are not interested in these files, and some of them should not be used directly
                # which we'll be doing here
                continue
            self.inspect_source_file(file)

        # CMake expects UNIX style paths even on Windows
        files = [str(file).replace('\\', '/') for file in self.files]
        return files

    def inspect_source_file(self, file: Path):
        name = str(file)
        if name in self.files:
            return

        with file.open(encoding='utf8') as f:
            source_lines = None
            if self.use_preprocessor:
                source_lines = preprocess(file, self.include_directories)
            if not self.use_preprocessor or source_lines is None:
                source_lines = f.readlines()
        try:
            self.search_for_included_files(source_lines, file)
        except UnicodeDecodeError:
            logging.info(f"'{name}' could not be opened / decoded as a text file. It's been ignored")

        self.files.append(name)

    def search_for_included_files(self, source_lines: list[str], file: Path):  # noqa: C901
        previous_line = ''
        for line in source_lines:
            match = self.include_pattern.search(line)
            if not match:
                match = self.define_pattern.search(line)
            if not match:
                if not previous_line.endswith('\n'):
                    previous_line += '\n'
                match = self.define_pattern.search(previous_line + line)
            if not match:
                match = self.completely_preprocessed_pattern.search(line)
            if not match:
                match = self.msvc_include_pattern.search(line)  # type: ignore # pyrefly is having issues
            if match:
                item = Path(match.group('name'))
                if (file.parent / item).is_file():
                    self.add_if_necessary(file.parent / item)
                elif item.is_file():
                    self.add_if_necessary(item)
                elif (self.src / item).is_file():
                    self.add_if_necessary(self.src / item)
            previous_line = line

    def add_if_necessary(self, file):
        if any(str(file).startswith(ignore_folder) for ignore_folder in self.ignore):
            return
        if file not in self.files and file not in self.files_to_be_inspected:

            def _add_file(repl: str, file_regex):
                target_file = file.parent / file_regex.sub(repl, file.name)
                if target_file.exists():
                    self.files_to_be_inspected.append(target_file)

            self.files_to_be_inspected.append(file)
            # TODO: Deal with dSFT.cpp has a .h file
            if file.suffix in ['.hpp', '.h']:
                _add_file(r'.c\1', self.header_regex)
                _add_file(r'.cpp', self.header_regex)
            if file.suffix in ['.cpp', '.c']:
                _add_file(r'.h\1', self.source_regex)
