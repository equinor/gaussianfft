#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"

# Remove all, but the oldest supported version of boost
# add that version to a file, which is read by `find_boost_version.py`

readonly boost_version="$(ls "$ROOT_DIR/sources/boost/" | sort -h | head -1)"

shopt -s extglob
cd "$ROOT_DIR/sources/boost"
rm -rf !("$boost_version")
cd - >/dev/null

echo "$boost_version" > "$ROOT_DIR/USE_BOOST_VERSION.txt"
