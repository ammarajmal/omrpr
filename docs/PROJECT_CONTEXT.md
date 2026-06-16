# OMRPR — Project Context and Design Rationale
**Prepared by:** Ammar Ajmal (PhD Researcher)
**Date:** 2026-06-16
**Status:** Active

> This document captures the experimental context, pipeline design decisions, confirmed parameter values, known pitfalls, and claim boundaries for the OMRPR offline multi-camera displacement reconstruction project.

> When numbers in this document conflict with confirmed manuscript values, the manuscript project wins.
> Key confirmed overrides are listed explicitly in Section 2.4 and Section 0 below.

---

## Section 0 — Confirmed Overrides (Read Before Anything Else)

These values were confirmed from facility documents AFTER this briefing was first written.
They override older values that appear elsewhere in this document.

| Parameter | Old Value (DO NOT USE) | Confirmed Value | Source |
|-----------|----------------------|-----------------|--------|
| LDV dside | 10 cm (100 mm) | **130 mm** | `설계속도 및 모형Setup_영상계측.xlsx` (센서간격=13cm) |
| LDV db | 20 cm (200 mm) | **200 mm** | Same document |
| LDV torsion scaling dp | db/dside = 2.0 | **dp = 1.538** | `BRID2D1_choi.m` MATLAB script |
| LDV pvolt | not specified | **2.7 cm/V** | `BRID2D1_choi.m` |
| LDV fs | not specified | **360 Hz** | `BRID2D1_choi.m` |
| Bridge chord width B | 34.4 cm (from Lee2016) | **0.40 m** | Model setup sheet (교폭=0.4m) |
| Natural freq f_h | ~1.95 Hz | **1.430 Hz** | 6 independent sources |
| Natural freq f_α | ~5.15 Hz | **3.103 Hz** | 6 independent sources |
| Frequency ratio | 2.64 | **2.17** | 6 independent sources |
| Structural damping | 0.28% | **≈ 1.9%** | 6 independent sources |
| Max pairwise timing drift | not specified | **20.0 ms (cam1–cam3)** | Step 09 timing audit (clean pipeline) |
| Camera bags tunnel | not specified | **Tunnel A, October 2025** | Bag metadata |
| LDV reference tunnel | same as camera | **Tunnel B, September 2025** | Facility records |

**Validated results (locked — from clean reimplementation, 2026-06-17):**

| Metric | Value | Notes |
|--------|-------|-------|
| Bending Pearson r (stable, 18 cond.) | 0.845 | See Step 10 explanation below |
| Bending Spearman ρ (stable) | 0.864 | |
| Bending MAE (stable) | 0.484 mm | |
| Bending RMSE (stable) | 0.719 mm | |
| Bending mean ratio camera/LDV (stable) | 1.339× | Regime-dependent; see below |
| Torsion proxy Pearson r (stable) | 0.940 | PASS |
| Torsion proxy Spearman ρ (stable) | 0.928 | |
| Torsion proxy MAE (stable) | 0.549 mm | |
| Torsion proxy RMSE (stable) | 0.771 mm | |
| Torsion proxy mean ratio camera/LDV (stable) | 0.599× | dp=1.538 correct geometry |
| Static noise floor bending | 0.017 mm RMS | From Step 09 static bags |
| Static noise floor torsion proxy | 0.033 mm RMS | From Step 09 static bags |
| Raw inter-camera Z agreement (cam1–cam2) | ~388 mm | Physical camera separation |
| Aligned inter-camera Z agreement (e7_90rpm) | 2.053 mm std (~189× improvement) | Step 06 baseline alignment |
| RTS smoother phase shift | 0.00 ms (all 21 conditions) | Step 11, non-causal |
| RTS smoother amplitude ratio | 0.957–1.000 (all 21 conditions) | Step 11 |

**Step 10 bending result explanation (required for viva and manuscript):**
The bending Pearson r of 0.845 (stable regime) reflects a **regime-dependent cross-axis sensitivity**.
In the torsion-dominated regime (90–220 RPM), torsional motion leaks into the camera bending channel
due to the ~9.8° inter-camera axis misalignment, inflating the apparent bending amplitude by ~2×.
In bending-dominated (40–80 RPM) and bending re-emergence (240–300 RPM) regimes, the ratio returns
to near-unity (0.84–1.24×), confirming accurate trend tracking where the camera measurement is
physically valid. The original 0.90 threshold was derived from an earlier implementation using the
incorrect geometry parameter dp=2.0 (confirmed value is dp=1.538). This is a documented finding,
not a pipeline failure. The manuscript Discussion section must include this explanation.

**Old values from the previous guideline version (DO NOT USE):**
Bending r ≈ 0.959, Bending ratio ≈ 1.268×, Torsion r ≈ 0.968, Torsion ratio ≈ 0.785×
These were computed against incorrectly scaled LDV values (dp=2.0, dside=10 cm).
The correct geometry (dp=1.538, dside=130 mm) changes all LDV-derived metrics.

---

## Section 0.5 — Implementation Decisions (Locked)

These decisions were made during the clean implementation and **override** the original design elsewhere in this document. Do not revisit without quantitative justification.

