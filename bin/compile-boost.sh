#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"

readonly BOOST_VERSION="${BOOST_VERSION:-${1-}}"

if [[ -z "$BOOST_VERSION" ]]; then
  echo "No version of Boost is given" >/dev/stderr
  exit 1
fi

readonly BOOST_DIR="$ROOT_DIR/sources/boost"

readonly SOURCE_ROOT="$BOOST_DIR/$BOOST_VERSION"

# Fetch files if necessary (this should probably not happen if we're building from a source distribution)
if [[ ! -d "$SOURCE_ROOT" ]]; then
  "$ROOT_DIR/bin/fetch-boost.sh" "$BOOST_VERSION"
fi

cd "$SOURCE_ROOT" >/dev/null
# Bootstrap compilation
if [[ ! -f b2 ]]; then
  if [ ! -x ./bootstrap.sh ]; then
    # When mounting the files in docker / GitHub Actions, it is possible the files looses their permissions
    chmod +x ./bootstrap.sh
  fi
  if [ ! -x ./tools/build/src/engine/build.sh ]; then
    chmod +x ./tools/build/src/engine/build.sh
  fi
./bootstrap.sh \
    --prefix="$ROOT_DIR" \
    --with-libraries=filesystem \
    --with-icu || {
      cat bootstrap.log >/dev/stderr ;
      exit 1 ;
    }
fi

# Compile necessary modules
./b2 \
    --with-filesystem \
    -q \
    cxxflags=-fPIC \
    cflags=-fPIC \
    threading=multi \
    variant=release \
    link=static \
    runtime-link=static \
    stage
