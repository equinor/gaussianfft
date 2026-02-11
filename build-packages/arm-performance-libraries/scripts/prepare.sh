#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "$0")/common.sh"

function main() {
    local os="$1"
	local library_root
	library_root=$(get_source_directory "$os")
	declare -a library_files=(
	  "bin"
	  "lib"
	  "include"  # TODO: Add option to choose the armpl_ version
	  "license_terms"
	)
    for dir in "${library_files[@]}"; do
      unlink "$ROOT_DIR/$dir"
      ln -s "$library_root/$dir" "$ROOT_DIR/$dir"
	done
	 get_platform "$os" > "$ROOT_DIR/.platform.txt"
}

function get_platform() {
  # The result from sysconfig.get_platform() in python on ARM for different OSes
  # Since this script can be executed from any OS, we want to compile the wheels with the appropriate tags
  # regardless of which platform was used to build the wheels.
  local os="$1"
  if [[ "$os" == "macos" ]]; then
    echo 'macosx-11.0-arm64'
  elif [[ "$os" == "linux"* ]]; then
    echo 'linux-aarch64'
  else
    abort "Unsupported OS $os"
  fi
}

function get_source_directory() {
  local os="$1"
    local installation_target="$CACHE_DIR/$os/data"
  if [[ ! -d "$installation_target" ]]; then
	abort "ARM performance library is missing. Please run ./script/fetch.sh first"
  fi
  if [[ "$os" == "macos" ]]; then
	echo "$installation_target/armpl_${ARMPL_VERSION}_flang-$FLANG_VERSION"
  elif [[ "$os" == "linux_gcc" ]]; then
	echo "$installation_target/opt/arm/armpl_${ARMPL_VERSION}_gcc"
  else
	abort "Unsupported OS $os"
  fi
}

main "$@"