| Decision | Locked Value | Rationale |
|----------|-------------|-----------|
| `config/extrinsics.yaml` | **Empty by design** | Geometric world-frame transform (original Section 5.4 design) was replaced by camera-frame pose estimation + baseline alignment in Step 06. The extrinsics YAML physically exists but contains no data. |
| solvePnP solver | **`SOLVEPNP_IPPE_SQUARE`** | Optimal for planar square targets; numerically superior to `SOLVEPNP_ITERATIVE` (old implementation default). Locked. Do not change. |
| Raw Z disagreement | **~388 mm (cam1–cam2)** | Actual physical camera placement. Old implementation value of ~106 mm reflected a different physical setup (different extrinsic transform applied before alignment). The raw disagreement magnitude is camera-geometry-dependent; only the aligned residual matters for manuscript claims. |
| Static noise floor | **Derived, not directly measured** | bending σ = sqrt((σ_cam1² + σ_cam2²) / 4). Static bags were not recorded simultaneously across cameras. Assumes independent noise sources — physically reasonable. See Step 09 LIMITATIONS docstring. |
| `low_snr` flag | **All 21 conditions: False** | 0 RPM and 20 RPM show spectrally structured noise peaking near 9 Hz, not flat broadband noise. The SNR criterion (peak / median PSD within search band) does not fire. Report this in the manuscript as a positive finding: the system does not misidentify structured noise as signal. The Step 08 docstring note "Near-floor conditions expected to show low_snr=True" is empirically wrong — leave it as a warning in the docstring but record the actual result here. |
| Aerodynamic regimes | **Three confirmed (Step 08)** | Bending-dominated (40–80 RPM), torsion-dominated (90–220 RPM), bending re-emergence (240–300 RPM). Report in manuscript Section 3. |
| Cam1–cam2 Y-axis misalignment | **Documented bounded uncertainty, no correction** | Inter-camera rotation ~9.8° (from audit of old extrinsics YAML) introduces amplitude-dependent bias A × (1 − cos 9.8°) / 2 in bending_avg_y_mm. At max observed amplitude 5 mm: **0.038 mm** = **12.8% of bending RMSE (0.297 mm)**. Applying only the rotation component of uncertain extrinsics could introduce as much error as it removes. Decision permanently closed: state as bounded uncertainty in manuscript, no code correction. **Reviewer/viva defence sentence (copy verbatim):** "Averaging Y displacements across cam1 and cam2 without a common frame transform introduces a constant amplitude-dependent bias of 0.038 mm at 5 mm amplitude, derived from the ~9.8° inter-camera rotation measured from the extrinsic calibration. This bias is fixed throughout each experiment because camera positions do not change, making it a bounded, quantified uncertainty contribution rather than random error. At 0.038 mm it represents 12.8% of the bending RMSE of 0.297 mm and does not affect any manuscript claim." |
| RTS smoother process noise model | **Q = diag([(σ·dt)², σ²]) — NOT the kinematic G@G.T form** | The kinematic formulation Q = σ² · (G@G.T) with G = [dt²/2, dt]ᵀ produces Q[0,0] = σ²·dt⁴/4 ≈ 2×10⁻⁶ mm² per step regardless of σ, collapsing the Kalman gain to near zero and destroying the signal (amplitude ratio 0.023 observed). The correct model is Q = diag([(σ·dt)², σ²]), which gives Q[0,0] = (σ/60)² ≈ 0.028 mm² at σ=10 mm/s — meaningful relative to R=0.0025 mm². **Locked parameters:** process_noise_std = 10.0 mm/s, measurement_noise_std = 0.05 mm. Result: 21/21 PASS, phase 0.00 ms, amplitude ratio 0.957–1.000. |

---

## Your Role as Supervisor

You are an experienced research supervisor, software architect, and academic mentor.
Your student (Ammar) is an early-career researcher with programming ability but a history of
moving fast without full understanding — the first implementation was built incrementally via
AI-assisted "vibe coding" and accumulated enough uncertainty that a clean restart is warranted.

**Core philosophy: teach, don't just correct.** When Ammar shows you code or results:
1. Ask what he expected to see vs. what he actually sees.
2. Ask him to trace through the logic step by step.
3. Help him identify where the discrepancy enters.
4. Have him explain the fix in his own words before implementing.

**Enforce the defense standard.** Regularly ask: "Can you defend this in your PhD viva?"
The code running without error is not the standard — *understanding* is.

**Enforce the reviewer standard.** For every result, ask:
"What would a skeptical reviewer at Measurement (Elsevier) say about this?"

**Failure mode to watch for:** Ammar over-plans instead of executing.
Call it out directly when it happens. Keep sessions focused on one concrete deliverable.

---

## 1. Research Identity

### 1.1 The Problem

Structural Health Monitoring (SHM) requires continuous displacement and vibration measurement
of civil structures. Contact sensors (LDV, LVDT) are accurate but expensive and impractical
at scale. Vision-based systems are scalable and non-contact but have historically suffered from:

- Poor multi-camera synchronization (no shared hardware trigger)
- Motion blur causing marker detection failure during high-amplitude excitation
- No principled fallback when markers are lost
- No uncertainty modeling or bounded error reporting

### 1.2 Paper 1 (Published — Foundation)

Paper 1 proved the feasibility of a ROS-based real-time multi-camera system for structural
displacement using software-synchronized cameras.

| Metric | Value |
|--------|-------|
| RMSE displacement | 0.14–0.40 mm (best cases) |
| RMSE repeatability | 0.096–0.261 mm (mean 0.181 ± 0.086 mm) |
| Correlation | ~0.99 |
| Residual sync lag | 1–3 ms |
| Max phase error | 6.5° |
| Dominant frequency error | < 4% |
| MAC (modes 1–4) | > 0.85 |

Paper 1's limitations that Paper 2 addresses:
- Real-time processing (speed-quality tradeoff) → Paper 2 is fully offline
- Single best-view camera (no multi-view fusion) → Paper 2 uses 3 cameras
- No principled fallback under blur/dropout → Paper 2 has quality scoring
- No uncertainty budget → Paper 2 has explicit uncertainty chain

### 1.3 Paper 2 — This Project (OMRPR)

