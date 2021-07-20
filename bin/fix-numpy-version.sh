#!/usr/bin/env bash
set -euo pipefail

name=$(python setup.py --fullname)
minimum_supported_python="$(cat LOWEST_SUPPORTED_PYTHON_VERSION.txt)"
minimum_supported_numpy=$(python bin/find_lowest_supported_numpy.py "$minimum_supported_python")

# Update pyproject.toml
sed -i -E "s/\"numpy==(.*)\",/\"numpy>=$minimum_supported_numpy\",/g" "pyproject.toml"
mv "dist/${name}.tar.gz" wheelhouse
