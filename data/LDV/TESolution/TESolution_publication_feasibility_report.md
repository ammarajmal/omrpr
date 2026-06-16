# Publication Feasibility Report — TESolution WTT Dataset

**Date:** 2026-06-09  
**Question:** Can the TESolution wind tunnel dataset (LDV reference + 3D video system, October 2024) support a new peer-reviewed publication in an impact-factor journal, without further laboratory or wind tunnel experiments?

**Short answer:** Borderline yes, but only as a narrowly scoped application/validation paper (Q2–Q3), not as a high-impact general contribution. Success depends on resolving four non-negotiable pre-conditions.

---

## 1. Summary of Available Data

| Asset | Availability | Quality |
|-------|-------------|---------|
| LDV reference (D1–D38, 360 Hz) | Complete | High |
| Video system CSVs (D0.csv–D37.csv) | 37 conditions | Good |
| Free vibration data (100 s, 57 FPS) | Yes | Good |
| Wind speed calibration table | Yes | High |
| Camera frame images (6 frames) | Yes | Evidence only |
| Raw video frames (for re-processing) | **NO** (2024) / YES as .bag (2025) | N/A / Reprocessable |
| Camera calibration (YAML) | **In codebase** (`sony_cam1_info.yaml`) | Good |
| Camera hardware specs | **In codebase** (MindVision MVSDK) | Good |
| Synchronization architecture | **In codebase** (`simple_camera_node.py`) | Documented |
| Dual-timestamp logs | **In every CSV** (`system_time` + `header_time`) | Available for jitter analysis |
| 2025 WTT offline bags (21 conditions, unprocessed) | YES | Raw — needs processing |

---

## 2. What Is Genuinely Novel (Publishable Contributions)

### 2.1 Novel application domain
Paper 1 (IEEE Access) validated the ROS/AprilTag framework on a shaking table (shear building, cantilever beam, acrylic box — civil lab environment). A wind tunnel bridge section test is:
- Aerodynamic excitation (VIV, flutter) rather than controlled ground motion
- Much larger and more unpredictable displacement range
- Open-flow environment (potential marker blur at high wind speeds)
- Different structural type (bridge section vs multi-story frame)

This is a genuine domain extension. Reviewers will not call it a minor variation of Paper 1.

### 2.2 Three distinct aerodynamic regimes captured
The dataset covers:
- **Vertical VIV** (D8–D11, 0.85–1.12 m/s): bending lock-in up to 2.76 mm RMS
- **Torsional VIV** (D12–D15, 1.21–1.49 m/s): torsional lock-in up to 2.16 mm RMS
- **Flutter** (D37–D38, > 5.28 m/s): catastrophic torsion RMS 15.97–17.08 mm

This is a technically rich dataset. Few vision-based SHM papers have results that span flutter — this is a high-amplitude, high-scientific-interest condition.

### 2.3 First AprilTag/ROS application in wind tunnel testing
The prior state of the art in vision-based WTT measurement is:
- RINO (2016): iPhone, color-blob, real-time, 2-camera — no offline reconstruction, no ROS
- Various photogrammetry setups: typically single camera, static targets, not aerodynamic testing

A ROS-based multi-camera AprilTag framework in a production wind tunnel environment has not been reported. This is a "first demonstration" contribution.

### 2.4 Camera noise floor lower than LDV at ambient
- Camera ambient torsion RMS: 0.022 mm
- LDV ambient torsion RMS: 0.107 mm
The camera has a 5× lower noise floor than the LDV at low amplitudes. This is counter-intuitive and publishable.

### 2.5 Symmetric placement finding (torsional VIV bending)
During torsional VIV (D12–D14), the camera correctly shows near-zero bending (symmetric Cam1/Cam3 cancels pure torsion), while LDV reports residual bending of ~0.05 cm. This may indicate that symmetric camera placement provides a physically cleaner bending/torsion decomposition than asymmetric LDV sensor placement.

---

## 3. Critical Problems Against Publication

