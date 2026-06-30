# Pipeline Diagram

12-step offline processing chain from raw ROS bag files to publication figures.
Each step has one input, one output, and documented acceptance criteria.

```
Raw .bag files (21 RPM conditions, 3 cameras)
        │
        ▼
Step 00 — Bag Audit
        Input:  .bag files
        Output: per-bag metadata (FPS, frame count, topic list, drop rate, skew)
        Accept: All bags open; FPS 59–61 Hz; no major frame drops
        │
        ▼
Step 01 — Frame Export
        Input:  .bag files
        Output: PNG frames + timestamps.csv + meta.json per camera per bag
        Accept: Frame count matches audit; timestamps monotonically increasing;
                max_gap < 0.1 s; no decode_failures
        Note:   timestamps.csv = frame_idx, timestamp_s (normalized from bag start)
        │
        ▼
Step 02 — AprilTag Detection
        Input:  PNG frame folders
        Output: detections.csv per camera per bag + summary.json
        Accept: Detection rate > 90% for stable conditions
        Note:   Sparse CSV — frames with no detection get no row
                All 3 cameras detect tag_id=0 in practice; route by camera, not tag ID
        │
        ▼
Step 02b — Detection Completeness Gate (DCG)
        Input:  step02 detections.csv + summary.json per camera per condition
        Output: gate_status.json per condition
        Accept: Designed criterion r_det ≥ 0.95 AND n_miss_max ≤ 3 AND v_peak < w_cell (all cameras)
        Note:   v_peak = 2π × f_struct × A_px / 60 (from cy amplitude in detections.csv)
                w_cell = mean tag side length / 10 (from corner coords, not hardcoded)
                Conditions that FAIL: excluded from all downstream steps
                e0–e19: PASS; e20_320rpm: EXCLUDED (cam1: 60.8%, v_peak = 67.8 > w_cell = 29)
        │
        ▼
Step 03 — Quality Scoring
        Input:  detections.csv
        Output: detections_with_quality.csv + quality_summary.json
        Accept: quality_score = dm × sqrt(area_px2)  [B0 formula — locked]
                area_px2 = shoelace formula on 4 detected corners
        Note:   corner_sharpness (Laplacian) added as diagnostic column only
        │
        ▼
Step 04 — Camera-Frame Pose Estimation
        Input:  detections.csv + camera_info from bags
        Output: world_pose.csv per camera per condition
                (columns x_w, y_w, z_w retained for schema compatibility;
                 values are in each camera's own coordinate frame)
        Accept: Solver: SOLVEPNP_IPPE_SQUARE (locked)
                Reprojection error < 1.0 px (good); > 3.0 px (suspicious)
                Raw Z disagreement ~388 mm (cam1–cam2) BEFORE alignment — expected
        Note:   extrinsics.yaml is intentionally empty; no world-frame transform applied
                Always call .flatten() on tvec immediately after solvePnP
        │
        ▼
Step 05 — Cross-Camera Synchronization
        Input:  world_pose.csv per camera (different timestamps)
        Output: Synchronized multi-camera traces on a common 60 Hz grid
        Accept: Direct common60 resampling; dense1000 gives < 0.08% improvement — skipped
        Note:   Normalize timestamps to bag-start BEFORE any sync analysis
                Max pairwise drift: 20.03 ms (cam1–cam3)
                Proposed gap-aware guard patch: gaps ≤ 3 frames → interpolate
                                                (ε = 0.008 mm, 0.46× noise floor)
                                                gaps > 3 frames → write NaN
                MAX_INTERP_GAP = 3 frozen from ε = A(πg/T_h)²/8 at T_h = 0.698 s,
                A = 1.25mm, but not yet implemented in live Step 05 code
        │
        ▼
Step 06 — Baseline-Aligned Fusion
        Input:  Synchronized camera-frame traces
        Output: Fused displacement traces + per-camera alignment offsets
        Accept: Aligned Z std < 15 mm for 20/21 stable conditions
        Note:   z_aligned = z_c − mean(z_c)  per camera
                Raw ~388 mm → aligned ~2.053 mm std (e7_90rpm, ~189× improvement)
                This replaces the extrinsics world-frame transform from original design
        │
        ▼
Step 07 — Motion Decomposition
        Input:  Fused synchronized traces
        Output: bending_avg_y_mm = mean(y_cam1, y_cam2)
                torsion_diff_y_mm = y_cam3 − bending_avg_y_mm
        Accept: Channels physically distinct; full-run mean removal
        Note:   NEVER use first-1-second removal — first second is already dynamic
        │
        ▼
Step 08 — Frequency Analysis
        Input:  bending_avg_y_mm and torsion_diff_y_mm per condition
        Output: FFT/PSD per condition, dominant peak frequency, nearest reference bin
        Accept: Bending peak within ±0.5 Hz of f_h = 1.4323 Hz for stable conditions
                Torsion proxy peak near f_α = 3.0827 Hz
        Note:   Three aerodynamic regimes: bending-dominated (40–80 RPM),
                torsion-dominated (90–220 RPM), bending re-emergence (240–300 RPM)
                All 21 conditions: low_snr = False (including 0 and 20 RPM)
                Always report dominant peak and nearest reference bin separately
        │
        ▼
Step 09 — Uncertainty Quantification
        Input:  Time series + static bags
        Output: Static noise floor, camera-agreement stats, bootstrap CIs, timing audit
        Accept: bending preferred full-pipeline bound < 0.05 mm (result: 0.017 mm)
                torsion proxy preferred full-pipeline bound < 0.1 mm (result: 0.033 mm)
                reproj error < 0.5 px (result: 0.04–0.17 px — confirms correct intrinsics)
                Bootstrap CI width < 20% relative for stable non-near-floor conditions
        Note:   Moving-block bootstrap (not standard bootstrap — time series)
                Manuscript-facing conservative bounds remain 0.017 mm bending,
                0.033 mm torsion proxy
        │
        ▼
Step 10 — LDV Condition-Level Comparison
        Input:  Per-condition bending/torsion RMS + LDV reference (converted to mm)
        Output: Comparison table, Pearson/Spearman, ratio analysis
        Accept: Torsion stable-regime Pearson > 0.90
                Bending above-floor stable Pearson is reported with physical explanation if below 0.90
        Note:   LDV raw files in CENTIMETERS — convert explicitly; use _mm_corrected columns
                LDV comparison is condition-level ONLY (same-tunnel Tunnel B, separate sessions 10 days apart, NOT simultaneous)
        │
        ▼
Step 11 — Non-Causal RTS Smoothing
        Input:  Fused displacement traces
        Output: Smoothed traces (Kalman forward + RTS backward pass)
        Accept: Phase shift < 10 ms; amplitude ratio 0.95–1.00; frequency preserved
        Note:   RTS is non-causal — only possible offline
                Process noise: Q = diag([(σ·dt)², σ²]), σ=10 mm/s, R=0.0025 mm²
                Result: 21/21 PASS, phase 0.00 ms, amplitude ratio 0.957–1.000
        │
        ▼
Step 12 — Manuscript Figures and Tables
        Input:  All result artifacts (Steps 00–11) + gate_status.json from Step 02b
        Output: 5 publication figures + 2 tables in results/step12/
        Accept: All figures programmatic; claim boundary PASS; captions use required language
                e20_320rpm: shown as DCG-EXCLUDED (not silently dropped)
                cam3 2.19mm: shown as separate labelled pre-flutter data point
                DCG velocity criterion stated in figure caption or table footnote
```

## Key Locked Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| solvePnP solver | `SOLVEPNP_IPPE_SQUARE` | Optimal for planar square targets |
| extrinsics.yaml | Empty by design | Replaced by camera-frame pose + baseline alignment |
| Quality score formula | `dm × sqrt(area_px2)` | B0 formula — locked |
| LDV dside | 130 mm | Confirmed from facility document |
| LDV dp (torsion scaling) | 1.538 | `BRID2D1_choi.m` MATLAB script |
| LDV pvolt | 2.7 cm/V | `BRID2D1_choi.m` |
| LDV fs | 360 Hz | `BRID2D1_choi.m` |
| f_h (bending nat. freq.) | 1.4323 Hz | Measured Tunnel B free-vibration result |
| f_α (torsion nat. freq.) | 3.0827 Hz | Measured Tunnel B free-vibration result |
| Bridge chord width B | 0.40 m | Model setup sheet |
| RTS process noise σ | 10.0 mm/s | Calibrated for 0.957–1.000 amplitude ratio |