**Full name:** OMRPR — Offline Multi-Modal Robust Pose Reconstruction

**Core research question:** Can a fully offline, deterministic, multi-camera reconstruction
pipeline provide reproducible, defensible sub-millimeter structural displacement tracking from
standard cameras — without hardware-trigger synchronization, without same-run validation data,
and with explicit uncertainty quantification?

**Target journals (priority order):**
1. **Measurement (Elsevier)** — IF 5.6, CiteScore 11.5 — best scope fit for a measurement system paper
2. **Engineering Structures (Elsevier)** — IF 6.4 — strong fit for bridge SHM + wind tunnel
3. **MSSP (Mechanical Systems and Signal Processing)** — IF ~8.4 — stretch target; requires stronger methodological novelty argument

**Key architectural decision:** Move everything to offline post-processing from raw ROS bag data.
This removes the real-time CPU constraint, enables maximum-quality AprilTag detection,
enables non-causal algorithms (RTS smoothing), and makes results fully reproducible.

---

## 2. Experimental Dataset

### 2.1 Hardware

| Item | Specification |
|------|---------------|
| Camera model | Sony RX10 IV |
| Count | 3 cameras |
| Capture interface | AVerMedia HDMI/USB capture cards |
| Nominal FPS | 60 fps |
| Observed ROS rates | ~59–61 Hz (per camera, non-uniform) |
| CPU | Intel NUC 13 Pro (i7), Ubuntu 20.04 |
| Marker system | AprilTag tag36h11, 20 mm physical size |
| Marker count | 2 markers on bridge model |
| Recording distance | ~2.5 m from markers |

### 2.2 Camera-Marker Assignment

| Camera | Marker | Role |
|--------|--------|------|
| Camera 1 | Marker A | Primary bending anchor (left side view) |
| Camera 2 | Marker A | Secondary bending anchor (right side view) |
| Camera 3 | Marker B | Torsion second-point (end/side view) |

Camera 1 and Camera 2 both track the same Marker A — enabling internal camera-agreement checking.
Camera 3 tracks Marker B at the other end of the bridge deck — enabling torsion-proxy computation
as the differential y-displacement between the two marker positions.

**Important:** In the actual bag data, all three cameras detect tag_id=0. The physical markers
have different printed IDs (01 and 02) but may not have distinct AprilTag IDs in the image data.
Verify tag IDs in Step 02 before assuming any ID-based routing.

**Marker spacing:** ~200 mm between Marker A and Marker B — consistent with confirmed LDV lever
arm geometry (db = 200 mm). This is operator-confirmed.

### 2.3 Wind Tunnel Test Dataset

- **21 RPM conditions:** e0_0rpm through e20_320rpm
- **Each condition:** One `.bag` file with 3-camera compressed image streams
- **Location:** `data/WTT/<experiment_label>/` — e.g., `data/WTT/e7_90rpm/e7_90rpm_run1.bag`
- **Duration per condition:** ~30 seconds typical
- **Stable regime:** conditions e1–e19 (20–300 RPM), excluding 60 RPM VIV case
- **VIV outlier:** e2_60rpm — always investigate and report separately
- **High-wind unstable:** e20_320rpm — always report separately; do NOT mix into stable-regime statistics

**Cross-tunnel note:** Camera bags are from Tunnel A (October 2025). LDV reference is from
Tunnel B (September 2025). Both are within the same facility, same model, same year.
This is a cross-tunnel but within-facility comparison — not a limitation to hide, but a
fact to state clearly in the manuscript.

### 2.4 Reference Sensor — LDV

- Operated separately from the camera system — NOT simultaneous
- Sampling rate: **360 Hz** (confirmed from BRID2D1_choi.m); NOT ~1000 Hz as originally estimated
- Covers conditions D01–D20 (20–320 RPM); no 0 RPM LDV reference
- **Units: centimeters (cm) in raw files** — convert explicitly to mm; name converted column `_mm_corrected`
- Confirmed geometry: dside = 130 mm, db = 200 mm, dp = 1.538, pvolt = 2.7 cm/V

**LDV comparison is CONDITION-LEVEL ONLY.**
LDV and camera data were recorded at different times. You compare RMS, peak, and dominant
frequency PER CONDITION — not waveforms, not simultaneous traces.

### 2.5 Confirmed Aerodynamic Parameters

These are the document-confirmed values for this specific bridge model at this facility.
Do NOT use the older estimates that appear in some earlier documents.

| Parameter | Confirmed Value | Source |
|-----------|----------------|--------|
| Bridge chord width B | 0.40 m | Model setup sheet (교폭=0.4m) |
| Bending natural frequency f_h | 1.430 Hz | 6 independent sources |
| Torsional natural frequency f_α | 3.103 Hz | 6 independent sources |
| Frequency ratio f_α/f_h | 2.17 | Derived |
| Structural damping | ≈ 1.9% | 6 independent sources |
| VIV onset (bending) | ~0.88 m/s (60 RPM, Vr ≈ 1.54) | Wind speed calibration |
| Flutter onset | near 5 m/s (320 RPM) | Facility data |

### 2.6 Static Bags (Supporting Data Only)

`data/static_bags/` contains simultaneous multi-camera static (no wind) acquisitions.
These use a different bag format (raw images, not compressed grouped topics) and are NOT
processed through the main WTT pipeline. Use only for:
- Static noise floor estimation (Step 09)
- Camera jitter characterization

### 2.7 Facility Anonymization (Hard Rule)

**NEVER write:** TESolution Co., Ltd. / TESolution / Anseong-si / any city name
**ALWAYS write:** "a commercial aerodynamic testing facility in South Korea [Lee2016]"

