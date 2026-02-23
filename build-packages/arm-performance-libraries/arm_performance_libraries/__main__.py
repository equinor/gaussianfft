import sys
from pathlib import Path


def install_dir():
    package_dir = Path(__file__).parent
    return package_dir.parent.parent.parent.parent.absolute()

if __name__ == '__main__':
    sys.stdout.write(str(install_dir()))
