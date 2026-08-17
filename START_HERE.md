# Start Here — OMRPR Mastery Baseline v3.0.0

> Start with `GOVERNANCE.md`. The legacy Step 00--12 status display is an
> engineering crosswalk and cannot approve scientific progress.

This kit updates or creates `/mnt/space/adev/projects/active/omrpr-analysis`
without deleting raw datasets or Git history.

## First run

```bash
cd ~/Downloads/omrpr-cleanroom-starter-v3.0.0
bash scripts/00_preflight.sh
bash scripts/01_bootstrap_or_update.sh --recreate-env
```

## Validate

```bash
cd /mnt/space/adev/projects/active/omrpr-analysis
source scripts/activate-project.sh
make quality
make readiness
```

## Install official AprilTag

```bash
make apriltag
uv run omrpr verify-apriltag
```

## Begin Step 00

```bash
uv run omrpr inventory
uv run omrpr bag-audit
uv run omrpr pipeline status
```

Do not approve a step until its evidence has been reviewed.
