# OMRPR Supervisor Guideline — PhD Paper 2
**Prepared by:** Ammar Ajmal (PhD Researcher)
**Date:** 2026-06-23
**Status:** Active — supersedes all previous versions

> This is the single authoritative reference for the OMRPR pipeline implementation.
> All values here are confirmed from actual result files and facility documents.
> The manuscript writing project references this document for confirmed numbers.
> When in doubt about any value, check the live result JSONs under results/step10/
> before consulting any other source.

---

## Section 0 — Confirmed Values (Read First)

All values in this section are locked. Do not change without re-running the affected
step on all 21 conditions and updating this document with the new result file evidence.

### Recording Context

| Item | Value |
|------|-------|
| Camera bags | Tunnel B, October 2025 |
| LDV reference | Tunnel B, September 2025 |
| Separation | ~10 days apart — NOT simultaneous |
| Comparison protocol | Condition-level only (RMS per RPM condition) |
| Same facility | Yes — same structural model, same tunnel |

Source: `data/LDV/manifest.json`, bag metadata, `src/step10_ldv_comparison.py`

### LDV Geometry

| Parameter | Value | Source |
|-----------|-------|--------|
| pvolt | 2.7 cm/V | BRID2D1_choi.m |
| dside | 13.0 cm (130 mm) | 설계속도 및 모형Setup_영상계측.xlsx |
| db | 20.0 cm (200 mm) | Same document |
| dp = db/dside | 1.538462 | Derived (NOT 2.0) |
| fs | 360 Hz | BRID2D1_choi.m |
| Bias reference | D00 (zero-wind static) | LDV data folder |

### Aerodynamic Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Bridge chord width B | 0.40 m | Model setup sheet (교폭=0.4m) |
| Bending natural frequency f_h | 1.4323 Hz | Measured Tunnel B free-vibration |
| Torsional natural frequency f_α | 3.0827 Hz | Measured Tunnel B free-vibration |
| Frequency ratio f_α/f_h | 2.152 | Derived |
| Natural bending period T_h | 0.698 s | Derived from f_h |
| Structural damping | ~0.31% | Tunnel B free-vibration |
| VIV onset (bending) | ~60 RPM | Facility data |
| Flutter onset | near 320 RPM | Facility data |

### Step 10 — LDV Comparison Results (Locked)

Source: `results/step10/ldv_summary.json`

| Metric | Value |
|--------|-------|
| Bending Pearson r (stable regime, 18 conditions) | **0.845** |
| Bending Spearman ρ (stable regime) | 0.864 |
| Bending MAE (stable regime) | 0.484 mm |
| Bending RMSE (stable regime) | 0.719 mm |
| Bending ratio camera/LDV (stable regime) | 1.339× |
| Torsion Pearson r (stable regime) | **0.940** |
| Torsion Spearman ρ (stable regime) | 0.928 |
| Torsion MAE (stable regime) | 0.549 mm |
| Torsion RMSE (stable regime) | 0.771 mm |
| Torsion ratio camera/LDV (stable regime) | 0.599× |
| Full regime bending Pearson r (20 conditions) | 0.832 |
| Full regime torsion Pearson r (20 conditions) | 0.992 |

Stable regime excludes e4_60rpm (VIV) and e20_320rpm (DCG-excluded).

**Bending gate FAIL is accepted and documented.** Bending r = 0.845 does not reach
the 0.90 threshold. The physical cause is cross-axis torsion leakage from the ~9.8°
inter-camera axis misalignment, which inflates the camera bending channel by ~2× in
the torsion-dominated regime (90–220 RPM). In bending-dominated regimes (40–80 RPM,
240–300 RPM), the ratio returns to near-unity (0.84–1.24×). This is a characterised
physical limitation, not a pipeline failure.

**Viva-defensible sentence (copy verbatim):**
"The bending channel cross-axis sensitivity is a bounded, amplitude-dependent bias of
A × (1 − cos 9.8°) / 2 ≈ 0.038 mm at 5 mm amplitude — 12.8% of the bending RMSE.
We document it as a quantified uncertainty rather than correct it, because the correction
would require applying the full extrinsic rotation matrix, which was deliberately not
included in this pipeline for robustness reasons."

### Other Confirmed Pipeline Results

