#!/usr/bin/env bash
set -Eeuo pipefail

: "${OMRPR_PROJECT_ROOT:?}"
: "${OMRPR_EXPECTED_BAGS:?}"
: "${OMRPR_EXPECTED_WTT_MAIN:?}"
: "${OMRPR_EXPECTED_WTT_5SEC:?}"
: "${OMRPR_EXPECTED_STATIC:?}"

ROOT="$OMRPR_PROJECT_ROOT/data/raw/source/camera/rosbag"

echo "[1/6] Preflight checks"

for command_name in python sha256sum find awk; do
  command -v "$command_name" >/dev/null || {
    echo "ERROR: Required command unavailable: $command_name"
    exit 3
  }
done

"$OMRPR_VENV/bin/omrpr" --help >/dev/null
python - <<'PY'
import importlib.util
missing = [
    name for name in ("pandas", "numpy", "rosbags")
    if importlib.util.find_spec(name) is None
]
if missing:
    raise SystemExit("Missing Python packages: " + ", ".join(missing))
PY

python_executable="$(python -c 'import sys; print(sys.executable)')"
if [[ "$python_executable" != "$OMRPR_VENV/"* ]]; then
  echo "ERROR: Python is outside the locked external environment: $python_executable"
  echo "Expected: $OMRPR_VENV"
  exit 3
fi

for directory in "$ROOT/wtt-main" "$ROOT/wtt-5sec" "$ROOT/static"; do
  [[ -d "$directory" ]] || {
    echo "ERROR: Missing required data directory: $directory"
    exit 3
  }
done

count_bags() {
  find "$1" -type f -name '*.bag' -printf '.' | wc -c
}

wtt_main="$(count_bags "$ROOT/wtt-main")"
wtt_5sec="$(count_bags "$ROOT/wtt-5sec")"
static="$(count_bags "$ROOT/static")"
total=$((wtt_main + wtt_5sec + static))

printf '  wtt-main: %s (expected %s)\n' "$wtt_main" "$OMRPR_EXPECTED_WTT_MAIN"
printf '  wtt-5sec: %s (expected %s)\n' "$wtt_5sec" "$OMRPR_EXPECTED_WTT_5SEC"
printf '  static: %s (expected %s)\n' "$static" "$OMRPR_EXPECTED_STATIC"
printf '  total: %s (expected %s)\n' "$total" "$OMRPR_EXPECTED_BAGS"

[[ "$wtt_main" -eq "$OMRPR_EXPECTED_WTT_MAIN" ]] || exit 3
[[ "$wtt_5sec" -eq "$OMRPR_EXPECTED_WTT_5SEC" ]] || exit 3
[[ "$static" -eq "$OMRPR_EXPECTED_STATIC" ]] || exit 3
[[ "$total" -eq "$OMRPR_EXPECTED_BAGS" ]] || exit 3

echo "Preflight: PASS"
