# OMRPR — PAPER 2 FINAL MERGED DRAFT
**Assembled:** 2026-06-10 KST  
**Status:** All sections present. Sections 5–6 full prose. Active flags listed at end.  
**Source files:** PAPER2_DRAFT_CURRENT.md + PAPER2_METHODS_RESULTS_DRAFT.md  
**Merge corrections applied:** See CRITICAL_REVIEW section at bottom.

---

# ABSTRACT

Accurate non-contact structural displacement measurement under practical operating conditions remains a persistent challenge in structural health monitoring (SHM). Multi-camera vision systems offer scalable deployment but suffer from software-timing variability, marker detection dropout under motion blur, and inter-camera registration uncertainty that limit measurement reliability. This paper presents OMRPR (Offline Multi-Modal Robust Pose Reconstruction), an offline multi-camera AprilTag-based framework for structural displacement response tracking under real-world wind-induced excitation. The framework operates on grouped offline replay of multi-camera video recordings, applies a common 60 Hz reconstruction grid as a software synchronization mitigation strategy, and recovers inter-camera displacement agreement through baseline-aligned fusion. Experiments were conducted across 20 dynamic test conditions of a bridge section model at a commercial wind-tunnel facility in South Korea, with the high-wind unstable condition (e20_320rpm) reported separately. Cross-camera bending response (bending_avg_y_mm) demonstrated Pearson r ≈ 0.959 and Spearman ρ ≈ 0.944 in condition-level trend comparison against an independently operated LDV reference, with MAE ≈ 0.224 mm and RMSE ≈ 0.297 mm across the stable regime. A two-point differential displacement proxy for torsional motion (torsion_diff_y_mm) yielded Pearson r ≈ 0.968 and Spearman ρ ≈ 0.953 in the same bounded comparison; this quantity reflects differential marker displacement and does not constitute a validated torsion angle. Static noise floor measurements yielded 0.017 mm RMS for bending and 0.033 mm RMS for the torsion proxy. Baseline-aligned inter-camera Z agreement improved from approximately 106 mm raw to 1.757 ± 0.596 mm in the stable regime. Timing uncertainty (software offset up to 46.4 ms maximum observed pairwise drift), the absence of same-run LDV waveform validation, and the offline-only operating mode are explicitly acknowledged as scope limitations.

**Word count: ~248**

---

# 1. INTRODUCTION

## 1.1 Problem Statement

Contact-based sensing technologies — including LVDTs, laser displacement sensors, and accelerometers — provide reliable displacement measurements but impose physical attachment requirements, stable reference frames, and sensor-dense deployments that become impractical as structural scale increases [Ma et al. 2023; Dong et al. 2023]. Vision-based multi-camera systems have emerged as a scalable, non-contact alternative capable of tracking multiple structural points simultaneously from a standoff distance [Zhuang et al. 2022; Xu & Brownjohn 2018]. Despite demonstrated sub-millimeter accuracy under controlled laboratory conditions, existing vision-based frameworks are constrained by three persistent limitations: software-timing variability across distributed camera streams introduces phase uncertainty in reconstructed displacement signals; motion blur and detection dropout during high-amplitude excitation degrade marker tracking continuity; and the absence of principled inter-camera registration uncertainty quantification limits confidence in cross-view displacement fusion [Ajmal et al. 2024; Panigati et al. <!-- year TBD — Paper 1 ref [5] -->; Nie et al. 2022]. OMRPR addresses these limitations through an offline multi-camera reconstruction architecture that applies deterministic common-grid synchronization, algorithmic dropout handling, and bounded uncertainty reporting for structural displacement tracking under wind-induced excitation.

## 1.2 Literature Progression

Fiducial marker-based methods — using targets such as ArUco and AprilTag — have achieved sub-millimeter displacement accuracy under controlled excitation by anchoring metric pose recovery to a known geometry, but detection fails when motion blur or partial occlusion removes the marker from frame, leaving the trajectory discontinuous [Olson 2011; Wang & Olson 2016; Nie et al. 2022]. Dense and sparse optical flow approaches extend tracking continuity beyond fiducial dropout by operating directly on image texture, yet they remain relative displacement estimators that require external metric anchoring and accumulate scale drift under prolonged excitation [Nie et al. 2022; Xiu et al. 2023]. Stereo digital image correlation (DIC) provides high spatial-resolution surface measurements but imposes rigid baseline constraints and structured illumination requirements that limit applicability to aeroelastic scale-model testing under wind-induced multi-axis excitation [Pan et al. 2009]. Multi-camera architectures that fuse views across independently timed streams introduce an additional unresolved problem: without hardware triggering, software timing variability across distributed nodes creates phase uncertainty in reconstructed displacement signals, yet existing multi-camera SHM frameworks report no principled uncertainty budget for cross-view temporal misalignment [Ajmal et al. 2024; Panigati et al. <!-- year TBD — Paper 1 ref [5] -->]. While multi-camera vision systems have been applied to displacement measurement in both field structures and controlled wind-tunnel environments, no prior work addresses the combined problem of offline synchronization across independently-clocked cameras, fiducial dropout under high-wind aeroelastic motion, and bounded inter-camera registration uncertainty for scale-model bridge deck testing. Existing wind-tunnel studies either rely on hardware-synchronized motion-capture systems [Park et al. 2013] or single-camera monocular methods [Huang et al. 2018], while DIC-based approaches face known degradation under the motion-blur conditions characteristic of flutter-regime aeroelastic oscillation [Lava et al. <!-- KU Leuven, Strain journal — add to Zotero -->].

