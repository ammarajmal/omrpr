# Claim Boundary

*Updated 2026-06-23 — aligned with PROJECT_CONTEXT.md Section 10 and current repo state. Includes e20 DCG exclusion, motion blur diagnosis, and interpolation-error-bound claims with Step 05 implementation status clarified.*
*Updated 2026-07-01 — DCG threshold corrected N=3→N=2 (interpolation error formula had a factor-of-4 bug: ω=π/T_h instead of ω=2π/T_h). Verified via step02 detections.csv frame_idx gap analysis that no condition other than e20_320rpm has any consecutive-miss gap at all (max_gap=1 for e0–e19), so the 18-stable-condition sample is unaffected.*

---

## What We CAN Claim

- Reproducible offline reconstruction of 21-condition WTT displacement
- Condition-level bending trend comparison against LDV reference (same-tunnel non-simultaneous comparison in Tunnel A; separate sessions ≈11 months apart — camera bags October 2025; LDV October–November 2024)
- Condition-level torsion-proxy trend comparison (operator-confirmed geometry, proxy only)
- Internal camera-agreement recovery: raw ~388 mm (cam1–cam2) → aligned ~2.053 mm std (~189× improvement)
- Cam1–cam2 Y-axis misalignment: two bounded documented effects — (1) averaging bias 0.038 mm
  at 5 mm amplitude (12.6% of LDV RMSE 0.301 mm), fixed bias; (2) torsion coupling y_leak ≈ 0.170α
  explains ~2× bending ratio in torsion-dominated regime. Both stated as uncertainty contributions.
- Noise floor (preferred, e0_0rpm full pipeline): bending 0.017 mm RMS, torsion proxy 0.033 mm RMS
- Static noise floor (static bags): bending 0.017 mm RMS, torsion proxy 0.033 mm RMS — derived from static bags with correct camera intrinsics (fx from pipeline_config.yaml; reproj error 0.04–0.17 px)
- Bootstrap within-run stability: ~13–15% CI width for stable non-near-floor conditions
- Timing mitigation: 20.03 ms max pairwise drift (cam1–cam3), software common-grid only
- 60 RPM case: diagnosed as VIV aerodynamic intermittency, not camera failure
- e20_320rpm cam1/cam2: DCG-excluded — motion blur at equilibrium crossing, proven by FFT at
  2×f_struct = 5.87 Hz, pixel velocity v_peak = 67.8 px/frame > blur threshold w_cell = 29 px/frame,
  and equilibrium clustering (93.4% of misses at equilibrium). This is a physical, diagnosable
  failure — not a pipeline deficiency.
- e20_320rpm cam3: clean amplitude 2.19 mm (pixel velocity 18.7 px/frame, below blur threshold).
  Reported as a separate pre-flutter trend data point, clearly labelled "cam3 only (cam1/cam2 DCG-excluded)"
- Motion blur physical diagnosis: four independent lines of evidence (FFT, pixel velocity, Laplacian
  sharpness, boundary analysis). Publishable diagnostic work. See docs/e20_outlier_analysis.md.
- DCG formal criterion: r_det ≥ 0.95 AND n_miss_max ≤ 2 AND v_peak < w_cell, designed for
  step02b and used as the analytical exclusion rule in the current writeup.
  The n_miss_max threshold is derived from ε = A(2πg/T_h)²/8; the velocity criterion is derived from
  tag geometry. Neither threshold is empirically chosen to match e20.
- Sinusoidal interpolation error bound: ε = A(2πg/T_h)²/8. N=2 frame guard derived from noise floor
  criterion at T_h = 0.698 s, A = 1.25 mm (g=2 frames/33ms → ε=0.0141mm safe; g=3 frames/50ms →
  ε=0.0317mm exceeds 0.017mm floor; corrected 2026-07-01 — original formula used ω=π/T_h,
  missing factor of 4 in ε). This currently supports the documented/proposed
  Step 05 guard rather than an implemented live-code guard. Novel formula not previously
  published in SHM literature.
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
| commercial aerodynamic testing facility in South Korea [Lee2016] | facility name / any city name |
| same-tunnel non-simultaneous comparison | invalid comparison wording |

## Validated Numbers (Locked) — Option B Canonical (Tunnel A LDV 2024)

These are the confirmed Option B values using Tunnel A LDV 2024 geometry (dp=2.0, dside=100mm).

| Metric | Value |
|--------|-------|
| Bending Pearson r (stable, 18 cond.) | 0.9577 (report ≈0.958) |
| Bending Spearman ρ (stable) | 0.9340 (report 0.934) |
| Bending RMSE (stable) | 0.3009 mm (report ≈0.301 mm) |
| Bending MAE (stable) | 0.2314 mm (report ≈0.232 mm) |
| Bending mean ratio camera/LDV (stable) | 1.2302× (report ≈1.230×) |
| Torsion proxy Pearson r (stable) | 0.9665 (report ≈0.967) |
| Torsion proxy mean ratio camera/LDV (stable) | 0.809× (camera underestimates torsion) |
| LDV geometry | Tunnel A 2024, pvolt=2.7 cm/V, dside=100mm, dp=2.0 |

**Superseded B0 values** (Tunnel B 2025 LDV, dp=1.538, dside=130mm — DO NOT USE):
r=0.845, RMSE=0.719mm, ratio=1.339×, torsion r=0.940, torsion ratio=0.599×

---
## Recording Context (Canonical — 2026-07-01)

Camera bags and LDV data were both recorded in **Tunnel A** at the same facility.
- LDV: October–November 2024 (Tunnel A)
- Camera: October 2025 (Tunnel A)
- Gap: ≈11 months — **NOT simultaneous**
- Comparison protocol: condition-level RMS, peak, and dominant frequency per RPM condition
- This is the maximum defensible evidence given the acquisition strategy.

Required phrase: "same-tunnel (Tunnel A), condition-matched, separate recording sessions (11 months apart)"
Banned phrases: invalid comparison terms listed above
