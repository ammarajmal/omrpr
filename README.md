# OMRPR — Offline Multi-Modal Robust Pose Reconstruction

PhD Paper 2 | Ammar Ajmal

## What This Is

A fully offline, deterministic, multi-camera reconstruction pipeline for reproducible
sub-millimeter structural displacement tracking using AprilTag markers — applied to
wind tunnel testing of a bridge section model (21 RPM conditions, 3 Sony RX10 IV cameras).

LDV comparison is condition-level only (non-simultaneous, cross-tunnel). No hardware sync.
See `docs/PROJECT_CONTEXT.md` for the full design rationale and claim boundaries.

## Pipeline Overview

12-step processing chain from raw ROS bag files to publication figures.
See `docs/pipeline_diagram.md` for the step-by-step description.

## Setup

```bash
conda env create -f environment.yml
conda activate omrpr
```

## Usage

Run a single step:
```bash
python src/step00_bag_audit.py --bag data/WTT/e7_90rpm/e7_90rpm_run1.bag
```

Run the full pipeline sweep (all 21 conditions):
```bash
for step in src/step00_bag_audit.py src/step02_detect_apriltag.py \
            src/step03_quality_score.py src/step04_world_transform.py \
            src/step05_synchronize.py src/step06_fuse_cameras.py \
            src/step07_motion_decompose.py src/step08_frequency_analysis.py \
            src/step09_uncertainty.py src/step10_ldv_comparison.py \
            src/step11_rts_smoothing.py src/step12_figures_tables.py; do
  python $step
done
# Note: Step 01 (frame export) is run once; frames are stored in results/step01/
```

Outputs land in `results/step<NN>/`. Each step also writes a `summary.json` with
acceptance-gate status.

## Key Results (Clean Reimplementation, 2026-06-17)

| Metric | Value |
|--------|-------|
| Bending noise floor (static RMS) | 0.017 mm |
| Torsion proxy noise floor (static RMS) | 0.033 mm |
| Camera Z agreement — raw cam1–cam2 | ~388 mm offset (physical separation) |
| Camera Z agreement — after baseline alignment (e7_90rpm) | 2.053 mm std (~189× improvement) |
| Bending Pearson r vs LDV (stable regime, 18 conditions) | 0.845 |
| Torsion proxy Pearson r vs LDV (stable regime) | 0.940 |
| Max pairwise timing drift (cam1–cam3) | 20.0 ms |
| RTS smoother phase shift | 0.00 ms (all 21 conditions) |
| RTS smoother amplitude ratio | 0.957–1.000 |

The bending r = 0.845 (below the 0.90 target) is due to regime-dependent cross-axis
sensitivity from the ~9.8° inter-camera misalignment, not a pipeline error. See
`docs/PROJECT_CONTEXT.md` Section 0 for the full explanation.

## Publication Outputs

All manuscript figures are generated programmatically in `results/step12/`:
- `fig01_displacement_traces.pdf` — e7_90rpm raw + RTS-smoothed traces
- `fig02_frequency_overview.pdf` — dominant frequency vs RPM, 3 aerodynamic regimes
- `fig03_ldv_scatter.pdf` — camera vs LDV RMS scatter (stable regime)
- `fig04_camera_agreement.pdf` — before/after baseline alignment
- `fig05_uncertainty.pdf` — per-condition RMS with bootstrap 95% CI and noise floor

## Status — ALL STEPS COMPLETE

- [x] Step 00 — Bag Audit
- [x] Step 01 — Frame Export
- [x] Step 02 — AprilTag Detection
- [x] Step 03 — Quality Scoring
- [x] Step 04 — Camera-Frame Pose Estimation (no extrinsics; IPPE_SQUARE solver)
- [x] Step 05 — Synchronization (common 60 Hz grid; direct resampling)
- [x] Step 06 — Baseline-Aligned Camera Fusion
- [x] Step 07 — Motion Decomposition
- [x] Step 08 — Frequency Analysis (3 aerodynamic regimes confirmed)
- [x] Step 09 — Uncertainty Quantification (all 4 gates PASS)
- [x] Step 10 — LDV Condition-Level Comparison
- [x] Step 11 — Non-Causal RTS Smoothing (21/21 PASS)
- [x] Step 12 — Manuscript Figures and Tables (5 figures, 2 tables)
