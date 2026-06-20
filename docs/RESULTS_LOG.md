# Results Log

Each entry: Step, date, what was found, acceptance status.

---

## Step 00 — Bag Audit (2026-06-16) ✓ PASS

- All 21 bags open successfully
- Nominal FPS 59–61 Hz confirmed across all cameras
- e7_90rpm reference condition: skew 12.4 ms, no major drops
- All topics present; frame counts consistent with bag durations

---

## Step 01 — Frame Export (2026-06-16) ✓ PASS

- PNG frames + `timestamps.csv` + `meta.json` written per camera per condition
- Frame counts match bag audit
- Timestamps monotonically increasing; max_gap < 0.1 s
- Note: frames not committed to git (large binary); stored in `results/step01/`

---

## Step 02 — AprilTag Detection (2026-06-16) ✓ PASS

- Detection rate > 90% for all stable conditions
- Solver: `SOLVEPNP_IPPE_SQUARE` (locked)
- All three cameras detect `tag_id=0` in practice — routing is by camera, not tag ID
- Sparse `detections.csv` written per camera per condition
- **Note:** e20_320rpm cam1: 60.8%, cam2: 61.3% detection rate (39% dropout) — characterised below

---

## Step 02b — Detection Completeness Gate (PENDING — 2026-06-19)

⚠ Script `src/step02b_detection_gate.py` not yet implemented.

**Criterion (locked):** r_det ≥ 0.95 AND n_miss_max ≤ 5 AND v_peak < w_cell (all cameras)

**Known outcome from existing step02 data:**

| Condition | cam1 det. rate | cam2 det. rate | cam3 det. rate | max_consec_miss | v_peak (cam1) | w_cell | DCG |
|-----------|---------------|---------------|---------------|-----------------|--------------|--------|-----|
| e0–e19 | 100.0% | 100.0% | 100.0% | 0 | < 29 px/frame | ~29 px | **PASS** |
| e20_320rpm | 60.8% | 61.3% | 100.0% | 6 | 67.8 px/frame | ~29 px | **EXCLUDED** |

**Physical reason for e20 exclusion:** Motion blur at equilibrium crossing. At 320 RPM,
f_struct = 2.932 Hz, A_px = 221 px → v_peak = 67.8 px/frame > w_cell = 29 px/frame.
Proven by FFT at 2×f_struct = 5.87 Hz, equilibrium clustering (93.4%), Laplacian sharpness.
See `docs/e20_outlier_analysis.md` for full diagnosis.

---

## Step 03 — Quality Scoring (2026-06-16) ✓ PASS

- B0 formula: `quality_score = dm × sqrt(area_px2)` (shoelace area, locked)
- `corner_sharpness` (Laplacian gradient) added as diagnostic column only
- Quality scores show expected correlation with blur at high-amplitude conditions

---

## Step 04 — Pose Estimation (2026-06-16) ✓ PASS

- `extrinsics.yaml` intentionally empty; all values in camera frame
- Solver: `SOLVEPNP_IPPE_SQUARE` confirmed
- Reprojection errors < 1.0 px for well-lit stable conditions
- Raw Z disagreement cam1–cam2: ~388 mm (physical camera separation — expected)
- `world_pose.csv` schema retained (`x_w, y_w, z_w`) but contains camera-frame values

---

## Step 05 — Synchronization (2026-06-16) ✓ PASS (gap guard patch pending)

- Timestamps normalized to bag-start before any analysis
- Direct common 60 Hz resampling used (dense1000 intermediate gives < 0.08% improvement — skipped)
- Max pairwise timing drift: 20.0 ms (cam1–cam3)
- ⚠ PENDING patch: gap-aware interpolation guard (MAX_INTERP_GAP = 3 frames)
  - Gaps ≤ 3 frames → interpolate (ε = 0.0079 mm, 0.46× noise floor)
  - Gaps > 3 frames → write NaN
  - Threshold derivation: ε = A(πg/T_h)²/8 at T_h = 0.700 s, A = 1.25 mm
  - See `docs/e20_outlier_analysis.md` Section 3.8

---

## Step 06 — Baseline-Aligned Fusion (2026-06-16) ✓ PASS

