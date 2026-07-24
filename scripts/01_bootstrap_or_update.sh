#!/usr/bin/env bash
set -Eeuo pipefail

KIT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PROJECT_ROOT=${PROJECT_ROOT:-/mnt/space/adev/projects/active/omrpr-analysis}
DATA_ROOT=${DATA_ROOT:-/mnt/space/adev/datasets/omrpr}
RUNTIME_ROOT=${RUNTIME_ROOT:-$HOME/Projects-runtime/research/omrpr-analysis}
ENV_ROOT="$RUNTIME_ROOT/.venv"
BACKUP_BASE=${BACKUP_BASE:-/mnt/space/adev/backups/omrpr-analysis/upgrades}
PYTHON_VERSION=${PYTHON_VERSION:-3.12.13}
RECREATE_ENV=0
MAKE_COMMIT=0

usage() {
  cat <<'USAGE'
Usage: scripts/01_bootstrap_or_update.sh [options]
  --project-root PATH
  --data-root PATH
  --runtime-root PATH
  --backup-base PATH
  --recreate-env
  --commit
USAGE
}

while (($#)); do
  case "$1" in
    --project-root) PROJECT_ROOT=$2; shift 2 ;;
    --data-root) DATA_ROOT=$2; shift 2 ;;
    --runtime-root) RUNTIME_ROOT=$2; ENV_ROOT="$2/.venv"; shift 2 ;;
    --backup-base) BACKUP_BASE=$2; shift 2 ;;
    --recreate-env) RECREATE_ENV=1; shift ;;
    --commit) MAKE_COMMIT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 2 ;;
  esac
done

STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="$BACKUP_BASE/$STAMP"
mkdir -p "$BACKUP_ROOT" "$PROJECT_ROOT" "$DATA_ROOT" "$RUNTIME_ROOT"

