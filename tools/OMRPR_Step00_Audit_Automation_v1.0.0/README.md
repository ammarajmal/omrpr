# OMRPR Step 00 Audit Automation v1.0.0

This package automates the verified OMRPR ROS-bag review workflow:

1. Validate the repository, external Python environment, CLI, and bag layout.
2. Run the existing `omrpr bag-audit` command.
3. Confirm coverage of all 62 expected bags.
4. Summarize PASS/WARN/FAIL results by dataset.
5. Locate significant gaps in static image topics.
6. Calculate contiguous static-data segments.
7. Generate a dataset-specific static acceptance table.
8. Save logs, reports, provenance, checksums, and the exact scripts used.

It is deliberately non-destructive. It does **not** move, rename, edit, extract,
or delete ROS bags. It also does not perform full frame export or AprilTag
processing.

## Expected system layout

```text
Repository:
/mnt/space/adev/projects/active/omrpr-analysis

External Python environment:
/home/ammar/Projects-runtime/research/omrpr-analysis/.venv

Raw data reached through:
<repository>/data/raw/source/camera/rosbag

Canonical audit CSV:
<repository>/data/interim/source/bag-audit/topic_audit.csv

Run records:
<repository>/outputs/audit-runs/<timestamp>/
```

## Where to extract

Extract the ZIP **inside the OMRPR repository's `tools` directory**:

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis
mkdir -p tools
unzip ~/Downloads/OMRPR_Step00_Audit_Automation_v1.0.0.zip -d tools/
```

The resulting launcher should be:

```text
/mnt/space/adev/projects/active/omrpr-analysis/tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh
```

Because `/mnt/space` may be an NTFS/FUSE mount, do not depend on executable
permission bits. Launch the package explicitly with `bash`.

## Run the complete audit

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis

bash tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh
```

The launcher activates the correct external environment itself. Do not source
the repository-local `.venv`.

## Dry-run preflight

To verify paths and dependencies without starting the full bag audit:

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis

bash tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh \
  --preflight-only
```

## Resume from an existing canonical audit CSV

If `omrpr bag-audit` has already completed and the canonical CSV is valid:

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis

bash tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh \
  --reuse-audit
```

The reused CSV is copied into the new run directory so that the run remains
self-contained.

## Override a path

Normally no configuration is required. Optional environment overrides:

```bash
export OMRPR_PROJECT_ROOT=/mnt/space/adev/projects/active/omrpr-analysis
export OMRPR_VENV=/home/ammar/Projects-runtime/research/omrpr-analysis/.venv
export OMRPR_EXPECTED_BAGS=62
export OMRPR_EXPECTED_WTT_MAIN=21
export OMRPR_EXPECTED_WTT_5SEC=21
export OMRPR_EXPECTED_STATIC=20
export OMRPR_GAP_THRESHOLD_S=0.025

bash tools/OMRPR_Step00_Audit_Automation_v1.0.0/run_step00.sh
```

## Output layout

Each execution creates a timestamped directory:

```text
outputs/audit-runs/20260728_013000/
├── RUN_STATUS.txt
├── logs/
│   └── run.log
├── provenance/
│   ├── command.txt
│   ├── environment.txt
│   ├── git_status.txt
│   └── package_manifest.sha256
├── reports/
│   ├── topic_audit.csv
│   ├── dataset_summary.csv
│   ├── bag_coverage.csv
│   ├── non_pass_records.csv
│   ├── static_gap_details.csv
│   ├── static_segment_summary.csv
│   ├── static_bag_acceptance_review_v2.csv
│   ├── STEP00_AUDIT_REPORT.md
│   └── output_manifest.sha256
└── scripts_used/
    └── exact package snapshot
```

`RUN_STATUS.txt` contains `RUNNING`, `SUCCESS`, or `FAILED`. A failed run is
kept for diagnosis rather than deleted.

## Read the result

After success:

```bash
RUN_DIR="$(readlink -f outputs/audit-runs/latest)"

cat "$RUN_DIR/RUN_STATUS.txt"
less "$RUN_DIR/reports/STEP00_AUDIT_REPORT.md"
column -s, -t < "$RUN_DIR/reports/dataset_summary.csv"
column -s, -t < "$RUN_DIR/reports/static_bag_acceptance_review_v2.csv" | less -S
```

If the filesystem cannot create the `latest` symbolic link, use:

```bash
RUN_DIR="$(find outputs/audit-runs -mindepth 1 -maxdepth 1 -type d \
  -printf '%f %p\n' | sort | tail -n 1 | cut -d' ' -f2-)"
```

## Current expected interpretation

The previously completed run found:

- 62 bags total;
- 21 `wtt-main` bags;
- 21 `wtt-5sec` bags;
- 20 static bags;
- 146 topic rows;
- 134 PASS, 5 WARN, and 7 FAIL rows;
- no non-PASS WTT topic rows;
- all WARN/FAIL rows confined to static image topics.

This package verifies those facts again from the live data. It does not hard-code
them as results.

## Exit codes

- `0`: completed successfully.
- `2`: configuration or command-line error.
- `3`: preflight/coverage validation failure.
- `4`: existing audit command failed.
- `5`: report generation failed.

## Scientific boundary

The acceptance labels are engineering review categories, not automatic
scientific exclusions:

- `ACCEPT_AS_RECORDED`
- `ACCEPT_LOWER_RATE_PENDING_IMAGE_CHECK`
- `ACCEPT_AFTER_SEGMENT_SELECTION`
- `REVIEW_LONG_GAP`
- `REJECT_TIMESTAMP_INTEGRITY`
- `MANUAL_REVIEW`

Any static bag marked for review remains in place. Final acceptance should be
confirmed during the Step 01 image-decode sampling audit.
