# OMRPR — Project Context and Design Rationale
**Prepared by:** Ammar Ajmal (PhD Researcher)
**Date:** 2026-06-16
**Last updated:** 2026-07-02 — Option B canonical switch (Tunnel A LDV 2024): LDV geometry, bending/torsion comparison numbers, and 60RPM status corrected against `claim_boundary.md` v2.1. See update summary at bottom. Earlier update (2026-06-30): stale aerodynamic parameters, tunnel attribution, and timing value corrected against OMRPR_SUPERVISOR_GUIDELINE.md (2026-06-23). Added Step 02b (DCG).
**Status:** Active
**NOTE:** f_h/f_α/damping values below are UNVERIFIED pending a provenance check (2025 standalone LDV session Sept 2025 vs. 2024 TESolution free-vibration data) — left unchanged in this pass.

> This document captures the experimental context, pipeline design decisions, confirmed parameter values, known pitfalls, and claim boundaries for the OMRPR offline multi-camera displacement reconstruction project.

> When numbers in this document conflict with confirmed manuscript values, the manuscript project wins.
> Key confirmed overrides are listed explicitly in Section 2.4 and Section 0 below.

---

## Section 0 — Confirmed Overrides (Read Before Anything Else)

These values were confirmed from facility documents AFTER this briefing was first written.
They override older values that appear elsewhere in this document.

**2026-07-02 SUPERSESSION NOTICE:** The dside/dp row below (130mm / dp=1.538, 2025 standalone LDV
session) was itself superseded on 2026-07-01 by the Option B canonical switch to the 2024 paired-session
geometry: **dside = 100 mm, dp = 2.0**. See `claim_boundary.md` v2.1. The rest of this table
(f_h/f_α/damping/timing) is unaffected by the Option B switch and left as-is pending a separate
provenance check.

**2026-07-03 RESOLVED — facility naming corrected:** "Tunnel B" throughout this table (and the rest of
this document) was a mislabel for the **2025 standalone LDV session** — confirmed to be the same
physical wind tunnel facility ("Tunnel A") as the 2024 paired session and 2025 camera bags, just a
different test session with a repositioned sensor rig. There is only one physical facility. Also: the
Option B canonical geometry (dp=2.0, dside=100mm) is now independently vendor-verified — see
`RESULTS_LOG.md` "2026-07-03 RESOLVED" entry.

| Parameter | Old Value (DO NOT USE) | Confirmed Value | Source |
|-----------|----------------------|-----------------|--------|
| LDV dside | 130 mm (superseded 2026-07-01 — B0, 2025 standalone LDV session) | **100 mm** | Option B canonical (2024 paired session, Tunnel A facility) — `claim_boundary.md` v2.1 |
| LDV db | 200 mm | **200 mm** | Same document |
| LDV torsion scaling dp | 1.538 (superseded 2026-07-01 — B0, 2025 standalone LDV session) | **dp = 2.0** | Option B canonical (2024 paired session, Tunnel A facility) — `claim_boundary.md` v2.1 |
| LDV pvolt | not specified | **2.7 cm/V** | `BRID2D1_choi.m` |
| LDV fs | not specified | **360 Hz** | `BRID2D1_choi.m` |
| Bridge chord width B | 34.4 cm (from Lee2016) | **0.40 m** | Model setup sheet (교폭=0.4m) |
| Natural freq f_h | ~1.95 Hz | **1.4323 Hz** | Free-vibration LDV, 2025 standalone LDV session |
| Natural freq f_α | ~5.15 Hz | **3.0827 Hz** | Free-vibration LDV, 2025 standalone LDV session |
| Frequency ratio | 2.64 | **2.152** | Derived from 1.4323 / 3.0827 |
| Structural damping | 0.28% | **~0.31%** | Log-decrement, 2025 standalone LDV session free-vibration |
| Max pairwise timing drift | not specified | **20.03 ms (cam1–cam3, e3_50rpm)** | Step 09 timing audit (clean pipeline) |
| Camera bags tunnel | not specified | **Tunnel A facility, October 2025** | OMRPR_SUPERVISOR_GUIDELINE 2026-06-23; "Tunnel B" corrected to "Tunnel A" facility 2026-07-03 |
| LDV reference tunnel (2025 standalone session) | same as camera | **Same Tunnel A facility, September 2025, different session/rig mounting** | Facility records |