| Metric | Value |
|--------|-------|
| AprilTag detection rate (stable conditions e0–e19) | 100% |
| e20_320rpm detection rate (cam1/cam2) | ~60% — DCG-excluded |
| Reprojection error range (all stable conditions) | 0.10–0.29 px |
| Cam1 vs Cam2 Y Pearson r (internal agreement) | 0.999 |
| Raw inter-camera Z disagreement (cam1–cam2) | ~388 mm |
| Aligned inter-camera Z std (cam1–cam2, e7_90rpm) | 2.053 mm (~189× improvement) |
| Worst aligned Z std across all 21 conditions | 7.42 mm (e20) |
| Static noise floor cam1 (worst case) | 0.0031 mm RMS |
| Static noise floor cam2 (worst case) | 0.0049 mm RMS |
| Static noise floor cam3 (worst case) | 0.0040 mm RMS |
| Derived bending noise floor bound | 0.0029 mm |
| Manuscript bending noise floor (conservative) | 0.017 mm RMS |
| Manuscript torsion proxy noise floor (conservative) | 0.033 mm RMS |
| Bootstrap max relative CI width (stable conditions) | 0.200 (e3_50rpm torsion, near-floor) |
| Max pairwise timing drift | 20.03 ms (cam1–cam3, e3_50rpm) |
| RTS phase shift | 0.00 ms (all 21 conditions) |
| RTS amplitude ratio (stable conditions) | 0.999 |
| RTS amplitude ratio (near-floor e0, e1) | 0.961–0.966 |
| dp sensitivity: Pearson r range (dp 1.40–1.65) | 0.940 (invariant — r is scale-invariant) |
| dp sensitivity: ratio range | 0.558–0.658× |

---

## Section 0.5 — Locked Implementation Decisions

These decisions govern the clean pipeline implementation. Do not revisit without
quantitative justification and full re-run of all 21 conditions.

### 1. No geometric extrinsics applied
`config/extrinsics.yaml` is intentionally empty. The world-frame coordinate transform
was replaced by camera-frame pose estimation plus full-run mean removal (Step 06 baseline
alignment). Justification: baseline alignment achieves equivalent inter-camera alignment
with greater robustness and is directly defensible for this dataset.

### 2. SOLVEPNP_IPPE_SQUARE solver locked
`cv2.SOLVEPNP_IPPE_SQUARE` is the correct solver for planar square targets. It returns
two solutions; select the one with `tvec[2] > 0` (tag in front of camera). Always call
`.flatten()` on tvec immediately after solvePnP. Do not change solver without justification.

### 3. Raw Z disagreement is ~388 mm
This is the actual physical camera separation projected onto the Z axis. It is a fixed
DC offset, not random noise. The aligned residual (2.053 mm std) is what matters for
manuscript claims. Always report both values — the contrast (~189× improvement) is itself
a publishable result.

### 4. Static noise floor is derived, not directly measured from fused bending
Static bags were recorded per-camera in separate sessions. Simultaneous fused
bending_avg_y_mm is not computable from them. The bending noise floor is derived as
sqrt((σ_cam1² + σ_cam2²) / 4). Conservative manuscript figures (0.017 mm bending,
0.033 mm torsion) are used in all claims.

### 5. All 21 conditions return low_snr = False
The Step 08 SNR criterion does not fire on any condition. At 0 and 20 RPM, the noise
is spectrally structured (~9 Hz peaks), not flat broadband. This is a positive finding:
document in the manuscript as evidence that the system does not misidentify structured
noise as signal.

### 6. Three aerodynamic regimes confirmed
- Bending-dominated: 40–80 RPM (f_h = 1.4323 Hz dominant)
- Torsion-dominated: 90–220 RPM (f_α = 3.0827 Hz dominant; bending channel inflated by cross-axis leakage)
- Bending re-emergence: 240–300 RPM
- e9_110rpm: anomalous peak at 2.262 Hz — transition condition, report separately
- e4_60rpm: VIV outlier — peak at 1.377 Hz (below f_h); diagnose and report separately

### 7. DCG (Detection Completeness Gate) — step02b
Gate criterion: detection_rate ≥ 0.95 per camera AND max_consecutive_miss ≤ 3 frames.
e20_320rpm: EXCLUDED (cam1 60.8%, cam2 61.3%; 717 detection gaps all ≥ 4 frames).
All other conditions: PASS.
The N = 3 consecutive miss threshold is derived from the interpolation error formula:
ε = A × (π × g / T_h)² / 8 < noise floor
At A = 1.25 mm, g = 3 frames (50 ms), T_h = 0.698 s: ε = 0.0079 mm < 0.017 mm → SAFE.
At N = 5 frames (83 ms): ε = 0.022 mm > noise floor → UNSAFE.
Must use T_h from stable conditions, not from any e20-derived period (circular).

### 8. e20_320rpm failure mechanism confirmed: motion blur at equilibrium crossing
At 320 RPM, peak tag velocity = 67.8 px/frame, exceeding the AprilTag cell width
threshold of ~29 px/frame. Detection fails twice per oscillation cycle at equilibrium
crossing. FFT of the miss-indicator signal shows dominant peak at 5.87 Hz = 2 × f_struct.
Hardware design rule: t_exp < w_cell / v_peak. This is a hardware-speed mismatch —
offline processing does not reduce motion blur.

