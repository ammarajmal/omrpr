# Results Log

Each entry: Step, date, what was found, acceptance status.

---

## Discrepancy Cleanup — 2026-06-22

All stale values corrected in this audit pass (canonical source: `step10_summary.json`):

| Item | Stale Value | Canonical Value | Source |
|------|-------------|-----------------|--------|
| Bending Pearson r | retired older value (stale) | **0.845** | canonical (stable, 18 cond.) |
| Bending Spearman ρ | 0.864/0.768 | **0.864** | canonical (stable) |
| Bending MAE | 0.484 mm / 0.562 mm | **0.484 mm** | canonical (stable) |
| Bending RMSE | 0.719 mm / 0.787 mm | **0.719 mm** | canonical (stable) |
| Bending ratio camera/LDV | 1.339× / 1.583× (also 1.268×) | **1.339×** | canonical (stable) |
| Torsion ratio camera/LDV | 0.785× | **0.599×** | `step10_summary.json` |
| Aligned Z residual | ~1.757 mm RMS / 62× | **~2.053 mm std / ~189×** | `results/step06/e7_90rpm/summary.json` |
| Max timing drift | stale larger value | **20.03 ms** | `step05` actual output |
| Camera bag tunnel | Stale tunnel label (wrong) | **Tunnel B, October 2025** | Confirmed 2026-06-22 |
| Recording simultaneity | stale concurrent-session assumption | **NOT simultaneous — 10 days apart** | `manifest.json` |
| DCG n_miss_max threshold | ≤ 5 frames | **≤ 3 frames** | Paired analytically with proposed Step 05 gap guard; not implemented in live Step 05 code |

Files corrected: `data/LDV/manifest.json`, `src/step10_ldv_comparison.py`, `src/step06_fuse_cameras.py`, `README.md`, `docs/PROJECT_CONTEXT.md`, `docs/claim_boundary.md`, `docs/RESULTS_LOG.md`

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

**Criterion (locked):** r_det ≥ 0.95 AND n_miss_max ≤ 3 AND v_peak < w_cell (all cameras)

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
- Max pairwise timing drift: 20.03 ms (cam1–cam3)
- ⚠ PENDING patch: gap-aware interpolation guard (MAX_INTERP_GAP = 3 frames)
  - Gaps ≤ 3 frames → interpolate (ε = 0.0079 mm, 0.46× noise floor)
  - Gaps > 3 frames → write NaN
  - Threshold derivation: ε = A(πg/T_h)²/8 at T_h = 0.698 s, A = 1.25 mm
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

## Step 09 — Uncertainty Quantification (2026-06-16; corrected 2026-06-20) ✓ PASS (all 4 gates)

| Gate | Target | Result |
|------|--------|--------|
| Bending noise floor (preferred manuscript reference: e0_0rpm full pipeline) | < 0.05 mm | **0.017 mm** |
| Torsion proxy noise floor (preferred manuscript reference: e0_0rpm full pipeline) | < 0.10 mm | **0.033 mm** |
| Bootstrap CI width (stable non-near-floor) | < 20% relative | ~13–15% |
| Timing audit (max pairwise drift) | report value | **20.03 ms** (cam1–cam3) |

- Moving-block bootstrap used (not standard bootstrap — time series)
- Preferred manuscript-facing bounds come from the `e0_0rpm` full-pipeline condition
- Static-bag bounds remain useful as supporting reference: bending **0.017 mm**, torsion **0.033 mm**
- Static noise floor derivation uses `sqrt((σ_cam1² + σ_cam2²) / 4)`; static bags are recorded in separate sessions

---

## Step 10 — LDV Comparison (2026-06-17) ✓ PASS (torsion); DOCUMENTED FAIL (bending)

| Metric | Value | Gate | Status |
|--------|-------|------|--------|
| Bending Pearson r (stable, 18 cond.) | 0.845 | > 0.90 | FAIL (explained) |
| Bending Spearman ρ (stable) | 0.864 | — | — |
| Torsion proxy Pearson r (stable) | 0.940 | > 0.90 | PASS |
| Torsion proxy Spearman ρ (stable) | 0.928 | — | — |

Bending Pearson r = 0.845 (gate FAIL; physically explained by regime-dependent cross-axis sensitivity from ~9.8° inter-camera misalignment). The misalignment inflates apparent bending amplitude by ~2× in the torsion-dominated regime (90–220 RPM). Correct geometry parameter dp=1.538 (not dp=2.0) changes all LDV-derived metrics from the original implementation. This is a documented finding, not a code error.
Bending gate FAIL is accepted and documented as a characterised physical limitation (cross-axis torsion leakage at ~9.8° misalignment), not a code or processing defect.