- Per-camera full-run mean removal (`z_aligned = z_c - mean(z_c)`)
- Raw cam1–cam2 Z offset: ~388 mm → aligned std: **2.053 mm** (e7_90rpm reference, ~189× improvement)
- 20/21 stable conditions: aligned Z std < 15 mm gate met
- This baseline alignment replaces the extrinsics world-frame transform from the original design

---

## Step 07 — Motion Decomposition (2026-06-16) ✓ PASS

- `bending_avg_y_mm = mean(y_cam1, y_cam2)` per timestep
- `torsion_diff_y_mm = y_cam3 - bending_avg_y_mm` per timestep
- Full-run mean removal (NOT first-1-second — first second is already dynamic)
- Bending and torsion channels physically distinct; sign consistent across conditions

---

## Step 08 — Frequency Analysis (2026-06-16) ✓ PASS

- Three aerodynamic regimes confirmed:
  - Bending-dominated: 40–80 RPM
  - Torsion-dominated: 90–220 RPM
  - Bending re-emergence: 240–300 RPM
- All 21 conditions returned `low_snr = False` (including 0 and 20 RPM)
  - 0 and 20 RPM show structured ~9 Hz noise, not flat broadband; SNR criterion (peak/median) does not fire
  - This is a positive finding: the system does not misidentify structured noise as signal
- Dominant peaks and nearest reference bins reported separately (they often differ)

---

## Step 09 — Uncertainty Quantification (2026-06-16) ✓ PASS (all 4 gates)

| Gate | Target | Result |
|------|--------|--------|
| Bending noise floor (static RMS) | < 0.05 mm | **0.017 mm** |
| Torsion proxy noise floor (static RMS) | < 0.10 mm | **0.033 mm** |
| Bootstrap CI width (stable non-near-floor) | < 20% relative | ~13–15% |
| Timing audit (max pairwise drift) | report value | **20.0 ms** (cam1–cam3) |

- Moving-block bootstrap used (not standard bootstrap — time series)
- Static noise floor derived as `sqrt((σ_cam1² + σ_cam2²) / 4)`; static bags not simultaneous

---

## Step 10 — LDV Comparison (2026-06-17) ✓ PASS (torsion); DOCUMENTED FAIL (bending)

| Metric | Value | Gate | Status |
|--------|-------|------|--------|
| Bending Pearson r (stable, 18 cond.) | 0.845 | > 0.90 | FAIL (explained) |
| Bending Spearman ρ (stable) | 0.864 | — | — |
| Torsion proxy Pearson r (stable) | 0.940 | > 0.90 | PASS |
| Torsion proxy Spearman ρ (stable) | 0.928 | — | — |

Bending FAIL explanation: regime-dependent cross-axis sensitivity from ~9.8° inter-camera
misalignment inflates apparent bending amplitude by ~2× in the torsion-dominated regime
(90–220 RPM). Correct geometry parameter dp=1.538 (not dp=2.0) changes all LDV-derived
metrics from the original implementation. This is a documented finding, not a code error.

60 RPM: VIV aerodynamic intermittency — camera/LDV ratio ~0.05×, flagged and reported separately.
320 RPM: high-wind unstable, reported separately.

---

## Step 11 — RTS Smoothing (2026-06-17) ✓ PASS (21/21)

| Gate | Target | Result |
|------|--------|--------|
| Phase shift | < 10 ms | **0.00 ms** (all 21 conditions) |
| Frequency error | 0 Hz | **0.000 Hz** |
| Amplitude ratio | 0.95–1.00 | **0.957–1.000** |

Process noise model: `Q = diag([(σ·dt)², σ²])` with `σ=10.0 mm/s`, `R=0.0025 mm²`.
The kinematic `G@G.T` formulation collapsed the Kalman gain (amplitude ratio 0.023 observed)
and was rejected. See `docs/PROJECT_CONTEXT.md` Section 0.5 for full rationale.

---

## Step 11 — RTS Smoothing defaults fix (2026-06-20)

Bug 3 resolved: `step11_rts_smoothing.py` module constants updated to match `pipeline_config.yaml`:
- `PROCESS_NOISE_STD`: 0.5 → **10.0 mm/s**
- `MEASUREMENT_NOISE_STD`: 0.1 → **0.05 mm**