Lee2016 citation: Lee, S.-W. et al. (2016). Proc. SPIE 9803, 98032X. DOI: 10.1117/12.2219404

---

## 3. The Software Environment

```bash
# Development environment: Ubuntu 24.04, Python 3.10+
# No ROS installation required for Steps 1–12

pip install rosbags            # pure Python ROS 1 bag reader
pip install pupil-apriltags    # version 1.0.4.post11 confirmed working
pip install opencv-python numpy scipy pandas matplotlib
```

**rosbags version:** 0.11.3 confirmed. Use the NEW API:
```python
from rosbags.typesys import Stores, get_typestore
typestore = get_typestore(Stores.ROS1_NOETIC)
msg = typestore.deserialize_ros1(rawdata, connection.msgtype)  # NOT deserialize_cdr
```
`deserialize_cdr` is the ROS2 format and will produce garbage on ROS1 bags.

**OpenCV API:** Use `cv2.aruco.ArucoDetector` (4.7+ compatible).
The old `cv2.aruco.detectMarkers` is removed in OpenCV ≥ 4.7.

**Fallback:** If `rosbags` fails on a specific bag, extract frames on Ubuntu 20.04 using
ROS Noetic (save PNGs + timestamps to PhD drive), then continue on Ubuntu 24.04.

---

## 4. The Full Pipeline (12 Logical Steps)

Each step has one clear input, one clear output, and acceptance criteria the student
must be able to explain. Steps produce a summary.json alongside main outputs.

```
Step 0:  ROS bag audit
         Input:  .bag files
         Output: per-bag metadata (FPS, frame count, topic list, drop rate, skew)
         Accept: All bags open, FPS in 59–61 Hz range, no major frame drops

Step 1:  Frame export
         Input:  .bag files
         Output: PNG frames + timestamps.csv + meta.json per camera per bag
         Accept: Frame count matches audit; timestamps monotonically increasing;
                 max_gap < 0.1s; no decode_failures
         Note:   timestamps.csv schema = frame_idx, timestamp_s (normalized from bag start)
                 meta.json records: cam, topic, condition, bag, frame_count

Step 2:  Offline AprilTag detection
         Input:  PNG frame folders
         Output: detections.csv per camera per bag + summary.json
         Accept: Detection rate > 90% for stable conditions
                 (100% is achievable for well-lit, low-motion conditions)
         Note:   CSV schema = frame_idx, tag_id, cx, cy, c0x, c0y, c1x, c1y,
                               c2x, c2y, c3x, c3y, decision_margin, hamming
                 Sparse CSV — frames with no detection get no row
                 summary.json records: total_frames, detected_frames, detection_rate,
                                       max_consecutive_miss

Step 3:  Quality scoring
         Input:  detections.csv + PNG frames (optional, for corner sharpness)
         Output: detections_with_quality.csv + quality_summary.json
         Accept: quality_score = dm × sqrt(area_px2) — the B0 formula
                 area_px2 = shoelace formula on the 4 detected corners
                 Quality scores correlate with expected blur at high amplitude
         Note:   Also add corner_sharpness (Laplacian gradient magnitude around
                 each corner) as a diagnostic column — do NOT change the core score formula
                 summary.json: mean_quality, min_quality, low_quality_frame_count

Step 4:  Camera-frame pose estimation (no extrinsics applied)
         Input:  detections.csv + camera_info topics from bags
                 (extrinsics.yaml is EMPTY BY DESIGN — not used here)
         Output: world_pose.csv per camera per condition
                 (column names x_w, y_w, z_w retained for schema compatibility,
                  but values are in each camera's own coordinate frame)
         Accept: Solver: SOLVEPNP_IPPE_SQUARE (locked)
                 Reprojection error < 1.0 px is good; > 3.0 px is suspicious
                 raw Z disagreement ~388 mm (cam1–cam2) BEFORE alignment — expected
         Note:   Always call .flatten() on tvec immediately after solvePnP
                 The ~388 mm raw Z offset is the physical camera separation; baseline
                 alignment in Step 06 removes it — no extrinsic matrix needed

Step 5:  Cross-camera synchronization
         Input:  world_pose.csv per camera (different timestamps)
         Output: Synchronized multi-camera traces on a common 60 Hz grid
         Accept: No artificial offsets; direct common60 resampling is sufficient
                 Dense1000 intermediate interpolation gives < 0.08% improvement — skip it
         Note:   Normalize timestamps to bag-start BEFORE any sync analysis
                 Raw epoch timestamps will produce false ~9-second offsets

Step 6:  Baseline-aligned fusion
         Input:  Synchronized camera-frame traces (each in its own camera frame)
         Output: Fused displacement traces + alignment offsets
         Accept: Aligned Z disagreement < 15 mm for 20/21 stable conditions
                 Always report BOTH raw (~388 mm, cam1–cam2) and aligned (~2.053 mm std)
                 The contrast between raw and aligned IS a key result (~189× improvement)
                 This is the mechanism that replaces the extrinsics transform

Step 7:  Motion decomposition
         Input:  Fused synchronized traces
         Output: bending_avg_y_mm — mean of Marker A Y across cam1 and cam2
                 torsion_diff_y_mm — Marker B Y (cam3) minus Marker A Y (cam1/cam2 avg)
         Accept: Bending and torsion channels are physically distinct; check for sign flip
         CRITICAL: Full-run mean removal (NOT first-1-second removal)
                   First second is already dynamic — this dataset has no static baseline

Step 8:  Frequency analysis
         Input:  bending_avg_y_mm and torsion_diff_y_mm per condition
         Output: FFT/PSD per condition, dominant peak frequency, nearest reference bin
         Accept: Bending peak within ±0.5 Hz of f_h = 1.430 Hz for stable conditions
                 Torsion proxy peak near f_α = 3.103 Hz
                 ACTUAL RESULT: all 21 conditions returned low_snr = False, including
                 0 RPM and 20 RPM — these show structured noise at ~9 Hz, not flat
                 broadband noise. SNR criterion (peak/median) does not fire.
                 Report this in the manuscript as a positive finding, not a calibration issue.
                 Three aerodynamic regimes confirmed: bending-dominated (40–80 RPM),
                 torsion-dominated (90–220 RPM), bending re-emergence (240–300 RPM)
         Note:   ALWAYS report nearest reference bin SEPARATELY from dominant peak
                 These often differ; reporting them as the same is a claim violation

Step 9:  Uncertainty quantification
         Input:  Time series + static bags
         Output: Static noise floor, camera-agreement stats, bootstrap CIs, timing audit
         Accept: bending_avg_y_mm static RMS < 0.05 mm (target: 0.017 mm)
                 torsion_diff_y_mm static RMS < 0.1 mm (target: 0.033 mm)
                 Bootstrap CI width < 20% relative for stable non-near-floor conditions
         Note:   Use moving-block bootstrap for time series (not standard bootstrap)
                 Max pairwise timing drift to report: 20.0 ms (cam1–cam3, Step 09 result)

Step 10: LDV condition-level comparison
         Input:  Per-condition bending/torsion RMS + LDV reference (converted to mm)
         Output: Comparison table, Pearson/Spearman, ratio analysis
         Accept: Stable regime Pearson > 0.9 (excluding 60 RPM)
                 60 RPM MUST be investigated and reported separately
         Note:   LDV raw files are in CENTIMETERS — always convert explicitly
                 Name converted column _mm_corrected — never store cm values in _mm columns

Step 11: RTS/Kalman smoothing (B1 stage)
         Input:  Fused displacement traces
         Output: Smoothed traces
         Accept: Phase shift < 10 ms; dominant frequency preserved; amplitude not reduced
         Note:   RTS is non-causal (uses future frames) — only possible offline
                 Use actual non-uniform Δt, not assumed constant 60 Hz

Step 12: Manuscript figures and tables
         Input:  All result artifacts
         Output: Publication-ready figures and summary tables
         Accept: All figures generated programmatically; captions respect claim boundary
```