60 RPM: VIV aerodynamic intermittency — camera/LDV ratio ~0.05×, flagged and reported separately.
320 RPM: high-wind unstable, reported separately.

---

## Step 11 — RTS Smoothing (2026-06-17) ✓ PASS (21/21)

| Gate | Target | Result |
|------|--------|--------|
| Phase shift | < 10 ms | **0.00 ms** (all 21 conditions) |
| Frequency error | 0 Hz | **0.000 Hz** |
| Amplitude ratio | 0.95–1.00 | **0.999** |

Process noise model: `Q = diag([(σ·dt)², σ²])` with `σ=10.0 mm/s`, `R=0.0025 mm²`.
The kinematic `G@G.T` formulation collapsed the Kalman gain (amplitude ratio 0.023 observed)
and was rejected. See `docs/PROJECT_CONTEXT.md` Section 0.5 for full rationale.

---

## Step 11 — RTS Smoothing defaults fix (2026-06-20)

Bug 3 resolved: `step11_rts_smoothing.py` module constants updated to match `pipeline_config.yaml`:
- `PROCESS_NOISE_STD`: 0.5 → **10.0 mm/s**
- `MEASUREMENT_NOISE_STD`: 0.1 → **0.05 mm**

Results (21/21 PASS, phase 0.00 ms, amplitude ratio 0.999) are unchanged — config values were passed as args at runtime.

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
| `fig_timeseries_overlay.png` | 562 KB | 20-second condition-matched overlay for e7_90rpm; camera 60 Hz (blue) + LDV 360 Hz (red dashed), mean-removed |

Key observations:
- Dominant frequency: both instruments agree on fn_t ≈ 3.08 Hz in torsional VIV regime; at ≤ 20 RPM, below threshold → noise peaks
- RMS ratio 1.339× in bending (stable regime; explained by torsion-coupling leakage), 0.599× in torsion (attenuation well understood)
- PSD overlay shows aligned spectral peaks; both instruments resolve fn_b and fn_t cleanly in their respective regimes
- Time-series overlay demonstrates condition-level response similarity only; it is not presented as a waveform-validation result because the recordings are separate-session and non-simultaneous

---

## Pre-Submission Pending Items (identified 2026-06-22, from context_rerun.md pipeline walkthrough)

### ~~⚠ Step 10 — stale output JSON needs re-run~~ ✓ RESOLVED (2026-06-22)

`results/step10/ldv_summary.json` and `results/step10/ldv_comparison_table.csv` were regenerated on 2026-06-22 with the e0_0rpm-derived noise floor. The JSON now includes a stable-regime block and reports bending r = 0.845 (18 stable conditions). Target values in the script are updated to r = 0.845 (bending), ratio = 1.339×. **Status:** RESOLVED.

### ⚠ Step 05 — gap-aware interpolation guard not implemented in code

`PROJECT_CONTEXT.md` Section 0.5 and this log (2026-06-16 entry) describe a locked `MAX_INTERP_GAP = 3 frames` gap-aware guard as a design decision. The actual script `src/step05_synchronize.py` has **no MAX_INTERP_GAP check** — it calls `interp1d(..., bounds_error=True)` unconditionally, silently interpolating across any gap regardless of size. The fix (add gap-length check before interpolating, write NaN for gaps > 3 frames) is documented and the threshold is derived, but the code was never patched. Since e20 is DCG-excluded before Step 05, this has no effect on current results, but the methods description claims an implemented guard that does not exist.
**Current status:** Main docs have been softened to match live code. The implementation decision still remains open if full code-method parity is desired.

### ~~⚠ Step 06 — docstring has stale alignment numbers~~ ✓ RESOLVED (2026-06-22)

`src/step06_fuse_cameras.py` docstring updated: lines 16–18 now correctly state "~2.053 mm std" and "~189× improvement". Previously quoted values from an earlier pipeline state — corrected in this audit pass.

---

## Comparison Plots v2 — Bug Fixes and Publication Figures (2026-06-22) ✓ FIXED

Investigation of Camera Peak anomaly in `src/comparison_plots_v2.py` identified and resolved two bugs.

### Bug 4 — LDV Peak non-demeaned (RESOLVED)

**Problem:** `ldv_stats()` computed LDV Peak as `max(|b_mm_raw|)` where b_mm_raw was NOT mean-subtracted, while camera peak used `max(|b - mean(b)|)`. The LDV records a small DC aerodynamic mean offset (+0.1–0.3 mm for most conditions, +1.648 mm for e20), causing the comparison to be inconsistent.

**Impact on LDV Peak values:**

