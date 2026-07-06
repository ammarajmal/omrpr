# Claim Boundary — LOCKED GROUND TRUTH
<!-- ================================================================
     IMMUTABLE REFERENCE FILE — v2.1 (2026-07-02)
     All manuscript numbers MUST match this file exactly.
     Do NOT edit without recording a changelog entry below.
     All changes must be cross-checked against option_b_verified_table.csv.
     ================================================================ -->

*Canonical for: Option B — Tunnel A LDV 2024, camera Tunnel A October 2025*
*Locked: 2026-07-01 | Last audit: 2026-07-03*

---

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| 2026-06-23 | Initial B0 lock (r=0.845, RMSE=0.719mm, 2025 standalone LDV session) | First pipeline run |
| 2026-07-01 | **v2.0 — Option B canonical** | Switched to Tunnel A LDV 2024 (dp=2.0, dside=100mm); B0 values superseded |
| 2026-07-03 | Facility naming corrected: "Tunnel B" (2025 standalone LDV session) was a mislabel — confirmed same physical facility as Tunnel A across all sessions; 2024 dp=2.0/dside=100mm geometry independently vendor-verified | See `RESULTS_LOG.md` "2026-07-03 RESOLVED" entry |
| 2026-07-01 | DCG threshold corrected: N=3→N=2 frames | Eq.\ref{eq:dcg-threshold} used ω=π/T_h instead of the correct ω=2π/T_h (missing factor of 4 in ε); recomputed ε at g=3 frames (50ms) = 0.0317mm exceeds 0.017mm bending noise floor, forcing N≤2. Verified via frame_idx gap analysis on step02 detections.csv (all 60fps): every condition e0–e19 has max_gap=1 (zero missed frames) on all 3 cameras, so no condition reclassifies — the 18-stable-condition sample and locked Pearson/RMSE/ratio numbers below are unaffected. Only e20_320rpm (already DCG-excluded, max_gap=7 on cam1/cam2) is affected by the threshold change. |
| 2026-07-02 | 60RPM LDV bending RMS corrected: 1.766mm→0.0492mm (ratio 0.05×→1.81×); torsion columns in Per-Condition Table corrected (were mislabeled duplicates of bending-peak values, not real torsion RMS data) | The 1.766mm figure could not be traced to any raw-data computation; `scripts/option_b_verified_table.csv` (this file's own designated cross-check source) and `docs/option_B_guide.md` (explicit raw-D-file computation, cross-verified against `ldv_processed_summary.csv`) both give LDV bend RMS = 0.0492mm at 60RPM. Recomputing aggregate bending stats with 60RPM's corrected value shows it is not an outlier (r=0.9577→0.9598, RMSE=0.3009→0.2930mm when included), so 60RPM is no longer excluded from stable-regime statistics: 18→19 stable conditions. All aggregate bending/torsion numbers below, the Per-Condition Table, and the cam-bias percentage (12.6%→13.0%, since it is a fraction of RMSE) are updated accordingly. The "60 RPM VIV aerodynamic intermittency" claim is removed — the numeric basis for that diagnosis no longer exists. |
| 2026-07-03 | Bootstrap CI mean relative width corrected: bending 13.3%→14.3%, torsion proxy 15.0%→16.3% (both stable non-near-floor, n=18) | `omrpr_fin/src/step09_uncertainty.py` still hardcoded `e4_60rpm` as an excluded "VIV" condition in its own `stable_conditions` list and bootstrap summary filter, independently of the 2026-07-02 LDV-side correction above — found while wiring Fig. 5 (uncertainty) into the manuscript. Fixed to include 60RPM as a normal stable condition and rerun; recomputed over `results/step09/bootstrap_ci/bootstrap_ci_per_condition.csv` (stable & non-near-floor, n=18: 19 stable minus e1_20rpm near-floor). Also found and fixed the same hardcoded exclusion, plus a wrong LDV dataset/geometry (2025 standalone session, dside=130mm/dp=1.538) and a wrong bending formula ([cam1+cam2]/2 only, not the cross-bridge [[cam1+cam2]/2+cam3]/2 average behind the locked r=0.960), in `step07_motion_decompose.py` and `step10_ldv_comparison.py` — see those files' docstrings for the full fix. Bending/torsion r, RMSE, MAE, and ratio in this file are unaffected (independently re-verified against `option_b_verified_table.csv` after the fix, matching to 4 decimal places); only the bootstrap CI-width statistic changes. |
| 2026-07-03 | Noise floor corrected: 0.017/0.033mm → 0.004/0.005mm (bending/torsion, e0_0rpm full-pipeline RMS); DCG threshold correspondingly corrected: N≤2 → N≤1 frame | 0.017/0.033mm was a pre-2026-06-20-intrinsics-fix value that had never propagated into manuscript-facing text (abstract, Methods, Results, this file), despite `step09_uncertainty.py` computing and gate-checking against the corrected ~0.003-0.005mm value ever since. Confirmed via `config/pipeline_config.yaml`'s fx values (20327.9/25749.5/25630.9) matching the documented post-fix intrinsics, `noise_floor_summary.json`'s reprojection error (0.035-0.17px, in the documented correct range), and a fresh `results/step07/e0_0rpm/summary.json` recomputation (0.0038/0.0052mm) after today's step07 formula fix. Re-derived the DCG interpolation-error threshold (Eq. dcg-threshold, ε=A/8·(2πg/T_h)²) against the corrected noise floor: ε(g=1 frame)=0.0035mm < 0.004mm (safe), ε(g=2 frames)=0.0141mm > 0.004mm (unsafe) — threshold is N≤1, not N≤2. Verified via `results/step02/*/summary.json` max_consecutive_miss values that this changes NO reported result: all 20 non-e20_320rpm conditions have max_consecutive_miss=0 (zero missed frames) on every camera, so the N=1-vs-N=2 threshold choice has no practical effect on DCG pass/fail or the 19-stable-condition sample. Updated: abstract.tex, 01_introduction.tex (Contribution 2), 02_methods.tex (Eq. dcg + Eq. dcg-threshold derivation), 04_results.tex (noise floor values, Table 1 caption, Frequency section), 07_conclusion.tex. |
| 2026-07-03 | Removed retired "torsion coupling y_leak ≈ 0.170α" bending-ratio explanation from "What We CAN Claim" | That mechanism was derived to defend the retired B0-era bending result (r=0.845) and was never updated after the Option B switch, even though Discussion Sec. 5.2 and the manuscript figures already use a different, correct 3-factor explanation (non-simultaneity, spatial-averaging geometry, residual timing). The two documents had silently drifted apart. The still-valid, separate 0.038mm/13.0%/9.8° fixed-bias claim (Limitations Sec. 6.6) is retained unchanged. |

---

## What We CAN Claim

- Reproducible offline reconstruction of 21-condition WTT displacement
- Condition-level bending trend comparison against LDV reference (same-tunnel non-simultaneous comparison in Tunnel A; separate sessions ≈11 months apart — camera bags October 2025; LDV October–November 2024)
- Condition-level torsion-proxy trend comparison (operator-confirmed geometry, proxy only)
- Internal camera-agreement recovery: raw ~388 mm (cam1–cam2) → aligned ~2.053 mm std (~189× improvement)
- Cam1–cam2 Y-axis misalignment: a bounded, amplitude-dependent fixed bias of 0.038 mm at 5 mm
  amplitude (13.0% of LDV RMSE 0.293 mm), derived from the ≈9.8° inter-camera rotation measured
  from the extrinsic calibration (Limitations Sec. 6.6). Stated as one bounded uncertainty
  contribution among several — see the bending-ratio explanation below.
- Bending cam/LDV over-read (≈1.261×, stable mean): explained by three documented,
  non-exclusive factors (Discussion Sec. 5.2) — non-simultaneous acquisition (≈11 months
  apart), point-vs-spatial-averaging geometry (LDV single point vs. camera cross-bridge
  average), and residual software timing uncertainty (≤20.03 ms max pairwise drift).
  REMOVED 2026-07-03: the earlier "torsion coupling y_leak ≈ 0.170α, ~2× bending-ratio
  inflation in the torsion regime" explanation was derived to defend the retired B0-era
  bending result (r=0.845) and does not transfer to Option B's different dataset pairing
  or its already-passing r=0.960 — do not reintroduce it (see FINALIZATION_PLAN.md Phase 4).
- Noise floor (preferred, e0_0rpm full pipeline): bending 0.004 mm RMS, torsion proxy 0.005 mm RMS
  (corrected 2026-07-03 — see changelog; previously stated as 0.017/0.033 mm, a stale pre-intrinsics-fix
  value that had never propagated into manuscript-facing text despite the pipeline computing correctly)
- 60 RPM: low-amplitude stable condition (cam bending RMS 0.089 mm, ≈22x the noise floor — not
  near-floor by either the old or corrected noise-floor value), included in the 19-condition
  stable-regime statistics after LDV value correction (2026-07-02); no longer treated as an anomaly.
- Static noise floor (static bags): bending ≈0.003 mm RMS, torsion proxy ≈0.005 mm RMS — derived
  from static bags with correct camera intrinsics (fx from pipeline_config.yaml; reproj error
  0.04–0.17 px); consistent with the e0_0rpm full-pipeline value above (corrected 2026-07-03)
- Bootstrap within-run stability: bending 14.3% mean relative CI width, torsion proxy 16.3%
  (stable non-near-floor conditions, n=18; corrected 2026-07-03 — see changelog)
- Timing mitigation: 20.03 ms max pairwise drift (cam1–cam3), software common-grid only
- e20_320rpm cam1/cam2: DCG-excluded — motion blur at equilibrium crossing, proven by FFT at
  2×f_struct = 5.87 Hz, pixel velocity v_peak = 67.8 px/frame > blur threshold w_cell = 29 px/frame,
  and equilibrium clustering (93.4% of misses at equilibrium). This is a physical, diagnosable
  failure — not a pipeline deficiency.
- e20_320rpm cam3: clean amplitude 2.19 mm (pixel velocity 18.7 px/frame, below blur threshold).
  Reported as a separate pre-flutter trend data point, clearly labelled "cam3 only (cam1/cam2 DCG-excluded)"
- Motion blur physical diagnosis: four independent lines of evidence (FFT, pixel velocity, Laplacian
  sharpness, boundary analysis). Publishable diagnostic work.
- DCG formal criterion: r_det ≥ 0.95 AND n_miss_max ≤ 1 AND v_peak < w_cell, designed for
  step02b and used as the analytical exclusion rule in the current writeup (threshold
  corrected 2026-07-03 from N≤2 to N≤1, see changelog).
  The n_miss_max threshold is derived from ε = A(2πg/T_h)²/8; the velocity criterion is derived from
  tag geometry. Neither threshold is empirically chosen to match e20.
- Sinusoidal interpolation error bound: ε = A(2πg/T_h)²/8. N=1 frame guard derived from noise floor
  criterion at T_h = 0.698 s, A = 1.25 mm (g=1 frame/16.7ms → ε=0.0035mm safe; g=2 frames/33ms →
  ε=0.0141mm exceeds the corrected 0.004mm floor, forcing N≤1). Novel formula not previously
  published in SHM literature. (Corrected 2026-07-03: this passage previously read N=2/0.017mm,
  matching the pre-noise-floor-correction threshold; see changelog for the full derivation.)
- Future hardware recommendation (Discussion section only): t_exp < w_cell / v_peak = 7.1 ms
  for Sony RX10 IV at 320 RPM. Novel quantitative design criterion derived from the physics.
- LDV geometry (Tunnel A 2024): pvolt=2.7 cm/V, dside=100 mm, dp=2.0, fs=360 Hz

## What We CANNOT Claim

- LDV-equivalent absolute displacement accuracy
- Same-run waveform validation against LDV
- True torsion angle measurement
- Hardware-synchronized multi-camera capture
- Modal validation (restrict to response characterization only)
- KLT or B2 robustness improvement
- Any MCI-supported improvement
- C1/C2 stereo fusion validity (coordinate orientation mismatch unresolved)

## Required Language

| Use | Never Use |
|-----|-----------|
| condition-level LDV trend comparison | LDV-validated accuracy |
| offline common-grid reconstruction | waveform-level validation from a concurrent recording |
| software/offline synchronization mitigation | hardware-synchronized / hardware-triggered |
| two-point differential displacement proxy | torsion angle / validated torsion |
| DCG-excluded (with stated physical reason) | measurement failure / silently omitted |
| near-flutter / pre-flutter condition | high-wind failure |
| cam3 clean amplitude 2.19 mm (cam1/cam2 DCG-excluded) | e20 bending result |
| internal camera-agreement uncertainty | absolute accuracy |
| commercial aerodynamic testing facility in South Korea (no citation) | facility name / any city name / [Lee2016] (identifies TESolution via author affiliation) |
| same-tunnel (Tunnel A) non-simultaneous comparison | "different tunnel"/"Tunnel B" for the 2025 standalone LDV session (mislabel, corrected), or simultaneous |

## Validated Numbers — LOCKED (Option B Canonical, Tunnel A LDV 2024)

> **Cross-check source:** `scripts/option_b_verified_table.csv`
> These values must not be changed without updating the changelog and re-verifying the CSV.

| Metric | Exact Value | Report As |
|--------|-------------|-----------|
| Bending Pearson r (stable, 19 cond.) | 0.9598 | ≈0.960 |
| Bending Spearman ρ (stable) | 0.9439 | 0.944 |
| Bending RMSE (stable) | 0.2930 mm | ≈0.293 mm |
| Bending MAE (stable) | 0.2213 mm | ≈0.221 mm |
| Bending mean ratio camera/LDV (stable) | 1.2609× | ≈1.261× |
| Torsion proxy Pearson r (stable) | 0.9676 | ≈0.968 |
| Torsion proxy mean ratio camera/LDV (stable) | 0.7853× | ≈0.785× |
| LDV geometry | 2024 paired session (Tunnel A facility), pvolt=2.7 cm/V, dside=100mm, dp=2.0 | — |
| Cam bias (13.0% of RMSE) | 0.038mm / 0.293mm | 13.0% |

Geometry vendor-verified 2026-07-03 via TESolution's own `BRID2D1_choi.m` (Ver 2.1, 2024.11.11) and
`Displacement Measurement System_V2.pdf` — see `RESULTS_LOG.md` "2026-07-03 RESOLVED" entry for the
full provenance chain.

**Note on torsion Spearman/MAE/RMSE:** Not reported in manuscript — proxy comparison only.
Pearson r and mean ratio are the only aggregate torsion metrics in the paper.

**Superseded B0 values** (2025 standalone LDV session, same Tunnel A facility — different session
with a repositioned sensor rig, NOT a different tunnel; dp=1.538, dside=130mm — DO NOT USE IN MANUSCRIPT):

| Metric | B0 Value |
|--------|----------|
| Bending r | 0.845 |
| Bending RMSE | 0.719 mm |
| Bending mean ratio | 1.339× |
| Torsion r | 0.940 |
| Torsion ratio | 0.599× |

---

## Recording Context (Canonical, facility naming corrected 2026-07-03)

Camera bags and LDV data were both recorded in **Tunnel A** at the same facility. The 2025 standalone
LDV session (superseded B0 above) was also recorded at this same facility — earlier "Tunnel B" naming
for that session was a mislabel (see `RESULTS_LOG.md` 2026-07-03 entry); there is only one physical
wind tunnel facility across all 2024/2025 sessions.
- LDV: October–November 2024 (Tunnel A)
- Camera: October 2025 (Tunnel A)
- Gap: ≈11 months — **NOT simultaneous**
- Comparison protocol: condition-level RMS, peak, and dominant frequency per RPM condition
- This is the maximum defensible evidence given the acquisition strategy.

Required phrase: "same-tunnel (Tunnel A), condition-matched, separate recording sessions (≈11 months apart)"
Banned phrases: all invalid comparison terms listed in Required Language table above

---

## Per-Condition Table (Locked — from option_b_verified_table.csv)

Wind speed formula: U = RPM × 0.01845 − 0.26077 (m/s)

| RPM | Wind (m/s) | Cam Bend RMS | LDV Bend RMS | Bend Ratio | Cam Tors RMS | LDV Tors RMS | Tors Ratio |
|-----|------------|--------------|--------------|------------|--------------|--------------|------------|
| 20  | 0.11 | 0.018 | 0.027 | 0.67× | 0.034 | 0.107 | 0.32× |
| 40  | 0.48 | 0.015 | 0.027 | 0.55× | 0.029 | 0.108 | 0.27× |
| 50  | 0.66 | 0.034 | 0.030 | 1.13× | 0.037 | 0.107 | 0.34× |
| 60  | 0.85 | 0.089 | 0.049 | 1.81× | 0.040 | 0.110 | 0.36× |
| 70  | 1.02 | 3.111 | 2.758 | 1.13× | 0.146 | 0.224 | 0.65× |
| 80  | 1.21 | 1.371 | 1.477 | 0.93× | 0.137 | 0.272 | 0.50× |
| 90  | 1.40 | 0.813 | 0.581 | 1.40× | 1.611 | 2.156 | 0.75× |
| 100 | 1.58 | 0.174 | 0.315 | 0.55× | 0.220 | 1.194 | 0.18× |
| 110 | 1.77 | 0.161 | 0.169 | 0.96× | 0.087 | 0.128 | 0.68× |
| 120 | 1.95 | 0.192 | 0.134 | 1.44× | 0.167 | 0.127 | 1.31× |
| 140 | 2.32 | 0.752 | 0.360 | 2.09× | 1.340 | 1.128 | 1.19× |
| 160 | 2.69 | 1.243 | 0.739 | 1.68× | 2.267 | 2.638 | 0.86× |
| 180 | 3.06 | 1.466 | 0.958 | 1.53× | 2.690 | 3.669 | 0.73× |
| 200 | 3.43 | 1.510 | 0.939 | 1.61× | 2.804 | 3.906 | 0.72× |
| 220 | 3.80 | 1.178 | 0.719 | 1.64× | 2.002 | 3.010 | 0.67× |
| 240 | 4.17 | 0.688 | 0.756 | 0.91× | 0.431 | 0.281 | 1.54× |
| 260 | 4.54 | 0.804 | 0.676 | 1.19× | 0.483 | 0.333 | 1.45× |
| 280 | 4.91 | 1.039 | 0.786 | 1.32× | 0.660 | 0.429 | 1.54× |
| 300 | 5.27 | 1.203 | 0.847 | 1.42× | 0.700 | 0.814 | 0.86× |
| 320* | 5.65 | — | — | — | — | — | — |

*320 RPM: cam1/cam2 DCG-excluded; cam3 only amplitude = 2.19 mm reported as pre-flutter trend point.