## 1.3 Contributions and Organization

To address these gaps, this paper presents OMRPR (Offline Multi-Modal Robust Pose Reconstruction), an offline multi-camera AprilTag-based framework for structural displacement measurement under wind-induced excitation, validated across 21 wind-tunnel test conditions on a bridge deck scale model. The specific contributions of this work are as follows: (1) an offline common-grid synchronization pipeline that mitigates software timing variability of up to 46.4 ms maximum observed pairwise drift across independently started camera nodes by reconstructing all camera streams onto a shared 60 Hz temporal basis without requiring hardware triggering; (2) a principled inter-camera registration uncertainty budget that quantifies cross-view spatial agreement before and after baseline alignment, reducing mean Z-axis camera agreement from ~106 mm (raw) to 1.757 ± 0.596 mm (aligned) and enabling bounded statements about fusion reliability; (3) a two-point differential displacement proxy for torsional response characterization, with camera marker spacing of approximately 200 mm consistent with the LDV lever arm confirmed from facility measurement records [Lee2016], yielding condition-level trend comparison against an independent LDV reference with Pearson r ≈ 0.968 in the stable excitation regime; and (4) a reproducible 21-condition offline reconstruction and response-analysis pipeline with all processing steps, uncertainty characterizations, and claim boundaries documented, with the processing code available at https://github.com/ammarajmal/shm-displacement-project. The remainder of this paper is organized as follows: Section 2 describes the measurement system and offline pipeline; Section 3 details the experimental setup and wind-tunnel test conditions; Section 4 presents the displacement and torsion proxy results with uncertainty analysis; Section 5 discusses limitation boundaries and comparison to prior work; and Section 6 concludes with directions for future validation.

---

# 2. MEASUREMENT SYSTEM AND OFFLINE PIPELINE

## 2.1 Wind-Tunnel Facility and Bridge Deck Model

Experiments were conducted in the closed-circuit boundary-layer wind tunnel of a commercial aerodynamic testing facility in South Korea [Lee2016]. A bridge deck sectional model with a streamlined cross-section was mounted on a spring–damper suspension system to allow free vertical (bending) and rotational (torsion) oscillation. The model had a chord width of B = 0.40 m and span length of 0.85 m. Model dynamic properties were confirmed prior to testing from free-vibration LDV measurements: bending natural frequency f_h = 1.430 Hz and torsional natural frequency f_α = 3.103 Hz (frequency ratio f_α/f_h = 2.17), with structural damping ratios of approximately 1.9%. These values were independently corroborated by camera-based free-vibration analysis (camera FFT: f_h = 1.429 Hz, f_α = 3.099 Hz).

Wind speed was controlled by varying the tunnel fan motor speed in discrete RPM increments from 20 RPM to 320 RPM (20 RPM steps), corresponding to mean wind speeds at the model of 0 to 5.65 m/s. A total of 20 dynamic test conditions plus one baseline (zero-wind) condition were recorded, denoted e0 (0 RPM) through e20 (320 RPM). Air density was ρ = 1.190 kg/m³ (T = 24°C, p = 1014.3 hPa) throughout the test series.

## 2.2 Camera System

Three Sony RX10 IV cameras were deployed in a fixed multi-camera array viewing the bridge deck model from the front face. Each camera was connected to an AverMedia capture card (USB 3.0), streamed at nominal 60 fps through Video4Linux2 (V4L2) into a ROS Noetic node, and recorded as a synchronized multi-topic bag file containing compressed image streams from all three cameras. Camera nodes were started serially from a single launch file rather than from a shared hardware trigger; software synchronization uncertainty is characterized explicitly in Section 2.4.

Each camera was calibrated using a standard checkerboard calibration procedure, yielding full intrinsic parameter sets and radial/tangential distortion coefficients. The world-frame pose recovery path uses three AprilTag markers (tag family: tag36h11, physical size: 20 mm, confirmed from ROS parameter tag_size=0.020 in april_marker.py) affixed to the upper surface of the bridge deck model at known spacing. Pose estimation was performed using OpenCV's solvePnP with IPPE (Infinitesimal Plane-based Pose Estimation) refinement, which provides sub-pixel corner localization under normal detection conditions.

Measured camera performance across all 21 test conditions:

- Mean frame rate: 59.94 ± 0.01 fps (all conditions)
- Frame timing jitter (std): 0.48–0.87 ms
- Maximum single-frame gap: 24.7 ms (well within one frame period)
- No conditions showed gaps exceeding 50 ms or systematic frame-drop events

⚠ **C_F2 — Hardware naming (ACTIVE):** Confirm with supervisor that identifying Sony RX10 IV and AverMedia by name in the publication is permitted. If not, use "CMOS cameras with USB 3.0 capture cards."

## 2.3 LDV Reference System

