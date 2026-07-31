#!/usr/bin/env bash
set -Eeuo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="${OMRPR_PROJECT_ROOT:-/mnt/space/adev/projects/active/omrpr-analysis}"
VENV_DIR="${OMRPR_VENV:-/home/ammar/Projects-runtime/research/omrpr-analysis/.venv}"
BAG_ROOT="${OMRPR_BAG_ROOT:-$PROJECT_ROOT/data/raw/source/camera/rosbag}"
SAMPLES="${OMRPR_SAMPLES_PER_STREAM:-12}"
MODE="full"

# Keep this Python 3.12 project isolated from pytest plugins exposed by ROS 2
# Lyrical's Python 3.14 installation.
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

while (($#)); do
  case "$1" in
    --preflight-only) MODE="preflight" ;;
    --samples-per-stream)
      shift
      SAMPLES="${1:?missing value for --samples-per-stream}"
      ;;
    --help|-h)
      sed -n '/^## Run Step 01/,/^## Output layout/p' "$PACKAGE_DIR/README.md"
      exit 0
      ;;
    *) echo "ERROR: Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

RUN_ID="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$PROJECT_ROOT/outputs/image-audit-runs/$RUN_ID"
mkdir -p "$RUN_DIR"/{logs,provenance,reports,scripts_used}
printf 'RUNNING\n' > "$RUN_DIR/RUN_STATUS.txt"
exec > >(tee -a "$RUN_DIR/logs/run.log") 2>&1

on_error() {
  local code=$?
  printf 'FAILED (exit %s)\n' "$code" > "$RUN_DIR/RUN_STATUS.txt"
  echo "FAILED: diagnostics retained at $RUN_DIR"
  exit "$code"
}
trap on_error ERR

[[ -d "$PROJECT_ROOT" ]] || { echo "ERROR: Missing project: $PROJECT_ROOT"; exit 3; }
[[ -d "$BAG_ROOT" ]] || { echo "ERROR: Missing bag root: $BAG_ROOT"; exit 3; }
if [[ ! -f "$VENV_DIR/bin/activate" && -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
  VENV_DIR="$PROJECT_ROOT/.venv"
fi
[[ -f "$VENV_DIR/bin/activate" ]] || {
  echo "ERROR: Missing environment. Checked:"
  echo "  $VENV_DIR"
  echo "  $PROJECT_ROOT/.venv"
  exit 3
}
[[ "$SAMPLES" =~ ^[1-9][0-9]*$ ]] || { echo "ERROR: samples must be positive"; exit 2; }

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
cd "$PROJECT_ROOT"
python -c 'import cv2, matplotlib, numpy, PIL, rosbags'

bag_count="$(find "$BAG_ROOT" -type f -name '*.bag' | wc -l)"
printf 'Bags discovered: %s\n' "$bag_count"
[[ "$bag_count" -eq 62 ]] || { echo "ERROR: Expected 62 bags"; exit 3; }

cp -a "$PACKAGE_DIR/." "$RUN_DIR/scripts_used/"
{
  printf 'Run ID: %s\n' "$RUN_ID"
  printf 'Started: %s\n' "$(date --iso-8601=seconds)"
  printf 'Project: %s\nBag root: %s\nSamples/stream: %s\n' \
    "$PROJECT_ROOT" "$BAG_ROOT" "$SAMPLES"
  printf 'Python: %s\n' "$(command -v python)"
  python --version
} > "$RUN_DIR/provenance/run.txt"
find "$RUN_DIR/scripts_used" -type f -print0 | sort -z | xargs -0 sha256sum \
  > "$RUN_DIR/provenance/package_manifest.sha256"

if [[ "$MODE" == "preflight" ]]; then
  printf 'SUCCESS (preflight only)\n' > "$RUN_DIR/RUN_STATUS.txt"
  trap - ERR
  echo "Preflight successful: $RUN_DIR"
  exit 0
fi

python scripts/steps/step01_image_decode_sampling_audit.py \
  --root "$BAG_ROOT" \
  --output "$RUN_DIR/reports" \
  --samples-per-stream "$SAMPLES"

python "$PACKAGE_DIR/scripts/generate_report.py" "$RUN_DIR/reports"
(
  cd "$RUN_DIR/reports"
  find . -type f ! -name output_manifest.sha256 -print0 \
    | sort -z | xargs -0 sha256sum > output_manifest.sha256
)
printf 'SUCCESS\n' > "$RUN_DIR/RUN_STATUS.txt"
ln -sfn "$RUN_ID" "$PROJECT_ROOT/outputs/image-audit-runs/latest" 2>/dev/null \
  || printf '%s\n' "$RUN_DIR" > "$PROJECT_ROOT/outputs/image-audit-runs/LATEST_RUN.txt"
trap - ERR
echo "SUCCESS"
echo "Report: $RUN_DIR/reports/STEP01_IMAGE_AUDIT_REPORT.md"
echo "Manual review: $RUN_DIR/reports/manual_review.csv"