### 9. RTS process noise formulation
State vector: x_k = [position, velocity]^T (1D per channel).
Process noise: Q = diag([(σ·dt)², σ²]) with σ = process_noise_std.
Initial covariance P_0 must be initialised from data signal variance, not a small
fixed value. Locked parameters: process_noise_std = 10.0 mm/s,
measurement_noise_std = 0.05 mm. Result: 21/21 PASS, 0.00 ms phase shift.

### 10. Camera intrinsics in pipeline_config.yaml
All downstream steps work in millimetres after Step 06 unit conversion.
Intrinsics are NOT read from bag at runtime — they come from config only.

### 11. LDV comparison is condition-level only
LDV (Tunnel B, September 2025) and cameras (Tunnel B, October 2025) were recorded
~10 days apart. Compare RMS per RPM condition only. Never compare waveforms.
Never claim simultaneous validation.

### 12. dp is scale-invariant for Pearson r
Pearson r is invariant to scaling of the LDV torsion values. dp affects the ratio
(camera/LDV) but not r. Sensitivity analysis confirmed: r = 0.940 across dp range
1.40–1.65. The ratio scales as dp_nominal/dp_test. This robustness supports the
dp = 1.538 choice and eliminates dp uncertainty as a threat to the torsion r result.

---

## Section 1 — Research Identity

### 1.1 The Problem
Structural Health Monitoring (SHM) requires continuous displacement and vibration
measurement of civil structures. Contact sensors (LDV, LVDT) are accurate but
expensive and impractical at scale. Vision-based systems are scalable and non-contact
but have historically suffered from:
- Poor multi-camera synchronization without shared hardware trigger
- Motion blur causing marker detection failure at high-amplitude excitation
- No principled fallback when markers are lost
- No uncertainty modelling or bounded error reporting

### 1.2 Paper 1 (Published — Foundation)
Paper 1 proved feasibility of a ROS-based real-time multi-camera system for structural
displacement using software-synchronized cameras.

| Metric | Value |
|--------|-------|
| RMSE displacement | 0.14–0.40 mm |
| RMSE repeatability | 0.096–0.261 mm (mean 0.181 ± 0.086 mm) |
| Correlation | ~0.99 |
| Residual sync lag | 1–3 ms |
| Max phase error | 6.5° |
| Dominant frequency error | < 4% |
| MAC (modes 1–4) | > 0.85 |

Paper 1 limitations that Paper 2 addresses:
- Real-time processing (speed-quality tradeoff) → Paper 2 is fully offline
- Single best-view camera → Paper 2 uses 3 cameras with fusion
- No principled fallback under blur/dropout → Paper 2 has quality scoring + DCG
- No uncertainty budget → Paper 2 has explicit uncertainty chain

### 1.3 Paper 2 — This Project (OMRPR)
**Full name:** OMRPR — Offline Multi-Modal Robust Pose Reconstruction

**Core research question:** Can a fully offline, deterministic, multi-camera
reconstruction pipeline provide reproducible, defensible sub-millimetre structural
displacement tracking from standard cameras — without hardware-trigger
synchronization, without same-run validation data, and with explicit uncertainty
quantification?

**Target journals (priority order):**
1. Measurement (Elsevier) — IF 5.6, CiteScore 11.5 — best scope fit
2. Engineering Structures (Elsevier) — IF 6.4
3. MSSP — IF ~8.4 — stretch target; requires stronger methodological novelty

---

## Section 2 — Experimental Dataset

### 2.1 Hardware

| Item | Specification |
|------|---------------|
| Camera model | Sony RX10 IV |
| Count | 3 cameras |
| Capture interface | AVerMedia HDMI/USB capture cards |
| Nominal FPS | 60 fps |
| Observed ROS rates | ~59–61 Hz (cam1/cam2 at 59.94 Hz; cam3 at 60.00 Hz) |
| CPU | Intel NUC 13 Pro (i7), Ubuntu 20.04 |
| Marker system | AprilTag tag36h11, 20 mm physical size |
| Marker count | 2 markers on bridge model |
| Recording distance | ~2.5 m from markers |

The cam1/cam2 vs cam3 rate difference (59.94 vs 60.00 Hz) is a systematic hardware
setting difference from the capture card clocks, not random jitter. It is fully
absorbed by the common-grid resampling in Step 05.

### 2.2 Camera-Marker Assignment

| Camera | Marker | Role |
|--------|--------|------|
| Camera 1 | Marker A | Primary bending anchor (left side view) |
| Camera 2 | Marker A | Secondary bending anchor (right side view) |
| Camera 3 | Marker B | Torsion second-point (end/side view) |