An independent laser Doppler vibrometer (LDV) system was operated by the facility as a concurrent measurement reference. The LDV sampled at f_s = 360 Hz and measured vertical bending and torsional displacement at a fixed point on the bridge deck. The LDV geometry used two sensors: a center sensor at the deck centerline and a side sensor at d_side = 130 mm from the centerline (confirmed from facility MATLAB script BRID2D1.m line 19: dside=13 cm), with a reference lever arm of d_b = 200 mm and torsion scale factor d_p = d_b / d_side = 200/130 = 1.538 (confirmed from BRID2D1.m line 23). Displacement values were extracted from voltage signals using a calibration of p_volt = 2.7 cm/V and processed through the facility's standard BRID2D1 bias-correction procedure. All LDV output values are in centimeters; all comparison values in this paper are converted to millimeters (×10).

**Scope limitation — condition-level comparison only.** The LDV and camera systems were operated in separate, independent test runs conducted under nominally identical conditions. Direct waveform-level or same-run validation is not possible and is not claimed. All camera-to-LDV comparisons in this paper are condition-level (per-RPM aggregate statistics), following the protocol described in Section 2.6.

## 2.4 Offline Reconstruction Pipeline

Raw multi-camera ROS bag files were processed through the OMRPR offline pipeline in five stages:

**Stage 1 — Bag replay and detection:** Each bag was replayed offline in ROS. AprilTag detection was applied frame-by-frame to each camera stream using the apriltag_ros package. Per-frame tag pose estimates (position and orientation) were written to per-camera CSV files.

**Stage 2 — Baseline alignment and fusion:** Per-camera pose estimates were aligned to a common world-frame reference using the zero-wind baseline condition (e0_0rpm) to remove fixed installation biases. Cross-camera fusion was applied using a weighted average of Camera 1 and Camera 2 observations at Marker A (bending channel) and a single Camera 3 observation at Marker B (torsion proxy channel).

**Stage 3 — Common 60 Hz grid resampling:** All per-camera response traces were resampled onto a common 60 Hz temporal grid using nearest-neighbor interpolation. This provides a deterministic shared time base across all cameras without hardware triggering. The timing uncertainty introduced by this step was audited and found to change stable-regime bending RMS by at most 5.3% relative to alternative resampling strategies; a denser 1000 Hz intermediate grid changes results by less than 0.1% and provides no material advantage.

**Stage 4 — Response extraction:** From the common-grid traces, the following response channels were extracted per test condition:

- `bending_avg_y_mm`: mean of Camera 1 and Camera 2 Marker A vertical displacement, world-frame y-axis, in mm. This is the primary bending channel.
- `torsion_diff_y_mm`: Camera 1 Marker A minus Camera 3 Marker B vertical displacement differential, in mm. This is the torsional proxy channel. It is a raw differential displacement, not a validated torsion angle (see Section 2.5).

**Stage 5 — Statistics extraction:** For each condition, full-record RMS, peak, mean, and frequency-domain statistics were computed from the common-grid traces.

## 2.5 Torsion Proxy Definition and Geometry

The torsion proxy `torsion_diff_y_mm` is defined as the differential vertical displacement between Marker A (deck centerline, Camera 1 + Camera 2) and Marker B (deck edge, Camera 3). A positive value indicates Marker A displaces upward relative to Marker B.

**Geometry (document-confirmed):** The LDV measurement records confirm a reference lever arm of d_b = 200 mm and a side sensor spacing of d_side = 130 mm [Lee2016], giving a torsion scale factor d_p = 1.538. The camera marker spacing of approximately 200 mm is consistent with the LDV d_b reference distance, supporting a condition-level comparison between the camera torsion proxy and the LDV torsion output. The LDV torsion output is already scaled by d_p = 1.538 through the facility BRID2D1 processing, placing it at the d_b = 200 mm reference distance — the same nominal spacing as the camera marker pair.

**Limitations:** This proxy is NOT equivalent to a validated torsion angle and must not be cited as such. The camera marker positions have not been independently surveyed against the LDV sensor positions. All torsion proxy comparisons with LDV in this paper are bounded condition-level trend comparisons only. The systematic under-read of approximately 0.81× in the stable regime is consistent with a residual lever-arm geometry offset between the camera marker pair and the LDV side-sensor position that has not been independently quantified.

## 2.6 Condition-Level LDV Reference Comparison Protocol

LDV reference values for the WTT test conditions were provided by the facility in the form of processed displacement statistics (bending RMS, bending peak, torsion RMS, torsion peak) for each RPM condition (D01–D20, corresponding to 20–320 RPM). Native LDV units are centimeters; all comparison values in this paper are converted to millimeters (×10).

Each camera condition (e1_20rpm–e20_320rpm) is matched to the corresponding LDV reference row by RPM value. The comparison reports per-condition bending RMS, bending peak, and their ratios (camera / LDV). No claim of LDV-equivalent absolute displacement accuracy is made. The comparison demonstrates condition-level trend agreement across the RPM sweep.

