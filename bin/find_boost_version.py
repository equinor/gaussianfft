#!/usr/bin/env python3
import sys


PYTHON_VERSION = sys.version_info

KNOWN_MINIMUMS = [
    {"python_version": (3, 11), "min_version": (1, 81, 0)},
]


def run():
    version = (1, 76, 0)
    python_version = (PYTHON_VERSION.major, PYTHON_VERSION.minor)
    for constraint in KNOWN_MINIMUMS:
        if constraint["python_version"] <= python_version:
            version = constraint["min_version"]
    sys.stdout.write('.'.join(map(str, version)))


if __name__ == '__main__':
    run()
