#!/usr/bin/env bash
# Build and run NRLib C++ unit tests.

set -euo pipefail

build_dir="build-cpp-tests"
jobs="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)"

mkdir -p "$build_dir"
cd "$build_dir"

cmake ../tests/cpp -DCMAKE_BUILD_TYPE=Debug
cmake --build . -j"$jobs"

ctest --output-on-failure