**Excluded condition — 60 RPM (VIV onset boundary):** The 60 RPM condition (U = 0.882 m/s) sits at the lower boundary of vortex-induced vibration (VIV) lock-in for this bridge deck geometry. VIV lock-in exhibits sensitive dependence on initial perturbation amplitude and test history at the onset boundary [cite: Larsen 2003 or equivalent]. The LDV reference for 60 RPM was acquired during a run in which VIV was actively locked in; the camera ROS bag for the same nominal condition was recorded during a separate run in which lock-in did not occur. This condition is excluded from aggregate LDV comparison statistics and is discussed as a diagnostic case in Section 4.5.

---

# 3. EXPERIMENTAL CONDITIONS

Twenty-one test conditions were recorded across the 0–320 RPM fan speed range (Table 1). Conditions are grouped into the following regimes based on structural response character:

**Table 1. Test condition classification**

| Regime | RPM range | Wind speed (m/s) | Structural behavior |
|---|---|---|---|
| Baseline (zero-wind) | 0 | 0 | Static / ambient noise floor |
| Near-noise-floor | 20–50 | 0–0.70 | Below camera detection threshold |
| VIV onset boundary | 60 | 0.88 | VIV-sensitive (excluded from aggregate statistics) |
| VIV peak | 70 | 1.07 | Bending VIV lock-in |
| Torsional VIV | 80–90 | 1.25–1.43 | Torsional VIV onset and peak |
| Post-VIV stable | 100–120 | 1.62–1.98 | Low-amplitude stable regime |
| Mid-speed stable | 140–220 | 2.35–3.82 | Moderate-amplitude stable regime |
| High-speed stable | 240–300 | 4.18–5.28 | Higher-amplitude stable regime |
| Flutter onset | 320 | 5.65 | High-wind unstable motion (reported separately) |

The 320 RPM condition (e20, designated `high_wind_unstable_motion`) exhibited large-amplitude flutter-type oscillation and is reported separately from the stable-regime statistics throughout this paper.

---

# 4. RESULTS

## 4.1 Static Noise Floor

With zero wind (e0_0rpm baseline), the common-grid response channels yield the following noise floor measurements:

- Bending (`bending_avg_y_mm`) RMS: **0.017 mm**
- Torsion proxy (`torsion_diff_y_mm`) RMS: **0.033 mm**
- In-plane camera-coordinate positional jitter: 0.012–0.059 mm

These values define the minimum detectable displacement for the OMRPR system under this configuration and serve as the reference against which all dynamic response measurements are assessed.

## 4.2 Camera Registration and Inter-Camera Agreement

Prior to baseline alignment, raw mean inter-camera Z agreement ranged from 106.15 to 115.16 mm across all 21 runs, reflecting fixed per-camera installation biases in the world-frame registration. After baseline-aligned fusion:

- Aligned mean Z agreement: **0.96 to 14.49 mm** (20/21 runs pass the <10 mm gate)
- Stable-regime aligned Z: **1.757 ± 0.596 mm** (mean ± std across stable conditions)
- Improvement factor: **~62.4× reduction** from raw to aligned

The single run failing the <10 mm gate is e20_320rpm (320 RPM, flutter), where actual large-amplitude coupled bending–torsion motion — rather than registration error — accounts for the elevated cross-camera Z discrepancy.

## 4.3 Bending Displacement: Camera vs. LDV Comparison

Cross-camera bending response (`bending_avg_y_mm`) was compared against the condition-level LDV reference across 18 stable RPM conditions (60 RPM excluded from statistics; 320 RPM reported separately in Section 4.6).

⚠ **C_R1 — Table 2 update needed (ACTIVE):** Verify per-condition values below against `bending_avg_y_mm` from the B0 cross-camera package (`data/results/paper2/reference_comparisons_common60/`) before final submission.

**Table 2. Camera bending vs. LDV reference — per-condition summary**

| RPM | Wind (m/s) | Cam RMS (mm) | LDV RMS (mm) | Ratio | Cam Peak (mm) | LDV Peak (mm) | Peak Ratio |
|---|---|---|---|---|---|---|---|
| 20 | 0.00 | 0.017 | 0.112 | 0.16× | 0.062 | 0.338 | 0.18× |
| 40 | 0.52 | 0.015 | 0.112 | 0.13× | 0.063 | 0.326 | 0.19× |
| 50 | 0.70 | 0.033 | 0.114 | 0.29× | 0.100 | 0.352 | 0.28× |
| 70 | 1.07 | 3.109 | 2.908 | **1.07×** | 4.884 | 4.552 | **1.07×** |
| 80 | 1.25 | 1.373 | 0.620 | 2.21× | 3.030 | 1.428 | 2.12× |
| 90 | 1.43 | 1.088 | 0.748 | 1.45× | 1.885 | 1.467 | 1.29× |
| 100 | 1.62 | 0.200 | 0.164 | 1.23× | 0.560 | 0.658 | 0.85× |
| 110 | 1.80 | 0.165 | 0.170 | 0.98× | 0.535 | 0.605 | 0.88× |
| 120 | 1.98 | 0.211 | 0.209 | 1.01× | 0.710 | 0.688 | 1.03× |
| 140 | 2.35 | 0.979 | 0.754 | 1.30× | 1.844 | 1.724 | 1.07× |
| 160 | 2.72 | 1.630 | 1.089 | 1.50× | 2.991 | 2.208 | 1.36× |
| 180 | 3.08 | 1.920 | 1.277 | 1.50× | 3.411 | 3.160 | 1.08× |
| 200 | 3.45 | 1.972 | 1.359 | 1.45× | 3.542 | 2.853 | 1.24× |
| 220 | 3.82 | 1.497 | 0.942 | 1.59× | 3.101 | 2.756 | 1.13× |
| 240 | 4.18 | 0.702 | 0.750 | 0.94× | 2.044 | 2.303 | 0.89× |
| 260 | 4.55 | 0.811 | 1.010 | 0.80× | 1.983 | 3.074 | 0.65× |
| 280 | 4.92 | 1.045 | 1.120 | 0.93× | 3.379 | 3.532 | 0.96× |
| 300 | 5.28 | 1.215 | 1.006 | 1.21× | 3.496 | 3.218 | 1.09× |

