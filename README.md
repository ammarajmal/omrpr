# OMRPR Clean-Room Analysis — Mastery Baseline v3.0.0

Professional, reproducible camera–LDV analysis project for Ammar Ajmal's OMRPR
wind-tunnel research. The package follows the validated Ammar Engineering
Mastery workstation model: durable source and datasets on `/mnt/space`, a
rebuildable Python runtime on `/home`, evidence-backed quality gates, deliberate
dependency upgrades, and release-grade backups.

## Scientific constraints

- Official AprilRobotics `apriltag` C library only.
- Reviewed release `v3.4.5`; do not follow upstream `master` automatically.
- `tag36h11`, physical tag size `0.020 m`.
- Fresh camera calibration; no legacy intrinsic files.
- Fusion strictly separated by tag ID.
- Camera–LDV results are non-simultaneous condition-level benchmarking.
- Tunnel B geometry uses `dside=0.13 m`, `db=0.20 m`, `dp=1.538...` when applicable.
- Natural-frequency references are 1.430 Hz and 3.103 Hz.
- High-wind `e20_320rpm` and the 60 RPM VIV diagnostic remain separately reported.

## Engineering baseline

- Python 3.12.13.
- `uv` project management with a committed lockfile.
- Runtime environment at `~/Projects-runtime/research/omrpr-analysis/.venv`.
- Ruff, strict mypy, isolated pytest, pre-commit, environment evidence, Git bundles,
  and idempotent controlled-tree upgrades.

Start with [START_HERE.md](START_HERE.md), then follow
[docs/MASTER_EXECUTION_ROADMAP.md](docs/MASTER_EXECUTION_ROADMAP.md).