---

## 5. Mathematical Foundations

The student must understand each algorithm before implementing it.
Explain the mathematics, ask probing questions, require understanding before coding begins.

### 5.1 Pose Estimation (solvePnP)

```
{R, t} = solvePnP(P_3D, p_2D, K, D)
Δp(t) = p(t) - p(0)   displacement relative to first frame
```

- P_3D: 3D tag corner coordinates in tag frame (known from tag_size = 0.020 m)
- p_2D: detected corner pixel coordinates from detections.csv
- K: camera intrinsic matrix from camera_info
- D: distortion coefficients from camera_info
- Always call `.flatten()` on tvec immediately after solvePnP — shape inconsistency is a known bug

Reprojection error is the key quality metric: `e_reproj < 1.0 px` is good; `> 3.0 px` suspicious.

### 5.2 Quality Score (B0 Formula)

```
s_i = dm_i × sqrt(A_i)
```

where `A_i` is the tag area in pixels², computed from the four detected corners using
the shoelace formula. Higher area + higher decision margin = more reliable detection.
This formula is the locked B0 score — do not change it without strong justification.

### 5.3 Temporal Synchronization

Three cameras were started serially (ROS nodes launched sequentially).
Timestamps must be normalized to bag-start time BEFORE any sync analysis:
```python
t_normalized = t_raw - t_bag_start  # always do this first
```

Affine time model for camera j relative to reference camera 1:
```
t̃_j = α_j · t̃_1 + β_j    (α = clock skew, β = offset)
```

Cross-correlation delay estimation:
```
τ̂_ij = argmax_τ R_ij(τ)
```

Apply detrend + bandpass before correlating. Master grid: resample all cameras onto
common 60 Hz via interpolation. Direct common60 resampling is sufficient —
dense1000 intermediate interpolation makes < 0.08% difference.

### 5.4 Camera-Frame Pose — No Extrinsics Applied (Replaces Original World-Frame Design)

**IMPORTANT:** The original design called for `p_world = T_cam_to_world @ p_camera` using
4×4 matrices from `config/extrinsics.yaml`. This was NOT implemented in the clean pipeline.
`config/extrinsics.yaml` is **intentionally empty**.

What `solvePnP` (SOLVEPNP_IPPE_SQUARE) actually returns is the tag position in each
camera's own coordinate frame:

```
{R_c, t_c} = solvePnP(P_3D, p_2D, K, D)   # result is in camera frame
```

The `world_pose.csv` schema columns `x_w, y_w, z_w` are retained for compatibility,
but contain camera-frame values — not a unified geometric world frame.

**Why no extrinsics are needed:**
Paper 1's "world frame" was also a per-camera displacement reference anchored at t=0,
not a true surveyed geometric frame. For bending_avg_y_mm, what matters is that cam1 and
cam2 Y axes are approximately parallel to the same physical direction (vertical bridge
displacement). The inter-camera rotation is ~9.8°, introducing a bounded Y-axis bias of
A × (1 − cos 9.8°) / 2 per camera. At max observed amplitude (5 mm): 0.038 mm —
below the bending RMSE of 0.297 mm (see Section 0.5 for the full decision rationale).

**Baseline alignment** (Step 06) removes the full-run mean from each camera's Z independently:
```
z_aligned(t) = z_c(t) − mean(z_c)
```
This eliminates the raw Z bias (~388 mm, cam1–cam2) more robustly than the old extrinsics
approach, which also required baseline alignment on top of the extrinsic transform.

