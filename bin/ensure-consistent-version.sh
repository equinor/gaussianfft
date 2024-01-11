#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"
readonly ARTIFACT_DIR="$ROOT_DIR/dist"

readonly PYTHON="${PYTHON:-python3}"

function abort() {
  echo "$1" >/dev/stderr
  exit 1
}

if [[ ! -d "$ARTIFACT_DIR" ]]; then
  abort "No distribution folder exists"
fi

if [[ ! -d "$ROOT_DIR/venv" ]]; then
  echo "Creating a virtual environment"
  "$PYTHON" -m venv "$ROOT_DIR/venv"
fi
source "$ROOT_DIR/venv/bin/activate"

function install_dependency() {
  echo "-- installing $1"
  python -m pip install --upgrade "$1" >/dev/null
}

if [[ ! $(python -c 'import setuptools_scm' 2>/dev/null) ]]; then
  install_dependency 'setuptools>=64'
  install_dependency setuptools-scm
fi

# Expected version tag
readonly version="$(python -m setuptools_scm)"

echo "Expected version is $version"

# There should be one, and only one source distribution artifact
if [[ ! -f "$ARTIFACT_DIR/gaussianfft-${version}.tar.gz" ]]; then
  abort "Missing source distribution"
fi
readonly num_source_distributions="$(find "$ARTIFACT_DIR" -name "gaussianfft-*.tar.gz" | wc -l)"
if [[ $num_source_distributions != 1 ]]; then
  abort "There are more than one source distribution"
fi

# Count the number of artifacts with that version
readonly expected_num_artifacts="$(find "$ARTIFACT_DIR" -name "gaussianfft-${version}-*.whl" -type f | wc -l)"

readonly actual_num_artifacts="$(find "$ARTIFACT_DIR" -name "gaussianfft-*.whl" -type f | wc -l)"
if [[ "$expected_num_artifacts" != "$actual_num_artifacts" ]]; then
  abort "There are some artifacts that does not have the correct version"
fi

readonly expected_total_num_artifacts=$((num_source_distributions + expected_num_artifacts))
readonly actual_total_num_artifacts=$(find "$ARTIFACT_DIR" -mindepth 1 | wc -l)

if [[ $expected_total_num_artifacts != "$actual_total_num_artifacts" ]]; then
  abort "There are some files that are not part of the distribution"
fi

echo "Artifacts have consistent names"
