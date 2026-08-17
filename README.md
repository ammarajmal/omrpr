# OMRPR Clean-Room Analysis — Mastery Baseline v3.0.0

> **Governance:** Read `GOVERNANCE.md` before interpreting pipeline status or
> approving work. OMRPR-NS-001 in the sibling `structural-vision-research`
> repository is the sole scientific progress authority.

Professional, reproducible camera–LDV analysis project for Ammar Ajmal's OMRPR
wind-tunnel research. The package follows the validated Ammar Engineering
Mastery workstation model: durable source and datasets on `/mnt/space`, a
rebuildable Python runtime on `/home`, evidence-backed quality gates, deliberate
dependency upgrades, and release-grade backups.

## Scientific constraints

- Official AprilRobotics `apriltag` C library only.
- Reviewed release `v3.4.5`; do not follow upstream `master` automatically.
- `tag36h11`, physical tag size `0.020 m`.
- No legacy intrinsic file is accepted as governing calibration. Because a new
  physical calibration cannot be acquired, image-plane displacement is primary
  and metric outputs remain calibration-sensitive until bounded sensitivity
  analysis supports them.
- Fusion is strictly separated by physical marker group and camera coverage.
  Both physical WTT markers decode as tag ID 0.
- Camera–LDV results are non-simultaneous condition-level benchmarking.
- Laser geometry is campaign-specific. For the canonical 2024 laser campaign,
  the current locked candidate is `dside=0.10 m`, `db=0.20 m`, and `dp=2.0`.
  The earlier `dside=0.13 m`, `dp=1.538...` values belong to a superseded
  standalone 2025 session. These constants remain subject to formal provenance
  verification before quantitative torsion claims.

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
