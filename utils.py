import logging
import re
from pathlib import Path
from typing import Iterable, Optional, List


def collect_sources(
        from_source_files: Iterable[str],
        ignore: Optional[List[str]] = None,
        source_dir: str = 'src',
        use_absolute: bool = False,
) -> List[str]:
    if ignore is None:
        ignore = []
    files = set()

    src = Path(source_dir)
    root = Path('.').absolute()
    _files_to_be_inspected = set(Path(file) for file in from_source_files)
    files_to_be_inspected = set()
    for file in _files_to_be_inspected:  # type: Path
        if file.is_dir():
            for child in file.glob('*'):
                if child.is_file():
                    files_to_be_inspected.add(child)
        else:
            files_to_be_inspected.add(file)

    header_regex = re.compile(r'\.h(pp)?$')
    source_regex = re.compile(r'\.c(pp)?$')

    def add_if_necessary(file):
        if any(str(file).startswith(ignore_folder) for ignore_folder in ignore):
            return
        if file not in files and file not in files_to_be_inspected:
            files_to_be_inspected.add(file)
            if file.suffix in ['.hpp', '.h']:
                source_file = file.parent / header_regex.sub(r'.c\1', file.name)
                if source_file.exists():
                    files_to_be_inspected.add(source_file)
            if file.suffix in ['.cpp', '.c']:
                header_file = file.parent / source_regex.sub(r'.h\1', file.name)
                if header_file.exists():
                    files_to_be_inspected.add(header_file)

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

        include_pattern = re.compile(r'^ *# *include *[<"](?P<name>[a-z0-9/._]*)[">]', re.IGNORECASE)
        define_pattern = re.compile(r'^ *# *define \w+ *(\\\n)? *[<"](?P<name>[\w/.]+)[>"]', re.IGNORECASE | re.MULTILINE)

        try:
            with file.open(encoding='utf8') as f:
                previous_line = ''
                for line in f.readlines():
                    match = include_pattern.search(line)
                    if not match:
                        match = define_pattern.search(line)
                    if not match:
                        if not previous_line.endswith('\n'):
                            previous_line += '\n'
                        match = define_pattern.search(previous_line + line)
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

        files.add(name)

    return list(files)
