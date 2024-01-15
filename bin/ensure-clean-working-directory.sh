#!/usr/bin/env bash
set -euo pipefail

readonly ROOT_DIR="$(cd "$(dirname -- "$0")/.." >/dev/null; pwd -P)"

CHANGED_FILES=$(git -C "$ROOT_DIR" status --untracked-files=no --porcelain | wc -l)

if [[ "$CHANGED_FILES" -eq 0 ]]; then
  echo "Clean working directory"
else
  echo "Changes detected" >/dev/stderr
  git status --untracked-files=no >/dev/stderr
  exit 1
fi