**Validated results — SUPERSEDED 2026-07-01/02 by Option B canonical (Tunnel A LDV 2024). Current locked
numbers are in `claim_boundary.md` v2.1: bending r≈0.960 (19 stable cond., includes 60RPM after the
2026-07-02 correction), RMSE≈0.293mm, MAE≈0.221mm, ratio≈1.261×; torsion r≈0.968, ratio≈0.785×.
The table below is the retired B0 (2025 standalone LDV session, dp=1.538) result — kept for history, DO NOT USE in the manuscript:**

| Metric | Value (B0, superseded) | Notes |
|--------|-------|-------|
| Bending Pearson r (stable, 18 cond.) | 0.845 | Superseded — see current numbers above |
| Bending Spearman ρ (stable) | 0.864 | |
| Bending MAE (stable) | 0.484 mm | |
| Bending RMSE (stable) | 0.719 mm | |
| Bending mean ratio camera/LDV (stable) | 1.339× | |
| Torsion proxy Pearson r (stable) | 0.940 | |
| Torsion proxy Spearman ρ (stable) | 0.928 | |
| Torsion proxy MAE (stable) | 0.549 mm | |
| Torsion proxy RMSE (stable) | 0.771 mm | |
| Torsion proxy mean ratio camera/LDV (stable) | 0.599× | dp=1.538, superseded geometry |
| Static noise floor bending | 0.017 mm RMS | From Step 09 static bags (unaffected by Option B switch) |
| Static noise floor torsion proxy | 0.033 mm RMS | From Step 09 static bags (unaffected by Option B switch) |
| Raw inter-camera Z agreement (cam1–cam2) | ~388 mm | Physical camera separation (unaffected) |
| Aligned inter-camera Z agreement (e7_90rpm) | 2.053 mm std (~189× improvement) | Step 06 baseline alignment (unaffected) |
| RTS smoother phase shift | 0.00 ms (all 21 conditions) | Step 11, non-causal (unaffected) |
| RTS smoother amplitude ratio | 0.999 (stable); 0.961–0.966 (near-floor e0, e1) | Step 11 (unaffected) |

**Step 10 bending result — updated status:** Under Option B (2024 paired session, Tunnel A facility), bending Pearson r ≈ 0.960
PASSES the >0.90 gate cleanly across all 19 stable conditions (60RPM included after the 2026-07-02
LDV-value correction) — no gate failure to explain. The B0-era "regime-dependent cross-axis sensitivity"
narrative below is retained as historical context for why the *old* r=0.845 fell short, and the
underlying ~9.8° inter-camera misalignment remains a valid general uncertainty contribution
(see `claim_boundary.md` "Cam1–cam2 Y-axis misalignment" bullet), but it is no longer required as an
excuse for a failing gate:

*(B0-era explanation, retained for history):* The bending Pearson r of 0.845 (stable regime) reflected a
**regime-dependent cross-axis sensitivity**. In the torsion-dominated regime (90–220 RPM), torsional motion
leaks into the camera bending channel due to the ~9.8° inter-camera axis misalignment, inflating the
apparent bending amplitude by ~2×. In bending-dominated (40–80 RPM) and bending re-emergence (240–300 RPM)
regimes, the ratio returned to near-unity (0.84–1.24×).

**Earlier dp=2.0/dside=10cm values (superseded by the B0 lock below, kept for audit trail only):**
Bending r ≈ 0.959, Bending ratio ≈ 1.268×, Torsion r ≈ 0.968, Torsion ratio ≈ 0.785× — computed with
dp=2.0, dside=10cm (=100mm). This was itself superseded by the B0 lock (dp=1.538/dside=130mm) directly
above, which has now in turn been superseded by the current Option B canonical (dp=2.0/dside=100mm,
2024 paired session, Tunnel A facility) at the top of this section.

