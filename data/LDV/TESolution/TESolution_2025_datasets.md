# TESolution — 2025 Datasets: LDV Campaign (Tunnel B) and WTT Offline Bags (Tunnel A)

**Last updated:** 2026-06-09  
**Purpose:** Document the two datasets collected in 2025. These are the newest data and were not covered in the original .md files (which only documented the 2024 WTT campaign).

---

## Part 1: 2025 LDV Campaign — Tunnel B (September 2025)

### 1.1 Overview

| Property | Value |
|----------|-------|
| Date | September 2025 (file dates: Sep 19–21, 2025) |
| Wind tunnel | **Tunnel B** — different lab from the 2024 WTT + 2025 bags |
| Data type | LDV only (no camera data) |
| Conditions | 21 wind conditions (D00 baseline + D01–D20) |
| Location | `context_data/TESolution/Video Measurement/laser_displacement/` |

**⚠️ This dataset cannot be used as a validation reference for the camera system.** There is no paired camera data, the sensor geometry is different (dside=13 cm vs 10 cm in Tunnel A), and the model may have a different configuration.

---

### 1.2 Wind Tunnel B Evidence

Five independent indicators confirm this is a different wind tunnel than the 2024 experiment:

| Indicator | 2024 Tunnel A | 2025 Tunnel B | Significance |
|-----------|--------------|---------------|-------------|
| `dside` | 10 cm | **13 cm** | Physical sensor repositioning |
| `dp = db/dside` | 2.0 | **1.538** | 23% different torsion scale |
| `cal` (free-vib) | ~34.3 (cal=2.7×12.7) | **27** | Different DAQ/sensor setup |
| Duration/condition | 30 s (10800 samples) | 20 s (7200 samples) | Different test protocol |
| Directory naming | RPM-indexed D-series | Korean descriptive (등류, 자유진동) | Different operator convention |
| Model variants | None (single config) | Bj1, Bm1, Tj1, Tm1 | Possibly TMD study |

---

### 1.3 Directory Structure

```
laser_displacement/
├── 등류/                          (Uniform flow tests)
│   └── 영각00/                    (0° angle of attack)
│       ├── BRID2D1.m             (analysis script, pvolt=2.7, dside=13, dp=1.538)
│       ├── brid2d_sub1.m         (subroutine called by BRID2D1.m)
│       ├── D00                   (7200 rows = 20s @ 360Hz, static baseline)
│       ├── D01–D20               (7200 rows each = 20s, wind conditions)
│       ├── result_bending.txt    (20 rows: D01–D20 bending statistics)
│       └── result_torsion.txt    (20 rows: D01–D20 torsion statistics)
├── 자유진동/                       (Free vibration)
│   ├── Bd1                       (72000 rows = 200s, 2-col, bending free decay)
│   ├── Td1                       (72000 rows = 200s, 2-col, torsion free decay)
│   ├── fq.m                      (general free-vib analysis)
│   ├── fqb.m                     (bending-specific: bandpass, log-decrement, FFT)
│   └── fqt.m                     (torsion-specific)
└── 모형_setup/                    (Model setup verification)
    ├── B1, T1                    (plain model, bending and torsion)
    ├── Bj1, Tj1                  (joint configuration)
    ├── Bm1, Tm1                  (modified configuration)
    ├── fq.m                      (frequency analysis for each configuration)
    └── 설계속도 및 모형Setup_영상계측.xlsx  (design wind speed + model setup)
```

---

### 1.4 MATLAB Script Parameters (`등류/영각00/BRID2D1.m`)

```matlab
pvolt  = [2.7, 2.7];   % calibration: cm/V (same as Tunnel A)
dside  = 13;           % side sensor at 13 cm from centerline (NOT 10 cm)
db     = 20;           % reference distance 20 cm
dp     = db/dside;     % = 1.538 (NOT 2.0)
```

**Wind velocity formula (from pitot column):**
```matlab
wind_vel_tunnel = 4 * sqrt(4.002 * mean(dat0(:,nn)))
```
This is different from Tunnel A which used a lookup table (`Windspeed.xlsx`). Tunnel B computes wind speed from pitot pressure directly.

