#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR=$(realpath "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)/..")

readonly FFTW_VERSION="${FFTW_VERSION:-$1}"
readonly FFTW_DIR="$ROOT_DIR/sources/fftw/$FFTW_VERSION"
readonly FFTW_ARCHIVE="$FFTW_DIR.tar.gz"


mkdir -p "$ROOT_DIR/sources/fftw"
if [[ ! -f "$FFTW_ARCHIVE" ]]; then
  curl -L --output "$FFTW_ARCHIVE" \
    "https://fftw.org/fftw-$FFTW_VERSION.tar.gz"
fi

if [[ ! -d "$FFTW_DIR" ]]; then
  mkdir -p "$FFTW_DIR"
  tar -xvf "$FFTW_ARCHIVE" -C "$FFTW_DIR" --strip-components=1
fi
