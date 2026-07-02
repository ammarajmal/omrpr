# OMRPR Codebase Context

## Purpose
Multi-camera AprilTag-based framework for measuring bridge deck displacement
under wind-induced excitation. Wind tunnel experiment, 21 conditions.

## Key File
- docs/claim_boundary.md — CANONICAL source of truth for ALL reported numbers

## Pipeline
- Ubuntu 20.04 (ROS1) — DO NOT migrate to ROS2 until after paper submission
- Ubuntu 24.04 (Python analysis, manuscript writing, shared drive)

## Data
- Code: PUBLIC (this repo)
- Raw experimental data: PRIVATE (do not include in code)

## Cameras
- Sony RX10 IV cameras + AverMedia video capture cards — naming CONFIRMED (2026-07-01, personal equipment)

## Ground Truth — Option B Canonical (LOCKED 2026-07-01)
docs/claim_boundary.md holds the full table; headline numbers only here:
- Bending Pearson r (stable, 18 cond.) = 0.9577 (report ≈0.958), RMSE = 0.3009 mm (≈0.301 mm)
- Torsion proxy Pearson r (stable) = 0.9665 (report ≈0.967)
- LDV geometry: Tunnel A 2024, dside=100mm, dp=2.0, pvolt=2.7 cm/V, fs=360 Hz
- Superseded: B0 values (Tunnel B 2025 LDV, dp=1.538, dside=130mm) — DO NOT USE

## DCG Threshold Correction (2026-07-01)
Interpolation error formula had a factor-of-4 bug (used ω=π/T_h instead of ω=2π/T_h).
Corrected: N_miss_max threshold 3→2 frames. Verified via step02 detections.csv
frame_idx gap analysis — no condition e0–e19 has any consecutive-miss gap
(max_gap=1), so the 18-stable-condition sample and all locked Pearson/RMSE/ratio
numbers above are unaffected. Only e20_320rpm (already DCG-excluded) is affected.
step05_synchronize.py now has a MAX_INTERP_GAP diagnostic guard (2 frames/33ms)
that warns and logs to summary.json["large_gaps"] — diagnostic only, not a hard stop.

## Related Repo
- Manuscript: ../omrpr-paper2-manuscript/ (https://github.com/ammarajmal/omrpr-paper2-manuscript)
- Manuscript's docs/source_of_truth/claim_boundary.md must mirror this repo's
  docs/claim_boundary.md exactly — cross-check both after any number change here.