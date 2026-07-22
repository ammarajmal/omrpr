# OMRPR Camera-LDV Clean-Room Analysis

A reproducible research-software project for auditing ROS 1 camera bags,
recalibrating three cameras, detecting 20 mm `tag36h11` AprilTags with the
official AprilRobotics C library, aligning detections by timestamp and tag ID,
constructing bending and torsion-proxy responses, processing non-simultaneous
LDV references, generating uncertainty-aware results, and preparing the
manuscript for submission.

Read these first:

1. `AGENTS.md`
2. `LEGACY_ANALYSIS_REPORT.md`
3. `docs/MASTER_EXECUTION_ROADMAP.md`
4. `docs/DATA_PLACEMENT.md`

## Hard scientific constraints

- Fresh calibration only; no legacy camera intrinsics.
- Official AprilRobotics AprilTag v3.4.5 or newer verified release.
- Required family: `tag36h11`; measured tag size: `0.020 m`.
- Static: one shared tag. WTT: tag 0 for cam1+cam2 and tag 1 for cam3.
- Never pool detections across tag IDs.
- Paper-2 LDV geometry: `dside=0.13 m`, `db=0.20 m`, `dp=1.538461538...`.
- Model reference frequencies: bending `1.430 Hz`, torsion `3.103 Hz`.
- Camera-LDV comparison is non-simultaneous condition-level benchmarking.
- `e20_320rpm` remains separate from stable-regime statistics.
- `e4_60rpm` remains an explicit VIV/onset diagnostic.

## Routine commands

```bash
source scripts/activate-project.sh
uv run omrpr doctor
uv run omrpr inventory
uv run omrpr pipeline status
make quality
```
