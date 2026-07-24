#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/activate-project.sh"
cd "$ROOT"

pass=0
warn=0
fail=0

ok() {
    echo "PASS: $*"
    pass=$((pass + 1))
}

warnf() {
    echo "WARN: $*"
    warn=$((warn + 1))
}

bad() {
    echo "FAIL: $*"
    fail=$((fail + 1))
}

section() {
    printf '\n== %s ==\n' "$*"
}

section "Required project files"

[[ -f AGENTS.md ]] \
    && ok "AGENTS.md present" \
    || bad "AGENTS.md missing"

[[ -f LEGACY_ANALYSIS_REPORT.md ]] \
    && ok "legacy audit present" \
    || bad "legacy audit missing"

[[ -f uv.lock ]] \
    && ok "uv.lock present" \
    || bad "uv.lock missing"

[[ -f pyproject.toml ]] \
    && ok "pyproject.toml present" \
    || bad "pyproject.toml missing"

[[ -f .python-version ]] \
    && ok ".python-version present" \
    || warnf ".python-version missing"

section "Python and runtime"

python_version="$(
    uv run python -c \
        'import platform; print(platform.python_version())' \
        2>/dev/null || true
)"

if [[ "$python_version" == "3.12.13" ]]; then
    ok "Python 3.12.13"
else
    bad "Python is ${python_version:-unavailable}; expected 3.12.13"
fi

python_executable="$(
    uv run python -c \
        'import sys; print(sys.executable)' \
        2>/dev/null || true
)"

if [[ "$python_executable" == "$UV_PROJECT_ENVIRONMENT/"* ]]; then
    ok "Python executable is inside project runtime"
else
    bad "unexpected Python executable: ${python_executable:-unavailable}"
fi

runtime_fs="$(
    findmnt \
        -T "$UV_PROJECT_ENVIRONMENT" \
        -n \
        -o FSTYPE \
        2>/dev/null || true
)"

if [[ "$runtime_fs" == "ext4" ]]; then
    ok "runtime environment on ext4"
elif [[ -n "$runtime_fs" ]]; then
    warnf "runtime filesystem=$runtime_fs; ext4 recommended"
else
    bad "unable to determine runtime filesystem"
fi

section "External data links"

for rel in raw interim processed metadata; do
    link="data/$rel/source"

    if [[ -L "$link" && -e "$link" ]]; then
        resolved="$(readlink -f "$link")"
        ok "$link valid -> $resolved"
    elif [[ -L "$link" ]]; then
        bad "$link is a broken symlink"
    elif [[ -e "$link" ]]; then
        bad "$link exists but is not a symlink"
    else
        bad "$link missing"
    fi
done

section "AprilTag detector constraints"

pupil_status="$(
    uv run python - <<'PY' 2>/dev/null || true
import importlib.util

print(
    "installed"
    if importlib.util.find_spec("pupil_apriltags")
    else "absent"
)
PY
)"

if [[ "$pupil_status" == "absent" ]]; then
    ok "pupil_apriltags absent"
else
    bad "pupil_apriltags installed"
fi

forbidden_matches="$(
    grep -RInE \
        --exclude-dir=.git \
        --exclude-dir=.venv \
        --exclude-dir=__pycache__ \
        --exclude-dir=.pytest_cache \
        --exclude-dir=.ruff_cache \
        --exclude='uv.lock' \
        --exclude='cli.py' \
        --exclude='test_constraints.py' \
        '(from[[:space:]]+pupil_apriltags|import[[:space:]]+pupil_apriltags|cv2[.]aruco)' \
        src scripts tests \
        2>/dev/null || true
)"

if [[ -n "$forbidden_matches" ]]; then
    bad "forbidden detector implementation found"
    printf '%s\n' "$forbidden_matches"
else
    ok "forbidden detector implementations absent"
fi

apriltag_status="$(
    uv run python - <<'PY' 2>/dev/null || true
try:
    from apriltag import apriltag

    detector = apriltag("tag36h11")
except Exception as exc:
    print(f"error:{type(exc).__name__}:{exc}")
else:
    print("ok" if detector is not None else "error:null-detector")
PY
)"

if [[ "$apriltag_status" == "ok" ]]; then
    ok "official AprilTag tag36h11 detector available"
else
    warnf "official AprilTag detector verification: $apriltag_status"
fi

if [[ -f environment/apriltag-install.json ]]; then
    ok "AprilTag installation provenance present"
else
    warnf "environment/apriltag-install.json missing"
fi

section "Research data"

bag_root="${OMRPR_DATA_ROOT}/raw/camera/rosbag"

if [[ -d "$bag_root" ]]; then
    bags="$(
        find "$bag_root" \
            -type f \
            -iname '*.bag' \
            -print 2>/dev/null \
            | wc -l
    )"
else
    bags=0
fi

if ((bags > 0)); then
    ok "bag files found: $bags"
else
    warnf "no bag files found"
fi

