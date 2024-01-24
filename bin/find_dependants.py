import argparse
import utils
import sysconfig


def parse_arguments():
    parser = argparse.ArgumentParser("find-dependencies")
    parser.add_argument("--use-preprocessor", action="store_true", help="Whether to use the C++ preprocessor on the source files before finding their dependencies")
    parser.add_argument("source_files", nargs="+", help="List of source files to look through")
    parser.add_argument("--include-directories", help="List of directories to include while preprocessing the file(s), seperated by ';'")
    return parser.parse_args()


def run():
    args = parse_arguments()
    include_directories = None
    if args.include_directories:
        include_directories = args.include_directories.split(";")
        include_directories.append(f"{sysconfig.get_path('data')}/include")

    print(' '.join(utils.collect_sources(
        args.source_files,
        use_preprocessor=args.use_preprocessor,
        include_directories=include_directories,
        ignore=include_directories,
    )))


if __name__ == '__main__':
    run()