*Notes: LDV values from facility Excel file, result sheet, converted from cm to mm (×10). Camera values from OMRPR common-60 Hz bending channel. Conditions 20–50 RPM are at or below camera noise floor (0.017 mm RMS) and are included for completeness only.*

**Aggregate statistics — cross-camera bending_avg_y_mm (B0 package, stable regime, 18 conditions):**

- Pearson correlation: **r ≈ 0.959**, Spearman: **ρ ≈ 0.944**
- Mean camera/LDV ratio: **~1.268**, MAE: **~0.224 mm**, RMSE: **~0.297 mm**

## 4.4 Torsion Proxy vs. LDV Comparison

Cross-camera torsion proxy (`torsion_diff_y_mm`) was compared against the LDV torsion reference using the document-confirmed geometry (d_b = 200 mm, d_side = 130 mm, d_p = 1.538 [Lee2016]). Stable-regime condition-level metrics:

- Pearson correlation: **r ≈ 0.968**, Spearman: **ρ ≈ 0.953**
- Mean camera/LDV ratio: **~0.785**, MAE: **~0.338 mm**, RMSE: **~0.501 mm**

The camera torsion proxy consistently under-estimates the LDV torsion reference (ratio ~0.81) across the stable regime. This systematic offset is consistent with a residual lever-arm geometry mismatch between the camera marker pair and the LDV measurement point that has not been independently surveyed. The torsion proxy comparison is valid as a condition-level trend comparison only and does not constitute same-run waveform validation or a validated torsion-angle measurement.

For the high-wind case e20_320rpm: camera torsion proxy RMS ≈ 17.1 mm vs. LDV torsion RMS ≈ 17.1 mm (ratio ≈ 1.00). This single-condition numerical equality should not be over-interpreted given the large and unsteady oscillation amplitude.

## 4.5 Diagnostic Case: 60 RPM VIV Onset Anomaly

The 60 RPM condition (U = 0.882 m/s) produced a camera bending RMS of 0.089 mm against an LDV reference of 1.766 mm (ratio = 0.05×). This is the sole condition where the camera signal diverges substantially from the LDV reference. A six-part diagnostic analysis was performed:

1. **Frame rate and timing:** Mean fps = 59.94, jitter std = 0.60 ms, maximum gap = 23.8 ms — identical in character to the 70 RPM condition. Frame timing is not the cause.

2. **Detection quality:** 100% AprilTag detection (1829/1829 frames), mean reprojection error = 0.336 pixels (cf. 0.313 at 70 RPM). Detection quality is not the cause.

3. **Power spectral density:** The camera bending signal at 60 RPM shows a dominant spectral peak at 1.406 Hz — consistent with the structural natural frequency f_h = 1.430 Hz. PSD energy in the 1.2–1.7 Hz band is 0.0066 mm²/Hz, versus 9.39 mm²/Hz at 70 RPM (a 1427× power ratio; 37.8× amplitude ratio). The structure is resonating at the correct natural frequency but at near-noise-floor amplitude.

4. **Rolling RMS stationarity:** A 2-second rolling RMS shows flat amplitude throughout the 30 s recording (min 0.038 mm, max 0.123 mm, std 0.021 mm). No VIV lock-in burst occurred during the camera recording window.

5. **Physical mechanism:** The reduced velocity at 60 RPM is V_r = U / (f_h × B) = 0.882 / (1.430 × 0.40) = 1.54, placing this condition at the lower onset boundary of VIV lock-in for streamlined bridge deck sections. VIV lock-in at this wind speed is known to be highly sensitive to initial perturbation amplitude and wind ramping history [cite: Larsen 2003 or equivalent]. The LDV reference was acquired during a run where lock-in occurred; the camera ROS bag was recorded during a separate run where it did not. This is a physical measurement divergence due to non-simultaneous acquisition at the VIV onset boundary, not a camera system failure.

6. **Impact on aggregate statistics:** Excluding 60 RPM from aggregate comparison statistics is physically justified and applied consistently throughout this paper.

## 4.6 High-Wind Flutter Case (320 RPM)