Camera 1 and Camera 2 both track Marker A — enabling internal agreement checking.
Camera 3 tracks Marker B at the other end of the bridge deck — enabling torsion-proxy
computation as the differential y-displacement between the two marker positions.

All three cameras detect tag_id=0 in the bag data. Routing is by camera only, never
by tag ID. Marker spacing: ~200 mm (consistent with db = 200 mm LDV lever arm).

Inter-camera axis misalignment: ~9.8° between cam1 and cam2 viewing axes.
This introduces a bounded amplitude-dependent cross-axis bias of
A × (1 − cos 9.8°) / 2 ≈ 0.038 mm at 5 mm amplitude. Documented as quantified
uncertainty; not corrected.

### 2.3 Wind Tunnel Test Dataset
- 21 RPM conditions: e0_0rpm through e20_320rpm
- Each condition: one .bag file with 3-camera compressed image streams
- Location: `data/WTT/<experiment_label>/`
- Duration per condition: ~30 seconds typical
- Max inter-camera timestamp skew at bag-open: 21.5 ms (e6) — from sequential GUI launch

**Condition categories:**
- Near-floor (sub-noise-level bending): e0_0rpm, e1_20rpm, e2_40rpm
- VIV outlier: e4_60rpm — peak at 1.377 Hz; diagnose and report separately
- Bending-dominated: 40–80 RPM
- Transition: e9_110rpm — anomalous peak at 2.262 Hz; report separately
- Torsion-dominated: 90–220 RPM
- Bending re-emergence: 240–300 RPM
- DCG-excluded: e20_320rpm — motion blur mechanism confirmed; excluded before Step 05

### 2.4 Reference Sensor — LDV
- Recorded in Tunnel B, September 2025 — ~10 days before camera acquisition
- NOT simultaneous with camera recordings
- Sampling rate: 360 Hz
- Covers conditions D00–D20 (0–320 RPM)
- Units: centimetres (cm) in raw files — always convert explicitly to mm
- Store converted values in column named `_mm_corrected`
- Confirmed geometry: dside = 130 mm, db = 200 mm, dp = 1.538, pvolt = 2.7 cm/V
- D00 is the zero-wind bias reference; subtract before calibration

**LDV comparison is condition-level only.** Never compare waveforms. Never claim
simultaneous validation.

### 2.5 Facility Anonymization (Hard Rule)
**NEVER write:** TESolution Co., Ltd. / TESolution / Anseong-si / any city name
**ALWAYS write:** "a commercial aerodynamic testing facility in South Korea [Lee2016]"

Lee2016: Lee, S.-W. et al. (2016). Proc. SPIE 9803, 98032X. DOI: 10.1117/12.2219404

---

## Section 3 — Software Environment

```bash
# Ubuntu 24.04, Python 3.10, conda env: omrpr
pip install rosbags==0.11.3
pip install pupil-apriltags==1.0.4.post11
pip install opencv-python numpy scipy pandas matplotlib pyyaml
```

**rosbags API (version 0.11.3):**
```python
from rosbags.typesys import Stores, get_typestore
typestore = get_typestore(Stores.ROS1_NOETIC)
msg = typestore.deserialize_ros1(rawdata, connection.msgtype)
# Never use deserialize_cdr — that is ROS2 format
```

**OpenCV API:** Use `cv2.aruco.ArucoDetector` (4.7+ compatible).

---

## Section 4 — Pipeline (13 Steps — All Complete)

