# Claim Boundary

*Updated 2026-06-17 — matches PROJECT_CONTEXT.md Section 10 (clean reimplementation values).*

---

## What We CAN Claim

- Reproducible offline reconstruction of 21-condition WTT displacement
- Condition-level bending trend comparison against LDV reference (non-simultaneous)
- Condition-level torsion-proxy trend comparison (operator-confirmed geometry, proxy only)
- Internal camera-agreement recovery: raw ~388 mm (cam1–cam2) → aligned ~2.053 mm std (~189× improvement)
- Cam1–cam2 Y-axis misalignment: bounded, quantified — 0.038 mm at 5 mm amplitude (12.8% of RMSE); fixed bias, not random; stated as uncertainty contribution
- Static noise floor: bending 0.017 mm RMS, torsion proxy 0.033 mm RMS
- Bootstrap within-run stability: ~13–15% CI width for stable non-near-floor conditions
- Timing mitigation: 20.0 ms max pairwise drift (cam1–cam3), software common-grid only
- 60 RPM case: diagnosed as VIV aerodynamic intermittency, not camera failure
- e20_320rpm: characterized as high-wind unstable motion, reported separately

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
| high_wind_unstable_motion | measurement failure |
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
