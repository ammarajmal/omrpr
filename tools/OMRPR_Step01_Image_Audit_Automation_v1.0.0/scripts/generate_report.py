from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path


def main() -> None:
    report_dir = Path(sys.argv[1])
    with (report_dir / "stream_summary.csv").open(encoding="utf-8") as handle:
        streams = list(csv.DictReader(handle))
    with (report_dir / "frame_metrics.csv").open(encoding="utf-8") as handle:
        frames = list(csv.DictReader(handle))
    types = Counter(row["msgtype"] for row in streams)
    statuses = Counter(row["status"] for row in streams)
    failures = sum(row["decode_ok"].lower() != "true" for row in frames)
    text = f"""# OMRPR Step 01 — Image Decode and Sampling Audit

## Outcome

- Bags inspected: **{len({row["bag"] for row in streams})}**
- Image streams inspected: **{len(streams)}**
- Sampled frames: **{len(frames)}**
- Decode failures: **{failures}**
- PASS streams: **{statuses["PASS"]}**
- REVIEW streams: **{statuses["REVIEW"]}**
- Compressed streams: **{types["sensor_msgs/msg/CompressedImage"]}**
- Raw streams: **{types["sensor_msgs/msg/Image"]}**

## Interpretation

This is a bounded visual and image-quality audit. It does not extract all frames,
run AprilTag pose estimation, accept/reject scientific conditions automatically,
or modify ROS bags. Review every contact sheet and complete `manual_review.csv`
before closing the Step 01 gate.

## Files

- `stream_summary.csv`: automated stream-level checks.
- `frame_metrics.csv`: brightness, contrast, sharpness, clipping and hashes.
- `contact_sheets/`: one sheet per bag/topic/type stream.
- `samples/`: deterministic sampled JPEG frames.
- `manual_review.csv`: human review record; initially PENDING.
"""
    (report_dir / "STEP01_IMAGE_AUDIT_REPORT.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