### Problem 1 (SEVERE): 2D analysis only
The MATLAB script uses only Cam1 Y and Cam3 Y — vertical displacements only. Paper 1's headline contribution is **3D** displacement tracking. Publishing this WTT data as "3D framework applied to WTT" would be misleading. The analysis is fundamentally 2D (bending and torsion from Y-axis only).

**Mitigation:** Do NOT claim "3D" in the paper title or abstract. Instead: "Multi-camera ROS framework for bridge section aerodynamic displacement measurement" — accurate and honest.

### Problem 2 (SEVERE): Flutter underestimation (~34%)
At D37 (flutter, 5.28 m/s), camera torsion RMS = 10.58–10.93 mm vs LDV = 15.97 mm. That is a 32–34% underestimate. This is a large systematic error at the most dramatic test condition. Reviewers will focus on this and ask whether the system is trustworthy at high amplitudes.

**Possible causes (must investigate and address in paper):**
1. AprilTag detection degradation under fast large-amplitude motion (marker blur)
2. Large displacement exceeds linear calibration zone
3. D37 video run was cut to 21 s vs LDV 30 s — RMS may differ due to different sampling of the flutter oscillation
4. Camera cannot track at 60 FPS what oscillates at 5.15 Hz torsion (Nyquist: 60/2 = 30 Hz — should be adequate but check for aliasing at higher harmonics)

**Mitigation:** Explicitly characterize flutter-regime limitations. Present as "preliminary flutter observation" or "flutter onset detection," not full flutter characterization.

### Problem 3 (MODERATE): No raw video frames available
Only processed CSV outputs exist. Cannot:
- Perform dropout analysis (how many frames had failed detection?)
- Show blur effects at different wind speeds
- Reprocess with improved parameters
- Demonstrate the claimed dropout recovery from Paper 1 framework

**Mitigation:** Use the detection ID data in CSV files. If Fiducial ID column ever shows 0 AND position is exactly [0,0,0], that indicates dropout. Count those per condition. Build a detection reliability curve vs wind speed.

