#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"

readonly BOOST_VERSION="${BOOST_VERSION:-$1}"

if [[ -z $BOOST_VERSION ]]; then
  echo "No version of Boost is given" >/std/err
  exit 1
fi

readonly BOOST_DIR="$ROOT_DIR/sources/boost"
readonly BOOST_ARCHIVE="$BOOST_VERSION.tar.gz"

readonly PYTHON="${PYTHON:-$(which python)}"

readonly SOURCE_ROOT="$BOOST_DIR/$BOOST_VERSION"

mkdir -p "$BOOST_DIR"
cd "$BOOST_DIR"

if [[ ! -f "$BOOST_ARCHIVE" ]]; then
  file_name="boost_$(echo "$BOOST_VERSION" | tr '.' '_').tar.gz"
  curl -L --output "$BOOST_VERSION".tar.gz \
  "https://boostorg.jfrog.io/artifactory/main/release/$BOOST_VERSION/source/$file_name"
fi

function extract_files() {
  # TODO: Extract only necessary files directly from the archive
  local boost_dir
  boost_dir="boost_$(echo "$BOOST_VERSION" | tr '.' '_')"
  if [[ ! -d "$boost_dir" ]]; then
    tar -xf "$BOOST_ARCHIVE"
  fi
  local file_name="$1"
  mkdir -p "$BOOST_VERSION/$(dirname "$file_name")"
  if [[ -d "$boost_dir/$file_name" && "${file_name: -1}" != "/" ]]; then
    file_name="$file_name/"
  fi
  # TODO: Fall back on cp -r ---no-target-directory
  if [[ $(command -v rsync) ]]; then
    sync="rsync -ruat"
  else
    # TODO: Check if cp supports --no-target-directory / -t (GNU)
    sync="cp -r --no-target-directory"
  fi
  $sync "$boost_dir/$file_name" "$BOOST_VERSION/$file_name"
}

function files_depending_on() {
  local boost_dir
  boost_dir="boost_$(echo "$BOOST_VERSION" | tr '.' '_')"
  cd "$boost_dir" >/dev/null
  PYTHONPATH="$ROOT_DIR" "$PYTHON" -c "
import utils
from pathlib import Path


if '${2:-}' == 'missing_ok' and not Path('$1').exists():
    # The file does not exist, but that's ok
    exit(0)

print(' '.join(utils.collect_sources(['$1'], use_absolute=True)))
"
  cd - >/dev//null
}

function extract_files_depending_on() {
  local source="$1"
  local may_be_missing=${2:-}
  echo "Analysing dependencies of $source"
  read -ra dependencies <<< "$(files_depending_on "$source" "$may_be_missing")"
  if [[ -z ${dependencies:-} ]]; then
    if [[ "$may_be_missing" == "missing_ok" ]]; then
      echo "$source not found"
      return
    else
      # The file does not exist. This can happen because it may not be included in the desired version of Boost
      echo "$source is missing, and that's not ok"
    fi
  fi
  for file in "${dependencies[@]}"; do
    if [[ -d "$SOURCE_ROOT/$file" || -f "$SOURCE_ROOT/$file" ]]; then
      continue
    fi
    echo "Copying $source -> $file"
    extract_files "$file"
  done
}

function extract_boost_files_used_by_us() {
  local source="$1"
  echo "Analysing dependencies of $source"
  read -ra dependencies <<< "$(files_depending_on "$source")"
  for file in "${dependencies[@]}"; do
    if [[ "$file" == "$ROOT_DIR"/* ]]; then
      continue
    else
      extract_files "$file"
    fi
  done
}

# extract necessary files
# Files for bootstrapping the compilation
extract_files bootstrap.sh
extract_files tools/build/src/engine
extract_files_depending_on "tools/build/src/engine/"
extract_files_depending_on "tools/build/src/engine/modules"

# Files for configuring / starting the compilation
extract_files Jamroot
extract_files boostcpp.jam
extract_files boost-build.jam

extract_files tools/build/src/bootstrap.jam
extract_files tools/build/src/build/
extract_files tools/build/src/util/
extract_files tools/build/src/tools/

extract_files tools/boost_install/Jamfile
extract_files tools/boost_install/boost-install.jam
extract_files tools/boost_install/boost-install-dirs.jam
extract_files tools/boost_install/BoostDetectToolset.cmake
extract_files tools/boost_install/BoostConfig.cmake

# Used during runtime of b2
extract_files tools/build/src/kernel/
extract_files tools/build/src/util/option.jam
extract_files tools/build/src/build-system.jam
# TODO: Seems we also need Boost.Regex for ICU

# Libraries
## Configuration
extract_files libs/config/checks/architecture
extract_files libs/config/checks/std
extract_files libs/config/checks/Jamfile.v2
extract_files libs/config/checks/config.jam
extract_files libs/config/test
extract_files libs/headers/build
# Only required in newer versions
extract_files_depending_on libs/config/checks/test_case.cpp

## Filesystem
extract_files libs/filesystem/build
extract_files libs/filesystem/config
extract_files libs/filesystem/meta
extract_files_depending_on "libs/filesystem/src/"
extract_files_depending_on "libs/filesystem/src/path.cpp"

## Required in 1.81.0
extract_files libs/atomic/build
extract_files libs/atomic/config
extract_files libs/atomic/meta
extract_files_depending_on "libs/atomic/src/"

extract_files_depending_on "boost/align/aligned_alloc.hpp"
# Related to static linking
extract_files_depending_on "boost/preprocessor/iteration/detail/iter/forward1.hpp"
extract_files_depending_on "boost/type_traits/alignment_of.hpp"
extract_files boost/preprocessor

## Filesystem
extract_files_depending_on "boost/filesystem.hpp"
extract_files_depending_on "boost/filesystem/config.hpp"
## Somewhat dynamic dependencies (through macro)
extract_files "boost/atomic/detail"

### Somewhat dynamic dependency (it is reached through a macro, which we are unable to parse)
extract_files "boost/mpl/aux_/preprocessed"

# Fetch all boost files that are used by gaussianfft
extract_boost_files_used_by_us "$ROOT_DIR/src/gaussfftinterface.cpp"