| Condition | Old LDV Peak | New LDV Peak | Change |
|-----------|-------------|-------------|--------|
| e12_160rpm | 2.420 mm | 2.208 mm | −9% |
| e14_200rpm | 3.121 mm | 2.852 mm | −9% |
| e13_180rpm | 2.889 mm | 3.160 mm | +9% (was underestimated) |
| e9_110rpm  | 0.685 mm | 0.605 mm | −12% |
| e20_320rpm | 8.492 mm | 6.844 mm | −24% |

**Fix:** `ldv_stats()` now computes `b_dem = b_mm - np.mean(b_mm)` and returns `max(|b_dem|)` for both bending and torsion. Consistent with camera.

### Bug 5 — e20 camera artifact drawn as connected line (RESOLVED)

**Problem:** The e20_320rpm camera recording is entirely corrupted by the interpolation artifact (gap-filling across 39% frame dropouts): b_rms=9.843mm, b_peak=15.530mm, t_rms=11.125mm, t_peak=16.755mm. These were drawn as connected lines in the "All 20" top panels, forcing the y-axis to ~16mm (bending) and ~25mm (torsion), compressing all 19 valid conditions into the lower third of the plot.

**Fix:** `fig_A_full()` now uses `valid_cam = ~np.isnan(cam_rms) & ~(flag == "DCG_excluded")` for both Camera RMS and Camera Peak lines. The e20 camera point is drawn as isolated × markers labelled "Camera (DCG artifact)". LDV lines for e20 are retained (LDV data is genuine; the large torsion proxy peak of 25.747mm demeaned is real and is the physical reason the camera failed).

**Confirmed: Camera Peak elevation is physics, not a bug.** Camera Peak is 1.5–2.2× LDV Peak in the torsional VIV regime (90–220 RPM). Camera RMS is elevated by the same factor (same peak/rms ratios). Root cause is cross-axis leakage (torsional coupling through ~9.8° axis misalignment) documented as Bug 2 in the Step 10 entry. This is a reported finding, not something to correct.

### Updated output: `results/comparison_plots_v2/`

Six figures regenerated: figA (rpm), figB (wind speed), figC (FFT physical + normalised), figE (regime scatter), figF (time-series).

---

## LDV Geometry Verification — 2026-06-24

Triggered by handwritten image of the Tunnel B setup showing a torsion formula with a `/2` factor not present in the Python code. Full investigation conducted to verify whether the pipeline formula was correct.

**Geometry confirmed — center+side configuration:**

| Sensor | Position |
|--------|----------|
| ch1 (center) | 0 cm from deck centerline |
| ch2 (side) | 13 cm from deck centerline |

Source: setup sheet `설계속도 및 모형Setup_영상계측.xlsx`, row `센서간격 = 13 cm`.
Korean 간격 = "gap between things" → total distance from ch1 to ch2 = 13 cm.
Bridge half-chord: db = 20 cm (교폭 40 cm ÷ 2).

**Formula investigation — `/2` is wrong for center+side:**

| Formula | Correct geometry | Result for center+side (ch1=0, ch2=13 cm) |
|---------|-----------------|------------------------------------------|
| `(ch2-ch1)/2 × dp` | Symmetric ±d sensors | Halves the signal — no physical basis |
| `(ch2-ch1) × dp` | Center+side | (θ×13) × (20/13) = θ×20 ✓ |

The MATLAB source `BRID2D1_choi.m` used `(ch2-ch1)/2` with incorrect `dside=10` (wrong dp=2.0), designed for symmetric sensors. Python pipeline correctly uses no `/2` with dp=20/13=1.538.

**Scale-invariance check:** Pearson r = 0.9396 is identical for both formula variants (r is invariant to constant scaling). The ratio changes: `/2` formula → ratio = 1.197 (camera appears to overestimate LDV), implying camera marker arm ≈ 24 cm — outside the deck edge. Physically implausible. Confirms original formula is correct.

**Net result:** No code change. `/2` briefly introduced and reverted. All canonical results unchanged.

**Torsion ratio 0.599 — physical explanation derived:**
Camera torsion proxy (`y_cam3 − bending_avg`) measures differential displacement at Marker B arm ≈ 13–14 cm from deck center. LDV torsion proxy is scaled to db = 20 cm (deck half-chord). For the same angle θ: camera measures θ×13, LDV measures θ×20. Expected ratio = 13/20 ≈ 0.65. Observed: 0.599 stable mean, 0.61–0.76 in torsional VIV. Physically consistent — no correction needed.

**Bending contamination identified (center+side geometry):**
LDV bending channel = `(ch1+ch2)/2 = δ + θ×6.5` — contains torsion leakage of θ×6.5 mm. In the torsional VIV regime, this independently elevates LDV bending, contributing to the lower bending Pearson r = 0.845 (alongside the camera-side 9.8° misalignment leakage).
