#!/usr/bin/env python3
import sys
from pathlib import Path


PYTHON_VERSION = sys.version_info

KNOWN_MINIMUMS = [
    {"python_version": (3, 11), "min_version": (1, 81, 0)},
]

ROOT = Path(__file__).parent


def fixed_boost_version():
    path = ROOT / "USE_BOOST_VERSION.txt"
    version = None
    if path.exists():
        with open(path) as f:
            content = f.read().strip()
        version = map(int, content.split('.'))
    return version


def dynamic_boost_version():
    version = (1, 76, 0)
    python_version = (PYTHON_VERSION.major, PYTHON_VERSION.minor)
    for constraint in KNOWN_MINIMUMS:
        if constraint["python_version"] <= python_version:
            version = constraint["min_version"]
    return version


def run():
    version = fixed_boost_version()
    if version is None:
        version = dynamic_boost_version()
    sys.stdout.write('.'.join(map(str, version)))


if __name__ == '__main__':
    run()
