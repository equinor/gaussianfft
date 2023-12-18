#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(realpath "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)/..")

readonly BOOST_VERSION="${BOOST_VERSION:-$1}"

if [[ -z "$BOOST_VERSION" ]]; then
  echo "No version of Boost is given" >/std/err
  exit 1
fi

readonly BOOST_DIR="$ROOT_DIR/sources/boost"

readonly PYTHON="${PYTHON:-$(which python)}"
# TODO: Check if NumPy is installed!

readonly SOURCE_ROOT="$BOOST_DIR/$BOOST_VERSION"

# Fetch files if necessary (this should probably not happen if we're building from a source distribution)
if [[ ! -d "$SOURCE_ROOT" ]]; then
  "$ROOT_DIR/bin/fetch-boost.sh" "$BOOST_VERSION"
fi

cd "$SOURCE_ROOT"
# Bootstrap compilation
if [[ ! -f b2 ]]; then
./bootstrap.sh \
    --prefix="$PWD/build" \
    --with-python="$PYTHON" \
    --with-icu
fi

# Compile necessary modules
CPLUS_INCLUDE_PATH=$($PYTHON -c "from sysconfig import get_paths; print(get_paths()['include'])") \
./b2 \
    --with-python \
    --with-filesystem \
    --with-system \
    -q \
    cxxflags=-fPIC \
    cflags=-fPIC \
    python-debugging=off \
    threading=multi \
    variant=release \
    link=static \
    runtime-link=static \
    "$ROOT_DIR/stage"