**2026-07-03 RESOLVED:** dside=10cm=100mm and dp=2.0 in this earlier entry are numerically identical
to the current Option B canonical geometry because they ARE the same geometry — both are independently
grounded in the same vendor-delivered `BRID2D1_choi.m` (Ver 2.1, 2024.11.11) shipped with the 2024
dataset (see `RESULTS_LOG.md` "2026-07-03 RESOLVED" entry). The small numeric difference
(0.959/1.268× here vs. 0.960/1.261× current) reflects the separate 18-vs-19-stable-condition (60RPM
reclassification) correction, not a geometry discrepancy — not independent coincidence, and not
uncertain provenance.

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
| Cam1–cam2 Y-axis misalignment | **Documented bounded uncertainty, no correction** | Inter-camera rotation ~9.8° (from audit of old extrinsics YAML) introduces amplitude-dependent bias A × (1 − cos 9.8°) / 2 in bending_avg_y_mm. At max observed amplitude 5 mm: **0.038 mm** = **13.0% of LDV RMSE (0.293 mm, Option B canonical — superseded B0 figure was 5.3% of 0.719 mm)**. Applying only the rotation component of uncertain extrinsics could introduce as much error as it removes. Decision permanently closed: state as bounded uncertainty in manuscript, no code correction. **Reviewer/viva defence sentence (copy verbatim):** "Averaging Y displacements across cam1 and cam2 without a common frame transform introduces a constant amplitude-dependent bias of 0.038 mm at 5 mm amplitude, derived from the ~9.8° inter-camera rotation measured from the extrinsic calibration. This bias is fixed throughout each experiment because camera positions do not change, making it a bounded, quantified uncertainty contribution rather than random error. At 0.038 mm it represents 13.0% of the LDV comparison RMSE of 0.293 mm and does not affect any manuscript claim." |
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

**Same-tunnel note (corrected 2026-06-30; facility naming corrected 2026-07-03):** Camera bags and
this section's LDV reference (2025 standalone LDV session, described below in 2.4/2.5) were both
recorded at the same Tunnel A facility. Camera: October 2025. LDV: September 2025. Gap: ~10 days —
NOT simultaneous. This is a same-tunnel, condition-matched, non-simultaneous comparison.
Required phrase: "same-tunnel (Tunnel A), condition-matched, separate recording sessions". NOTE: the
current canonical LDV reference for the manuscript is the 2024 paired session (Option B), not the
2025 standalone session described in this section — see `claim_boundary.md`.

### 2.4 Reference Sensor — LDV

- Operated separately from the camera system — NOT simultaneous
- Sampling rate: **360 Hz** (confirmed from BRID2D1_choi.m); NOT ~1000 Hz as originally estimated
- Covers conditions D01–D20 (20–320 RPM); no 0 RPM LDV reference
- **Units: centimeters (cm) in raw files** — convert explicitly to mm; name converted column `_mm_corrected`
- Confirmed geometry (Option B canonical, 2024 paired session, Tunnel A facility — superseded
  2026-07-01 the earlier dside=130mm/dp=1.538 B0 lock from the 2025 standalone LDV session):
  dside = 100 mm, db = 200 mm, dp = 2.0, pvolt = 2.7 cm/V. Vendor-verified 2026-07-03 — see
  `RESULTS_LOG.md`.

**LDV comparison is CONDITION-LEVEL ONLY.**
LDV and camera data were recorded at different times. You compare RMS, peak, and dominant
frequency PER CONDITION — not waveforms, not simultaneous traces.

### 2.5 Confirmed Aerodynamic Parameters

These are the document-confirmed values for this specific bridge model at this facility.
Do NOT use the older estimates that appear in some earlier documents.

| Parameter | Confirmed Value | Source |
|-----------|----------------|--------|
| Bridge chord width B | 0.40 m | Model setup sheet (교폭=0.4m) |
| Bending natural frequency f_h | 1.4323 Hz | Free-vibration LDV, 2025 standalone LDV session |
| Torsional natural frequency f_α | 3.0827 Hz | Free-vibration LDV, 2025 standalone LDV session |
| Frequency ratio f_α/f_h | 2.152 | Derived |
| Natural bending period T_h | 0.698 s | Derived from f_h |
| Structural damping | ~0.31% | Log-decrement, 2025 standalone LDV session free-vibration |
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
**ALWAYS write:** "a commercial aerodynamic testing facility in South Korea" (no citation)

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

