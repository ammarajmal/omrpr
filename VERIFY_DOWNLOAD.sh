#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
ARCHIVE="${1:-OMRPR_Automation_Master_v1.0.1.tar.gz}"
CHECKSUM="${2:-${ARCHIVE}.sha256}"

cd "$SCRIPT_DIR"
[[ -f "$ARCHIVE" ]] || { echo "ERROR: Missing archive: $ARCHIVE" >&2; exit 2; }
[[ -f "$CHECKSUM" ]] || { echo "ERROR: Missing checksum: $CHECKSUM" >&2; exit 2; }

expected="$(awk 'NR == 1 {print $1}' "$CHECKSUM")"
actual="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
[[ "$expected" =~ ^[0-9a-fA-F]{64}$ ]] || {
  echo "ERROR: Invalid checksum file: $CHECKSUM" >&2
  exit 2
}

if [[ "$expected" != "$actual" ]]; then
  echo "FAIL: checksum mismatch" >&2
  echo "Expected: $expected" >&2
  echo "Actual:   $actual" >&2
  exit 1
fi

echo "PASS: $ARCHIVE checksum is valid."