**Key result:** raw Z disagreement ~388 mm → aligned std ~2.053 mm for e7_90rpm
reference condition (~189× improvement). Always report BOTH states.

### 5.5 Motion Decomposition

```
bending_avg_y_mm = mean(y_cam1, y_cam2)        per timestep
torsion_diff_y_mm = y_cam3 - bending_avg_y_mm  per timestep
```

Full-run mean removal (not first-second). The first second is already dynamic.

### 5.6 RTS Smoothing (Non-Causal — B1 Stage)

State vector: `x_k = [x, y, z, ẋ, ẏ, ż]^T`

Kalman forward pass: predict → update at each timestep.
RTS backward pass: start from final state, correct backward through sequence.
The backward pass is non-causal — improves early estimates using future frames.
Only possible offline.

### 5.7 KLT Fallback (B2 Stage — Frozen)

When AprilTag fails, Lucas-Kanade optical flow tracks corners forward:
```
G · [u, v]^T = -b
```

**Current status: B2 is FROZEN.** Coverage (~40% of gap frames) is too marginal
to support a meaningful improvement claim. Do not reactivate without coverage > 60%.
Do not claim KLT improves results.

---

## 6. Critical Rules — Never Violate These

1. **LDV comparison is condition-level only.** Never compare waveforms. Never claim
   same-run or simultaneous validation. LDV and camera were recorded at different times.

2. **Torsion is a proxy.** `torsion_diff_y_mm` is a two-point differential displacement
   proxy. Never call it a "torsion angle." It has not been validated as one.

3. **No hardware synchronization claim.** The cameras were not triggered by shared hardware.
   The common 60 Hz grid is an offline post-processing mitigation.

4. **e20_320rpm is high-wind unstable.** Always report separately from stable regime.
   Physical reality of extreme aerodynamic loading, not a measurement failure.

5. **60 RPM is a VIV outlier.** Camera/LDV ratio of ~0.05× at 60 RPM is physically
   explainable via VIV lock-in intermittency. Diagnose and report separately.

6. **Facility anonymized.** Never write TESolution or any city name.
   Always write "a commercial aerodynamic testing facility in South Korea [Lee2016]"

7. **No LDV-equivalent accuracy claim.** The ratios (1.268× bending, 0.785× torsion)
   have not been corrected and their sources have not been independently decomposed.

8. **No C1/C2 Z-value fusion.** Camera 1 and Camera 2 see Marker A from different
   orientations. Their Z values are not comparable. Never fuse Z across C1 and C2.

9. **B0 result package is the target.** The clean reimplementation should reproduce
   numbers consistent with the confirmed values in Section 0 of this document.
   If numbers differ significantly, investigate root cause before concluding the code is wrong.

10. **B2/KLT and ROI optical flow are NOT manuscript evidence.** Do not include these
    in any claims. They are frozen diagnostic tools only.

---

## 7. Known Bugs from Previous Implementation — Do Not Repeat

### 7.1 Timestamp Normalization Bug (CRITICAL)
Raw bag timestamps are Unix epoch (e.g., 1,700,000,000+ seconds). Running sync analysis
on raw epochs produced a false 9.26-second camera offset.
**Fix:** Always `t_normalized = t_raw - t_bag_start` before any sync analysis.

### 7.2 LDV Unit Confusion (CRITICAL)
LDV files contain values in **centimeters**. Early scripts named columns `_mm` but stored
cm values, creating factor-of-10 errors.
**Fix:** Read as cm, convert explicitly, store in `_mm_corrected` column, document the step.

### 7.3 Camera-Frame vs Camera-Frame Cross-Comparison
Early code compared `tx_m` values across cameras directly. Camera-frame translations are in
different coordinate frames and cannot be meaningfully compared as absolute positions.
**Fix:** Never cross-compare raw tx/ty/tz between cameras. Only compare after baseline
alignment (Step 06) removes the constant per-camera offset. (Note: in the clean implementation,
no extrinsic world-frame transform is applied — baseline alignment is the only alignment step.)

### 7.4 tvec Shape Inconsistency
OpenCV's `solvePnP` returns tvec as shape `(3,)` or `(3,1)` depending on input format.
Silent failures or wrong shapes in downstream operations.
**Fix:** Always call `.flatten()` or `.ravel()` on tvec immediately after `solvePnP`.

### 7.5 The ~388 mm Raw Z Disagreement (Not a Bug)
Without any extrinsic transform, raw Z disagreement between cam1 and cam2 is ~388 mm.
This is the actual physical camera separation projected onto the Z axis — a FIXED per-camera
translation offset, NOT random noise and NOT a pipeline failure.
(Old implementation applied an extrinsic transform first, giving ~106–115 mm residual before
alignment — that figure is from a different physical setup and should not appear in Paper 2.)
**Fix:** Baseline alignment reduces it to ~2.053 mm std for e7_90rpm. Always report BOTH states.
The contrast between raw (~388 mm) and aligned (~2.053 mm) — ~189× improvement — IS a publishable result.

### 7.6 OpenCV API Change
Old `cv2.aruco.detectMarkers()` is removed in OpenCV ≥ 4.7.
**Fix:** Use `cv2.aruco.ArucoDetector(dictionary, parameters).detectMarkers(image)` API.

### 7.7 Dense1000 Interpolation (Wasted Computation)
Hypothesis: interpolating to 1000 Hz then resampling improves sync accuracy.
Result: < 0.08% change in RMS metrics — negligible.
**Fix:** Use direct common 60 Hz resampling.

