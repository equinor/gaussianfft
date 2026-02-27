import argparse
import sys
from pathlib import Path


def install_dir():
    package_dir = Path(__file__).parent
    return package_dir.parent.parent.parent.parent.absolute()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="store_true")
    return parser.parse_args()

def run():
    args = parse_args()
    if args.version:
        from . import __version__
        sys.stdout.write(__version__)
    else:
        sys.stdout.write(str(install_dir()))

if __name__ == '__main__':
    run()