Step 2b: Detection Completeness Gate (DCG)  [added 2026-06-30]
         Input:  detections.csv + summary.json per camera per condition
         Output: gate_status.json per condition → PASS or EXCLUDED
         Accept: detection_rate ≥ 0.95 per camera AND max_consecutive_miss ≤ 2 frames
         RESULT: e20_320rpm EXCLUDED (cam1: 60.8%, cam2: 61.3%; max_consec = 6)
                 All other 20 conditions: PASS (100% detection, 0 consecutive misses)
         Note:   N=2 threshold proven via interpolation error (corrected 2026-07-01 —
                 original formula used ω=π/T_h, missing factor of 4 in ε):
                   ε = A(2πg/T_h)²/8 < noise floor
                   At A=1.25 mm, g=2 frames (33 ms), T_h=0.698 s → ε=0.0141 mm SAFE
                   At N=3 frames (50 ms) → ε=0.0317 mm > 0.017 mm UNSAFE
                 Physical mechanism (e20 exclusion):
                   v_peak = 67.8 px/frame > w_cell = 29 px/frame → motion blur
                   FFT of miss-indicator: dominant peak at 5.87 Hz = 2 × 2.932 Hz (2×f_struct)
                   93.4% of 717 missed frames cluster in equilibrium band (cy 300–540 px)
                 cam3 unaffected: v_peak = 18.7 px/frame < threshold; amp = 2.19 mm (clean)
                 cam3 amplitude 2.19 mm is the ONLY valid result for e20 — report separately
                 Hardware design rule: t_exp < w_cell/v_peak = 7.1 ms (future campaigns)

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
         Accept: Bending peak within ±0.5 Hz of f_h = 1.4323 Hz for stable conditions
                 Torsion proxy peak near f_α = 3.0827 Hz
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
                 Max pairwise timing drift to report: 20.03 ms (cam1–cam3, e3_50rpm, Step 09 result)

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
13.0% of the LDV comparison RMSE of 0.293 mm, Option B canonical (see Section 0.5 for the full decision rationale).

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

4. **e20_320rpm is DCG-excluded (cam1/cam2).** Motion blur at equilibrium crossing is the confirmed physical mechanism (FFT at 2×f_struct = 5.87 Hz; v_peak = 67.8 px/frame > w_cell = 29 px/frame; 93.4% of misses at equilibrium). cam3 is unaffected (v_peak = 18.7 px/frame < threshold); cam3 amplitude 2.19 mm is reported separately as a pre-flutter trend data point. Never report cam1/cam2 values (9.84 mm) for this condition — they are interpolation artifacts.

5. **60 RPM is a stable condition (updated 2026-07-02).** The B0-era ~0.05× ratio and "VIV
   aerodynamic intermittency" diagnosis are retracted — the underlying 1.766mm LDV bend RMS figure
   could not be traced to any raw-data computation. The corrected LDV bend RMS (0.0492mm) gives a
   ratio of ~1.81× and is not an outlier; 60 RPM is now included in the 19-condition stable-regime
   statistics like any other condition. Do not diagnose or report it separately.

6. **Facility anonymized.** Never write TESolution or any city name.
   Always write "a commercial aerodynamic testing facility in South Korea" (no citation)

7. **No LDV-equivalent accuracy claim.** Current locked ratios (Option B canonical, `claim_boundary.md`
   v2.1): ≈1.261× bending, ≈0.785× torsion (dp=2.0, Tunnel A 2024). The B0 ratios (1.339× bending,
   0.599× torsion — dp=1.538, 2025 standalone LDV session) are superseded and must never be used.

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

### Phase 2: Detection + Quality + DCG Gate — COMPLETE
- Step 02: AprilTag detection ✓ (SOLVEPNP_IPPE_SQUARE; all 21 conditions)
- Step 02b: Detection Completeness Gate ✓ — e20 EXCLUDED (cam1/cam2 blur); cam3 clean (2.19 mm)
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

