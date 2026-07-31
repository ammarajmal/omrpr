#!/usr/bin/env bash
set -Eeuo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

mkdir -p "$TEST_ROOT/run/reports"
cp "$PACKAGE_DIR/tests/topic_audit_fixture.csv" \
  "$TEST_ROOT/run/reports/topic_audit.csv"

export OMRPR_RUN_DIR="$TEST_ROOT/run"
export OMRPR_EXPECTED_BAGS=5

python "$PACKAGE_DIR/scripts/03_summarize_audit.py"

test -s "$TEST_ROOT/run/reports/dataset_summary.csv"
test -s "$TEST_ROOT/run/reports/bag_coverage.csv"
test -s "$TEST_ROOT/run/reports/non_pass_records.csv"

echo "Fixture test: PASS"