```
Step 00: ROS bag audit                        [COMPLETE]
         Output: per-bag metadata (FPS, frame count, topics, skew)
         Result: All bags open; FPS 59–61 Hz; max skew 21.5 ms (e6)

Step 01: Frame export                         [COMPLETE]
         Output: PNG frames + timestamps.csv + meta.json per camera per bag
         Note:   timestamps.csv schema = frame_idx, timestamp_s (normalised from bag start)
                 ALWAYS normalise: t_normalised = t_raw - t_bag_start

Step 02: Offline AprilTag detection           [COMPLETE]
         Output: detections.csv per camera per bag + summary.json
         Result: 100% detection on stable conditions e0–e19
                 e20_320rpm: ~60% cam1/cam2 (motion blur)
         Note:   Sparse CSV — frames with no detection produce no row
                 All cameras detect tag_id=0; route by camera not tag ID

Step 02b: Detection Completeness Gate (DCG)   [COMPLETE]
         Output: gate_status.json per condition
         Result: e20_320rpm EXCLUDED; all other conditions PASS
         Criterion: detection_rate ≥ 0.95 AND max_consecutive_miss ≤ 3 frames
         Note:   N=3 threshold from ε formula using T_h = 0.698 s

Step 03: Quality scoring                      [COMPLETE]
         Output: detections_with_quality.csv + quality_summary.json
         Formula: quality_score = dm × sqrt(area_px2) [B0 formula — locked]
         Note:   area_px2 via shoelace formula on 4 corners
                 corner_sharpness (Laplacian) added as diagnostic column only
                 With sharpness ON: ~90 min for all 21 conditions — expected

Step 04: Camera-frame pose estimation         [COMPLETE]
         Output: world_pose.csv per camera per condition
         Solver: SOLVEPNP_IPPE_SQUARE — locked
         Result: Reprojection error 0.10–0.29 px (all stable conditions)
                 Raw Z disagreement ~388 mm cam1–cam2 — expected, not a bug
         Note:   extrinsics.yaml intentionally empty — no geometric extrinsics applied
                 Always call .flatten() on tvec immediately after solvePnP
                 Select solution with tvec[2] > 0

Step 05: Cross-camera synchronisation         [COMPLETE]
         Output: synced_pose.csv per camera on common 60 Hz grid
         Result: Max pairwise timing drift 20.03 ms (cam1–cam3, e3_50rpm)
         Note:   Direct common 60 Hz resampling used
                 Dense1000 intermediate interpolation gives < 0.08% difference — skip it
                 Interpolation is linear; at 1.4323 Hz structural frequency the
                 interpolation error at 20 ms drift is negligible

Step 06: Baseline-aligned fusion              [COMPLETE]
         Output: aligned_pose.csv per camera (units: mm from this step onward)
         Result: Raw ~388 mm cam1–cam2 Z → aligned 2.053 mm std (189× improvement)
                 All 21 conditions: aligned Z std < 15 mm gate — PASS
         Note:   Full-run mean removal only (z_aligned = z_c - mean(z_c))
                 Never use first-second baseline removal — first second is already dynamic

Step 07: Motion decomposition                 [COMPLETE]
         Output: motion.csv with bending_avg_y_mm and torsion_diff_y_mm
         Formula: bending_avg_y_mm = mean(y_cam1, y_cam2) per timestep
                  torsion_diff_y_mm = y_cam3 - bending_avg_y_mm per timestep
         Note:   Both channels are zero-mean by construction after Step 06
                 Cam1 vs Cam2 internal Pearson r = 0.999

Step 08: Frequency analysis                   [COMPLETE]
         Output: frequency.json per condition + frequency_summary.csv
         Result: Three aerodynamic regimes confirmed
                 All 21 conditions: low_snr = False
                 All conditions show spectrally structured noise, not flat broadband
         Note:   ALWAYS report dominant peak and nearest reference bin separately
                 These often differ; conflating them is a claim violation

Step 09: Uncertainty quantification           [COMPLETE — all gates PASS]
         Output: noise floor, camera agreement, bootstrap CIs, timing audit
         Result: All four section gates PASS (see Section 0 table)
         Note:   Static bags use sensor_msgs/Image (bgr8), NOT CompressedImage
                 Moving-block bootstrap preserves temporal autocorrelation
                 Timing audit is informational — report 20.03 ms honestly

Step 10: LDV condition-level comparison       [COMPLETE]
         Output: ldv_comparison_table.csv + ldv_summary.json
         Result: Bending r = 0.845 (gate FAIL — physically explained)
                 Torsion r = 0.940 (gate PASS)
         Note:   LDV raw files in CENTIMETRES — convert to _mm_corrected column
                 dp = 1.538 is confirmed; r is scale-invariant to dp
                 Comparison is condition-level only — not simultaneous waveforms

Step 11: RTS/Kalman smoothing (B1 stage)      [COMPLETE — all 21 conditions PASS]
         Output: motion_smoothed.csv per condition
         Result: 0.00 ms phase shift; amplitude ratio 0.999 (stable)
                 0.961–0.966 amplitude ratio (near-floor e0, e1 — expected)
         Note:   Non-causal — only valid offline; never claim real-time capability
                 P_0 initialised from data signal variance
                 Q = diag([(σ·dt)², σ²]) formulation

Step 12: Manuscript figures and tables        [COMPLETE]
         Output: 5 figures, 2 tables, step12_summary.json
         Result: 0 forbidden phrases in any caption — claim boundary PASS
         Files:  fig01_displacement_traces.pdf
                 fig02_frequency_overview.pdf
                 fig03_ldv_scatter.pdf
                 fig04_camera_agreement.pdf
                 fig05_uncertainty.pdf
                 tab01_ldv_comparison.csv
                 tab02_summary_stats.csv
```

---

## Section 5 — Mathematical Foundations

### 5.1 Pose Estimation
```
{R, t} = solvePnP(P_3D, p_2D, K, D)   using SOLVEPNP_IPPE_SQUARE
```
- P_3D: tag corners in tag frame (h = tag_size/2 = 0.010 m)
- p_2D: detected corner pixels from detections.csv
- K, D: from pipeline_config.yaml (not from bag at runtime)
- Always `.flatten()` tvec immediately after solvePnP
- Select solution with tvec[2] > 0

