#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
START=0
STOP=1
REUSE_STEP00=0

while (($#)); do
  case "$1" in
    --from) shift; START="${1:?missing --from value}" ;;
    --through) shift; STOP="${1:?missing --through value}" ;;
    --reuse-step00) REUSE_STEP00=1 ;;
    --help|-h)
      echo "Usage: bash run_pipeline.sh [--from 0|1] [--through 0|1] [--reuse-step00]"
      exit 0
      ;;
    *) echo "ERROR: Unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

if ((START <= 0 && STOP >= 0)); then
  args=()
  ((REUSE_STEP00)) && args+=(--reuse-audit)
  bash "$PROJECT_ROOT/tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh" \
    "${args[@]}"
fi

if ((START <= 1 && STOP >= 1)); then
  bash "$PROJECT_ROOT/tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh"
fi

if ((STOP > 1)); then
  echo "ERROR: Steps 02-12 are scientifically gated and not implemented in this release." >&2
  exit 6
fi
