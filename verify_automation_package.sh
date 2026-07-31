#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$ROOT"

sha256sum -c AUTOMATION_PACKAGE_MANIFEST.sha256
bash -n \
  scripts/activate-project.sh \
  run_pipeline.sh \
  tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh \
  tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh

source scripts/activate-project.sh
python -c 'import cv2, matplotlib, numpy, PIL, rosbags'
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  uv run --active python -m pytest tests/python -q

echo "Automation package verification: PASS"