**Free vibration script (`자유진동/fq.m`):**
```matlab
cal1 = 27; cal2 = 27;   % calibration factor (pvolt equivalent × DAQ gain)
fs   = 360;              % same sampling rate as Tunnel A
```

---

### 1.5 LDV Results (D00–D20, Uniform Flow, 0° AoA)

All values in mm. Converted from cm output of BRID2D1.m × 10.

| D# | Approx U (m/s) | B_rms (mm) | T_rms (mm) | Regime |
|----|---------------|-----------|-----------|--------|
| D00 | ~0 | Baseline | Baseline | Static |
| D01 | ~0.3 | 0.112 | 0.133 | Ambient noise floor |
| D02 | ~0.5 | 0.113 | 0.134 | Ambient |
| D03 | ~0.7 | 0.114 | 0.135 | Ambient |
| D04 | ~0.9 | 1.766 | 0.145 | **Bending VIV onset** |
| D05 | ~1.0 | 2.908 | 0.154 | **Bending VIV peak** |
| D06 | ~1.1 | 0.620 | 1.024 | VIV transition |
| D07 | ~1.2 | 0.748 | 1.125 | Torsional VIV onset |
| D08 | ~1.3 | 0.587 | 1.088 | Torsional VIV |
| D09 | ~1.4 | 0.632 | 1.103 | Torsional VIV |
| D10 | ~1.5 | 0.621 | 1.132 | Torsional VIV |
| D11 | ~1.7 | 0.726 | 1.356 | Torsional VIV growing |
| D12 | ~2.0 | 1.089 | 1.573 | Torsional VIV / turbulent |
| D13 | ~2.3 | 1.233 | 1.782 | Turbulent |
| D14 | ~2.6 | 1.359 | 2.175 | Turbulent |
| D15 | ~2.9 | 1.047 | 2.058 | Turbulent |
| D16 | ~3.2 | 0.954 | 1.933 | Turbulent |
| D17 | ~3.5 | 1.022 | 2.189 | Turbulent buffeting |
| D18 | ~3.8 | 1.756 | 3.342 | Turbulent high |
| D19 | ~4.1 | 2.893 | 5.471 | **Flutter buildup** |
| D20 | ~4.4 | 3.575 | **8.684** | **Flutter onset** |

**Note:** Wind speeds are approximate, estimated from pitot formula. Exact values require the DAQ calibration constant.

**⚠️ Torsion values are NOT directly comparable to Tunnel A (2024 campaign).** The dp factor of 1.538 (vs 2.0) means the Tunnel B torsion output = 76.9% of an equivalent Tunnel A measurement for the same physical rotation angle. Any cross-tunnel comparison must account for this scaling difference.

---

### 1.6 Modal Properties (Tunnel B Model)

From `자유진동/fq.m` with cal=27, fs=360:
- **Bending free vibration:** `Bd1` file, 200s = 72000 samples
- **Torsion free vibration:** `Td1` file, 200s = 72000 samples
- Natural frequencies extracted by FFT peak after bandpass filtering
- Damping from logarithmic decrement over 100 peaks

**Model configuration variants in `모형_setup/`:**
- `B1/T1`: Plain model (no TMD or modification)
- `Bj1/Tj1`: "j" suffix — likely "joint" configuration
- `Bm1/Tm1`: "m" suffix — likely "modified" configuration (possibly TMD installed)

The existence of j/m variants strongly suggests this is a **tuned mass damper (TMD) effectiveness study** — measuring bridge response with and without damping devices. This is an independent study, not a direct continuation of the 2024 camera validation.

---

### 1.7 How to Use This Data

| Use case | Verdict |
|---------|---------|
| Camera system validation reference | NOT SUITABLE — no camera data, different geometry |
| Tunnel A cross-reference | NOT SUITABLE — different model, different dp |
| Independent aerodynamic characterization | SUITABLE — 21 conditions, VIV + flutter captured |
| TMD effectiveness analysis (if j/m variants) | POTENTIALLY SUITABLE — requires more information from TESolution |
| Thesis aerodynamics chapter | SUITABLE as a supplementary dataset |

