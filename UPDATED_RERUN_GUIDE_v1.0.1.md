# OMRPR Automation Master v1.0.1 — Update and Rerun

This release fixes the ROS 2 Lyrical pytest-plugin conflict, the unbounded
`uv_build` warning, portable archive verification, and Step 01 results
inspection.

## 1. Verify the download

Keep these three files together in `~/Downloads`:

- `OMRPR_Automation_Master_v1.0.1.tar.gz`
- `OMRPR_Automation_Master_v1.0.1.tar.gz.sha256`
- `VERIFY_OMRPR_DOWNLOAD_v1.0.1.sh`

Then run:

```bash
cd ~/Downloads
bash VERIFY_OMRPR_DOWNLOAD_v1.0.1.sh
```

## 2. Extract the update

This updates project-controlled scripts and documentation. It does not remove
existing data or outputs.

```bash
cd /mnt/space/adev/projects/active
tar -xzf ~/Downloads/OMRPR_Automation_Master_v1.0.1.tar.gz
```

## 3. Synchronize and verify

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis
source scripts/activate-project.sh
uv sync
bash verify_automation_package.sh
```

Expected final lines:

```text
10 passed
Automation package verification: PASS
```

## 4. Inspect the already completed Step 01 run

Do not rerun the 62-bag image audit merely to inspect its results:

```bash
python scripts/08_inspect_step01_results.py \
  --run-dir outputs/image-audit-runs/20260728_020809
```

## 5. Optional clean Step 01 rerun

Only rerun if you intentionally want a fresh audit:

```bash
bash tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh \
  --preflight-only

bash tools/OMRPR_Step01_Image_Audit_Automation_v1.0.0/run_step01.sh
```

The script creates a new timestamped run directory and does not overwrite the
completed `20260728_020809` run.
