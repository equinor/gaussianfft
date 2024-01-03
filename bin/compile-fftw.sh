#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR=$(realpath "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)/..")

readonly FFTW_VERSION="${FFTW_VERSION:-$1}"
readonly FFTW_DIR="$ROOT_DIR/sources/fftw/$FFTW_VERSION"

if [[ ! -d "$FFTW_DIR" ]]; then
  "$ROOT_DIR/bin/fetch-fftw.sh" "$FFTW_VERSION"
fi
cd "$FFTW_DIR"

 # TODO: Cache
 # TODO: Works with make; make it work with cmake
 # For the time being, compiling it with cmake and single / float results in a binary
 # without _fftwf_ symbols...
 # https://github.com/FFTW/fftw3/issues/237

#CMAKE=${CMAKE:-cmake}
function compile() {
  #"$CMAKE" -S . -B build \
  #    -DBUILD_SHARED_LIBS=OFF \
  #    -DBUILD_TESTS=OFF \
  #    -DCFLAGS="-m64" \
  #    -DCMAKE_INSTALL_PREFIX="$ROOT_DIR/vendor"
  #"$CMAKE" --build build
  #"$CMAKE" --install build
  local precision="${1:-double}"
  declare -a args=()
  case $precision in
  double)
    # Nothing to do
    ;;
  single|float)
      args+=(--enable-single)
      args+=(--enable-neon)
    ;;
  esac

  ./configure \
    --prefix="$ROOT_DIR/vendor" \
    --enable-threads \
    "${args[@]:-}"
  make
  make install

  make clean
}

compile

compile float
