#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"
readonly ROOT_DIR
export ROOT_DIR

function abort() {
  echo "$1" >/dev/stderr
  exit 1
}

function has() {
  command -v "$1" >/dev/null 2>&1
}

declare -a TARGET_PLATFORMS=(
	"macos"
	"linux_gcc"
)
  export TARGET_PLATFORMS
# Download necessary files
readonly ARMPL_VERSION="26.01"
export ARMPL_VERSION
readonly FLANG_VERSION=21
export FLANG_VERSION

readonly CACHE_DIR="$ROOT_DIR/.cache"
export CACHE_DIR