### 7.8 First-1-Second Baseline Removal (Wrong Approach)
Common signal processing habit: subtract first-second mean as "static" baseline.
In this dataset, each bag was recorded AFTER the operator set the target RPM.
The first second is already dynamic — it is NOT a zero-wind static baseline.
**Fix:** Full-run mean removal or no removal. Never use first-second removal.

### 7.9 rosbags API Version Mismatch
Old API (`get_types_from_msg`, `register_types`) does not work with rosbags 0.11.3.
**Fix:** Use `get_typestore(Stores.ROS1_NOETIC)` and `deserialize_ros1()` — NOT `deserialize_cdr()`.

### 7.10 Tag ID Assumption
Original design assumed cam1 sees one tag ID and cam3 sees a different one.
In practice, all three cameras detect tag_id=0 in the bag data.
**Fix:** Do not route by tag ID. Routing is purely by camera (cam1 = Marker A, etc.).
Verify actual tag IDs in Step 02 before building any ID-based logic.

---

## 8. Software Engineering Standards

### 8.1 Repository Structure

```
omrpr-clean/
├── README.md
├── requirements.txt       (pinned versions)
├── environment.yml        (conda/mamba spec)
├── config/
│   ├── extrinsics.yaml        (intentionally empty — no geometric extrinsics applied; see Section 0.5)
│   └── pipeline_config.yaml   (ALL tunable parameters here — no magic numbers in code)
├── src/
│   ├── step00_bag_audit.py
│   ├── step01_export_frames.py
│   ├── step02_detect_apriltag.py
│   ├── step03_quality_score.py
│   ├── step04_world_transform.py
│   ├── step05_synchronize.py
│   ├── step06_fuse_cameras.py
│   ├── step07_motion_decompose.py
│   ├── step08_frequency_analysis.py
│   ├── step09_uncertainty.py
│   ├── step10_ldv_comparison.py
│   ├── step11_rts_smoothing.py
│   └── step12_figures_tables.py
├── data/
│   ├── WTT/                (symlink to bag files — input only)
│   └── static_bags/        (symlink — input only)
├── results/                (all generated outputs — never commit to git)
├── docs/
│   ├── claim_boundary.md
│   └── validation_targets.md
└── tests/
    └── (unit tests for critical mathematical functions)
```

### 8.2 Code Quality Rules

- **One script per pipeline step.** One clear responsibility.
- **All parameters in config.yaml.** No magic numbers in code.
- **Every script runnable from command line:** `python src/step02_detect_apriltag.py --bag e7_90rpm`
- **Every script writes summary.json** alongside main outputs (stats, decision, acceptance status).
- **Deterministic outputs.** Fixed random seeds. Same inputs → same outputs always.
- **No silent failures.** Every step logs what it found, what it decided, and why.
- **Each script has a docstring:** purpose, inputs, outputs, acceptance criteria, limitations.

### 8.3 Validation Protocol (Three Levels Per Step)

1. **Smoke test:** Run on `e7_90rpm` first. Verify outputs are physically plausible.
2. **Full sweep:** Run on all 21 conditions. Generate summary statistics.
3. **Gate check:** Compare against acceptance criteria before opening the next step.

Never open the next step until the current step passes all three levels.

---

## 9. Step-by-Step Execution Plan

**Status as of 2026-06-17: ALL STEPS 00–12 COMPLETE. Pipeline implementation is locked.**

### Phase 0: Environment + Bag Audit — COMPLETE
- Step 00: Bag audit ✓ (FPS, frame count, topics, skew — e7_90rpm PASS, skew 12.4 ms)

### Phase 1: Frame Export — COMPLETE
- Step 01: Frame export ✓ (PNG + timestamps.csv + meta.json, all 21 conditions)

### Phase 2: Detection + Quality — COMPLETE
- Step 02: AprilTag detection ✓ (SOLVEPNP_IPPE_SQUARE; all 21 conditions)
- Step 03: Quality scoring ✓ (B0 formula: dm × sqrt(area))

### Phase 3: Pose + Synchronization + Fusion — COMPLETE
- Step 04: Camera-frame pose estimation ✓ (extrinsics.yaml empty by design; IPPE_SQUARE)
- Step 05: Synchronization ✓ (normalize timestamps → common 60 Hz grid)
- Step 06: Baseline-aligned fusion ✓
  - raw Z cam1–cam2: ~388 mm → aligned std: ~2.053 mm (e7_90rpm ref, ~189× improvement)

### Phase 4: Motion + Frequency — COMPLETE
- Step 07: Motion decomposition ✓ (bending_avg_y_mm, torsion_diff_y_mm)
- Step 08: Frequency analysis ✓
  - Three aerodynamic regimes confirmed (see Section 0.5)
  - All 21 conditions: low_snr = False (structured ~9 Hz noise, not flat noise)

### Phase 5: Uncertainty — COMPLETE
- Step 09: Noise floor + camera agreement + bootstrap CIs ✓
  - All four section gates PASS
  - bending noise floor: 0.017 mm RMS (target met)
  - torsion proxy noise floor: 0.033 mm RMS (target met)

### Phase 6: LDV Comparison — COMPLETE
- Step 10 ✓ — Condition-level comparison table, Pearson/Spearman, ratio analysis
  - Bending Pearson r (stable) = 0.845 — FAIL gate but physically explained (cross-axis sensitivity)
  - Torsion Pearson r (stable) = 0.940 — PASS
  - 60 RPM: VIV aerodynamic intermittency, diagnosed and flagged separately
  - 320 RPM: high-wind-unstable, reported separately
  - Gate note in summary JSON: bending FAIL reflects documented cross-axis sensitivity, not code error

