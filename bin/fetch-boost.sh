#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(realpath "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)/..")

readonly BOOST_VERSION="${BOOST_VERSION:-$1}"

if [[ -z $BOOST_VERSION ]]; then
  echo "No version of Boost is given" >/std/err
  exit 1
fi

readonly BOOST_DIR="$ROOT_DIR/sources/boost"
readonly BOOST_ARCHIVE="$BOOST_VERSION.tar.gz"

readonly PYTHON="${PYTHON:-$(which python)}"
# TODO: Check if NumPy is installed!

readonly SOURCE_ROOT="$BOOST_DIR/$BOOST_VERSION"

mkdir -p "$BOOST_DIR"
cd "$BOOST_DIR"

if [[ ! -f "$BOOST_ARCHIVE" ]]; then
  file_name="boost_$(echo "$BOOST_VERSION" | tr '.' '_').tar.gz"
  curl -L --output "$BOOST_DIR".tar.gz \
  "https://boostorg.jfrog.io/artifactory/main/release/$BOOST_VERSION/source/boost_$file_name"
fi

function extract_files() {
  # TODO: Extract only necessary files directly from the archive
  local boost_dir="boost_$(echo "$BOOST_VERSION" | tr '.' '_')"
  if [[ ! -d "$boost_dir" ]]; then
    tar -xvf "$BOOST_ARCHIVE"
  fi
  local file_name="$1"
  mkdir -p "$BOOST_VERSION/$(dirname "$file_name")"
  cp -r --no-target-directory "$boost_dir/$file_name" "$BOOST_VERSION/$file_name"
}

function files_depending_on() {
  local boost_dir="boost_$(echo "$BOOST_VERSION" | tr '.' '_')"
  cd "$boost_dir" >/dev/null
  PYTHONPATH="$ROOT_DIR" "$PYTHON" -c "
import utils
print(' '.join(utils.collect_sources(['$1'], use_absolute=True)))
"
  cd - >/dev//null
}

function extract_files_depending_on() {
  local source="$1"
  read -ra dependencies <<< "$(files_depending_on "$source")"
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
extract_files libs/headers/build

## Python
extract_files libs/python/build
extract_files libs/python/meta
extract_files "libs/python/src/"
extract_files_depending_on "libs/python/src/"
extract_files libs/python/fabscript
# Dependencies not caught in extract_files_depending_on
extract_files_depending_on "libs/python/src/converter/type_id.cpp"

extract_files_depending_on "libs/python/src/object/class.cpp"
extract_files_depending_on "boost/detail/binary_search.hpp"

extract_files_depending_on "libs/python/src/object/inheritance.cpp"
extract_files_depending_on "boost/graph/breadth_first_search.hpp"
extract_files_depending_on "boost/pending/queue.hpp"
extract_files_depending_on "boost/graph/graph_traits.hpp"
extract_files "boost/type_traits"
extract_files_depending_on "boost/type_traits.hpp"

extract_files_depending_on "boost/graph/graph_concepts.hpp"
extract_files_depending_on "boost/graph/named_function_params.hpp"
extract_files_depending_on "boost/utility/detail/result_of_variadic.hpp"

extract_files_depending_on "libs/python/src/list.cpp"

#extract_files "boost/preprocessor"
extract_files_depending_on "boost/preprocessor.hpp"

# from libs/python/src/object/inheritance.cpp:7 (related to regex / strange include)
extract_files_depending_on "boost/graph/detail/empty_header.hpp"

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

extract_files_depending_on "libs/atomic/src/lock_pool.cpp"

extract_files_depending_on "boost/align/aligned_alloc.hpp"
# Related to static linking
extract_files_depending_on "boost/preprocessor/iteration/detail/iter/forward1.hpp"
extract_files_depending_on "boost/type_traits/alignment_of.hpp"
extract_files boost/preprocessor

## System
extract_files libs/system/build
extract_files libs/system/meta
extract_files_depending_on "libs/system/src/"
extract_files_depending_on "libs/filesystem/src/operations.cpp"


# Source files and headers
## Python
extract_files "boost/python"
extract_files_depending_on "boost/python.hpp"
# Additional files not caught above
extract_files_depending_on "boost/python/detail/decorated_type_id.hpp"


## Filesystem
extract_files_depending_on "boost/filesystem.hpp"
extract_files_depending_on "boost/filesystem/config.hpp"
## Somewhat dynamic dependencies (through macro)
extract_files "boost/atomic/detail"

## System
extract_files_depending_on "boost/system.hpp"

### Somewhat dynamic dependency (it is reached through a macro, which we are unable to parse)
extract_files "boost/mpl/aux_/preprocessed"


## Used for static linking
# TODO: We may want to include ARM / macOS M
extract_files_depending_on "boost/predef/architecture/x86.h"
extract_files_depending_on "boost/predef/hardware/simd/x86.h"

extract_files boost/mpl/vector/aux_/preprocessed/typeof_based
#
#extract_files_depending_on "boost/atomic/detail/int_sizes.hpp"
#extract_files_depending_on "boost/atomic/detail/intptr.hpp"
#extract_files_depending_on "boost/config/warning_disable.hpp"

#extract_files boost/config
#extract_files boost/config.hpp

# Fetch all boost files that are used by gaussianfft
extract_boost_files_used_by_us "$ROOT_DIR/src/gaussfftinterface.cpp"
