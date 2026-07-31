#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
STAMP=$(date +%Y%m%d_%H%M%S)
DEST=${BACKUP_DEST:-/mnt/space/adev/backups/omrpr-analysis/releases/$STAMP}
mkdir -p "$DEST"

if [[ -d "$ROOT/.git" ]]; then
  git -C "$ROOT" bundle create "$DEST/omrpr-analysis.bundle" --all
fi

tar \
  --exclude='.git' --exclude='.venv' \
  --exclude='data/raw/source' --exclude='data/interim/source' \
  --exclude='data/processed/source' --exclude='data/metadata/source' \
  --exclude='__pycache__' --exclude='.ruff_cache' --exclude='.pytest_cache' \
  --exclude='*.pyc' \
  -czf "$DEST/omrpr-analysis-source.tar.gz" \
  -C "$(dirname "$ROOT")" "$(basename "$ROOT")"

sha256sum "$DEST"/* > "$DEST/SHA256SUMS"
echo "Backup created: $DEST"
