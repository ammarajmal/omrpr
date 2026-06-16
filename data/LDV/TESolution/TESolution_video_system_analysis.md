# TESolution Video System — Identity, Format, and Measurement Analysis

**Date:** 2026-06-09 (updated from original 2026-06-09 to correct camera identity and add codebase findings)  
**Purpose:** Document the 3D_video_system data format, confirm system identity, analyse measurement performance vs LDV reference.

---

## 1. System Identity Determination

### Evidence that this is the user's ROS/AprilTag system (Paper 1)

| Evidence item | Detail |
|--------------|--------|
| Column header "Fiducial ID" | AprilTag-specific language; RINO (2016) used color-blob tracking, not fiducials |
| Positions in **meters** | ROS standard (SI); RINO iPhone output was pixels |
| Quaternion rotation (X, Y, Z, W) | `geometry_msgs/Quaternion` — ROS message type |
| 25-column structure | Exactly matches `fiducial_msgs/FiducialTransformArray` synchronized multi-camera output |
| Frame rate ≈ **59–61 FPS** | AverMedia capture card 60 fps limit (Sony RX10 IV → HDMI → AverMedia → V4L2) |
| Unix timestamps = **October 30, 2024** | Post-publication of Paper 1 (IEEE Access) |
| MATLAB script modified **2024-11-11** by "CHOI" | TESolution researcher adapted Paper 1 CSV format |
| `pvolt = [100, 100]` | Explicit ×100 factor = ROS meters → cm conversion |
| 3-camera setup (Cam1, Cam2, Cam3) | Matches Paper 1's 3-camera configuration |
| Free vibration images (B_C1.jpg, T_C3.jpg, etc.) | Physical 3-camera setup confirmed by photographic evidence |
| MVSDK driver in codebase | `simple_camera_node.py` uses `import mvsdk` — confirms MindVision hardware |
| Serial numbers in `cameras.yaml` | CAM1: 053012620218, CAM2: 052120120268, CAM3: 052120120267 |

**Conclusion:** The `3D_video_system/` data is output from the user's ROS-based multi-camera AprilTag framework. The cameras are **MindVision industrial USB cameras** (MVSDK SDK). TESolution applied the system at their Tunnel A facility on October 30, 2024, and researcher "CHOI" adapted the analysis MATLAB scripts on November 11, 2024.

**NOTE on naming:** The `/sony_cam1` topic names and `sony_cam1_info.yaml` YAML files correctly reflect **Sony RX10 IV cameras** — the user's own hardware. The `python_camera_driver` package (which uses MVSDK for MindVision cameras) is a separate, coexisting driver for TESolution's facility cameras and was NOT used for this data. See `TESolution_codebase_analysis.md` for full hardware details.

### What RINO (Lee 2016) was

For contrast: RINO (2016) was:
- A real-time iOS smartphone app
- Color-blob tracking (red/blue blobs on bridge model)
- Pixel coordinates in image frame (not ROS)
- 2 iPhones, not a 3-camera ROS system
- No fiducial markers, no quaternion, no YAML calibration

The 2024 dataset is categorically different in technology, architecture, and output format.

---

## 2. Camera Hardware Specification

| Parameter | Value |
|-----------|-------|
| Camera | **Sony RX10 IV** (3 cameras, user-owned) |
| Capture interface | **AverMedia Video Capture Card** (HDMI → USB, V4L2 device) |
| Signal chain | Sony RX10 IV → HDMI → AverMedia card → `/dev/video_camN` (udev symlink) |
| Driver | `src/sony_cam/node/sony_cam.cpp` using `cv::VideoCapture` + `cv::CAP_V4L2` |
| Resolution | 1920×1080 |
| Frame rate | 60 fps (AverMedia card bottleneck — not the camera limit) |
| Trigger | No hardware trigger; free-running via V4L2 blocking read |
| Calibration | `src/sony_cam/config/sony_cam1_info.yaml` (rational_polynomial, 14 coefficients) |
| Lens | 600mm zoom (fx ≈ 20328 px → ~5.4° horizontal FoV at 1920-px width) |

**Calibration matrix (Camera 1):**
```
fx = 20327.9 px,  fy = 20240.8 px
cx = 967.046 px,  cy = 530.314 px
Distortion: rational_polynomial, 14 coefficients
```

**Why device IDs are stable:** AverMedia cards enumerate randomly as `/dev/video0`, `/dev/video2` etc. at boot. udev rules map them to fixed symlinks `/dev/video_cam1`, `/dev/video_cam2`, `/dev/video_cam3` using AverMedia serial numbers, ensuring CAM1 in the GUI always maps to the same physical camera position.

