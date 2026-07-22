#!/usr/bin/env bash
set -Eeuo pipefail
DATA_ROOT=${DATA_ROOT:-/mnt/space/adev/datasets/omrpr}
cat <<EOF
Canonical data root: $DATA_ROOT

WTT bags:
  $DATA_ROOT/raw/camera/rosbag/wtt-main/<condition>/*.bag
Static bags:
  $DATA_ROOT/raw/camera/rosbag/static/cam1/*.bag
  $DATA_ROOT/raw/camera/rosbag/static/cam2/*.bag
  $DATA_ROOT/raw/camera/rosbag/static/cam3/*.bag
Fresh calibration images:
  $DATA_ROOT/raw/camera/calibration-images/cam1/*
  $DATA_ROOT/raw/camera/calibration-images/cam2/*
  $DATA_ROOT/raw/camera/calibration-images/cam3/*
Extracted inspection frames:
  $DATA_ROOT/interim/frame-extracts/<condition>/<camera>/*
Laser CSV:
  $DATA_ROOT/raw/laser/csv/tunnel-a-2024/*
  $DATA_ROOT/raw/laser/csv/tunnel-b-2025-paper2-reference/*
Laser workbooks:
  $DATA_ROOT/raw/laser/spreadsheets/*
EOF