### Phase 6: LDV Comparison — COMPLETE (updated 2026-07-02, Option B canonical)
- Step 10 ✓ — Condition-level comparison table, Pearson/Spearman, ratio analysis (Tunnel A LDV 2024)
  - Bending Pearson r (stable, 19 cond.) ≈ 0.960 — PASS gate cleanly (see `claim_boundary.md` v2.1)
  - Torsion Pearson r (stable) ≈ 0.968 — PASS
  - 60 RPM: included in stable-regime statistics (2026-07-02 LDV-value correction); no longer flagged
  - 320 RPM: cam1/cam2 DCG-excluded (motion blur); cam3 reported separately as pre-flutter trend point
  - Superseded (B0, 2025 standalone LDV session): bending r=0.845 FAIL gate, torsion r=0.940 PASS — DO NOT USE

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
- Cam1–cam2 Y-axis misalignment: bounded, quantified — 0.038 mm at 5 mm amplitude (13.0% of LDV RMSE
  0.293 mm, Option B canonical); fixed bias, not random; stated as uncertainty contribution
  (superseded B0 figure: 5.3% of 0.719 mm — DO NOT USE)
- Static noise floor: bending 0.017 mm RMS, torsion proxy 0.033 mm RMS
- Bootstrap within-run stability: ~13–15% CI width for stable non-near-floor conditions
- Timing mitigation: 20.03 ms max pairwise drift (cam1–cam3, e3_50rpm), software common-grid only
- 60 RPM case: included in the 19-condition stable-regime statistics (2026-07-02 LDV-value correction);
  the earlier "VIV aerodynamic intermittency" diagnosis is retracted — do not use it
- e20_320rpm cam1/cam2: DCG-excluded — motion blur (v_peak = 67.8 px/frame > 29 px/frame); cam3 amplitude 2.19 mm reported separately as pre-flutter trend data point

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
| commercial aerodynamic testing facility in South Korea (no citation) | TESolution / any city name / [Lee2016] (identifies TESolution via author affiliation) |

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
| Reproducibility | All 13 steps (incl. Step 02b) run from raw bags in < 8 hours with one command |
| Noise floor | bending_avg_y_mm static RMS < 0.05 mm |
| Camera agreement | 20/21 conditions: aligned Z < 15 mm after baseline alignment |
| Bending correlation | Stable regime Pearson vs LDV > 0.90 (19 cond., includes 60 RPM as of 2026-07-02) |
| Torsion proxy correlation | Stable regime Pearson vs LDV > 0.90 |
| Bootstrap CI | Stable non-near-floor mean relative CI width < 20% |
| Frequency presence | Bending peak within 0.5 Hz of 1.4323 Hz for 15+ stable conditions |
| RTS phase shift | < 10 ms (B1 stage) |
| 60 RPM | Included in stable-regime statistics (2026-07-02 LDV correction) — no separate explanation needed |
| Claim language | Zero forbidden phrases in any output or figure caption |
| Environment lock | requirements.txt with pinned versions committed to git |

---

*Updated 2026-06-17. Supersedes version dated 2026-06-16.*
*Key changes: Section 0 validated results table replaced with actual clean-implementation values;*
*Step 10 bending r explanation added; Section 0.5 RTS Q-formulation decision added;*
*Section 9 pipeline status updated to all 13 steps complete (incl. Step 02b).*

---

## 2026-06-30 Update Summary (against OMRPR_SUPERVISOR_GUIDELINE.md 2026-06-23)

The following values were corrected. See G:\omrpr\docs\OMRPR_SUPERVISOR_GUIDELINE.md for full canonical reference.