conditions=(
    e0_0rpm
    e1_20rpm
    e2_40rpm
    e3_50rpm
    e4_60rpm
    e5_70rpm
    e6_80rpm
    e7_90rpm
    e8_100rpm
    e9_110rpm
    e10_120rpm
    e11_140rpm
    e12_160rpm
    e13_180rpm
    e14_200rpm
    e15_220rpm
    e16_240rpm
    e17_260rpm
    e18_280rpm
    e19_300rpm
    e20_320rpm
)

wtt_root="$bag_root/wtt-main"
missing_condition_count=0
empty_condition_count=0
populated_condition_count=0

for condition in "${conditions[@]}"; do
    condition_dir="$wtt_root/$condition"

    if [[ ! -d "$condition_dir" ]]; then
        warnf "missing condition directory $condition"
        missing_condition_count=$((missing_condition_count + 1))
        continue
    fi

    condition_bags="$(
        find "$condition_dir" \
            -maxdepth 1 \
            -type f \
            -iname '*.bag' \
            -print 2>/dev/null \
            | wc -l
    )"

    if ((condition_bags == 0)); then
        warnf "condition directory empty: $condition"
        empty_condition_count=$((empty_condition_count + 1))
    else
        populated_condition_count=$((populated_condition_count + 1))
    fi
done

if ((missing_condition_count == 0)); then
    ok "all 21 canonical WTT condition directories present"
fi

if ((populated_condition_count == 21)); then
    ok "all 21 canonical WTT conditions contain bag files"
else
    warnf \
        "canonical WTT population: populated=$populated_condition_count, empty=$empty_condition_count, missing=$missing_condition_count"
fi

for static_camera in cam1 cam2 cam3; do
    static_dir="$bag_root/static/$static_camera"

    if [[ -d "$static_dir" ]]; then
        ok "static bag directory present: $static_camera"
    else
        warnf "static bag directory missing: $static_camera"
    fi
done

[[ -d "$bag_root/wtt-5sec" ]] \
    && ok "wtt-5sec directory present" \
    || warnf "wtt-5sec directory missing"

section "Software quality"

if uv run ruff format --check . >/dev/null; then
    ok "Ruff format"
else
    bad "Ruff format"
fi

if uv run ruff check . >/dev/null; then
    ok "Ruff lint"
else
    bad "Ruff lint"
fi

if uv run mypy src/omrpr_analysis >/dev/null; then
    ok "mypy"
else
    bad "mypy"
fi

if env -u PYTHONPATH \
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    uv run pytest \
        -p pytest_cov \
        -q \
        >/dev/null
then
    ok "pytest isolated"
else
    bad "pytest isolated"
fi

if uv run omrpr doctor >/dev/null; then
    ok "project doctor"
else
    bad "project doctor"
fi

section "Git state"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    ok "Git repository detected"

    git_status="$(git status --short)"

    if [[ -z "$git_status" ]]; then
        ok "Git working tree clean"
    else
        warnf "Git working tree has uncommitted changes"
        printf '%s\n' "$git_status"
    fi
else
    bad "not inside a Git repository"
fi

section "Disk capacity"

project_free_kb="$(
    df --output=avail "$ROOT" 2>/dev/null \
        | tail -n 1 \
        | tr -d ' '
)"

data_free_kb="$(
    df --output=avail "$OMRPR_DATA_ROOT" 2>/dev/null \
        | tail -n 1 \
        | tr -d ' '
)"

minimum_free_kb=$((20 * 1024 * 1024))

if [[ "$project_free_kb" =~ ^[0-9]+$ ]] \
    && ((project_free_kb >= minimum_free_kb))
then
    ok "project filesystem has at least 20 GiB free"
else
    warnf "project filesystem has less than 20 GiB free"
fi

if [[ "$data_free_kb" =~ ^[0-9]+$ ]] \
    && ((data_free_kb >= minimum_free_kb))
then
    ok "data filesystem has at least 20 GiB free"
else
    warnf "data filesystem has less than 20 GiB free"
fi

section "Readiness report"

mkdir -p \
    environment/system-baseline \
    outputs/reports

report_path="outputs/reports/project-readiness-latest.txt"

{
    echo "date=$(date --iso-8601=seconds)"
    echo "project=$ROOT"
    echo "data=${OMRPR_DATA_ROOT}"
    echo "runtime=${UV_PROJECT_ENVIRONMENT}"
    echo "runtime_filesystem=${runtime_fs:-unknown}"
    echo "python=${python_version:-unknown}"
    echo "python_executable=${python_executable:-unknown}"
    echo "bags=$bags"
    echo "wtt_populated_conditions=$populated_condition_count"
    echo "wtt_empty_conditions=$empty_condition_count"
    echo "wtt_missing_conditions=$missing_condition_count"
    echo "PASS=$pass"
    echo "WARN=$warn"
    echo "FAIL=$fail"
} | tee "$report_path"

echo
echo "SUMMARY: PASS=$pass WARN=$warn FAIL=$fail"

if ((fail == 0)); then
    exit 0
fi

exit 1
