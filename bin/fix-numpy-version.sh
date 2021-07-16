#!/usr/bin/env bash
set -euo pipefail

name=$(python setup.py --fullname)
minimum_supported_numpy=$(python bin/find_lowest_supported_numpy.py "$MINIMUM_SUPPORTED_PYTHON")

cd wheelhouse
# Extract content
tar -xvf "${name}.tar.gz"
rm -f "${name}.tar.gz"

sed -i -E "s/\"numpy==(.*)\",/\"numpy>=$minimum_supported_numpy\",/g" "${name}/pyproject.toml"
tar -cvzf "${name}.tar.gz" "$name"
rm -rf "$name"