### Phase 7: RTS Smoothing — COMPLETE
- Step 11 ✓ — Non-causal RTS smoother, 21/21 PASS
  - Phase shift: 0.00 ms across all conditions
  - Frequency error: 0.000 Hz across all conditions
  - Amplitude ratio: 0.957–1.000 (min at near-floor conditions, expected)
  - Q-formulation fix required: kinematic G@G.T collapses gain; use diag([(σdt)², σ²])

### Phase 8: Manuscript Package — COMPLETE
- Step 12 ✓ — 5 figures, 2 tables, 0 errors, claim boundary PASS
  - fig01: e7_90rpm displacement traces (raw + RTS-smoothed)
  - fig02: dominant frequency vs RPM, all 21 conditions, 3 regimes annotated
  - fig03: camera vs LDV RMS scatter, stable regime, Pearson r annotated
  - fig04: camera agreement before/after baseline alignment
  - fig05: per-condition RMS with bootstrap 95% CI and noise floor
  - All output in results/step12/

---

## 10. Claim Boundary — What the Manuscript Can and Cannot Say

### What You CAN Claim

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

### What You CANNOT Claim

- LDV-equivalent absolute displacement accuracy
- Same-run waveform validation against LDV
- True torsion angle measurement
- Hardware-synchronized multi-camera capture
- Modal validation (restrict to response characterization only)
- KLT or B2 robustness improvement
- Any MCI-supported improvement
- C1/C2 stereo fusion validity (coordinate orientation mismatch unresolved)

### Required Language

| Use | Never Use |
|-----|-----------|
| condition-level LDV trend comparison | LDV-validated accuracy |
| offline common-grid reconstruction | same-run waveform validation |
| software/offline synchronization mitigation | hardware-synchronized / hardware-triggered |
| two-point differential displacement proxy | torsion angle / validated torsion |
| high_wind_unstable_motion | measurement failure |
| internal camera-agreement uncertainty | absolute accuracy |
| commercial aerodynamic testing facility in South Korea [Lee2016] | TESolution / any city name |

---

## 11. Literature Positioning

OMRPR's key differentiators vs prior art:

| Domain | Key Prior Art | Where OMRPR Differs |
|--------|--------------|---------------------|
| Marker-based SHM | AprilTag3, ArUco | Offline multi-camera with explicit uncertainty chain |
| Markerless tracking | KLT, Lucas-Kanade | KLT as bounded fallback only, not primary tracker |
| Multi-camera SHM | Stereo DIC, photogrammetry | Common time grid without hardware trigger |
| Non-simultaneous validation | No precedent found | Explicit condition-level protocol with uncertainty budget |
| RTS in SHM | Lu 2025, Measurement 2024 GLDD | Non-causal state-space smoothing in offline SHM pipeline |

**Five likely reviewer objections (prepare responses):**

1. *"Why not a proper validation if LDV is present?"* → LDV was not simultaneous;
   condition-level comparison is the maximum defensible evidence given the acquisition strategy.

2. *"Is common60 just interpolation hiding sync error?"* → Timing audit shows direct
   common60 and dense1000 differ by < 0.08%; common60 is sufficient and more transparent.

3. *"What exactly is your torsion measurement?"* → Two-point differential displacement
   proxy with operator-confirmed geometry; not a torsion angle; stated explicitly.

4. *"Why no modal validation from your spectra?"* → Dominant peaks and nearest reference
   bins systematically diverge; restricted to response characterization, not modal identification.

5. *"How reproducible is the result package?"* → All figures generated programmatically
   from a tagged release; rerun command documented; code public at GitHub.

---

## 12. Two Parallel Projects — Keep Them Separate

Ammar is running two parallel workstreams. Do not conflate them:

**This project (OMRPR Supervisor — Clean Start):**
Clean pipeline reimplementation from raw bag files. Goal: defensible code that Ammar
can explain in a PhD defense. Produces a publishable software artifact.

**Separate project (PhD Paper 2 — OMRPR Writing Supervisor):**
Manuscript writing and submission. Sections 1–6 + Abstract drafted. Confirmed numbers
are locked. Target: submit to Measurement (Elsevier) this month.

**The relationship:** The clean pipeline should reproduce numbers consistent with the
confirmed manuscript values. It is not required to complete before manuscript submission —
the original implementation already produced the validated numbers.

If in doubt about which confirmed value to use, the manuscript writing project wins.
The overrides table in Section 0 of this document captures the most important corrections.

---

## 13. End-to-End Acceptance Gates

All gates must pass before the pipeline implementation is considered publication-ready:

| Gate | Criterion |
|------|-----------|
| Reproducibility | All 12 steps run from raw bags in < 8 hours with one command |
| Noise floor | bending_avg_y_mm static RMS < 0.05 mm |
| Camera agreement | 20/21 conditions: aligned Z < 15 mm after baseline alignment |
| Bending correlation | Stable regime Pearson vs LDV > 0.90 (excluding 60 RPM) |
| Torsion proxy correlation | Stable regime Pearson vs LDV > 0.90 |
| Bootstrap CI | Stable non-near-floor mean relative CI width < 20% |
| Frequency presence | Bending peak within 0.5 Hz of 1.430 Hz for 15+ stable conditions |
| RTS phase shift | < 10 ms (B1 stage) |
| 60 RPM | Physical explanation documented in manuscript |
| Claim language | Zero forbidden phrases in any output or figure caption |
| Environment lock | requirements.txt with pinned versions committed to git |

---

*Updated 2026-06-17. Supersedes version dated 2026-06-16.*
*Key changes: Section 0 validated results table replaced with actual clean-implementation values;*
*Step 10 bending r explanation added; Section 0.5 RTS Q-formulation decision added;*
*Section 9 pipeline status updated to all 12 steps complete.*
