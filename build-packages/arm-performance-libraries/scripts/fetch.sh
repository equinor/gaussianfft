#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "$0")/common.sh"

# TODO: Check if bash is 'modern' (5+)

if ! has 'zsh'; then
  abort "zsh is required to 'install' / extract files for macos'"
fi

if ! has '7z' && ! has '7zz'; then
  abort "7-zip is required to extract the source archive for macos"
fi

function _7z() {
  if has '7zz'; then
	7zz "$@"
  else
	7z "$@"
  fi
}

function main() {
	mkdir -p "$CACHE_DIR"

  local url
  local archive_path
  local installation_script
  for os in "${TARGET_PLATFORMS[@]}"; do
    url="$(get_download_url "$os")"
    archive_path="$(download "$url")"
    installation_script="$(get_expected_installation_script "$os")"
    if [[ ! -f "$installation_script" ]]; then
	  extract_archive "$archive_path" "$os"
	  if [[ "$os" == "macos" ]]; then
		extract_archive "$CACHE_DIR/armpl_${ARMPL_VERSION}_flang-$FLANG_VERSION.dmg" "$os"
	  fi
	fi
	extract_library_files "$installation_script" "$os"
  done
}

function extract_library_files() {
  local installation_script="$1"
  local os="$2"
  local installation_target="$CACHE_DIR/$os/data"

  if [[ ! -d "$installation_target" ]]; then
	  if [[ "$os" == "macos" ]]; then
		"$installation_script" -y --install_dir="$installation_target"
	  elif [[ "$os" == "linux_gcc" ]]; then
		bash "$installation_script" --accept --save-packages-to "$installation_target"
		pushd "$installation_target"
		tar -xvf "armpl_${ARMPL_VERSION}_gcc.deb"
		tar -xvf "data.tar.gz"
		rm ./*.deb ./*.tar.gz
		popd >/dev/null
	  else
		abort "Unsupported OS $os"
	  fi
	fi
}

function get_expected_installation_script() {
  local os="$1"
  if [[ "$os" == "macos" ]]; then
	echo "$CACHE_DIR/$os/armpl_${ARMPL_VERSION}_flang-${FLANG_VERSION}_installer/armpl_${ARMPL_VERSION}_flang-${FLANG_VERSION}_install.sh"
  elif [[ "$os" == "linux_gcc" ]]; then
	echo "$CACHE_DIR/$os/arm-performance-libraries_${ARMPL_VERSION}_deb/arm-performance-libraries_${ARMPL_VERSION}_deb.sh"
  else
	abort "Unsupported OS $os"
  fi
}

function get_download_url() {
  local os="$1"
  if [[ "$os" == "macos" ]]; then
	  echo "https://developer.arm.com/-/cdn-downloads/permalink/Arm-Performance-Libraries/Version_$ARMPL_VERSION/arm-performance-libraries_${ARMPL_VERSION}_macOS.tgz"
	elif [[ "$os" == "linux_gcc" ]]; then
	  echo "https://developer.arm.com/-/cdn-downloads/permalink/Arm-Performance-Libraries/Version_$ARMPL_VERSION/arm-performance-libraries_${ARMPL_VERSION}_deb_gcc.tar"
  else
	abort "Unsupported OS $os"
  fi
}

function extract_archive() {
  local path="$1"
  local os="$2"
  local target_dir="$CACHE_DIR/$os"
  mkdir -p "$target_dir"
  if [[ "$path" == *.tar ]] || [[ "$path" == *.tgz ]]; then
    tar -xvf "$path" -C "$target_dir"
  elif [[ "$path" == *.dmg ]]; then
	_7z x "$path" -o"$target_dir"
  else
    abort "Unsupported archive format for $path"
  fi
}


function download() {
  local url="$1"
  local file_name
  file_name="$(basename "$url")"
  local target_path="$CACHE_DIR/$file_name"
  if [[ ! -f "$target_path" ]]; then
    echo "Fetching $url" >/dev/stderr
	curl -sSL "$url" --output "$target_path"
  fi
  echo "$target_path"
}


main "$@"
