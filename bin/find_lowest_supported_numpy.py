import sys
import json
import re
try:
    from typing import Tuple, Optional
except ImportError:
    pass

PYTHON_VERSION = sys.version_info

if PYTHON_VERSION.major < 3 or (PYTHON_VERSION.major == 3 and PYTHON_VERSION.minor < 6):
    raise RuntimeError(
        'Python 3.6, or greater is required. You are using Python {}.{}, which is not supported'
        ''.format(PYTHON_VERSION.major, PYTHON_VERSION.minor)
    )

SEMVER = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')  # Exclude Release candidates, betas, and alpha releases


def get_numpy_meta_data():
    # type: () -> dict
    import urllib.request
    from pathlib import Path

    numpy_data = Path('.numpy.json').absolute()

    if not numpy_data.exists():
        with urllib.request.urlopen('https://pypi.org/pypi/numpy/json') as response:
            with numpy_data.open('wb') as f:
                f.write(response.read())

    with numpy_data.open() as f:
        content = json.load(f)
    return content


def get_minimum_supported_numpy_version(python_version = None):
    # type: (Optional[str]) -> Optional[str]
    supported_versions = []
    if python_version is None:
        current_python_version = "cp{}{}".format(PYTHON_VERSION.major, PYTHON_VERSION.minor)
    else:
        python_version = python_version.replace('.', '').strip()
        current_python_version = "cp{}".format(python_version)

    content = get_numpy_meta_data()
    for version_key, distributions in content['releases'].items():
        if SEMVER.match(version_key) and any(
                distribution['python_version'] == current_python_version
                and distribution['packagetype'] == 'bdist_wheel'
                for distribution in distributions
        ):
            supported_versions.append(version_key)

    def to_semver(version):
        # type: (str) -> Tuple[int, int, int]
        major, minor, patch = version.split('.')
        return int(major), int(minor), int(patch)

    versions = [to_semver(version) for version in supported_versions]
    versions.sort()  # From lowest to highest

    if len(versions) >= 1:
        return '.'.join(str(num) for num in versions[0])
    return None


if __name__ == '__main__':
    try:
        _, python_version, *rest = sys.argv  # type: Optional[str]
    except ValueError:
        python_version = None
    min_version = get_minimum_supported_numpy_version(python_version)
    if min_version:
        print(min_version)
