# TESolution Wind Tunnel Dataset — Complete Inventory

**Last updated:** 2026-06-09  
**Dataset location:** `context_data/TESolution/`  
**Reference paper:** Lee et al. (2016), SPIE 9803, 98032X — see `TESolution_citation_novelty.md`

---

## 1. Top-Level Directory Structure

```
context_data/TESolution/
├── TE SOLUTION RESULTS PAPER.pdf       ← RINO 2016 SPIE paper (Lee et al.)
└── Video Measurement/
    ├── RAW_Data/
    │   ├── laser_displacement/
    │   │   └── 2D_WTT/
    │   │       ├── BRID2D1_choi.m      ← LDV analysis MATLAB script (Ver 2.1)
    │   │       ├── fqB.m               ← Bending free-vibration analysis
    │   │       ├── fqT.m               ← Torsion free-vibration analysis
    │   │       ├── D0                  ← Static baseline (10 s, 3600 rows)
    │   │       ├── D1 – D38            ← Wind conditions (30 s, 10800 rows each)
    │   │       ├── result_bending.txt  ← Computed bending statistics (38 rows)
    │   │       ├── result_torsion.txt  ← Computed torsion statistics (38 rows)
    │   │       └── Windspeed.xlsx      ← RPM → wind speed calibration table
    │   └── 3D_video_system/
    │       ├── 2D_WTT/
    │       │   ├── BRID2D1_choi.m      ← Video analysis MATLAB script (Ver 2.1)
    │       │   ├── D0.csv – D37.csv    ← Wind conditions (each ~60 FPS × ~30 s)
    │       │   ├── result_bending_camera1_2.txt
    │       │   ├── result_bending_camera1_3.txt
    │       │   ├── result_torsion_camera1_2.txt
    │       │   └── result_torsion_camera1_3.txt
    │       └── free_vibration/
    │           ├── B1_100s_2024-10-30_16-49-51.csv   ← Bending FV (100 s)
    │           ├── T1_100s_2024-10-30_16-53-17.csv   ← Torsion FV (100 s)
    │           ├── B_C1.jpg, B_C2.jpg, B_C3.jpg      ← Camera frames (bending test)
    │           └── T_C1.jpg, T_C2.jpg, T_C3.jpg      ← Camera frames (torsion test)
    └── Video Measurement_Test_1_4 Section_Smooth Flow_Attack Angle 00.xlsx
        (Master results file — 5 sheets)
```

---

## 2. LDV Raw Data Files

**Format:** Space-delimited, no header, 3 columns per file.

| Column | Content | Units | Notes |
|--------|---------|-------|-------|
| 1 | Center LDV voltage | V | Sensor at bridge deck centerline |
| 2 | Side LDV voltage | V | Sensor at dside = 10 cm from centerline |
| 3 | Pitot tube voltage | V | ~Constant per file; NOT used in analysis |

| File | Rows | Duration | Condition |
|------|------|----------|-----------|
| D0 | 3600 | 10 s | Static baseline |
| D1–D38 | 10800 each | 30 s | Wind on |

Sensor: KEYENCE LB-1201/301 (±10 cm range)  
Sampling rate: **360 Hz** (confirmed from fqB.m, fqT.m)  
Low-pass filter: 9B02 (NEC), 1 Hz – 1 kHz passband

---

## 3. Video System Raw Data Files

**Format:** CSV, 25 columns, Unix timestamp, header row included.

| Column # | Header | Data type |
|---------|--------|-----------|
| 1 | Time (s) | Unix epoch float (e.g., 1730337778.264842) |
| 2 | Cam1 Fiducial ID | int (0 = AprilTag ID 0) |
| 3–5 | Cam1 Position X, Y, Z | float, meters (ROS standard) |
| 6–9 | Cam1 Rotation X, Y, Z, W | float, quaternion |
| 10 | Cam2 Fiducial ID | int |
| 11–17 | Cam2 Position / Rotation | same format |
| 18 | Cam3 Fiducial ID | int |
| 19–25 | Cam3 Position / Rotation | same format |

**Key identity markers confirming ROS origin:**
- "Fiducial ID" = AprilTag fiducial tracking terminology
- Positions in **meters** (ROS convention, converted ×100 by pvolt=100)
- Quaternion rotation fields (X, Y, Z, W) match `geometry_msgs/Transform`
- 25-column structure matches `fiducial_msgs/FiducialTransformArray` exactly
- First timestamp = `1730337778.264842` → **October 30, 2024**
- Frame rate: **~59–61 FPS** (mean Δt ≈ 0.017 s) — MindVision USB cameras at 60 fps target

| File | Rows | Duration | Notes |
|------|------|----------|-------|
| D0.csv | 1730 | 29 s | Static baseline |
| D1–D36.csv | ~1800 each | ~30 s | Wind on |
| D37.csv | 1185 | 21 s | **Flutter — run stopped early** |
| (No D38.csv) | — | — | 310 RPM not captured by camera system |

