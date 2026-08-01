#!/usr/bin/env bash
set -Eeuo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="${OMRPR_PROJECT_ROOT:-/mnt/space/adev/projects/active/omrpr-analysis}"
VENV_DIR="${OMRPR_VENV:-/home/ammar/Projects-runtime/research/omrpr-analysis/.venv}"
EXPECTED_BAGS="${OMRPR_EXPECTED_BAGS:-62}"
EXPECTED_WTT_MAIN="${OMRPR_EXPECTED_WTT_MAIN:-21}"
EXPECTED_WTT_5SEC="${OMRPR_EXPECTED_WTT_5SEC:-21}"
EXPECTED_STATIC="${OMRPR_EXPECTED_STATIC:-20}"
GAP_THRESHOLD_S="${OMRPR_GAP_THRESHOLD_S:-0.025}"
MODE="full"
ORIGINAL_ARGS=("$@")

usage() {
  sed -n '/^## Run the complete audit/,/^## Output layout/p' "$PACKAGE_DIR/README.md"
}

while (($#)); do
  case "$1" in
    --preflight-only) MODE="preflight" ;;
    --reuse-audit) MODE="reuse" ;;
    --help|-h) usage; exit 0 ;;
    *) echo "ERROR: Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "ERROR: Project root does not exist: $PROJECT_ROOT" >&2
  exit 3
fi

RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_ROOT="$PROJECT_ROOT/outputs/audit-runs"
RUN_DIR="$RUN_ROOT/$RUN_ID"
LOG_DIR="$RUN_DIR/logs"
REPORT_DIR="$RUN_DIR/reports"
PROVENANCE_DIR="$RUN_DIR/provenance"
SCRIPTS_DIR="$RUN_DIR/scripts_used"

mkdir -p "$LOG_DIR" "$REPORT_DIR" "$PROVENANCE_DIR" "$SCRIPTS_DIR"
printf 'RUNNING\n' > "$RUN_DIR/RUN_STATUS.txt"

exec > >(tee -a "$LOG_DIR/run.log") 2>&1

on_error() {
  local code=$?
  printf 'FAILED (exit %s)\n' "$code" > "$RUN_DIR/RUN_STATUS.txt"
  echo
  echo "FAILED: retained diagnostic run at $RUN_DIR"
  exit "$code"
}
trap on_error ERR

echo "OMRPR Step 00 audit run: $RUN_ID"
echo "Project: $PROJECT_ROOT"
echo "Package: $PACKAGE_DIR"
echo "Mode: $MODE"
echo

cp -a "$PACKAGE_DIR/." "$SCRIPTS_DIR/"
find "$SCRIPTS_DIR" -type f -print0 \
  | sort -z \
  | xargs -0 sha256sum > "$PROVENANCE_DIR/package_manifest.sha256"

{
  printf 'Invocation:'
  printf ' %q' "$0" "${ORIGINAL_ARGS[@]}"
  printf '\n'
  printf 'Run ID: %s\n' "$RUN_ID"
  printf 'Started: %s\n' "$(date --iso-8601=seconds)"
  printf 'Project root: %s\n' "$PROJECT_ROOT"
  printf 'Virtual environment: %s\n' "$VENV_DIR"
  printf 'Expected bags: %s\n' "$EXPECTED_BAGS"
  printf 'Gap threshold seconds: %s\n' "$GAP_THRESHOLD_S"
} > "$PROVENANCE_DIR/command.txt"

if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
  echo "ERROR: Missing environment activation script: $VENV_DIR/bin/activate"
  exit 3
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
export UV_LINK_MODE=copy

if [[ "${VIRTUAL_ENV:-}" != "$VENV_DIR" ]]; then
  echo "ERROR: Wrong environment active: ${VIRTUAL_ENV:-unset}"
  exit 3
fi

cd "$PROJECT_ROOT"

{
  printf 'Captured: %s\n' "$(date --iso-8601=seconds)"
  printf 'Host: '; hostname
  printf 'Kernel: '; uname -srmo
  printf 'Python: '; python --version
  printf 'Python executable: '; command -v python
  printf 'uv: '; uv --version
  printf 'OMRPR CLI: '; "$VENV_DIR/bin/omrpr" version 2>&1 || true
  printf '\nDisk:\n'; df -Th "$PROJECT_ROOT" "$VENV_DIR" 2>&1 || true
  printf '\nInstalled project packages:\n'
  python -m pip freeze 2>/dev/null || uv pip freeze --active 2>/dev/null || true
} > "$PROVENANCE_DIR/environment.txt"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  {
    git rev-parse HEAD
    git describe --tags --always --dirty
    git status --short
  } > "$PROVENANCE_DIR/git_status.txt"
else
  printf 'Not a Git worktree\n' > "$PROVENANCE_DIR/git_status.txt"
fi

export OMRPR_PROJECT_ROOT="$PROJECT_ROOT"
export OMRPR_VENV="$VENV_DIR"
export OMRPR_EXPECTED_BAGS="$EXPECTED_BAGS"
export OMRPR_EXPECTED_WTT_MAIN="$EXPECTED_WTT_MAIN"
export OMRPR_EXPECTED_WTT_5SEC="$EXPECTED_WTT_5SEC"
export OMRPR_EXPECTED_STATIC="$EXPECTED_STATIC"
export OMRPR_GAP_THRESHOLD_S="$GAP_THRESHOLD_S"
export OMRPR_RUN_DIR="$RUN_DIR"

bash "$PACKAGE_DIR/scripts/01_preflight.sh"

if [[ "$MODE" == "preflight" ]]; then
  printf 'SUCCESS (preflight only)\n' > "$RUN_DIR/RUN_STATUS.txt"
  echo "Preflight completed successfully."
  echo "Run record: $RUN_DIR"
  exit 0
fi

bash "$PACKAGE_DIR/scripts/02_run_audit.sh" "$MODE"
python "$PACKAGE_DIR/scripts/03_summarize_audit.py"
python "$PACKAGE_DIR/scripts/04_static_gap_diagnostics.py"
python "$PACKAGE_DIR/scripts/05_static_acceptance.py"
python "$PACKAGE_DIR/scripts/06_generate_report.py"

(
  cd "$REPORT_DIR"
  find . -type f ! -name output_manifest.sha256 -print0 \
    | sort -z \
    | xargs -0 sha256sum > output_manifest.sha256
)

printf 'SUCCESS\n' > "$RUN_DIR/RUN_STATUS.txt"
printf 'Completed: %s\n' "$(date --iso-8601=seconds)" \
  >> "$PROVENANCE_DIR/command.txt"

mkdir -p "$RUN_ROOT"
if ln -sfn "$RUN_ID" "$RUN_ROOT/latest" 2>/dev/null; then
  :
else
  printf '%s\n' "$RUN_DIR" > "$RUN_ROOT/LATEST_RUN.txt"
fi

trap - ERR
echo
echo "SUCCESS"
echo "Report: $REPORT_DIR/STEP00_AUDIT_REPORT.md"
echo "Run directory: $RUN_DIR"