Actually — from D7 data inspection, all 1793 rows have non-zero data and Fiducial ID = 0 (AprilTag #0 detected). ID=0 is a valid detection (not a failure flag). Need to look for NaN values or exact zeros to find actual dropouts.

### Problem 4 (LARGELY RESOLVED): Camera calibration and system documentation
~~Missing camera calibration~~ — Camera calibration YAML files exist in the `tesol_ws` codebase (`src/sony_cam/config/sony_cam1_info.yaml`). Camera hardware is confirmed as MindVision USB cameras (MVSDK SDK), serial numbers documented in `cameras.yaml`.

Remaining gaps to address in the paper Methods section:
- Stand-off distance (camera-to-bridge not in any data file)
- MindVision camera model number and lens focal length (serial numbers known but model catalog lookup needed)
- Whether `tag_size=0.020` (20 mm) was the actual physical tag size or a parameter error

**Mitigation:** Codebase documents the calibration matrix (fx=20327.9, rational_polynomial distortion), AprilTag parameters (tag36h11, 20 mm, quad_decimate=1.0, solvePnP ITERATIVE). Report these in Methods. Get stand-off distance and exact camera model from TESolution by personal communication.

### Problem 5 (MODERATE, PARTLY MITIGATED): No time-domain waveform comparison possible
LDV (360 Hz) and camera (~60 FPS) are not synchronized. No Chrony NTP was used in this deployment. Therefore:
- Can only compare **condition-level statistics** (RMS, peak, mean over 30 s)
- **Cannot compute RMSE** in the time-domain sense used in Paper 1
- Cannot show waveform overlay plots (LDV vs camera vs time)

**However — dual-timestamp opportunity (new finding from codebase analysis):**
Every CSV row contains both `Cam1 System Time (s)` AND `ROS Header Time (s)`. The difference `latency = system_time − header_time` quantifies the per-frame software timestamp offset. This enables:
1. Per-camera latency histogram (mean, σ, max)
2. Inter-camera timing jitter characterization
3. Quantitative demonstration that RMS statistics are insensitive to observed jitter

This transforms the timing limitation into a characterized synchronization section — publishable in its own right.

**Mitigation:** Frame as "condition-level statistical comparison" (standard in wind engineering) AND add a synchronization characterization subsection. See `TESolution_codebase_analysis.md` §4 for the analysis method.

### Problem 6 (LOW-MODERATE): RINO 2016 precedent
The RINO paper already demonstrated: vision camera vs laser sensor in wind tunnel bridge test. An 8-year-old paper with the same concept will be cited by reviewers. The specific novelty of AprilTag vs color-blob, and ROS vs iOS, must be argued compellingly.

**Mitigation:** Quantitative comparison with RINO's accuracy claims (RINO had ~3–5% error in some conditions but was real-time, single-phone). Your system extends to multi-camera, higher accuracy at noise floor, offline reconstruction.

### Problem 7 (LEGAL): Data ownership and authorship
Not a scientific problem but a publication-blocking issue. The data was collected by TESolution at their facility using the user's system. "CHOI" modified the analysis scripts.

**Required actions before submission:**
1. Written data use agreement with TESolution
2. Authorship agreement: who are the co-authors?
3. Acknowledgment of camera hardware providers
4. Clarification of whether any non-disclosure agreement applies

---

## 4. Honest Feasibility Assessment by Journal Tier

| Journal tier | Target journals | Feasibility | What's needed |
|-------------|-----------------|-------------|---------------|
| Q1 (IF > 4) | JWEIA, Structural Health Monitoring, Mechanical Systems and Signal Processing | LOW without additional work | Needs waveform comparison, dropout analysis, flutter explanation |
| Q2 (IF 2–4) | Measurement, Engineering Structures, Sensors & Actuators | MODERATE | Needs system documentation, dropout statistics, honest limitation framing |
| Q3 (IF 1–2) | Sensors (MDPI), Experimental Techniques, Journal of Vibration and Control | HIGHER | As-is data + honest discussion may be sufficient |
| Conference | IMAC, SPIE Smart Structures, IABSE | YES | Current dataset supports a conference paper with modest analysis |

**Recommended first step:** Write a conference paper (SPIE or IMAC) based on this data to test reviewer feedback. Then extend to journal.

---

## 5. Recommended Paper Framing

### Title direction (DO use)
- "Multi-camera ROS-based AprilTag displacement measurement for bridge section aerodynamic testing: comparison with laser displacement sensors"
- "Open-source AprilTag framework for structural displacement monitoring in wind tunnel tests"
- "Vision-based displacement tracking of a bridge section model under VIV and flutter"

### Title direction (DO NOT use)
- "3D displacement tracking of ..." — the analysis uses only Y-axis, not 3D
- "High-accuracy real-time ..." — LDV comparison shows 34% error at flutter

### Paper structure (recommended sections)

1. **Introduction:** Vision-based SHM, WTT measurement needs, gap after [Lee2016]
2. **Measurement System:** ROS/AprilTag framework (brief; cite Paper 1 for detail), wind tunnel test setup
3. **Signal Processing:** Bias correction, bending/torsion decomposition, geometry
4. **Results:**
   - Noise floor comparison (camera better than LDV)
   - Vertical VIV regime (D8–D10): RMS comparison
   - Torsional VIV regime (D12–D14): RMS comparison + symmetric placement observation
   - Turbulent regime (D20–D30): broad comparison
   - Flutter (D37): partial agreement, limitation discussion
5. **Discussion:** Accuracy vs amplitude, detection reliability, comparison with [Lee2016], limitations
6. **Conclusions:** First ROS/AprilTag WTT validation, conditions of agreement, recommended improvements

---

## 6. What Would Strengthen the Paper Significantly

If additional work is possible (even without new experiments):

1. **Dropout analysis from CSV:** Count frames where detection failed vs wind speed. Build detection reliability curve. Shows the system's robustness.

2. **Spectral analysis:** Compute PSD of camera displacement and compare VIV peak frequencies against LDV. Shows frequency-domain agreement even if amplitude differs. This does not require time synchronization — both independently show the same VIV frequency.

3. **Free vibration natural frequency extraction:** Use `B1_100s_2024-10-30_16-49-51.csv` (100 s bending FV) and `T1_100s_2024-10-30_16-53-17.csv` to extract natural frequencies from camera data. Compare against LDV free-vib frequencies from `fqB.m`/`fqT.m`. Shows the camera resolves modal properties.

4. **Flutter onset characterization:** D36 is just before flutter onset (0.814 mm torsion RMS), D37 is full flutter (15.97 mm). Show the flutter onset wind speed from camera data vs LDV. Even if amplitudes differ, the onset detection wind speed may agree.

5. **D38 LDV reprocessing:** D38 (310 RPM, 5.475 m/s) raw LDV file exists but has no video counterpart. Process D38 LDV to complete the post-flutter picture. Strengthens the flutter characterization section.

---

## 7. Non-Negotiable Pre-Conditions for Submission

1. **Written data use agreement from TESolution** — without this, you cannot submit
2. **Authorship consensus** — CHOI and any other TESolution contributors must be agreed
3. **Confirm bridge model configuration** — 2024 model same as 2016? If not, cannot cite [Lee2016] specs
4. **System identification** — document in paper what cameras/hardware were used (even a personal communication from TESolution researchers suffices)

---

## 8. Four-Experiment Context and Publication Strategy

You have **four experiments** from two wind tunnels:

| Experiment | Camera | LDV | Usable for paper? |
|------------|--------|-----|-------------------|
| RINO 2016 | iPhone RINO | KEYENCE | Background reference [Lee2016] only |
| 2024 WTT (Tunnel A) | D0–D37.csv (processed) | D0–D38 (processed) | **YES — primary dataset** |
| 2025 LDV (Tunnel B) | None | D00–D20 (processed) | No — different model geometry |
| 2025 WTT bags (Tunnel A) | e0–e20.bag (raw) | None | Optional — adds ~2–4 weeks |

**For fastest publication (Sensors MDPI, ~6–8 weeks):**
Use 2024 WTT exclusively. It is the only dataset with simultaneous camera + LDV. Everything else is either background or adds processing time.

**For a stronger paper (Q2, +2–4 weeks):**
Process the 2025 bags → adds cross-year reproducibility. Use 2024 LDV as the reference for 2025 camera data (same tunnel, same model, same RPM range, 1 year apart).

**Relationship to Paper 2 (Hybrid Framework):**
The 2025 WTT bags are the same dataset used in Paper 2 (`data/WTT/e0_0rpm` through `e20_320rpm`). Options:
- **Option A (standalone WTT paper):** Publish 2024+2025 WTT as a standalone application/validation paper. Reference it in Paper 2. Avoids expanding Paper 2's scope.
- **Option B (merge into Paper 2):** Add WTT section to Paper 2 as a real-world validation case. Avoids RINO overlap issue and strengthens the hybrid framework claim.

**Recommended for fastest PhD completion:** Option A (standalone WTT paper first), based on the 2024 data only. Write it in parallel with Paper 2.

---

## 9. Summary Verdict

| Dimension | Assessment |
|-----------|------------|
| Scientific value of data | HIGH — VIV, flutter, 38 conditions, LDV reference |
| Data completeness | MODERATE — no camera calibration, no sync logs, no raw frames |
| Novelty vs [Lee2016] | REAL but must be argued explicitly |
| Accuracy at key conditions | GOOD at torsional VIV; POOR at flutter (34% error) |
| Legal readiness | NOT READY — needs TESolution agreement |
| Journal tier achievable | Q2–Q3 without additional work; Q1 with additional analysis |
| Conference paper | YES, achievable now |
| As component of Paper 2 | IDEAL fit |
