# OMRPR — Offline Multi-Modal Robust Pose Reconstruction

PhD Paper 2 | Ammar Ajmal

## What This Is
A fully offline, deterministic, multi-camera reconstruction pipeline for 
reproducible sub-millimeter structural displacement tracking using AprilTag 
markers — applied to wind tunnel testing of a bridge section model.

## Pipeline Overview
12-step processing chain from raw ROS bag files to publication figures.
See `docs/pipeline_diagram.md` for the full pipeline.

## Setup
```bash
conda env create -f environment.yml
conda activate omrpr
```

## Usage
```bash
python src/step00_bag_audit.py --bag data/WTT/e7_90rpm/e7_90rpm_run1.bag
```

## Status
- [x] Step 00 — Bag Audit
- [x] Step 01 — Frame Export
- [x] Step 02 — AprilTag Detection
- [x] Step 03 — Quality Scoring
- [x] Step 04 — Camera-Frame Pose Estimation (no extrinsics; IPPE_SQUARE solver)
- [x] Step 05 — Synchronization
- [x] Step 06 — Baseline-Aligned Camera Fusion
- [x] Step 07 — Motion Decomposition
- [x] Step 08 — Frequency Analysis
- [x] Step 09 — Uncertainty Quantification
- [ ] Step 10 — LDV Comparison
- [ ] Step 11 — RTS Smoothing
- [ ] Step 12 — Figures and Tables
