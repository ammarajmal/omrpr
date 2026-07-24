#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/mnt/space/adev/projects/active/omrpr-analysis}"
DATA_ROOT="${DATA_ROOT:-/mnt/space/adev/datasets/omrpr}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$HOME/Projects-runtime/research/omrpr-analysis}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12.13}"

pass=0 warn=0 fail=0
ok(){ echo "PASS: $*"; pass=$((pass+1)); }
warnf(){ echo "WARN: $*"; warn=$((warn+1)); }
bad(){ echo "FAIL: $*"; fail=$((fail+1)); }

printf 'OMRPR Mastery-aligned preflight\n'
printf 'Project root: %s\nData root: %s\nRuntime root: %s\n' "$PROJECT_ROOT" "$DATA_ROOT" "$RUNTIME_ROOT"

for cmd in bash git rsync find sha256sum tar; do
  if command -v "$cmd" >/dev/null; then ok "$cmd available"; else bad "$cmd missing"; fi
done
if command -v uv >/dev/null; then ok "$(uv --version)"; else bad "uv missing"; fi

for path in "$PROJECT_ROOT" "$DATA_ROOT" "$RUNTIME_ROOT"; do
  [[ -e "$path" ]] && ok "exists: $path" || warnf "will create: $path"
done

if [[ -e /mnt/space ]]; then
  findmnt -T /mnt/space -o TARGET,SOURCE,FSTYPE,OPTIONS || true
  ok "/mnt/space mounted"
else
  bad "/mnt/space missing"
fi

if [[ -d "$DATA_ROOT" ]]; then
  bags=$(find "$DATA_ROOT" -type f -iname '*.bag' | wc -l)
  echo "INFO: existing bags=$bags"
fi

echo "SUMMARY: PASS=$pass WARN=$warn FAIL=$fail"
(( fail == 0 ))
