# Claim Boundary

*Updated 2026-06-19 — matches PROJECT_CONTEXT.md Section 10. Added e20 DCG exclusion, motion blur diagnosis, and interpolation error bound claims.*

---

## What We CAN Claim

- Reproducible offline reconstruction of 21-condition WTT displacement
- Condition-level bending trend comparison against LDV reference (simultaneous same-tunnel recording; condition-level due to 60 Hz vs 360 Hz sampling rate difference)
- Condition-level torsion-proxy trend comparison (operator-confirmed geometry, proxy only)
- Internal camera-agreement recovery: raw ~388 mm (cam1–cam2) → aligned ~2.053 mm std (~189× improvement)
- Cam1–cam2 Y-axis misalignment: two bounded documented effects — (1) averaging bias 0.038 mm
  at 5 mm amplitude (5.3% of LDV RMSE 0.719 mm), fixed bias; (2) torsion coupling y_leak ≈ 0.170α
  explains ~2× bending ratio in torsion-dominated regime. Both stated as uncertainty contributions.
- Static noise floor: bending 0.003 mm RMS (worst-case 0.005 mm), torsion proxy 0.005 mm RMS — derived from static bags with correct camera intrinsics (fx from pipeline_config.yaml; reproj error 0.04–0.17 px)
- Bootstrap within-run stability: ~13–15% CI width for stable non-near-floor conditions
- Timing mitigation: 20.0 ms max pairwise drift (cam1–cam3), software common-grid only
- 60 RPM case: diagnosed as VIV aerodynamic intermittency, not camera failure
- e20_320rpm cam1/cam2: DCG-excluded — motion blur at equilibrium crossing, proven by FFT at
  2×f_struct = 5.87 Hz, pixel velocity v_peak = 67.8 px/frame > blur threshold w_cell = 29 px/frame,
  and equilibrium clustering (93.4% of misses at equilibrium). This is a physical, diagnosable
  failure — not a pipeline deficiency.
- e20_320rpm cam3: clean amplitude 2.19 mm (pixel velocity 18.7 px/frame, below blur threshold).
  Reported as a separate pre-flutter trend data point, clearly labelled "cam3 only (cam1/cam2 DCG-excluded)"
- Motion blur physical diagnosis: four independent lines of evidence (FFT, pixel velocity, Laplacian
  sharpness, boundary analysis). Publishable diagnostic work. See docs/e20_outlier_analysis.md.
- DCG formal criterion: r_det ≥ 0.95 AND n_miss_max ≤ 5 AND v_peak < w_cell, applied at step02b.
  The n_miss_max threshold is derived from ε = A(πg/T_h)²/8; the velocity criterion is derived from
  tag geometry. Neither threshold is empirically chosen to match e20.
- Sinusoidal interpolation error bound: ε = A(πg/T_h)²/8. N=3 frame guard derived from noise floor
  criterion at T_h = 0.700 s, A = 1.25 mm. Novel formula not previously published in SHM literature.
- Future hardware recommendation (Discussion section only): t_exp < w_cell / v_peak = 7.1 ms
  for Sony RX10 IV at 320 RPM. Novel quantitative design criterion derived from the physics.

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
| offline common-grid reconstruction | same-run waveform validation |
| software/offline synchronization mitigation | hardware-synchronized / hardware-triggered |
| two-point differential displacement proxy | torsion angle / validated torsion |
| DCG-excluded (with stated physical reason) | measurement failure / silently omitted |
| near-flutter / pre-flutter condition | high-wind failure |
| cam3 clean amplitude 2.19 mm (cam1/cam2 DCG-excluded) | e20 bending result |
| internal camera-agreement uncertainty | absolute accuracy |
| commercial aerodynamic testing facility in South Korea [Lee2016] | TESolution / any city name |

## Validated Numbers (Locked)

These are the correct values from the clean reimplementation. The old values from the
previous guideline (r ≈ 0.959 bending, ratio ≈ 1.268×) were computed against incorrectly
scaled LDV values (dp=2.0, dside=10 cm) and must not be used.

| Metric | Value |
|--------|-------|
| Bending Pearson r (stable, 18 cond.) | 0.845 |
| Bending Spearman ρ (stable) | 0.864 |
| Bending MAE (stable) | 0.484 mm |
| Bending RMSE (stable) | 0.719 mm |
| Bending mean ratio camera/LDV (stable) | 1.339× |
| Torsion proxy Pearson r (stable) | 0.940 |
| Torsion proxy Spearman ρ (stable) | 0.928 |
| Torsion proxy MAE (stable) | 0.549 mm |
| Torsion proxy RMSE (stable) | 0.771 mm |
| Torsion proxy mean ratio camera/LDV (stable) | 0.599× |
