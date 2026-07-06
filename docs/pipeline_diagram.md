# Pipeline Diagram

13-step offline processing chain from raw ROS bag files to publication figures.
Each step has one input, one output, and documented acceptance criteria.

*Last updated: 2026-07-03 — facility naming corrected: "Tunnel B" was a mislabel for the 2025 standalone LDV session (same physical facility as Tunnel A); Option B geometry (dside=100mm/dp=2.0) independently vendor-verified, see `RESULTS_LOG.md`. Earlier: 2026-07-02 — LDV geometry (dside/dp) switched to Option B canonical (2024 paired session); superseded B0 (2025 standalone LDV session) geometry removed. See update summary at bottom. Earlier update (2026-06-30): Added Step 02b (DCG); corrected timing to 20.03 ms.*
*2026-07-06 RESOLVED — f_h/f_α/damping rows below were UNVERIFIED pending a provenance check; now
confirmed via `omrpr_fin/src/free_vib_analysis.py` reproducing the locked values from TESolution's
own vendor-delivered `Bd1`/`Td1` raw files (co-located with the 2025 standalone LDV session's D00–D20
wind data), cross-validated against an independent 2024-session free-vibration measurement
(f_h=1.4299/f_α=3.1098 Hz, within 0.2%/0.9%) and the camera-based FFT corroboration
(f_h=1.4290/f_α=3.0990 Hz). See `RESULTS_LOG.md` for the full provenance chain.*

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
        Input:  detections.csv + summary.json per camera per condition
        Output: gate_status.json per condition (PASS / EXCLUDED)
        Accept: detection_rate ≥ 0.95 per camera AND max_consecutive_miss ≤ 1 frame
                AND v_peak < w_cell (velocity-based blur criterion)
        Note:   N=1 threshold from ε = A(2πg/T_h)²/8 < noise floor (corrected 2026-07-03,
                see claim_boundary.md changelog: noise floor corrected 0.017→0.004 mm)
                At A=1.25 mm, g=1 frame (16.7 ms), T_h=0.698 s: ε=0.0035 mm < 0.004 mm → SAFE
                At g=2 frames (33 ms): ε=0.0141 mm > 0.004 mm → UNSAFE, hence N≤1
                e20_320rpm: EXCLUDED (cam1 60.8%, cam2 61.3%; v_peak=67.8 > w_cell=29 px/frame)
                All other 20 conditions: PASS
                Physical mechanism: motion blur at equilibrium crossing (2.932 Hz structural,
                FFT of miss-indicator at 5.87 Hz = 2×f_struct confirms threshold-crossing failure)
                cam3 at 320 RPM: v_peak=18.7 px/frame < threshold → unaffected; amp 2.19 mm (clean)
                Hardware design rule: t_exp < w_cell/v_peak = 7.1 ms (future campaigns)
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
                Max pairwise drift: 20.03 ms (cam1–cam3, e3_50rpm)
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
        Accept: bending static RMS < 0.05 mm (result: 0.003 mm, static bags; 0.004 mm
                preferred e0_0rpm full-pipeline value — corrected 2026-07-03, was 0.017 mm)
                torsion proxy static RMS < 0.1 mm (result: 0.005 mm, both static bags and
                e0_0rpm full-pipeline — corrected 2026-07-03, was 0.033 mm)
                Bootstrap CI width < 20% relative for stable non-near-floor conditions
        Note:   Moving-block bootstrap (not standard bootstrap — time series)
        │
        ▼
Step 10 — LDV Condition-Level Comparison
        Input:  Per-condition bending/torsion RMS + LDV reference (converted to mm)
        Output: Comparison table, Pearson/Spearman, ratio analysis
        Accept: Stable regime Pearson > 0.90 (excluding 60 RPM VIV outlier)
        Note:   LDV raw files in CENTIMETERS — convert explicitly; use _mm_corrected columns
                LDV comparison is condition-level ONLY (non-simultaneous, cross-tunnel)
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
        Input:  All result artifacts (Steps 00–11)
        Output: 5 publication figures + 2 tables in results/step12/
        Accept: All figures programmatic; claim boundary PASS; captions use required language
```

## Key Locked Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| solvePnP solver | `SOLVEPNP_IPPE_SQUARE` | Optimal for planar square targets |
| extrinsics.yaml | Empty by design | Replaced by camera-frame pose + baseline alignment |
| Quality score formula | `dm × sqrt(area_px2)` | B0 formula — locked |
| LDV dside | 100 mm | Option B canonical (2024 paired session, Tunnel A facility) — see `claim_boundary.md` v2.1, vendor-verified 2026-07-03 |
| LDV dp (torsion scaling) | 2.0 | Option B canonical (2024 paired session, Tunnel A facility) — see `claim_boundary.md` v2.1, vendor-verified 2026-07-03 |
| LDV pvolt | 2.7 cm/V | `BRID2D1_choi.m` |
| LDV fs | 360 Hz | `BRID2D1_choi.m` |
| f_h (bending nat. freq.) | 1.4323 Hz | Free-vibration LDV, 2025 standalone LDV session |
| f_α (torsion nat. freq.) | 3.0827 Hz | Free-vibration LDV, 2025 standalone LDV session |
| Bridge chord width B | 0.40 m | Model setup sheet |
| RTS process noise σ | 10.0 mm/s | Q = diag([(σ·dt)², σ²]); stable amplitude ratio 0.999 |
| Structural damping | ~0.31% | Log-decrement, 2025 standalone LDV session free-vibration |
| Max timing drift | 20.03 ms (cam1–cam3, e3_50rpm) | Step 09 timing audit |
| DCG N threshold | 2 consecutive frames | ε = A(2πg/T_h)²/8 < 0.017 mm noise floor |

---

## 2026-06-30 Update Summary

| Change | Old | New |
|--------|-----|-----|
| Step count | 12 steps | 13 steps (added Step 02b) |
| Step 02b (DCG) | Not present | Added — e20 EXCLUDED, all others PASS |
| f_h in Step 08 | 1.430 Hz | 1.4323 Hz |
| f_α in Step 08 | 3.103 Hz | 3.0827 Hz |
| Timing in Step 05 | 20.0 ms | 20.03 ms (cam1–cam3, e3_50rpm) |
| f_h locked parameter | 1.430 Hz | 1.4323 Hz |
| f_α locked parameter | 3.103 Hz | 3.0827 Hz |

## 2026-07-02 Update Summary (Option B canonical switch)

| Change | Old (B0, superseded) | New (Option B canonical) |
|--------|----------------------|---------------------------|
| LDV session | 2025 standalone LDV session (Tunnel A facility), 2025-09 | 2024 paired session (Tunnel A facility), 2024-10/11 |
| LDV dside | 130 mm | 100 mm |
| LDV dp | 1.538 | 2.0 |
| Stable-condition count | 18 | 19 (60 RPM restored after LDV bend RMS correction, 2026-07-02) |
| Bending r / RMSE | 0.845 / 0.719 mm | ≈0.960 / ≈0.293 mm |
| Torsion r | 0.940 | ≈0.968 |

See `claim_boundary.md` v2.1 for the full locked numbers and changelog. f_h/f_α/damping are NOT part of this switch and are left unchanged pending the provenance check noted above.