---

---

## Part 2: 2025 WTT Offline Bags — Tunnel A (October 1, 2025)

### 2.1 Overview

| Property | Value |
|----------|-------|
| Date | October 1, 2025 (17:15–18:14 local time) |
| Wind tunnel | **Tunnel A** — same as 2024 WTT campaign |
| Data type | ROS bags with raw compressed images (NOT yet processed with AprilTag) |
| Conditions | 21 (e0_0rpm through e20_320rpm) |
| Location | `/home/ammar/data/DEV/shm-displacement-project/data/WTT/` |
| System used | **Updated offline system** — captures to rosbag instead of live CSV |

---

### 2.2 Evidence for Tunnel A

| Indicator | Value | Matches 2024 Tunnel A? |
|-----------|-------|------------------------|
| RPM naming convention | e0_0rpm → e20_320rpm | ✅ Same RPM scale as D1–D38 |
| Max fan speed | 320 RPM (vs 310 RPM in 2024) | ✅ Same range |
| Duration per bag | ~30.5 s | ✅ Same as D1–D37 |
| Camera topics | `/sony_cam1`, `/sony_cam2`, `/sony_cam3` | ✅ Same camera naming |
| Number of cameras | 3 cameras, same topics | ✅ Same setup |

---

### 2.3 Bag Contents (Per Bag)

| Topic | Messages | Rate (Hz) | Type |
|-------|----------|-----------|------|
| `/sony_cam1/camera_info` | ~1830 | ~60 | `sensor_msgs/CameraInfo` |
| `/sony_cam1/image_raw/compressed` | ~1830 | ~60 | `sensor_msgs/CompressedImage` |
| `/sony_cam2/camera_info` | ~1830 | ~60 | `sensor_msgs/CameraInfo` |
| `/sony_cam2/image_raw/compressed` | ~1830 | ~60 | `sensor_msgs/CompressedImage` |
| `/sony_cam3/camera_info` | ~1830 | ~60 | `sensor_msgs/CameraInfo` |
| `/sony_cam3/image_raw/compressed` | ~1830 | ~60 | `sensor_msgs/CompressedImage` |

**Total per bag:** ~10,980 messages, ~5,490 frames across 3 cameras

**Key difference from 2024 data:** The 2024 data was captured as live CSV output (AprilTag detection running in real time). The 2025 bags are raw compressed images — AprilTag detection has NOT been run yet. This is the "offline pipeline" architecture.

---

### 2.4 Complete Condition Inventory

| e# | RPM | Approx U (m/s) | Bag file | Duration |
|----|-----|----------------|----------|----------|
| e0 | 0 | 0 (static) | e0_0rpm_run1.bag | 30.6 s |
| e1 | 20 | 0.109 | e1_20rpm_run1.bag | 30.5 s |
| e2 | 40 | 0.478 | e2_40rpm_run1.bag | 30.5 s |
| e3 | 50 | 0.663 | e3_50rpm_run1.bag | 30.5 s |
| e4 | 60 | 0.847 | e4_60rpm_run1.bag | 30.5 s |
| e5 | 70 | 1.032 | e5_70rpm_run1.bag | 30.5 s |
| e6 | 80 | 1.214 | e6_80rpm_run1.bag | 30.5 s |
| e7 | 90 | 1.399 | e7_90rpm_run1.bag | 30.5 s |
| e8 | 100 | 1.580 | e8_100rpm_run1.bag | 30.5 s |
| e9 | 110 | 1.761 | e9_110rpm_run1.bag | 30.5 s |
| e10 | 120 | 1.943 | e10_120rpm_run1.bag | 30.5 s |
| e11 | 140 | 2.314 | e11_140rpm_run1.bag | 30.5 s |
| e12 | 160 | 2.673 | e12_160rpm_run1.bag | 30.5 s |
| e13 | 180 | 3.042 | e13_180rpm_run1.bag | 30.5 s |
| e14 | 200 | 3.399 | e14_200rpm_run1.bag | 30.5 s |
| e15 | 220 | 3.761 | e15_220rpm_run1.bag | 30.5 s |
| e16 | 240 | 4.162 | e16_240rpm_run1.bag | 30.5 s |
| e17 | 260 | 4.519 | e17_260rpm_run1.bag | 30.5 s |
| e18 | 280 | 4.879 | e18_280rpm_run1.bag | 30.5 s |
| e19 | 300 | 5.245 | e19_300rpm_run1.bag | 30.5 s |
| e20 | 320 | 5.605 | e20_320rpm_run1.bag | 30.5 s |

