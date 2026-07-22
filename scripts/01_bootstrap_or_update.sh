#!/usr/bin/env bash
set -Eeuo pipefail

KIT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PROJECT_ROOT=/mnt/space/adev/projects/active/omrpr-analysis
DATA_ROOT=/mnt/space/adev/datasets/omrpr
PYTHON_PRIMARY=3.14.6
PYTHON_FALLBACK=3.13.14
RECREATE_ENV=0
MAKE_COMMIT=0

usage() {
  cat <<'EOF'
Usage: scripts/01_bootstrap_or_update.sh [options]
  --project-root PATH
  --data-root PATH
  --recreate-env
  --commit
EOF
}

while (($#)); do
  case "$1" in
    --project-root) PROJECT_ROOT=$2; shift 2 ;;
    --data-root) DATA_ROOT=$2; shift 2 ;;
    --recreate-env) RECREATE_ENV=1; shift ;;
    --commit) MAKE_COMMIT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
done

STAMP=$(date +%Y%m%d_%H%M%S)
ENV_ROOT="$HOME/.venvs/omrpr-analysis"
BACKUP_ROOT="$HOME/OMRPR_PROJECT_UPGRADE_BACKUPS/$STAMP"
mkdir -p "$BACKUP_ROOT"

if [[ -d "$PROJECT_ROOT" ]]; then
  echo "Backing up existing project-controlled files to $BACKUP_ROOT"
  rsync -a \
    --exclude '.git/' --exclude '.venv/' --exclude 'data/' \
    --exclude 'outputs/' --exclude 'manuscript/generated/' \
    --exclude 'manuscript/submission/' --exclude 'state/gates/' \
    "$PROJECT_ROOT/" "$BACKUP_ROOT/"
fi

mkdir -p "$PROJECT_ROOT"

# Update template-controlled files while preserving research data, Git history,
# local gates, local settings, generated outputs, and manuscript drafts.
rsync -a \
  --exclude '.git/' --exclude '.venv/' --exclude 'data/' \
  --exclude 'outputs/' --exclude 'manuscript/generated/' \
  --exclude 'manuscript/submission/' --exclude 'manuscript/drafts/' \
  --exclude 'state/gates/' --exclude 'uv.lock' \
  "$KIT_ROOT/" "$PROJECT_ROOT/"

mkdir -p \
  "$PROJECT_ROOT/data/raw" "$PROJECT_ROOT/data/interim" \
  "$PROJECT_ROOT/data/processed" "$PROJECT_ROOT/data/metadata" \
  "$PROJECT_ROOT/outputs/reports" "$PROJECT_ROOT/outputs/figures" \
  "$PROJECT_ROOT/outputs/tables" "$PROJECT_ROOT/outputs/logs" \
  "$PROJECT_ROOT/outputs/diagnostics" "$PROJECT_ROOT/manuscript/drafts" \
  "$PROJECT_ROOT/manuscript/generated/figures" \
  "$PROJECT_ROOT/manuscript/generated/tables" \
  "$PROJECT_ROOT/manuscript/generated/results" \
  "$PROJECT_ROOT/manuscript/submission" "$PROJECT_ROOT/state/gates" \
  "$PROJECT_ROOT/src/matlab" "$PROJECT_ROOT/notebooks/python" \
  "$PROJECT_ROOT/notebooks/matlab"

mkdir -p \
  "$DATA_ROOT/raw/camera/rosbag/wtt-main" \
  "$DATA_ROOT/raw/camera/rosbag/static/cam1" \
  "$DATA_ROOT/raw/camera/rosbag/static/cam2" \
  "$DATA_ROOT/raw/camera/rosbag/static/cam3" \
  "$DATA_ROOT/raw/camera/rosbag/wtt-5sec" \
  "$DATA_ROOT/raw/camera/calibration-images/cam1" \
  "$DATA_ROOT/raw/camera/calibration-images/cam2" \
  "$DATA_ROOT/raw/camera/calibration-images/cam3" \
  "$DATA_ROOT/raw/laser/csv/tunnel-a-2024" \
  "$DATA_ROOT/raw/laser/csv/tunnel-b-2025-paper2-reference" \
  "$DATA_ROOT/raw/laser/spreadsheets" "$DATA_ROOT/raw/experiment-logs" \
  "$DATA_ROOT/interim/frame-extracts" "$DATA_ROOT/interim/bag-audit" \
  "$DATA_ROOT/interim/apriltag-detections" "$DATA_ROOT/interim/calibration" \
  "$DATA_ROOT/interim/multicamera-aligned" \
  "$DATA_ROOT/interim/condition-matched" \
  "$DATA_ROOT/processed/conditions" "$DATA_ROOT/processed/metrics" \
  "$DATA_ROOT/processed/manuscript" "$DATA_ROOT/metadata/inventories" \
  "$DATA_ROOT/metadata/checksums" "$DATA_ROOT/metadata/sessions" \
  "$DATA_ROOT/metadata/conditions"

ensure_link() {
  local target=$1 link=$2
  if [[ -L "$link" ]]; then
    ln -sfn "$target" "$link"
  elif [[ -e "$link" ]]; then
    if [[ -d "$link" ]] && [[ -z "$(find "$link" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
      rmdir "$link"
      ln -s "$target" "$link"
    else
      mv "$link" "${link}.prelink.${STAMP}"
      ln -s "$target" "$link"
      echo "Preserved former path as ${link}.prelink.${STAMP}"
    fi
  else
    ln -s "$target" "$link"
  fi
}

ensure_link "$DATA_ROOT/raw" "$PROJECT_ROOT/data/raw/source"
ensure_link "$DATA_ROOT/interim" "$PROJECT_ROOT/data/interim/source"
ensure_link "$DATA_ROOT/processed" "$PROJECT_ROOT/data/processed/source"
ensure_link "$DATA_ROOT/metadata" "$PROJECT_ROOT/data/metadata/source"

if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
  git -C "$PROJECT_ROOT" init -b main
fi

if ((RECREATE_ENV)); then
  rm -rf "$ENV_ROOT"
fi
mkdir -p "$(dirname "$ENV_ROOT")"

export UV_PROJECT_ENVIRONMENT="$ENV_ROOT"
export UV_LINK_MODE=copy
cd "$PROJECT_ROOT"

select_python() {
  local version=$1
  echo "Trying Python $version"
  uv python install "$version"
  if uv lock --upgrade --python "$version" && uv sync --all-groups --locked --python "$version"; then
    printf '%s\n' "$version" > .python-version
    return 0
  fi
  return 1
}

if ! select_python "$PYTHON_PRIMARY"; then
  echo "Latest Python dependency resolution failed; falling back to $PYTHON_FALLBACK"
  rm -rf "$ENV_ROOT"
  select_python "$PYTHON_FALLBACK"
fi

uv run pre-commit install
chmod 755 .git/hooks/pre-commit 2>/dev/null || true
uv run ruff format .
uv run ruff check . --fix
uv run ruff format --check .
uv run ruff check .
uv run mypy src/omrpr_analysis
uv run pytest
uv run omrpr doctor

if ((MAKE_COMMIT)); then
  git add .
  uv run pre-commit run --all-files
  git add .
  if ! git diff --cached --quiet; then
    git commit -m "chore: install or update OMRPR clean-room starter v2"
  fi
fi

echo "Project ready: $PROJECT_ROOT"
echo "Data preserved at: $DATA_ROOT"
echo "Upgrade backup: $BACKUP_ROOT"