backup_existing_project() {
  [[ -d "$PROJECT_ROOT" ]] || return 0
  echo "Backing up existing project to $BACKUP_ROOT"
  if [[ -d "$PROJECT_ROOT/.git" ]]; then
    git -C "$PROJECT_ROOT" bundle create "$BACKUP_ROOT/omrpr-analysis.bundle" --all || true
  fi
  tar \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='data/raw/source' \
    --exclude='data/interim/source' \
    --exclude='data/processed/source' \
    --exclude='data/metadata/source' \
    --exclude='__pycache__' \
    --exclude='.ruff_cache' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    -czf "$BACKUP_ROOT/omrpr-analysis-source.tar.gz" \
    -C "$(dirname "$PROJECT_ROOT")" "$(basename "$PROJECT_ROOT")"
  sha256sum "$BACKUP_ROOT"/* > "$BACKUP_ROOT/SHA256SUMS" 2>/dev/null || true
}

replace_tree() {
  local rel=$1
  local src="$KIT_ROOT/$rel"
  local dst="$PROJECT_ROOT/$rel"
  [[ -e "$src" ]] || return 0
  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
}

backup_existing_project

# Template-controlled trees are replaced to prevent stale scripts and stubs.
for rel in \
  src/omrpr_analysis \
  scripts \
  tests \
  docs/steps \
  templates \
  environment/bootstrap; do
  replace_tree "$rel"
done

# Controlled top-level files and reviewed configs are updated in place.
for rel in \
  AGENTS.md LEGACY_ANALYSIS_REPORT.md LICENSE-DECISION.md \
  README.md README_FIRST.md START_HERE.md CURRENT_STATE.md CHANGELOG.md \
  MASTER_MANIFEST.md Makefile pyproject.toml uv.lock .python-version \
  .gitignore .pre-commit-config.yaml \
  configs/project.yaml configs/conditions.csv configs/calibration-target.yaml \
  configs/analysis-sets.yaml \
  docs/PROJECT_STRUCTURE.md docs/DATA_PLACEMENT.md docs/INSTALL_OR_UPDATE.md \
  docs/MASTER_EXECUTION_ROADMAP.md docs/SUBMISSION_READINESS_CHECKLIST.md; do
  [[ -e "$KIT_ROOT/$rel" ]] || continue
  mkdir -p "$(dirname "$PROJECT_ROOT/$rel")"
  cp -a "$KIT_ROOT/$rel" "$PROJECT_ROOT/$rel"
done

# User-controlled and durable project directories are created but never erased.
mkdir -p \
  "$PROJECT_ROOT/configs/local" "$PROJECT_ROOT/configs/datasets" \
  "$PROJECT_ROOT/configs/experiments" "$PROJECT_ROOT/configs/figures" \
  "$PROJECT_ROOT/data/raw" "$PROJECT_ROOT/data/interim" \
  "$PROJECT_ROOT/data/processed" "$PROJECT_ROOT/data/metadata" \
  "$PROJECT_ROOT/docs/architecture" "$PROJECT_ROOT/docs/data-dictionary" \
  "$PROJECT_ROOT/docs/decisions" "$PROJECT_ROOT/docs/experiments" \
  "$PROJECT_ROOT/docs/methods" "$PROJECT_ROOT/docs/validation" \
  "$PROJECT_ROOT/environment/system-baseline" \
  "$PROJECT_ROOT/outputs/reports" "$PROJECT_ROOT/outputs/figures" \
  "$PROJECT_ROOT/outputs/tables" "$PROJECT_ROOT/outputs/logs" \
  "$PROJECT_ROOT/outputs/diagnostics" "$PROJECT_ROOT/manuscript/drafts" \
  "$PROJECT_ROOT/manuscript/generated/figures" \
  "$PROJECT_ROOT/manuscript/generated/tables" \
  "$PROJECT_ROOT/manuscript/generated/results" \
  "$PROJECT_ROOT/manuscript/submission" "$PROJECT_ROOT/state/gates" \
  "$PROJECT_ROOT/src/matlab" "$PROJECT_ROOT/notebooks/python" \
  "$PROJECT_ROOT/notebooks/matlab" "$PROJECT_ROOT/tests/integration" \
  "$PROJECT_ROOT/tests/scientific"

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
      echo "Preserved conflicting path as ${link}.prelink.${STAMP}"
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

if (( RECREATE_ENV )); then
  rm -rf "$ENV_ROOT"
fi
mkdir -p "$RUNTIME_ROOT"

export OMRPR_PROJECT_ROOT="$PROJECT_ROOT"
export OMRPR_DATA_ROOT="$DATA_ROOT"
export UV_PROJECT_ENVIRONMENT="$ENV_ROOT"
export UV_LINK_MODE=copy
cd "$PROJECT_ROOT"

uv python install "$PYTHON_VERSION"
printf '%s\n' "$PYTHON_VERSION" > .python-version

if [[ -f uv.lock ]]; then
  uv sync --python "$PYTHON_VERSION" --all-groups --locked
else
  echo "No lockfile found; creating initial reviewed lockfile."
  uv lock --python "$PYTHON_VERSION"
  uv sync --python "$PYTHON_VERSION" --all-groups --locked
fi

uv run pre-commit install
chmod 755 .git/hooks/pre-commit 2>/dev/null || true
uv run ruff format .
uv run ruff check . --fix
uv run ruff format --check .
uv run ruff check .
uv run mypy src/omrpr_analysis
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest --cov=omrpr_analysis
uv run omrpr doctor
bash scripts/06_project_readiness.sh
uv run python scripts/write_environment_report.py

if (( MAKE_COMMIT )); then
  git add .
  uv run pre-commit run --all-files
  git add .
  if ! git diff --cached --quiet; then
    git commit -m "chore: install or update OMRPR Mastery baseline v3"
  fi
fi

echo "Project ready: $PROJECT_ROOT"
echo "Data preserved at: $DATA_ROOT"
echo "Runtime environment: $ENV_ROOT"
echo "Upgrade backup: $BACKUP_ROOT"