Wind speeds computed from 2024 Windspeed.xlsx linear fit: U ≈ RPM × 0.01845 − 0.26077 m/s

**⚠️ e20_320rpm (high_wind_unstable_motion):** The CLAUDE.md critical rules flag e20_320rpm as `high_wind_unstable_motion` — this condition corresponds to flutter regime and must always be reported separately from stable-regime statistics.

---

### 2.5 Session Timeline (October 1, 2025)

All bags were recorded in a single afternoon session at Tunnel A:

| Bag | Start time (UTC+9) |
|-----|-------------------|
| e0_0rpm | 17:15:xx |
| e1_20rpm → e19_300rpm | 17:15 → 18:10 |
| e20_320rpm | ~18:14 |

Total session duration: ~59 minutes for 21 conditions (~3 minutes per condition including setup).

---

### 2.6 No Simultaneous LDV

The 2025 WTT bags have no simultaneous LDV reference. Options for comparison:

| Reference option | Validity | Notes |
|----------------|---------|-------|
| 2024 Tunnel A LDV (D1–D38) | ACCEPTABLE | Same tunnel, same model, different date (1 year apart) |
| 2025 LDV Tunnel B | NOT VALID | Different tunnel, different model geometry |
| 2016 RINO paper LDV | HISTORICAL ONLY | Same tunnel, but iPhone app results, not modern LDV data |

The strongest approach: after processing the 2025 bags through the AprilTag pipeline, compare results against the 2024 LDV at matched wind speeds (using the Windspeed.xlsx table to match RPM → m/s values). This gives a cross-year reproducibility validation.

---

### 2.7 Processing Pipeline for Offline Bags

To convert 2025 WTT bags to CSV format matching the 2024 data:

```bash
# Step 1: Play bag (Terminal 1)
source /opt/ros/noetic/setup.bash
rosbag play e0_0rpm_run1.bag

# Step 2: Launch detection nodes (Terminal 2)
# Needs: simple_camera_node.py (NOT needed — images are already in bag)
# Need: april_marker.py to subscribe to CompressedImage
# Note: april_marker.py currently subscribes to image_raw (uncompressed)
# MODIFICATION NEEDED: Change april_marker.py to use CompressedImage subscriber
#   or add a decompression relay node

# Step 3: Launch GUI logger to save synchronized CSV
python3 gui/gui1.py  # or run time_sync_logger.py

# Step 4: Apply MATLAB processing
# Use RAW_Data/3D_video_system/2D_WTT/BRID2D1_choi.m
# with pvolt=[100,100], dside=10, dp=2.0
```

**Required code modification:** `april_marker.py` subscribes to `/sony_camN/image_raw` (uncompressed). The bags contain `/sony_camN/image_raw/compressed` (JPEG compressed). Either:
1. Modify the subscriber type to `CompressedImage` and decompress in the callback
2. Use `republish` node: `rosrun image_transport republish compressed raw in:=/sony_cam1/image_raw out:=/sony_cam1/image_raw`

---

### 2.8 Publication Role

| Paper scenario | Role of 2025 bags |
|---------------|-------------------|
| Standalone 2024 WTT paper (fastest) | Not needed; ignore 2025 bags |
| Combined 2024+2025 paper (extended) | Demonstrates same system working 1 year later; cross-year reproducibility |
| Paper 2 hybrid framework | Could serve as "new test case" with dropout simulation |
| Thesis | Comprehensive results using both 2024 (with LDV) and 2025 (offline pipeline) |

**For fastest publication:** Process the 2025 bags only AFTER the core paper is written. Adding 2025 data would strengthen the paper but adds ~2–4 weeks of processing work.
