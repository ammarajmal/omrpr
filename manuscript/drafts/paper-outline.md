# Paper 2 draft scaffold

Working title: Image-plane AprilTag tracking for condition-level bridge-deck
response benchmarking in wind-tunnel tests

Status: structured drafting scaffold; not author-approved prose.

## Abstract

Draft only after the results and discussion language is approved. The abstract
must describe LDV as a non-simultaneous condition-level benchmark, identify
the camera result as calibration-sensitive, use *torsion-proxy*, and keep the
320 RPM diagnostic separate from stable-regime evidence.

## 1. Introduction

1. Motivate non-contact response measurement for bridge-deck wind-tunnel
   experiments.
2. Explain the need for auditable detection, timing, fusion, and uncertainty
   controls in camera-based measurement.
3. State the contribution as a source-grounded camera pipeline and a
   condition-level comparison with a separate LDV campaign.
4. Avoid presenting LDV as ground truth or the two campaigns as synchronized.

## 2. Experimental evidence and methods

### 2.1 Facility, specimen, and campaigns

- Describe the facility as a commercial wind-tunnel facility in South Korea.
- State that the camera and LDV records are separate, non-concurrent campaigns.
- Record the 21 camera conditions from 0 to 320 RPM and the available LDV range.
- Report 320 RPM as diagnostic-only.

### 2.2 Camera acquisition and AprilTag tracking <!-- LEDGER-EXEMPT: section heading number -->

- Three cameras at a nominal 60 Hz.
- Official AprilRobotics C library v3.4.5, `tag36h11`, 20 mm tags.
- Two physical WTT markers both decode as tag ID 0: marker A is viewed by
  cam1+cam2 and marker B by cam3. Camera coverage and marker-group identity
  keep their observations separate.
- Preserve camera/marker-group identity and retain rejection reasons.

### 2.3 Observation admissibility and timing <!-- LEDGER-EXEMPT: section heading number -->

- Explain timestamp-derived FPS, gap, and stream-admissibility gates.
- Describe cross-camera alignment as timestamp-based software matching.
- Distinguish static stream review from WTT stream admissibility.

### 2.4 Calibration boundary <!-- LEDGER-EXEMPT: section heading number -->

- Image-plane displacement is the primary defensible observable.
- Metric values based on the current intrinsics are provisional and
  calibration-sensitive.
- Do not imply that legacy or laser-corrected intrinsics are fresh physical
  calibration evidence.

### 2.5 Fusion and response channels <!-- LEDGER-EXEMPT: section heading number -->

- Define bending as the average of the two marker-group channels.
- Define torsion-proxy as their difference.
- Do not call the torsion-proxy a validated torsion angle.

### 2.6 LDV preprocessing and benchmarking <!-- LEDGER-EXEMPT: section heading number -->

- Describe the Tunnel A D0-D38 source, unit normalization, and condition table.
- State explicitly that comparison is by operating condition, not synchronized
  sample-by-sample validation.
- Explain the predeclared exclusion of the 60/70/80 RPM resonance neighborhood
  from stable-trend fitting and the separate treatment of 320 RPM.

### 2.7 Frequency and uncertainty

- Use this specimen's reference frequencies: 1.43 Hz bending and 3.103 Hz
  torsion.
- Separate static precision, dynamic response, timing diagnostics, and
  calibration uncertainty.

## 3. Results

### 3.1 Detection and coverage <!-- LEDGER-EXEMPT: section heading number -->

Report 115,276 retained audit rows, including 75,404 valid detections and
39,872 invalid rows retained for traceability, across 21 conditions and three
cameras. Confirm these counts from the reviewed Step 05 artifact immediately
before submission.

### 3.2 Static precision and onset separation <!-- LEDGER-EXEMPT: section heading number -->

Use `figures/step04_static_precision_rms.png` and
`tables/step04_static_admissibility_thresholds.md`. Present the no-wind fused
baseline (0.1107 mm bending RMS; 0.1821 mm torsion-proxy RMS) as provisional.
The 60 RPM case rises to 0.3158 mm and 0.3860 mm, respectively, with a bending
PSD peak near 1.4055 Hz.

### 3.3 Condition-level camera-LDV comparison <!-- LEDGER-EXEMPT: section heading number -->

For the 16-condition stable-regime join, the reviewed summary reports fused
bending Pearson/Spearman correlations of 0.459/0.803 and torsion-proxy
correlations of 0.231/0.912. Frame these as association across independently
recorded operating conditions, not accuracy against ground truth.

### 3.4 Diagnostic regimes

- Explain 60-80 RPM as the VIV/resonance neighborhood.
- Present 320 RPM separately; it has no matching LDV condition and is not part
  of stable summaries.

## 4. Discussion

1. Interpret the strong rank association and modest linear association without
   overstating metrological agreement.
2. Discuss the 60 RPM peak relative to the 1.43 Hz bending mode.
3. Explain how static noise, stream timing, provisional intrinsics, and
   non-simultaneous campaigns limit the conclusions.
4. State what fresh physical calibration and independently resolved geometry
   would be required for absolute displacement and torsion-angle claims.

## 5. Conclusions

Keep conclusions bounded to the demonstrated image-plane tracking,
condition-level trends, onset separation, and auditable evidence chain.

## Author decisions required before full drafting

- Approve final facility-anonymization wording.
- Approve whether provisional millimetre results may appear in the abstract.
- Select the target journal and obtain its current template and word limits.
- Approve data/code availability language.
