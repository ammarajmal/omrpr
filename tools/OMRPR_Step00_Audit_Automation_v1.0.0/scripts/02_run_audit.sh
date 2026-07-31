#!/usr/bin/env bash
set -Eeuo pipefail

: "${OMRPR_PROJECT_ROOT:?}"
: "${OMRPR_RUN_DIR:?}"

MODE="${1:-full}"
CANONICAL="$OMRPR_PROJECT_ROOT/data/interim/source/bag-audit/topic_audit.csv"
REPORT_COPY="$OMRPR_RUN_DIR/reports/topic_audit.csv"

echo
echo "[2/6] ROS bag structural and timing audit"

if [[ "$MODE" == "reuse" ]]; then
  [[ -s "$CANONICAL" ]] || {
    echo "ERROR: Cannot reuse missing/empty audit CSV: $CANONICAL"
    exit 4
  }
  echo "Reusing canonical audit CSV."
else
  echo "Running: $OMRPR_VENV/bin/omrpr bag-audit"
  "$OMRPR_VENV/bin/omrpr" bag-audit || exit 4
fi

[[ -s "$CANONICAL" ]] || {
  echo "ERROR: Audit did not produce a non-empty CSV: $CANONICAL"
  exit 4
}

cp -f "$CANONICAL" "$REPORT_COPY"
sha256sum "$CANONICAL" > "$OMRPR_RUN_DIR/provenance/canonical_audit.sha256"
echo "Copied audit CSV to: $REPORT_COPY"
