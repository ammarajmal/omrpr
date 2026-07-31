# Data Placement

All large data remains outside Git under `/mnt/space/adev/datasets/omrpr`.

```text
raw/
  camera/
    rosbag/
      wtt-main/<condition>/*.bag
      static/cam1/*.bag
      static/cam2/*.bag
      static/cam3/*.bag
      wtt-5sec/<condition>/*.bag
    calibration-images/cam1/*
    calibration-images/cam2/*
    calibration-images/cam3/*
  laser/
    csv/tunnel-a-2024/*
    csv/tunnel-b-2025-paper2-reference/*
    spreadsheets/*
  experiment-logs/*
interim/
  frame-extracts/<condition>/<camera>/*
  bag-audit/*
  apriltag-detections/*
  calibration/*
  multicamera-aligned/*
  condition-matched/*
processed/
  conditions/*
  metrics/*
  manuscript/*
metadata/
  inventories/*
  checksums/*
  sessions/*
  conditions/*
```

ROS bags are raw acquisition containers. Images extracted from bags are
interim products. Only separately captured calibration images belong in
`raw/camera/calibration-images`.
