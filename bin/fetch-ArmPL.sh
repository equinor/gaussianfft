#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"

function abort() {
  echo "$1" >/dev/stderr
  exit 1
}
# Download necessary files
ARMPL_VERSION="${ARMPL_VERSION:-${1-}}"

if [[ -z $ARMPL_VERSION || "$ARMPL_VERSION" == 'OFF' ]]; then
  abort "No version of RMS Performance Libraries given"
fi

readonly OS="$(uname -o)"
readonly ARCH="$(uname -m)"

if [[ $ARCH != 'arm64' && $ARCH != 'aarch64' ]]; then
  abort "Can't use ARM libraries on a non-ARM architecture ($ARCH)"
fi

readonly ARMPL_DIR="$ROOT_DIR/sources/arm-performance-libraries"
ARMPL_SOURCES="$ARMPL_DIR/$ARMPL_VERSION"
mkdir -p "$ARMPL_DIR"


if [[ $OS == "Darwin" ]]; then
  ARMPL_SOURCES="$ARMPL_SOURCES/macOS"
  readonly ARMPL_ARCHIVE="$ARMPL_DIR/${ARMPL_VERSION}_macOS.dmg"
  if [[ ! -f "$ARMPL_ARCHIVE" ]]; then
    URL="https://developer.arm.com/-/media/Files/downloads/hpc/arm-performance-libraries/$(echo "$ARMPL_VERSION" | tr '.' '-')/macos/arm-performance-libraries_${ARMPL_VERSION}_macOS.dmg"
    echo "Downloading Arm Performance Libraries from '$URL'"
    curl -sSL "$URL" --output "$ARMPL_ARCHIVE"
  fi

  if [[ ! -d "$ARMPL_SOURCES" ]]; then
    mkdir -p "$ARMPL_SOURCES"
    VOLUME="/Volumes/armpl_${ARMPL_VERSION}_flang-new_clang_17_installer"

    if [[ ! -d $VOLUME ]]; then
      hdiutil attach "$ARMPL_ARCHIVE"
    fi

    # Install the libraries
    "$VOLUME/armpl_${ARMPL_VERSION}_flang-new_clang_17_install.sh" \
        --install_dir="$ARMPL_SOURCES" \
        -y
    diskutil unmount "$VOLUME"

    readonly install_dir=$(find "$ARMPL_SOURCES" -name "armpl_${ARMPL_VERSION}*" -type d)
    if [[ -z $install_dir ]]; then
      abort "Could not find installation directory"
    fi
    mv "$install_dir/"* "$ARMPL_SOURCES"
    rmdir "$install_dir"
  fi

else
  abort "Unsupported OS $OS"
fi

# Remove necessary files
rm -rf \
  "$ARMPL_SOURCES/arm-performance-libraries"* \
  "$ARMPL_SOURCES/examples"* \
  "$ARMPL_SOURCES/src"* \
  "$ARMPL_SOURCES/armpl_env_vars.sh" \
  "$ARMPL_SOURCES/CHANGELOG" \
  "$ARMPL_SOURCES/README"
# We don't use the shared libraries
rm -f \
  "$ARMPL_SOURCES"/lib/*.dylib* \
  "$ARMPL_SOURCES"/lib/*.so*