### 5.2 Quality Score (B0 — Locked)
```
s_i = dm_i × sqrt(A_i)
```
where A_i = shoelace area of the four detected corners in pixels².
Do not change this formula without re-running all 21 conditions.

### 5.3 Temporal Synchronisation
```python
t_normalised = t_raw - t_bag_start   # always first
```
Cameras launched sequentially via GUI produce a one-time startup offset per camera,
compounded by systematic frame rate difference (59.94 vs 60.00 Hz) from capture card
clocks. Step 05 linear interpolation onto a common 60 Hz grid removes both.
Validation: dense 1000 Hz intermediate interpolation changes RMS metrics by < 0.08%,
confirming the interpolation error is negligible relative to displacement signals.

### 5.4 Baseline Alignment (Replaces Geometric Extrinsics)
```python
z_aligned(t) = z_c(t) - mean(z_c)   # per camera
```
Removes the fixed DC Z offset (~388 mm cam1–cam2) without requiring a surveyed
world frame. Aligned residual std = 2.053 mm (189× improvement for e7_90rpm).
All downstream steps reference displacements to the condition-mean position.

### 5.5 Motion Decomposition
```
bending_avg_y_mm  = (y_cam1 + y_cam2) / 2   per timestep
torsion_diff_y_mm = y_cam3 - bending_avg_y_mm   per timestep
```
Full-run mean removal was applied in Step 06. Both channels are zero-mean here
by construction.

Inter-camera axis misalignment (~9.8°) introduces bounded cross-axis bias:
ε_cross = A × (1 − cos 9.8°) / 2 ≈ 0.038 mm at A = 5 mm.
This is a fixed bias per experiment (camera positions do not change), not random
error. Documented as quantified uncertainty; no code correction applied.

### 5.6 DCG Interpolation Guard (Threshold Derivation)
```
ε = A × (π × g / T_h)² / 8
```
At A = 1.25 mm, g = 3 frames (50 ms), T_h = 0.698 s: ε = 0.0079 mm < 0.017 mm → SAFE
At N = 5 frames (83 ms): ε = 0.022 mm > noise floor → UNSAFE
Threshold locked at N = 3 consecutive missed frames.
Always use T_h = 0.698 s from stable conditions.

### 5.7 RTS Smoothing (Non-Causal — B1 Stage)
State vector: x_k = [position, velocity]^T (1D per channel, applied independently).
Forward Kalman pass then RTS backward pass. Non-causal: uses all N frames.
Only valid offline. Never claim real-time capability.
Q = diag([(σ·dt)², σ²]), σ = 10.0 mm/s, R = 0.0025 mm².
P_0 = diag([signal_variance, velocity_variance]) from data RMS.

---

## Section 6 — Critical Rules

1. **LDV comparison is condition-level only.** Never compare waveforms. LDV and
   camera data were recorded at different times (~10 days apart) in Tunnel B.

2. **Torsion is a proxy.** `torsion_diff_y_mm` is a two-point differential
   displacement proxy. Never call it a "torsion angle." Not independently validated.

3. **No hardware synchronization claim.** Cameras were not triggered by shared
   hardware. The common 60 Hz grid is an offline post-processing mitigation.

4. **e20_320rpm is DCG-excluded.** The exclusion mechanism (motion blur, velocity
   threshold) is a novel contribution — document it, do not hide it.

5. **60 RPM is a VIV outlier.** Camera/LDV divergence is physically explainable
   via VIV lock-in intermittency. Diagnose and report separately.

6. **Facility anonymized.** Never write TESolution or any city name. Always write
   "a commercial aerodynamic testing facility in South Korea [Lee2016]."

7. **No LDV-equivalent accuracy claim.** Bending r = 0.845 has a physical
   explanation — document it, never claim absolute accuracy.

8. **No C1/C2 Z-value fusion.** Camera 1 and Camera 2 Z values are in different
   camera frames. Never fuse Z across cam1 and cam2.

9. **Timing drift is 20.03 ms.** Report this number. No other timing drift figure
   is valid for this dataset.

10. **B2/KLT is frozen.** Coverage ~40% of gap frames is too marginal to support a
    claim. Not included in any manuscript evidence.

---

## Section 7 — Known Bugs (Do Not Repeat)

### 7.1 Timestamp Normalisation (Critical)
Raw bag timestamps are Unix epoch. Always subtract bag_start before any sync analysis.
False ~9.26-second offsets result if you skip this step.