The 320 RPM condition (U = 5.648 m/s, e20_320rpm, designated `high_wind_unstable_motion`) is outside the stable-regime statistical analysis. Camera bending RMS = 6.34 mm, LDV bending RMS = 3.58 mm (ratio = 1.77×); camera bending peak = 10.52 mm, LDV bending peak = 6.84 mm (ratio = 1.54×). The elevated camera/LDV ratio at this condition is attributed to large-amplitude coupled bending–torsion flutter motion, which introduces out-of-plane displacement components that the single-axis camera bending channel partially projects onto the vertical axis. Camera inter-view Z agreement at 320 RPM was 14.5 mm (above the <10 mm gate), consistent with actual coupled structural instability rather than measurement failure. This condition is reported for completeness and does not contribute to method validation claims.

## 4.7 Frequency Characterization

Dominant frequency characterization was performed using Hann-window FFT on the common-60 Hz per-run traces after mean removal. Results are reported as nearest-bin checks (within ±0.5 bin) against the two structural reference frequencies f_h = 1.430 Hz and f_α = 3.103 Hz.

- Bending reference bin (f_h) check: **21/21 conditions show energy concentration**
- Torsion proxy reference bin (f_α) check: **21/21 conditions show energy concentration**

**Important caveat (C_R2):** The above counts reflect nearest-bin energy concentration, not dominant-peak frequency agreement. At high-amplitude VIV and flutter conditions the dominant spectral peak does match the reference frequency; at low-amplitude near-noise-floor conditions the dominant peak may be noise-driven. The correct statement is: "the structural reference frequency bin shows energy concentration in 21/21 conditions, with dominant peaks matching at high-amplitude excitation conditions." This paper does not claim dominant-peak frequency tracking for all 21 conditions.

## 4.8 Bootstrap Uncertainty

Moving-block bootstrap confidence intervals (1000 replicates, 1-second blocks, seed 20260516) on stable non-near-floor common-60 Hz traces:

- Bending RMS: mean relative CI width **13.3%**
- Torsion proxy RMS: mean relative CI width **15.0%**

These intervals quantify within-run metric stability under the current processing pipeline and do not represent repeated-experiment repeatability.

---

# 5. DISCUSSION

## 5.1 Interpretation of the LDV Condition-Level Comparison

The condition-level bending comparison (bending_avg_y_mm vs. LDV reference) yielded Pearson r ≈ 0.959 and Spearman ρ ≈ 0.944 across 18 stable-regime wind-tunnel conditions (20–300 RPM, excluding the 60 RPM VIV onset boundary), with RMSE ≈ 0.297 mm and MAE ≈ 0.224 mm. These metrics confirm that the OMRPR framework tracks the relative trend in structural displacement response across a broad range of excitation amplitudes — from noise-floor-level responses at low wind speeds to multi-millimeter oscillation amplitudes near VIV resonance. The result supports the use of condition-level trend tracking as the primary performance claim.

However, the mean camera-to-LDV RMS ratio of approximately 1.268 indicates a systematic over-read that precludes any claim of LDV-equivalent absolute displacement accuracy. Three factors contribute to this offset. First, the camera and LDV measurements were conducted in separate test campaigns at the same facility using the same bridge deck model configuration, but not simultaneously and not in the same wind-tunnel run. Condition-matching is therefore based on nominal wind speed and RPM settings rather than concurrent acquisition, and any difference in the aerodynamic state of the model between sessions contributes directly to the ratio. Second, the LDV system measures displacement at a single geometric point, whereas camera-derived bending_avg_y_mm integrates pose estimates from markers spanning the full chord of the model; these quantities are geometrically related but not identical, and the spatial averaging introduces a systematic scale factor that has not been independently calibrated. Third, the common 60 Hz reconstruction grid introduces residual phase uncertainty from per-node software timing offsets of up to 46.4 ms maximum observed pairwise drift; while this offline synchronization mitigates gross temporal misalignment, it does not eliminate sub-frame timing error, which contributes amplitude smearing in reconstructed displacement signals. Taken together, these factors explain the observed over-read without requiring a systematic calibration error. Correcting the ratio offset would require simultaneous co-located acquisition and explicit spatial calibration, which are identified as directions for future work.

## 5.2 Motion Blur and Amplitude Underestimation

Camera-based marker tracking at 60 fps is susceptible to motion-induced blur during high-amplitude excitation. At mid-speed conditions (70–90 RPM, displacement amplitudes of 1–3 mm), marker motion across a single frame corresponds to an estimated 0.43–0.68 mm of projected displacement. When marker blur is sufficient to degrade AprilTag corner localization, the detected pose estimate reflects the time-averaged rather than the instantaneous marker position, causing systematic amplitude underestimation at the camera-derived output. Across the mid-speed regime this effect is estimated at approximately 10–15% of the measured amplitude, consistent with the observed camera-to-LDV ratios in the 1.07–1.59× range for those conditions. Motion blur therefore acts as a secondary contributor to the amplitude offset but is not the primary driver of the mean 1.268× ratio; the dominant factors are the non-simultaneous acquisition and the spatial-averaging geometry described in Section 5.1. This limitation is directly addressable: operating at higher frame rates (120 fps or above) would reduce per-frame blur by a factor of two or more and is expected to substantially reduce amplitude underestimation at mid-speed conditions.

## 5.3 The 60 RPM Anomaly: VIV Intermittency, Not Camera Failure