---

## 3. CSV Data Format (Full Specification)

**File pattern:** `D0.csv` through `D37.csv`  
**Header row:** Yes  
**Encoding:** UTF-8

```
Time (s), Cam1 Fiducial ID, Cam1 Position X, Cam1 Position Y, Cam1 Position Z,
Cam1 Rotation X, Cam1 Rotation Y, Cam1 Rotation Z, Cam1 Rotation W,
Cam2 Fiducial ID, Cam2 Position X, Cam2 Position Y, Cam2 Position Z,
Cam2 Rotation X, Cam2 Rotation Y, Cam2 Rotation Z, Cam2 Rotation W,
Cam3 Fiducial ID, Cam3 Position X, Cam3 Position Y, Cam3 Position Z,
Cam3 Rotation X, Cam3 Rotation Y, Cam3 Rotation Z, Cam3 Rotation W
```

**Column index mapping (1-based for MATLAB):**

| Col | Content | Unit |
|-----|---------|------|
| 1 | Time (Unix epoch) | s (float64) |
| 2 | Cam1 Fiducial ID | int (0 = AprilTag #0) |
| 3 | Cam1 Position X | m |
| **4** | **Cam1 Position Y** | **m ← used in analysis** |
| 5 | Cam1 Position Z | m |
| 6–9 | Cam1 Rotation X,Y,Z,W | quaternion |
| 10 | Cam2 Fiducial ID | int |
| 11 | Cam2 Position X | m |
| **12** | **Cam2 Position Y** | **m ← used in camera1_2 analysis** |
| 13–17 | Cam2 rest | — |
| 18 | Cam3 Fiducial ID | int |
| 19 | Cam3 Position X | m |
| **20** | **Cam3 Position Y** | **m ← used in camera1_3 analysis** |
| 21–25 | Cam3 rest | — |

**Y-axis convention:** Vertical displacement of the AprilTag marker as seen from that camera. In wind tunnel coordinates, Y is up. Positive Y = upward displacement.

**Timestamp note:** Col 1 is the wall-clock time from the GUI callback, NOT the camera capture time. The ROS header timestamps (assigned by `simple_camera_node.py` after USB transfer + MVSDK ISP) are also present as `ROS Header Time (s)` columns — they appear to be grouped with each camera's data in the full GUI log format. See `TESolution_codebase_analysis.md` §4 for the dual-timestamp analysis opportunity.

---

## 4. Frame Rate and Data Duration

| File | Rows | Mean Δt (s) | FPS | Duration (s) | Notes |
|------|------|------------|-----|-------------|-------|
| D0.csv | 1730 | 0.01700 | 58.8 | 29.4 s | Static baseline |
| D7.csv | 1793 | 0.01643 | 60.9 | 29.5 s | Pre-VIV |
| D37.csv | 1185 | 0.01793 | 55.8 | 21.2 s | **Flutter — early stop** |
| FV B1_100s | 4874 | 0.01742 | 57.4 | 100.1 s | Free vib bending |

Frame-to-frame jitter: σ ≈ 3.2 ms (normal for ROS ApproximateTime synchronization)  
**D37 flutter run cut short at ~21 s** — safety stop due to extreme torsional oscillations

---

## 5. Camera Pair Analysis Variants

The MATLAB script was run twice with different column selections, producing two pairs of results:

| Pair | Columns used | Files produced |
|------|-------------|----------------|
| camera1_2 | Col 4 (Cam1 Y) + Col 12 (Cam2 Y) | result_bending_camera1_2.txt, result_torsion_camera1_2.txt |
| camera1_3 | Col 4 (Cam1 Y) + Col 20 (Cam3 Y) | result_bending_camera1_3.txt, result_torsion_camera1_3.txt |

**Cam2 interpretation:** Cam2's Y-position was also recorded but only used in the secondary (camera1_2) analysis. The primary analysis uses Cam1 and Cam3 — these are the cameras viewing opposite ends of the bridge model.

**Geometric interpretation:**
- **Cam1** tracks one end of the bridge section (one extension rod tip)
- **Cam3** tracks the other end (other extension rod tip)
- **Cam2** may provide a frontal/cross-check view, or tracks the same position as Cam1 from a different angle

---

## 6. Torsion Formula Derivation

Camera torsion formula (video BRID2D1_choi.m line 56):
```matlab
torsion_raw = (Cam3_Y - Cam1_Y) / 2
torsion_out = torsion_raw * dp          % dp = 2.0
```

**Why the /2?** The cameras are symmetric at ±L/2 from centerline:
- Cam1 at position −L/2: Y₁ displacement
- Cam3 at position +L/2: Y₃ displacement
- Differential at L/2 = (Y₃ − Y₁) / 2 ... displacement per unit (L/2)
- Scaled by dp = db / dside to reference distance 200 mm

This gives displacement at 200 mm reference, equivalent to the LDV formula. Both represent the same physical quantity.

**Bending formula:**
```matlab
bending = (Cam1_Y + Cam3_Y) / 2    % average = midpoint vertical displacement
```

Both in cm after pvolt=100 conversion (ROS meters × 100).

---

## 7. Vision vs LDV Comparison (RMS values, all in cm)

Bias correction: Cam1 Y and Cam3 Y from D0.csv static baseline.

| D# | Wind (m/s) | LDV_B | V12_B | V13_B | LDV_T | V12_T | V13_T | Regime |
|----|-----------|-------|-------|-------|-------|-------|-------|--------|
| D1 | 0.048 | 0.00266 | 0.00129 | 0.00113 | 0.01073 | 0.00261 | 0.00219 | Ambient |
| D7 | 0.741 | 0.00492 | 0.00789 | 0.00715 | 0.01096 | 0.00348 | 0.00430 | Pre-VIV |
| D8 | 0.846 | 0.22135 | 0.17832 | 0.17188 | 0.02312 | 0.01221 | 0.01560 | Vertical VIV |
| D9 | 0.939 | 0.27584 | 0.25933 | 0.25154 | 0.02242 | 0.01598 | 0.01484 | Vertical VIV peak |
| D10 | 1.031 | 0.27394 | 0.24645 | 0.23865 | 0.02211 | 0.01282 | 0.01243 | Vertical VIV |
| D11 | 1.123 | 0.14766 | 0.12005 | 0.11679 | 0.02715 | 0.01539 | 0.01726 | VIV decay |
| D12 | 1.215 | 0.04928 | 0.01988 | 0.01045 | 0.17846 | 0.21625 | 0.18798 | Torsional VIV |
| D13 | 1.307 | 0.05814 | 0.01862 | 0.01078 | 0.21558 | 0.23994 | 0.21729 | Torsional VIV |
| D14 | 1.400 | 0.05436 | 0.02012 | 0.01318 | 0.20436 | 0.21568 | 0.18549 | Torsional VIV |
| D15 | 1.492 | 0.03148 | 0.02375 | 0.01839 | 0.11942 | 0.09629 | 0.08535 | VIV decay |
| D20 | 2.129 | 0.03595 | 0.02514 | 0.02180 | 0.11279 | 0.12187 | 0.11121 | Turbulent |
| D25 | 3.043 | 0.09751 | 0.04975 | 0.04726 | 0.38040 | 0.40478 | 0.39294 | Turbulent |
| D30 | 3.994 | 0.07562 | 0.05278 | 0.05183 | 0.02807 | 0.04010 | 0.03501 | Turbulent |
| D35 | 4.905 | 0.07866 | 0.11229 | 0.10939 | 0.05226 | 0.05557 | 0.05280 | High wind |
| D37 | 5.281 | 0.25925 | 0.10443 | 0.12970 | 1.59698 | 1.09304 | 1.05814 | **FLUTTER** |

---

## 8. Measurement Performance Analysis

### Torsion Agreement (camera1_3 pair)

| Regime | Conditions | V13_T / LDV_T ratio | Interpretation |
|--------|-----------|--------------------|-|
| Ambient | D1 | 0.20 | Both near noise floor; ratio unreliable |
| Vertical VIV | D8–D11 | 0.56–0.71 | Camera underestimates torsion by 29–44% (torsion small) |
| Torsional VIV | D12–D14 | 0.91–1.05 | **Near-unity agreement ±9%** |
| Turbulent D20 | D20 | 0.99 | Excellent |
| Turbulent D25 | D25 | 1.03 | Excellent |
| Turbulent D30 | D30 | 1.25 | Camera overestimates by 25% |
| Flutter | D37 | 0.66 | Camera underestimates by 34% |

### Bending Agreement (camera1_3 pair)

| Regime | Conditions | V13_B / LDV_B ratio | Interpretation |
|--------|-----------|-------------------|-|
| Vertical VIV | D8–D11 | 0.78–0.91 | 9–22% underestimate |
| Torsional VIV | D12–D14 | 0.18–0.24 | **LDV shows 0.05 cm, camera shows 0.01 cm** — see note |
| Turbulent D20 | D20 | 0.61 | Underestimate |
| Turbulent D35 | D35 | 1.39 | Camera OVERESTIMATES |
| Flutter | D37 | 0.50 | 50% underestimate |

### Important observation — Torsional VIV bending discrepancy

During torsional VIV (D12–D14), LDV bending shows ~0.05 cm RMS while camera shows ~0.01 cm RMS (ratio 0.18–0.24). This is NOT necessarily a camera failure. Physical interpretation:

- **Camera result (correct physics):** Symmetric camera placement at ±L/2. In pure torsion, Cam1 and Cam3 move in equal and opposite directions; average = 0 → near-zero bending readout.
- **LDV result (asymmetric artifacts):** LDV center sensor is at the geometric center but may have slight positioning error or there may be real bending-torsion coupling at this bridge section. The ~0.05 cm value could represent geometric imperfection rather than true bending.
- **Implication:** The camera may be MORE physically accurate during torsional VIV because it naturally separates symmetric modes, while the LDV may conflate center sensor positioning errors as bending.

This is a potentially publishable finding that strengthens the case for symmetric camera placement.

### Key accuracy limitations

1. **Flutter torsion underestimate (~34%):** Most significant concern. At 15.97 mm LDV RMS, camera records 10.58 mm. Possible causes:
   - Large-amplitude motion exceeds linear calibration range
   - AprilTag detection robustness degrades under large oscillation (blur, partial out-of-frame)
   - Camera cannot fully track 55.8 FPS at amplitude of ~32 mm peak-to-peak
   - D37 video run was only 21 s vs 30 s LDV — statistical difference possible

2. **Bending at flutter (50% underestimate):** Bending LDV 2.59 mm, camera 1.30 mm. At flutter, coupling between bending and torsion is high and displacement vectors are large; same blur/FOV concerns apply.

3. **Vertical VIV bending underestimate (9–22%):** Less severe but consistent. Possible scale factor calibration offset.

---

## 9. Video System Noise Floor

From D1 (10 RPM, 0.048 m/s — essentially static):
- Camera1_3 bending RMS: 0.00113 cm = **0.011 mm**
- Camera1_3 torsion RMS: 0.00219 cm = **0.022 mm**
- LDV bending noise: 0.027 mm
- LDV torsion noise: 0.107 mm

**Camera noise floor is ~2.5× lower than LDV at ambient conditions** — the camera system is more precise at low amplitudes (noise-limited LDV vs marker centroid precision).

---

## 10. Synchronization Architecture and Timestamp Status

**No Chrony NTP was used** during the 2024 WTT experiment. All three cameras ran on a single PC using software timestamps (`rospy.Time.now()` assigned after USB transfer + MVSDK ISP processing).

**Key mitigating factor: Dual-timestamp logging.** The GUI saves both:
- `Cam1 System Time (s)`: wall clock at GUI callback time
- `ROS Header Time (s)`: timestamp from the camera node (post-processing)

This allows post-hoc jitter analysis: `latency = system_time − header_time`.

**Multi-camera sync:** `ApproximateTimeSynchronizer` with `slop=0.008s` ensures rows in the CSV correspond to frames captured within 8 ms of each other across all three cameras.

**Impact on RMS statistics:** At 5 Hz structural vibration frequency, 16 ms maximum inter-camera offset = 0.288° of phase — negligible for 30-second RMS statistics. The condition-level RMS comparison with LDV is valid despite the timing limitation.

See `TESolution_codebase_analysis.md` for full timestamp flaw analysis and mitigation strategy.

---

## 11. Open Questions for Publication

1. **Which camera is physically at which position?** Cam1 views which end of the bridge (leading edge or trailing edge)? This matters for aerodynamic interpretation.
2. **Why does camera1_3 and camera1_2 give different results?** If Cam2 is at a cross-view position, it measures a combination of bending and torsion. The discrepancy between the two pairs needs geometric explanation.
3. **What is the exact stand-off distance?** Camera-to-bridge distance is not documented in the data files. Needed for scale verification.
4. **What is the MindVision camera model and lens specification?** Serial numbers are known (from `cameras.yaml`); model number and lens focal length need documentation for the paper Methods section.
5. **Natural frequency discrepancy:** Free-vibration MATLAB scripts use 1.43/3.11 Hz; RINO 2016 paper says 1.95/5.15 Hz. Confirm which values apply to the 2024 bridge model before citing structural properties.
6. **Was the outlier-hold mechanism active frequently at flutter?** Count "frozen" consecutive frames in D37.csv to estimate AprilTag detection failure rate at flutter conditions.