---

## 4. Master Results Excel

**File:** `Video Measurement_Test_1_4 Section_Smooth Flow_Attack Angle 00.xlsx`

| Sheet | Korean name | Content |
|-------|-------------|---------|
| 1 | 등류 | Wind speed table (RPM → m/s) |
| 2 | 0°_laser | **Complete LDV results**, all 37 conditions, cm units |
| 3 | 0°_영상계측 | Video system results (camera1_3 pair) |
| 4 | 0°_영상계측_sub | Video system results (camera1_2 pair), verified match with result_bending_camera1_2.txt |
| 5 | 결과비교 | Empty (comparison sheet, not filled) |

---

## 5. MATLAB Scripts

### LDV: `laser_displacement/2D_WTT/BRID2D1_choi.m`
- Version 2.0 (2017-02-03), Modified by CHOI to Version 2.1 (2024-11-11)
- Processes 38 wind conditions (cn=38, i = 0 to 37 → D0 to D37, then D38)
- Loads raw LDV files, applies bias correction, calibration (pvolt=2.7 cm/V), outputs bending + torsion statistics
- Columns used: 1 (center V) and 2 (side V)
- Outputs: `result_bending.txt`, `result_torsion.txt`

### Video: `3D_video_system/2D_WTT/BRID2D1_choi.m`
- Same version scheme, same CHOI modification date (2024-11-11)
- Processes 38 CSV files (D0.csv to D37.csv)
- pvolt = [100, 100] (converts ROS meters → cm)
- **Uses columns 4 (Cam1 Position Y) and 20 (Cam3 Position Y) only**
  - camera1_3: bending = (Cam1Y + Cam3Y)/2, torsion = (Cam3Y – Cam1Y)/2 × dp
- A separate run with columns 4 and 12 produces camera1_2 results
- Outputs: `result_bending_camera1_2.txt`, `result_bending_camera1_3.txt`, etc.

### Free Vibration: `fqB.m`, `fqT.m`
- fs = 360 Hz (LDV sampling rate confirmed)
- cal = 27 (equivalent to pvolt=2.7 × DAQ gain factor)
- Bandpass frequencies: bending ≈ 1.43 Hz, torsion ≈ 3.11 Hz
  - **Note:** Differs from PDF Table 3 (1.95 Hz / 5.15 Hz) — possible different spring config or preliminary calibration run

---

## 6. Wind Speed Calibration Table (from Windspeed.xlsx)

Complete RPM-to-wind-speed mapping (smooth flow, 0° attack angle):

| D# | RPM | Wind (m/s) | D# | RPM | Wind (m/s) |
|----|-----|-----------|-----|-----|-----------|
| D1 | 10 | 0.0476 | D20 | 130 | 2.1286 |
| D2 | 20 | 0.1386 | D21 | 140 | 2.3159 |
| D3 | 30 | 0.2287 | D22 | 145 | 2.4017 |
| D4 | 40 | 0.3188 | D23 | 155 | 2.5844 |
| D5 | 50 | 0.4089 | D24 | 160 | 2.6739 |
| D6 | 55 | 0.6477 | D25 | 180 | 3.0428 |
| D7 | 55 | 0.7413 | D26 | 185 | 3.1263 |
| D8 | 60 | 0.8459 | D27 | 195 | 3.2972 |
| D9 | 65 | 0.9389 | D28 | 200 | 3.3798 |
| D10 | 70 | 1.0312 | D29 | 210 | 3.5467 |
| D11 | 75 | 1.1230 | D30 | 230 | 3.9938 |
| D12 | 80 | 1.2147 | D31 | 235 | 4.0754 |
| D13 | 85 | 1.3060 | D32 | 240 | 4.1564 |
| D14 | 90 | 1.3973 | D33 | 250 | 4.3174 |
| D15 | 95 | 1.4882 | D34 | 270 | 4.8152 |
| D16 | 100 | 1.5791 | D35 | 275 | 4.9049 |
| D17 | 105 | 1.6698 | D36 | 290 | 5.1793 |
| D18 | 110 | 1.7602 | D37 | 300 | 5.2810 |
| D19 | 120 | 1.9405 | D38 | 310 | 5.4747 |

**Linear fit:** U ≈ RPM × 0.01845 − 0.26077 m/s (valid for RPM ≥ 20)  
**Missing in video system:** D38.csv does not exist (310 RPM not captured)  
**Missing entirely:** D39 (320 RPM, 5.6483 m/s), D40 (350 RPM, 6.2144 m/s) — appear in speed table but no data files exist  
**User's e20_320rpm:** Has NO LDV counterpart in this dataset (closest: D38, 310 RPM)

---

## 7. Free Vibration Images