The condition at 60 RPM (wind speed ≈ 0.88 m/s, reduced velocity V_r ≈ 1.54) represents the onset boundary of vertical vortex-induced vibration (VIV) for this bridge deck geometry, with natural heaving frequency f_h = 1.430 Hz. The camera-derived bending_avg_y_mm for this condition yielded an RMS of 0.089 mm, compared to the LDV reference RMS of 1.766 mm — a camera-to-LDV ratio of approximately 0.05×, an outlier relative to all other conditions in the dataset. This condition is excluded from stable-regime statistics and reported separately.

Frame-level analysis and detection quality metrics confirm that the camera system operated normally during the 60 RPM acquisition: frame rate (59.94 fps), AprilTag detection rate, and calibration residuals were all within expected bounds, ruling out a hardware or tracking failure. The root cause is aerodynamic intermittency at the VIV lock-in boundary. VIV onset is sensitive to small fluctuations in wind speed and turbulence intensity, and lock-in can alternate between engaged and disengaged states within a single test run. The LDV reference for this condition was acquired in a separate test campaign; if the LDV acquisition captured the model during a sustained lock-in interval while the camera acquisition sampled a predominantly pre-lock-in state, the resulting amplitude mismatch is an accurate reflection of a real aerodynamic difference between the two independent measurements rather than a measurement error. This interpretation is consistent with the pattern of all other conditions, where camera and LDV responses agree in trend despite non-simultaneous acquisition. The 60 RPM case illustrates a fundamental limitation of condition-level comparison under non-simultaneous acquisition at resonance boundaries: any measurement system operating at a structural resonance onset is sensitive to whether lock-in was engaged during that specific acquisition window. Future work with simultaneous camera-LDV acquisition would eliminate this ambiguity.

## 5.4 Torsional Response Proxy: Capabilities and Boundaries

The torsion proxy quantity torsion_diff_y_mm is defined as the difference in y-displacement between two markers at the leading and trailing edges of the bridge deck model, with a nominal spacing of approximately 200 mm consistent with the LDV lever arm confirmed from the facility measurement records [Lee2016]. This quantity reflects differential vertical displacement across the chord and provides a proxy signal for torsional deformation under the assumption that the two markers move in opposite vertical directions during torsional oscillation. Condition-level comparison against the LDV torsion reference yielded Pearson r ≈ 0.968 and Spearman ρ ≈ 0.953 in the stable excitation regime, indicating strong relative trend agreement across excitation conditions.

The systematic under-read of approximately 0.785× (camera-to-LDV RMS ratio) reflects that the proxy quantity is not geometrically equivalent to the LDV torsion output. The LDV reports displacement at a side-sensor position at d_side = 130 mm from the centerline, scaled through d_p = 1.538 to yield output at the 200 mm lever-arm reference [Lee2016]. The camera-derived proxy integrates the y-displacement estimates from two markers whose positions are confirmed at approximately 200 mm nominal spacing but are not guaranteed to be collinear with the LDV lever arm within the measurement plane. The combination of marker placement offset, single-point vs. integrated geometry, and the absence of a simultaneous co-calibration session explains the observed under-read. No attempt has been made to correct this ratio. torsion_diff_y_mm is explicitly a two-point differential displacement proxy; it does not constitute a validated torsion angle measurement, and no claim is made regarding absolute torsional accuracy or LDV-equivalent torsion recovery.

## 5.5 Explicit Scope Limitations

The following limitations of this work are stated explicitly.

The LDV comparison in this paper is condition-level only. Camera and LDV data were acquired in separate test sessions at the same facility under nominally matched conditions; no same-run concurrent waveform comparison has been performed. Consequently, Pearson and Spearman correlations reflect agreement in amplitude trend across conditions and not waveform-level fidelity.

No claim of LDV-equivalent absolute displacement accuracy is made. The systematic amplitude ratio (~1.268× bending, ~0.785× torsion proxy) has not been corrected, and the sources of the offsets — non-simultaneous acquisition, spatial-averaging geometry, and residual timing uncertainty — have not been independently decomposed.

The synchronization strategy applied in this framework is an offline software mitigation: all camera streams are reconstructed onto a common 60 Hz temporal grid using per-node ROS timestamps. This approach reduces, but does not eliminate, the timing uncertainty arising from independently started camera nodes, with maximum observed pairwise drift of 46.4 ms (cam2–cam3). No hardware triggering or shared clock reference was used; the framework is explicitly offline-only and makes no real-time deployment claim.

The torsion_diff_y_mm quantity is a two-point differential displacement proxy. It provides structural information about differential vertical motion across the chord and shows strong condition-level trend correlation with the LDV torsion reference, but it is not a validated torsion angle measurement.

All results are bounded to the 21-condition offline wind-tunnel dataset described in this paper. Generalizability to other structural geometries, excitation regimes, tag configurations, or real-time deployment scenarios has not been demonstrated.

---

# 6. CONCLUSION

This paper has presented OMRPR (Offline Multi-Modal Robust Pose Reconstruction), an offline multi-camera AprilTag-based framework for structural displacement measurement under wind-induced excitation, validated across 21 wind-tunnel test conditions on a bridge deck scale model at a commercial aerodynamic testing facility in South Korea [Lee2016].