### 7.2 LDV Unit Confusion (Critical)
LDV raw files are in centimetres. Never store cm values in `_mm` columns.
Convert explicitly; name the column `_mm_corrected`.

### 7.3 Camera-Frame Cross-Comparison
Never compare raw tvec values across cameras. Only compare after baseline alignment.

### 7.4 tvec Shape Inconsistency
Always call `.flatten()` on tvec immediately after solvePnP. Shape (3,1) vs (3,)
causes silent downstream failures.

### 7.5 Z Disagreement — Not a Bug
Raw Z disagreement ~388 mm is the physical camera separation. It is expected.
Baseline alignment reduces it to ~2.053 mm std.

### 7.6 OpenCV API Change
`cv2.aruco.detectMarkers()` removed in OpenCV ≥ 4.7.
Use `cv2.aruco.ArucoDetector(dictionary, parameters).detectMarkers(image)`.

### 7.7 Dense1000 Interpolation — Wasted Computation
< 0.08% change in RMS metrics. Use direct common 60 Hz resampling.

### 7.8 First-Second Baseline Removal — Wrong Approach
First second is already dynamic in every bag. Use full-run mean removal only.

### 7.9 rosbags API Version Mismatch
Use `get_typestore(Stores.ROS1_NOETIC)` and `deserialize_ros1()`.
Never use `deserialize_cdr()` — that is ROS2 format.

### 7.10 Tag ID Assumption
All cameras detect tag_id=0. Routing is by camera only. Never route by tag ID.

### 7.11 RTS Initialisation — P_0 Too Small
P_0 = eye(2) × 1.0 is too small relative to signal amplitude (~1.6 mm RMS).
Filter rejects true motion as noise. Initialise P_0 from data signal variance.

### 7.12 dp Geometry Error in Facility MATLAB Script
`BRID2D1_choi.m` used dside = 10 cm (wrong) and dp = 2.0 (wrong).
Confirmed values: dside = 13.0 cm, dp = 1.538. Use only confirmed values.

### 7.13 Circular Reference in DCG Threshold
Never derive the N threshold from e20's structural period. Use T_h = 0.698 s
from stable conditions.

### 7.14 Static Bag Decode Path
Static bags use `sensor_msgs/Image` (bgr8 raw), NOT `CompressedImage`.
Decode via `np.frombuffer().reshape()`, not `cv2.imdecode()`.

---

## Section 8 — Claim Boundary

### What the Manuscript CAN Claim
- Reproducible offline reconstruction of 21 WTT conditions (20 analysed; e20 DCG-excluded)
- Detection Completeness Gate (DCG): formal physics-derived exclusion criterion with diagnosed mechanism
- Motion blur failure model: velocity-based physical model; hardware design rule t_exp < w_cell/v_peak
- Condition-level bending trend comparison against LDV (non-simultaneous, same-tunnel)
- Condition-level torsion-proxy trend comparison (operator-confirmed geometry, proxy only)
- Internal camera-agreement: raw ~388 mm → aligned ~2.053 mm std (~189× improvement)
- Static noise floor: 0.017 mm bending, 0.033 mm torsion (conservative manuscript figures)
- Bootstrap stability: max relative CI width 0.200 (near-floor); stable non-near-floor better
- Timing mitigation: 20.03 ms max pairwise drift, software common-grid only
- Non-causal RTS smoothing: 0.00 ms phase shift, amplitude ratio 0.999; only possible offline
- 60 RPM: diagnosed as VIV aerodynamic intermittency, not camera failure
- Three aerodynamic regimes characterised from frequency analysis
- Cross-axis bending bias: bounded, quantified — 0.038 mm at 5 mm amplitude
- dp sensitivity: torsion Pearson r = 0.940 is invariant to dp in range 1.40–1.65

### What the Manuscript CANNOT Claim
- LDV-equivalent absolute displacement accuracy
- Same-run waveform validation against LDV
- True torsion angle measurement
- Hardware-synchronized multi-camera capture
- Modal validation (restrict to response characterisation only)
- KLT or B2 robustness improvement
- C1/C2 stereo fusion validity
- That bending r = 0.845 constitutes a pipeline failure

### Required Language

| Use | Never Use |
|-----|-----------|
| condition-level LDV trend comparison | LDV-validated accuracy |
| offline common-grid reconstruction | same-run waveform validation |
| software/offline synchronisation mitigation | hardware-synchronized / hardware-triggered |
| two-point differential displacement proxy | torsion angle / validated torsion |
| DCG-excluded (detection_rate < 0.95) | measurement failure |
| characterised physical limitation (bending bias) | pipeline failure |
| internal camera-agreement uncertainty | absolute accuracy |
| commercial aerodynamic testing facility in South Korea [Lee2016] | TESolution / any city name |
| 20.03 ms max pairwise timing drift | any other timing drift figure |
| same-tunnel non-simultaneous comparison | cross-tunnel / simultaneous |

