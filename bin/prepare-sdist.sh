#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"
readonly PYTHON=${PYTHON:-python3}

# Remove all, but the oldest supported version of boost
# add that version to a file, which is read by `find_boost_version.py`

readonly boost_version="$("$PYTHON" "$ROOT_DIR/bin/find_boost_version.py" --sdist)"

shopt -s extglob
cd "$ROOT_DIR/sources/boost"
rm -rf !("$boost_version")
cd - >/dev/null

echo "$boost_version" > "$ROOT_DIR/USE_BOOST_VERSION.txt"

# Remove the build artifacts from FFTW
rm -rf "$ROOT_DIR/vendor"

# Remove "uncleaned" build artefacts from FFTW
find "$ROOT_DIR/sources/fftw/" \
    '(' \
        -name .deps -type d \
        -or \
        -name '*.pc' -type f \
        -or \
        -name '*.cmake' -type f \
        -or \
        -name 'config.*' -type f \
        -or \
        -name 'Makefile' -type f \
    ')' \
    -exec rm -rf {} +