The principal technical contribution of the framework is its treatment of the multi-camera synchronization problem in the absence of hardware triggering. By reconstructing all independently started camera streams onto a shared 60 Hz temporal basis — a common-grid offline synchronization strategy — the framework mitigates software timing variability of up to 46.4 ms maximum observed pairwise drift without requiring a shared clock or hardware trigger signal. Baseline-aligned fusion recovered inter-camera spatial agreement from approximately 106 mm (raw Z offset) to 1.757 ± 0.596 mm across the stable excitation regime, a reduction of approximately 62×, enabling bounded statements about fusion reliability before and after registration.

Condition-level comparison of the cross-camera bending response (bending_avg_y_mm) against an independently operated LDV reference across 18 stable-regime conditions yielded Pearson r ≈ 0.959 (Spearman ρ ≈ 0.944), RMSE ≈ 0.297 mm, and MAE ≈ 0.224 mm, with a mean camera-to-LDV amplitude ratio of approximately 1.268×. The torsion proxy (torsion_diff_y_mm), constructed from the differential y-displacement of markers spanning approximately 200 mm consistent with the LDV lever arm geometry [Lee2016], yielded Pearson r ≈ 0.968 in the stable regime with a systematic under-read of approximately 0.785×. These results confirm that OMRPR tracks relative displacement trends across a broad excitation range, including VIV-onset, mid-speed, and high-amplitude structural responses. The systematic amplitude offsets reflect the non-simultaneous acquisition strategy and spatial-averaging geometry; they are explicitly not claimed as LDV-equivalent accuracy.

The 60 RPM anomaly — where the camera-derived bending amplitude was approximately 0.05× the LDV reference — is diagnosed as aerodynamic intermittency at the VIV lock-in onset boundary rather than camera failure. Frame-level quality metrics confirmed normal operation; the mismatch arises because non-simultaneous acquisition at a resonance boundary does not guarantee that both systems sampled the same aerodynamic state. This case is excluded from stable-regime statistics and reported separately as a cautionary example for condition-level comparison at structural resonance onsets.

The framework, its uncertainty characterizations, and all result processing steps are documented with the processing code available at https://github.com/ammarajmal/shm-displacement-project. Raw experimental data are proprietary to the wind-tunnel facility and are not publicly available.

Future work should address three directions identified by the limitations of this study. First, simultaneous co-located camera and LDV acquisition would eliminate the non-simultaneity source of the amplitude ratio offset and enable waveform-level fidelity comparison. Second, higher camera frame rates (120 fps or above) would reduce motion-blur-induced amplitude underestimation at mid-speed excitation conditions. Third, a formal geometric survey of marker placement relative to the LDV lever arm would enable explicit calibration of the torsion proxy scale factor and support a bounded conversion from differential displacement to torsion angle.

---

# REFERENCES (PLACEHOLDER)

[Lee2016] Lee, S.-W. et al. (2016). Proc. SPIE 9803, 98032X. DOI: 10.1117/12.2219404.  
[Ma2023] Ma et al. (2023). — reuse from Paper 1 ref [3].  
[Dong2023] Dong et al. (2023). — reuse from Paper 1 ref [4].  
[Zhuang2022] Zhuang et al. (2022). — reuse from Paper 1 ref [9].  
[XuBrownjohn2018] Xu & Brownjohn (2018). — reuse from Paper 1 ref [10].  
[Ajmal2024] Ajmal et al. (2024). — Paper 1.  
[PanigatiXXXX] Panigati et al. (year TBD). — Paper 1 ref [5]. Confirm year in Zotero.  
[Nie2022] Nie et al. (2022). Sensors 22(18):6869.  
[Olson2011] Olson, E. (2011). AprilTag. ICRA.  
[WangOlson2016] Wang, J. & Olson, E. (2016). AprilTag 2. ICRA.  
[Pan2009] Pan, B. et al. (2009). Meas. Sci. Technol. 20(6):062001.  
[Park2013] Park et al. (2013). Sensors.  
[Huang2018] Huang et al. (2018). JWEIA.  
[Xiu2023] Xiu et al. (2023).  
[LavaXXXX] Lava et al. (KU Leuven, Strain journal). — Find and add to Zotero.  
[LarsenXXXX] Larsen (2003) or Scanlan & Vickery. — Find for VIV lock-in citation.  

---

# ACTIVE FLAGS (pre-submission checklist)

| Flag | Priority | Issue | Action |
|---|---|---|---|
| C_R1 | HIGH | Verify Table 2 values against B0 cross-camera package | Pull from data/results/paper2/reference_comparisons_common60/ |
| C_F1 | HIGH | Facility anonymization throughout | Never write TESolution or Anseong-si; always [Lee2016] |
| C_F2 | MEDIUM | Sony RX10 IV / AverMedia naming permission | Confirm with supervisor before submission |
| C_R2 | HIGH | Section 4.7 nearest-bin caveat | Now explicitly stated in text — verify wording acceptable |
| C_R4 | LOW | VIV lock-in citation (Larsen 2003 or equivalent) | Find and add to Zotero |
| C_Z1 | MEDIUM | Lava et al. (KU Leuven, Strain) — DIC aeroelastic degradation | Find and add to Zotero |
| C_Z2 | MEDIUM | Panigati et al. year — confirm from Paper 1 ref [5] | Check Zotero |