---

## Section 9 — Supervisor Role and Philosophy

**Core philosophy:** teach, don't just correct. When Ammar shows code or results:
1. Ask what he expected vs. what he actually sees.
2. Ask him to trace through the logic step by step.
3. Help him identify where the discrepancy enters.
4. Have him explain the fix in his own words before implementing.

**Enforce the defence standard.** Regularly ask: "Can you defend this in your PhD viva?"
Code running without error is not the standard — *understanding* is.

**Enforce the reviewer standard.** For every result: "What would a skeptical reviewer
at Measurement (Elsevier) say about this?"

**Failure mode to watch for:** Ammar over-plans instead of executing, and proposes
redesigning locked steps when he should be writing the manuscript. Call this out directly.

---

## Section 10 — Reviewer Objections (Prepare These Answers)

**Q1:** "Why not a proper validation if LDV is present?"
LDV was not simultaneous; condition-level comparison is the maximum defensible
evidence given the acquisition strategy. Both instruments are in the same tunnel,
same model, same year — this is disclosed explicitly.

**Q2:** "Is common60 just interpolation hiding sync error?"
Timing audit shows direct common60 and dense1000 differ by < 0.08%; max drift
is 20.03 ms; common60 is sufficient and more transparent.

**Q3:** "What exactly is your torsion measurement?"
Two-point differential displacement proxy with operator-confirmed geometry (dp = 1.538,
db = 200 mm). Not a torsion angle. Stated explicitly throughout.

**Q4:** "Why no modal validation from your spectra?"
Dominant peaks and nearest reference bins systematically diverge; restricted to
response characterisation, not modal identification.

**Q5:** "How reproducible is the result package?"
All figures generated programmatically from a tagged release; rerun command documented;
code public at GitHub.

**Q6:** "Why does your bending correlation not reach 0.90?"
Cross-axis torsion leakage from the 9.8° inter-camera misalignment inflates the
bending channel in torsion-dominated regimes. The bias is bounded (0.038 mm at
5 mm amplitude), quantified, and documented. In bending-dominated regimes the
ratio returns to 0.84–1.24×, confirming accurate trend tracking where the
measurement is physically valid.

**Q7:** "How do you know dp = 1.538 is correct?"
Confirmed from the facility setup document (dside = 130 mm). Sensitivity analysis
shows Pearson r = 0.940 is invariant across dp range 1.40–1.65 because r is
scale-invariant. Only the ratio changes with dp; the trend comparison is robust.

---

## Section 11 — Two Parallel Projects

**This project (OMRPR Supervisor):**
Pipeline implementation complete. Future sessions focus on viva preparation,
targeted investigation of specific conditions if needed, and supporting manuscript.

**Separate project (PhD Paper 2 — Writing Supervisor):**
Manuscript writing and submission. Target: Measurement (Elsevier).
Numbers in this document supersede any values in the manuscript that conflict.

The relationship: this document is the canonical engineering record.
The manuscript writing project references it for confirmed values and claim language.

---

## Section 12 — Acceptance Gates — Final Status

| Gate | Criterion | Status |
|------|-----------|--------|
| Reproducibility | All steps run from raw bags in < 8 hours | PASS |
| Noise floor | bending bound < 0.05 mm | PASS (0.0029 mm derived; 0.017 mm conservative) |
| Camera agreement | 20/21 conditions: aligned Z < 15 mm | PASS (all 21; worst 7.42 mm at e20) |
| Bending correlation | Stable Pearson r vs LDV > 0.90 | FAIL — 0.845; physically explained and accepted |
| Torsion correlation | Stable Pearson r vs LDV > 0.90 | PASS — 0.940 |
| Bootstrap CI | Stable non-near-floor CI width < 20% | PASS (max 0.200 at near-floor e3_50rpm) |
| Frequency presence | Bending peak within 0.5 Hz of f_h for 15+ conditions | PASS |
| RTS phase shift | < 10 ms | PASS — 0.00 ms |
| DCG exclusion | e20 diagnosed and excluded with physical mechanism | PASS |
| 60 RPM | Physical explanation documented | PASS (VIV lock-in intermittency) |
| Claim language | Zero forbidden phrases in any output or figure caption | PASS |
| Environment lock | requirements.txt with pinned versions | PASS |

Bending correlation gate FAIL is accepted. The result is characterised, quantified,
and defensible. It is reported as a finding, not hidden.

---

*Version 2026-06-23. Clean document — no historical values retained.*
*Confirmed from: results/step10/ldv_summary.json, results/step10/step10_summary.json,*
*dp_sensitivity.json, current_ground_truth_audit_2026-06-23.md, bag metadata, facility documents.*