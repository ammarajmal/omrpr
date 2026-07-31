# README First — OMRPR Mastery Baseline v3.0.0

This package updates an existing OMRPR repository or creates it from scratch.
It preserves raw datasets, Git history, pipeline gates, outputs, notebooks, and
manuscript work. It replaces only framework-controlled trees so stale stubs do
not survive upgrades.

## Fixed locations

- Project: `/mnt/space/adev/projects/active/omrpr-analysis`
- Dataset: `/mnt/space/adev/datasets/omrpr`
- Runtime: `~/Projects-runtime/research/omrpr-analysis/.venv`
- Backups: `/mnt/space/adev/backups/omrpr-analysis`

## Run

```bash
bash scripts/00_preflight.sh
bash scripts/01_bootstrap_or_update.sh --recreate-env
```

The first installation creates `uv.lock` using Python 3.12.13. Commit that
lockfile after all quality checks pass. Normal future installations use the
committed lockfile with `--locked` and do not upgrade dependencies silently.

## Verify

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

## Start Step 00

```bash
uv run omrpr inventory
uv run omrpr bag-audit
uv run omrpr pipeline status
```
