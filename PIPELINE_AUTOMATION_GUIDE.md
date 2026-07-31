# OMRPR Automation Guide — Runnable Release 1.0.0

## What this release automates

- **Step 00:** complete ROS-bag timing/integrity audit already validated against
  the current 62-bag dataset.
- **Step 01:** bounded decode, quality sampling, contact sheets and manual review
  for the confirmed 126 compressed and 20 raw image connections.

Steps 02–12 remain documented in `docs/steps/`, but are deliberately blocked
from `run_pipeline.sh`. Calibration must be redone from verified physical
targets; AprilTag processing must use the official AprilRobotics C library;
torsion geometry and LDV mapping must be resolved before quantitative claims.

## Install or update

Back up the repository first. Extract the archive over the existing repository;
it contains source/configuration only and no bags, generated outputs, `.git`, or
virtual environment:

```bash
cd /mnt/space/adev/projects/active
tar -xzf ~/Downloads/OMRPR_Automation_Master_v1.0.0.tar.gz
cd omrpr-analysis
source scripts/activate-project.sh
uv sync
```

Verify the package checksums:

```bash
sha256sum -c AUTOMATION_PACKAGE_MANIFEST.sha256
```

## Run

Run both implemented steps:

```bash
bash run_pipeline.sh --reuse-step00
```

Run separately:

```bash
bash tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh --reuse-audit
bash tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh
```

Step 01 may take substantial time because it seeks through every image stream,
but it stores only a bounded number of samples (12 per stream by default), not
all frames.

## Review and resume

After Step 01:

```bash
RUN_DIR="$(readlink -f outputs/image-audit-runs/latest)"
less "$RUN_DIR/reports/STEP01_IMAGE_AUDIT_REPORT.md"
xdg-open "$RUN_DIR/reports/contact_sheets"
libreoffice "$RUN_DIR/reports/manual_review.csv"
```

Complete every manual-review row. Preserve the run directory as the immutable
record. Do not overwrite its sampled images or automated CSVs.

## Scientific boundaries retained

- Official AprilRobotics `apriltag` C library only for future detection.
- `tag36h11`, 20 mm tag size.
- No legacy camera intrinsics; recalibrate.
- Fuse by tag ID; never pool marker 0 and marker 1.
- LDV is non-simultaneous condition-level benchmarking, not ground truth.
- Use “timestamp-based temporal alignment,” not hardware synchronization.
- Treat torsion as a proxy until geometry is independently resolved.
- Report `e20_320rpm` separately.
