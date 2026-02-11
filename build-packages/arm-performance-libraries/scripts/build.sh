#!/usr/bin/env bash
set -euo pipefail

source "$(dirname -- "$0")/common.sh"

if ! has uv; then
  abort "I require 'uv' to be installed in order to build the necessary wheels."
fi

function main() {
  "$ROOT_DIR/scripts/fetch.sh"

  for os in "${TARGET_PLATFORMS[@]}"; do
	"$ROOT_DIR/scripts/prepare.sh" "$os"
	uv build --wheel
  done
}

main "$@"
