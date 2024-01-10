#!/usr/bin/env python3
import argparse
import platform
import sys
from pathlib import Path


PYTHON_VERSION = sys.version_info

KNOWN_MINIMUMS = [
    {"python_version": (3, 6), "min_version": (1, 74, 0), "platform_system": "Linux"},
    {"python_version": (3, 6), "min_version": (1, 76, 0), "platform_system": "Darwin"},
    {"python_version": (3, 10), "min_version": (1, 76, 0), "platform_system": "Linux"},
    {"python_version": (3, 11), "min_version": (1, 81, 0)},
]

# These are known to cause problems on newer versions of Python and/or some OS-es
PROBLEMATIC_VERSIONS = [
    # Seem to not support Python 3.10 and newer
    # It is also problematic to compile on macOS
    (1, 74, 0),
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
    version = (1, 74, 0)
    python_version = (PYTHON_VERSION.major, PYTHON_VERSION.minor)
    for constraint in KNOWN_MINIMUMS:
        if constraint["python_version"] <= python_version:
            required_system = constraint.get("platform_system")
            if required_system is None or required_system == platform.system():
                version = constraint["min_version"]
    return version


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="find-relevant-boost-version",
        description="Gives the appropriate version of Boost, based on gaussianfft's known run environments",
    )
    parser.add_argument(
        "-s", "--sdist",
        action="store_true",
        required=False,
        help="Toggles if the version of Boost should be appropriate for inclusion in the source distribution",
    )
    return parser.parse_args()


def run():
    args = parse_arguments()
    if args.sdist:
        version = boost_version_for_sdist()
    else:
        version = boost_version_for_wheel()
    sys.stdout.write('.'.join(map(str, version)))


def boost_version_for_sdist():
    python_version = (float('inf'), float('inf'))
    boost_version = (0, 0, 0)
    for constraint in KNOWN_MINIMUMS:
        if python_version > constraint["python_version"] and constraint["min_version"] not in PROBLEMATIC_VERSIONS:
            python_version = constraint["python_version"]

    for constraint in KNOWN_MINIMUMS:
        if python_version == constraint["python_version"]:
            if boost_version < constraint["min_version"]:
                boost_version = constraint["min_version"]
    return boost_version


def boost_version_for_wheel():
    version = fixed_boost_version()
    if version is None:
        version = dynamic_boost_version()
    return version


if __name__ == '__main__':
    run()
