#!/usr/bin/env bash
set -euo pipefail

minimum_supported_python="$(cat LOWEST_SUPPORTED_PYTHON_VERSION.txt)"
minimum_supported_numpy=$(python bin/find_lowest_supported_numpy.py "$minimum_supported_python")

# Update pyproject.toml, and setup.py
sed -i '' -E "s/\"numpy==(.*)\",/\"numpy>=$minimum_supported_numpy\",/g" "pyproject.toml"
sed -i '' -E "s/\"<NUMPY_VERSION>\",/\"$minimum_supported_numpy\",/g" "setup.py"