| Location | Old value | New value | Reason |
|----------|-----------|-----------|--------|
| Section 0 override table — f_h | 1.430 Hz | 1.4323 Hz | Free-vib LDV, Tunnel B (confirmed) |
| Section 0 override table — f_α | 3.103 Hz | 3.0827 Hz | Free-vib LDV, Tunnel B (confirmed) |
| Section 0 override table — ratio | 2.17 | 2.152 | Derived from confirmed frequencies |
| Section 0 override table — damping | ≈ 1.9% | ~0.31% | Log-decrement, Tunnel B (confirmed) |
| Section 0 override table — timing | 20.0 ms | 20.03 ms | Exact value from step09 result |
| Section 0 override table — camera bags tunnel | Tunnel A | Tunnel B | Corrected per SUPERVISOR_GUIDELINE 2026-06-23 |
| Section 0.5 — misalignment % | 12.8% of RMSE (0.297 mm) | 5.3% of LDV RMSE (0.719 mm) | Use LDV comparison RMSE, not old internal RMSE |
| Section 0.5 — RTS amplitude ratio | 0.957–1.000 | 0.999 stable; 0.961–0.966 near-floor | From SUPERVISOR_GUIDELINE confirmed results |
| Section 2.3 — tunnel note | Cross-tunnel (Camera A, LDV B) | Same-tunnel (both Tunnel B) | Confirmed per SUPERVISOR_GUIDELINE 2026-06-23 |
| Section 2.5 — all aerodynamic parameters | Old estimates | Confirmed values (see table) | Confirmed from free-vib measurements |
| Section 4 Step 8 — f_h | 1.430 Hz | 1.4323 Hz | Confirmed |
| Section 4 Step 8 — f_α | 3.103 Hz | 3.0827 Hz | Confirmed |
| Section 4 Step 9 — timing | 20.0 ms | 20.03 ms | Exact value |
| Section 6 Rule 4 — e20 framing | "high-wind unstable, report separately" | DCG-excluded with full motion blur diagnosis | DCG work completed 2026-06-18/19 |
| Section 6 Rule 7 — old ratios | "1.268× bending, 0.785× torsion" | "1.339× bending, 0.599× torsion" | Correct geometry (dp=1.538) |
| Section 10 — timing claim | 20.0 ms | 20.03 ms | Exact value |
| Section 10 — e20 claim | "high-wind unstable, reported separately" | DCG-excluded; cam3 2.19 mm separately | DCG framing |
| Section 13 — frequency gate | 1.430 Hz | 1.4323 Hz | Confirmed |

**Note:** Step 02b (Detection Completeness Gate) exists in the codebase pipeline (13 steps total)
but has not been added to this document's pipeline listing (Section 4). See RESULTS_LOG.md
for Step 02b result entry and pipeline_diagram.md for the updated diagram.

---

## 2026-07-02 Update Summary (Option B canonical switch, against claim_boundary.md v2.1)

The following values were corrected. See `claim_boundary.md` v2.1 for the full canonical reference
and changelog. **f_h/f_α/damping/timing values are NOT part of this switch and are unchanged pending
a separate provenance check.**

| Location | Old value (B0, Tunnel B) | New value (Option B, Tunnel A 2024) | Reason |
|----------|---------------------------|--------------------------------------|--------|
| Section 0 — LDV dside | 130 mm | 100 mm | Option B canonical switch, 2026-07-01 |
| Section 0 — LDV dp | 1.538 | 2.0 | Option B canonical switch, 2026-07-01 |
| Section 0 — Bending r (stable) | 0.845 (18 cond.) | ≈0.960 (19 cond.) | Option B + 2026-07-02 60RPM correction |
| Section 0 — Bending RMSE/MAE/ratio | 0.719mm / 0.484mm / 1.339× | ≈0.293mm / ≈0.221mm / ≈1.261× | Option B canonical |
| Section 0 — Torsion r / ratio | 0.940 / 0.599× | ≈0.968 / ≈0.785× | Option B canonical |
| Section 2.4 — LDV geometry | dside=130mm, dp=1.538 | dside=100mm, dp=2.0 | Option B canonical |
| Section 6 Rule 5 — 60 RPM status | "VIV outlier, report separately" | Stable condition, included in 19-cond. stats | 2026-07-02 LDV value correction |
| Section 6 Rule 7 — ratios | 1.339× bending, 0.599× torsion | ≈1.261× bending, ≈0.785× torsion | Option B canonical |
| Section 9 Phase 6 — bending gate | r=0.845 FAIL (explained) | r≈0.960 PASS | Option B canonical |
| Section 10 — misalignment % | 5.3% of 0.719mm | 13.0% of 0.293mm | Option B canonical (same 0.038mm absolute bias) |
| Section 10 — 60 RPM claim | "VIV intermittency" | Included, no separate claim needed | 2026-07-02 correction |
| Section 13 — bending gate / 60 RPM row | excludes 60 RPM / needs explanation | includes 60 RPM / no explanation needed | 2026-07-02 correction |