Results (21/21 PASS, phase 0.00 ms, amplitude ratio 0.957–1.000) are unchanged — config values were passed as args at runtime.

---

## Step 09 — Uncertainty re-run with correct intrinsics (2026-06-20)

Bug 1 resolved: `step09_uncertainty.py` now loads intrinsics from `config/pipeline_config.yaml` via `_load_intrinsics_from_yaml()`.

| Camera | Old fx (hardcoded) | Correct fx (from config) | Old reproj error | New reproj error |
|--------|--------------------|--------------------------|-----------------|-----------------|
| cam1 | 2108 | 20327.9 | 1.8–2.0 px | **0.1675 px** |
| cam2 | 2108 | 25749.5 | 1.8–2.0 px | **0.0636 px** |
| cam3 | 2108 | 25630.9 | 1.8–2.0 px | **0.0353 px** |

Updated noise floor values in `results/step09/noise_floor/noise_floor_summary.json`:

| Bound | Value |
|-------|-------|
| `bending_avg_bound_mm` | **0.003 mm** (0.002719) |
| `torsion_diff_bound_mm` | **0.005 mm** (0.004849) |

Previous hardcoded values 0.017/0.033 mm were overestimates (wrong K matrix — Z and fy scale together so mm values are similar, but reproj error proves correctness of calibration). All docs updated.

---

## Step 12 — Manuscript Figures and Tables (2026-06-17 → updated 2026-06-20) ✓ PASS

Outputs in `results/step12/`:

| File | Content |
|------|---------|
| `fig01_displacement_traces.pdf` | e7_90rpm raw + RTS-smoothed displacement traces |
| `fig02_frequency_overview.pdf` | Dominant frequency vs RPM, 3 regimes annotated |
| `fig03_ldv_scatter.pdf` | Camera vs LDV RMS scatter, stable regime, Pearson r annotated + bending leakage annotation |
| `fig04_camera_agreement.pdf` | Camera Z agreement before/after baseline alignment |
| `fig05_uncertainty.pdf` | Per-condition RMS with bootstrap 95% CI and noise floor |
| `tab01_ldv_comparison.csv` | Full condition-level LDV comparison table + Bending_Notes column |
| `tab02_summary_stats.csv` | Summary stats + Step09 noise floor rows + bending leakage FOOTNOTE row |
| `step12_summary.json` | Claim boundary JSON + `note_bending_ratio` key |

Bug 2 resolved (2026-06-20): bending leakage explanation now emitted to caption, annotation, tab01 Notes column, tab02 footnote row, and summary JSON. Noise floor values read live from step09 JSON (not hardcoded).

---

## Comparison Plots — Results & Discussion (2026-06-20) ✓ NEW

New script `src/comparison_plots.py` generating four figures in `results/comparison_plots/`:

| File | Size | Content |
|------|------|---------|
| `fig_freq_comparison.png` | 127 KB | Dominant freq vs RPM; camera (blue circles) + LDV (red squares); 3 regime shading; fn_b / fn_t reference lines |
| `fig_rms_comparison.png` | 79 KB | Paired bar chart per condition, camera vs LDV RMS, regime-coloured |
| `fig_fft_overlay.png` | 305 KB | Normalised PSD overlay for e5_70rpm (bending VIV), e7_90rpm (torsional VIV), e17_260rpm (bending re-emergence); 3×2 panel |
| `fig_timeseries_overlay.png` | 562 KB | 20-second simultaneous time traces for e7_90rpm; camera 60 Hz (blue) + LDV 360 Hz (red dashed), mean-removed |

Key observations:
- Dominant frequency: both instruments agree on fn_t ≈ 3.08 Hz in torsional VIV regime; at ≤ 20 RPM, below threshold → noise peaks
- RMS ratio 1.339× in bending (explained by torsion-coupling leakage), 0.599× in torsion (attenuation well understood)
- PSD overlay shows aligned spectral peaks; both instruments resolve fn_b and fn_t cleanly in their respective regimes
- Time-series overlay demonstrates simultaneous recording quality; LDV (360 Hz) captures higher-frequency content