Six camera frame images exist in `free_vibration/`:
- `B_C1.jpg`, `B_C2.jpg`, `B_C3.jpg` — Bending free vibration test, captured from Cam1, Cam2, Cam3
- `T_C1.jpg`, `T_C2.jpg`, `T_C3.jpg` — Torsion free vibration test, Cam1, Cam2, Cam3

These confirm a **three-camera physical setup** and provide visual evidence of the wind tunnel geometry and marker placement. The bridge model is visible in the images.

---

## 8. Key Dates

| Event | Date |
|-------|------|
| RINO paper published | 2016-04 (Presented 2016-04-01) |
| LDV MATLAB script original version | 2017-02-03 |
| Wind tunnel experiments (video) | **2024-10-30** (Unix timestamp 1730337778) |
| Free vibration data collected | 2024-10-30 (16:49 and 16:53 local time) |
| MATLAB scripts modified by CHOI | **2024-11-11** |

---

## 9. Two Wind Tunnels — Quick Reference

| Feature | Tunnel A (2024 + 2025 bags) | Tunnel B (2025 LDV) |
|---------|----------------------------|---------------------|
| Experiments | Exp 2 (2024 WTT) + Exp 4 (2025 bags) | Exp 3 (2025 LDV) |
| Camera data | Yes (2024) + raw bags (2025) | No |
| dside | 10 cm | 13 cm |
| dp | 2.0 | 1.538 |
| Conditions | 38 (2024) / 21 (2025) | 21 |
| Duration/condition | 30 s | 20 s |
| Naming convention | D-series + RPM table | Korean descriptive |

**For full four-experiment cross-reference, see `TESolution_four_experiments_map.md`.**

---

## 10. 2025 LDV Campaign — Tunnel B (September 2025)

**Location:** `context_data/TESolution/Video Measurement/laser_displacement/`

| Property | Value |
|----------|-------|
| Date | September 2025 (file dates Sep 19–21, 2025) |
| Wind tunnel | **Tunnel B** (different lab from 2024 WTT) |
| Conditions | D00 (baseline) + D01–D20 = 21 conditions |
| Duration/condition | 20 s (7200 rows @ 360 Hz) |
| MATLAB params | pvolt=2.7, dside=13, db=20, dp=1.538 |
| Outputs | result_bending.txt (20 rows), result_torsion.txt (20 rows) |
| Camera data | **NONE** — LDV only |
| Model variants | B1/Bj1/Bm1 and T1/Tj1/Tm1 — possibly TMD study |

**⚠️ Cannot be used as camera system validation reference.** Different tunnel, different model geometry. See `TESolution_2025_datasets.md` for full details.

---

## 11. 2025 WTT Offline Bags — Tunnel A (October 1, 2025)

**Location:** `/home/ammar/data/DEV/shm-displacement-project/data/WTT/`

| Property | Value |
|----------|-------|
| Date | October 1, 2025 (17:15–18:14 local time) |
| Wind tunnel | **Tunnel A** (same as 2024 WTT campaign) |
| Conditions | e0_0rpm through e20_320rpm = 21 conditions |
| Duration/bag | ~30.5 s each |
| Topics per bag | 6: `/sony_camN/camera_info` + `/sony_camN/image_raw/compressed` × 3 cameras |
| Messages/bag | ~10,980 total (~1830 × 3 cameras × 2 topics) |
| Processing status | **RAW ONLY — AprilTag detection NOT yet run** |
| Simultaneous LDV | **No** — use 2024 Tunnel A LDV (D1–D38) as approximate reference |

**⚠️ e20_320rpm** is flagged as `high_wind_unstable_motion` and must always be reported separately from stable-regime statistics.

For full processing pipeline and publication strategy, see `TESolution_2025_datasets.md`.

---

## 12. Complete Four-Experiment Overview

| Experiment | Date | Tunnel | Type | Status |
|------------|------|--------|------|--------|
| RINO 2016 | Apr 2016 | Tunnel A? | iPhone RINO app | Background reference [Lee2016] |
| 2024 WTT Campaign | Oct 30–31, 2024 | **Tunnel A** | Camera + LDV (simultaneous) | Processed, primary validation |
| 2025 LDV Campaign | Sep 2025 | **Tunnel B** | LDV only | Processed, separate facility |
| 2025 WTT Bags | Oct 1, 2025 | **Tunnel A** | Raw camera bags (no LDV) | Unprocessed |

**For the fastest publication path:** Use the 2024 WTT Campaign exclusively.  
**For a stronger paper:** Process 2025 bags and combine with 2024 LDV reference.

---

## 14. Anonymization Rules

**NEVER include in any publication:**
- "TESolution Co., Ltd."
- "Anseong-si, South Korea"
- Any identifying detail from the RINO PDF cover page

**Safe usage:**
- Cite [Lee2016] for facility/model specifications  
- Refer to "the wind tunnel operator" or "the testing facility"
- Reference PDF table numbers for structural model properties
