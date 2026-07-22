#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/mnt/space/adev/projects/active/omrpr-analysis}"
DATA_ROOT="${DATA_ROOT:-/mnt/space/adev/datasets/omrpr}"

printf 'OMRPR clean-room preflight\n'
printf 'Project root: %s\nData root: %s\n' "$PROJECT_ROOT" "$DATA_ROOT"

for cmd in bash git rsync find sha256sum; do
  command -v "$cmd" >/dev/null || { echo "MISSING: $cmd"; exit 1; }
done

if command -v uv >/dev/null; then
  uv --version
else
  echo 'MISSING: uv. Install with the official Astral installer before continuing.'
  exit 1
fi

for path in "$PROJECT_ROOT" "$DATA_ROOT"; do
  if [[ -e "$path" ]]; then
    printf 'EXISTS: %s\n' "$path"
  else
    printf 'WILL CREATE: %s\n' "$path"
  fi
done

if [[ -d "$DATA_ROOT" ]]; then
  printf 'Existing bags: '
  find "$DATA_ROOT" -type f -iname '*.bag' | wc -l
fi

echo 'Preflight passed.'
