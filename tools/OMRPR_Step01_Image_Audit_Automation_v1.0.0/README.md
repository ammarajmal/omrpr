# OMRPR Step 01 Image Audit Automation v1.0.0

This package performs bounded deterministic sampling of all OMRPR ROS image
streams. It supports both observed formats:

- `sensor_msgs/msg/CompressedImage` (JPEG/PNG through OpenCV);
- `sensor_msgs/msg/Image` with row-step-aware decoding for common 8/16-bit
  mono, RGB, BGR, RGBA and BGRA encodings.

It records decode failures, resolution/encoding consistency, brightness,
contrast, Laplacian sharpness, clipping, perceptual hashes, contact sheets and
a manual-review CSV. It does not alter or fully extract any bag.

## Run Step 01

Extract the master archive into the repository root, then:

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis
bash tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh
```

Preflight only:

```bash
bash tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh \
  --preflight-only
```

Change the bounded sample count:

```bash
bash tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh \
  --samples-per-stream 16
```

## Output layout

```text
outputs/image-audit-runs/<RUN_ID>/
├── RUN_STATUS.txt
├── logs/run.log
├── provenance/
├── reports/
│   ├── STEP01_IMAGE_AUDIT_REPORT.md
│   ├── frame_metrics.csv
│   ├── stream_summary.csv
│   ├── manual_review.csv
│   ├── contact_sheets/
│   ├── samples/
│   └── output_manifest.sha256
└── scripts_used/
```

Do not proceed to AprilTag verification until contact sheets are reviewed and
`manual_review.csv` no longer contains unresolved `PENDING` decisions.
