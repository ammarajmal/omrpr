# TESolution — Master Map: Four Experiments, Two Wind Tunnels

**Status:** Authoritative cross-reference. Supersedes any partial references in other files.  
**Last updated:** 2026-06-09  
**Purpose:** Single-source-of-truth for understanding which data belongs to which experiment, which wind tunnel, and what is available for publication.

---

## 0. TL;DR for Quick Context

| Experiment | Date | Tunnel | Camera | LDV | Conditions | Status |
|------------|------|--------|--------|-----|------------|--------|
| RINO 2016 | Apr 2016 | Unknown (Tunnel ?) | iPhone (RINO app) | KEYENCE LDV | Unknown | Background reference only |
| 2024 WTT Campaign | Oct 30–31, 2024 | **Tunnel A** | D0–D37.csv (3-cam, ~60fps) | D0–D38 (360Hz) | 38 conditions, 10–310 RPM | **SIMULTANEOUS** — primary validation |
| 2025 LDV Campaign | Sep 2025 | **Tunnel B** | None | D00–D20 (360Hz) | 21 conditions | LDV only, different model |
| 2025 WTT Offline Bags | Oct 1, 2025 | **Tunnel A** | e0–e20.bag (raw compressed) | None | 21 conditions, 0–320 RPM | Raw unprocessed bags |

---

## 1. Experiment 1 — RINO 2016 (Background Reference)

**What it is:** The original TESolution paper demonstrating vision-based measurement in a wind tunnel.

**Citation:** Lee, S.-W., Jeong, J.-H., Knez, K. P., Min, J.-H., & Jo, H. (2016). Practical application of RINO, smartphone-based dynamic displacement sensing application, for wind tunnel tests. *Proc. SPIE*, 9803, 98032X.

**Technology used:**
- iOS RINO app (iPhone 6s)
- Color-blob tracking (red/blue blobs)
- Real-time processing on iPhone
- 1–2 phones, NOT a multi-camera ROS system

**Facility (from PDF):**
- Eiffel-type tunnel, test section 1.0 m (W) × 1.5 m (H) × 6.0 m (L)
- Wind speed range 0.3–21.0 m/s, turbulence < 0.7%
- Bridge model: 34.4 cm wide, 1:50 scale

**Structural properties (PDF Table 3):**
- Bending frequency: 1.95 Hz
- Torsion frequency: 5.15 Hz
- Frequency ratio: 2.64
- Bending damping: 0.28%; Torsion damping: 0.13%

**Data available:** Only the published PDF. No raw files.

**Role in your paper:** Cited as [Lee2016] in Related Work. Establishes the prior art gap that your system improves upon.

**⚠️ ANONYMIZATION:** NEVER name TESolution, Anseong-si, or any identifying detail in any paper. Write "commercial wind tunnel testing facility [Lee2016]."

---

## 2. Experiment 2 — 2024 WTT Campaign (Primary Dataset)

**This is your GOLD MINE. Camera and LDV were simultaneous. Use this for publication.**

### Dates
- Free vibration: **October 30, 2024** (16:49 and 16:53 local time)
- Wind conditions (D0–D37 camera + D0–D38 LDV): **October 30–31, 2024** (Unix: 1730337778–1730341244)
- MATLAB analysis adapted by CHOI: **November 11, 2024**

### Wind Tunnel
- **Tunnel A** (same Eiffel-type tunnel as RINO 2016)
- Same KEYENCE LDV setup, same bridge section model
- Max fan speed used: 310 RPM → 5.475 m/s

### LDV Data
| Parameter | Value |
|-----------|-------|
| Location | `RAW_Data/laser_displacement/2D_WTT/` |
| Files | D0 (10s baseline) + D1–D38 (30s each) |
| Format | ASCII 3-col: center_V, side_V, pitot_V |
| Sample rate | 360 Hz |
| Conditions | 39 total (D0 baseline + D1–D38) |
| `pvolt` | 2.7 cm/V (center and side) |
| `dside` | 10 cm (side sensor from centerline) |
| `db` | 20 cm (reference lever arm) |
| `dp = db/dside` | 2.0 (torsion scale factor) |
| Processed results | `result_bending.txt`, `result_torsion.txt` (37 rows: D1–D37; D38 computed separately) |
| Wind speeds | Windspeed.xlsx: 10 RPM=0.048 m/s → 310 RPM=5.475 m/s |

### Camera Data
| Parameter | Value |
|-----------|-------|
| Location | `RAW_Data/3D_video_system/2D_WTT/` |
| Files | D0.csv (static baseline) + D1–D37.csv |
| Format | CSV 25-col: timestamp, Cam1 pose, Cam2 pose, Cam3 pose |
| Sample rate | ~59–61 fps (software-timestamped) |
| Conditions | 38 (D0–D37); D38 NOT captured (test stopped) |
| `pvolt` in MATLAB | [100, 100] — converts ROS meters to cm |
| Columns used | Col 4 (Cam1 Y), Col 12 (Cam2 Y), Col 20 (Cam3 Y) |
| Geometry | `dside`=10, `db`=20, `dp`=2.0 (same as LDV) |
| Processed results | `result_bending_camera1_2.txt` (Cam1+Cam2), `result_bending_camera1_3.txt` (Cam1+Cam3), and torsion equivalents (37 rows each: D1–D37) |

### Free Vibration Data
| File | Duration | Notes |
|------|----------|-------|
| `free_vibration/B1_100s_2024-10-30_16-49-51.csv` | ~100s, ~57fps | Bending free-decay from camera |
| `free_vibration/T1_100s_2024-10-30_16-53-17.csv` | ~100s, ~57fps | Torsion free-decay from camera |
| `laser_displacement/2D_WTT/Bd1` | 200s (via fqB.m) | Bending LDV free-decay |
| `laser_displacement/2D_WTT/Td1` | 200s (via fqT.m) | Torsion LDV free-decay |
| Detected bending freq | ~1.43 Hz | From fqB.m bandpass (differs from PDF 1.95 Hz) |
| Detected torsion freq | ~3.11 Hz | From fqT.m bandpass (differs from PDF 5.15 Hz) |

**⚠️ NOTE:** The natural frequencies from the 2024 MATLAB scripts (1.43 Hz, 3.11 Hz) DIFFER from the RINO 2016 paper (1.95 Hz, 5.15 Hz). Before publication, confirm with TESolution whether the 2024 bridge model retained the same spring configuration as 2016.

### Key Results Summary (D1–D37 camera1_3 pair vs LDV)
| Regime | Wind (m/s) | D# | LDV_B_rms (mm) | Cam_B_rms (mm) | LDV_T_rms (mm) | Cam_T_rms (mm) |
|--------|-----------|----|----|----|----|-----|
| Noise floor | 0.048 | D1 | 0.027 | 0.011 | 0.107 | 0.022 |
| Vertical VIV | 0.939 | D9 | 2.758 | 2.515 | 0.224 | 0.148 |
| Torsional VIV | 1.307 | D13 | 0.581 | 0.108 | 2.156 | 2.173 |
| Turbulent | 2.129 | D20 | 0.360 | 0.218 | 1.128 | 1.112 |
| Flutter | 5.281 | D37 | 2.592 | 1.297 | **15.970** | **10.581** |

### Why This Is Your Publication Dataset
- Simultaneous LDV + camera → condition-level RMS comparison is valid same-session
- 37 wind conditions spanning ambient → VIV → flutter → complete aerodynamic envelope
- Already partially processed (MATLAB results exist)
- Camera noise floor (0.022 mm) LOWER than LDV noise floor (0.107 mm) — novel finding

---

## 3. Experiment 3 — 2025 LDV Campaign (Separate Tunnel B)

**This is NOT usable as a camera reference. Different tunnel, different model, no camera data.**

### Date
September 2025 (file dates: Sep 19–21, 2025)

### Wind Tunnel
- **Tunnel B** — different TESolution lab than Experiments 2 and 4
- Identified by: different model geometry, different directory naming convention, different test durations

### Evidence for Tunnel B (not Tunnel A)
1. `dside` changed from 10 cm to **13 cm** — physical sensor repositioning, not a parameter change
2. `dp` changed from 2.0 to **1.538** — 23% reduction in torsion scale
3. `cal = 27` in free-vibration scripts (Tunnel A uses cal ≈ 34.3)
4. Korean descriptive directory names (`등류`, `자유진동`, `모형_setup`) vs RPM-indexed D-files
5. Duration per condition: 20s (Tunnel A uses 30s)
6. Free vibration length: 72000 samples = 200s (Tunnel A had ~100s)
7. Model setup variants: `Bj1`, `Bm1`, `Tj1`, `Tm1` — possibly TMD study, not pure aerodynamic sweep

### Data Structure
```
laser_displacement/
├── 등류/영각00/          (Uniform flow, 0° angle of attack)
│   ├── BRID2D1.m         (pvolt=2.7, dside=13, db=20, dp=1.538)
│   ├── brid2d_sub1.m     (processing subroutine)
│   ├── D00               (static baseline, 7200 rows = 20s @ 360Hz)
│   ├── D01–D20           (21 wind conditions, 7200 rows each)
│   ├── result_bending.txt (20 rows: D01–D20)
│   └── result_torsion.txt (20 rows: D01–D20)
├── 자유진동/             (Free vibration)
│   ├── Bd1               (72000 rows = 200s, 2-col LDV bending)
│   ├── Td1               (72000 rows = 200s, 2-col LDV torsion)
│   ├── fq.m, fqb.m, fqt.m (natural freq / damping analysis)
└── 모형_setup/           (Model setup verification)
    ├── B1, Bj1, Bm1      (Bending: plain / joint / modified config)
    ├── T1, Tj1, Tm1      (Torsion: plain / joint / modified config)
    ├── fq.m              (frequency analysis for setup verification)
    └── 설계속도 및 모형Setup_영상계측.xlsx
```

### 2025 LDV Results Summary (D00-D20 at 0° AoA, Tunnel B)
| Regime | D# | B_rms (mm) | T_rms (mm) | Notes |
|--------|----|-----------|-----------|-------|
| Noise floor | D01–D03 | 0.112–0.114 | 0.133–0.135 | Ambient |
| Bending VIV | D04–D05 | 1.766–2.908 | 0.145–0.154 | VIV peak at D05 |
| Torsion VIV onset | D06–D07 | 0.620–0.748 | 1.024–1.125 | |
| Torsion VIV peak | D12–D14 | 1.089–1.359 | 1.573–2.175 | |
| Flutter/divergence | D20 | 3.575 | 8.684 | Largest amplitudes |

**⚠️ Sensor geometry change means torsion amplitudes are NOT directly comparable to Tunnel A values.** The dp=1.538 vs dp=2.0 means Tunnel B torsion output = 76.9% of equivalent Tunnel A value for the same physical rotation angle.

### How to Use This Data
- Do NOT use for validating your camera system (no paired camera data)
- Potentially useful as: additional aerodynamic reference for a second paper or thesis chapter
- The free-vibration data gives modal properties of the Tunnel B model (natural freq, damping)
- The `모형_setup` variants may relate to a TMD effectiveness study — ask TESolution

---

## 4. Experiment 4 — 2025 WTT Offline Bags (Tunnel A, Updated System)

### Date
**October 1, 2025** — entire test session from 17:15 to 18:14 (59 minutes total, 21 conditions × ~3 min each including setup)

### Wind Tunnel
**Tunnel A** — same as Experiment 2 (2024 campaign)

### Evidence for Tunnel A
1. Same RPM naming convention: e1_20rpm → e20_320rpm matches 2024 Windspeed.xlsx
2. Same max fan speed range (up to 320 RPM vs 310 RPM in 2024)
3. Same 3-camera MindVision hardware (bag topics: `/sony_cam1`, `/sony_cam2`, `/sony_cam3`)
4. Same 30.5s recording duration per condition as 2024

### Data Structure
```
data/WTT/
├── e0_0rpm/e0_0rpm_run1.bag     (30.6s, 3 × ~1830 CompressedImage)
├── e1_20rpm/e1_20rpm_run1.bag   (30.5s)
├── e2_40rpm/e2_40rpm_run1.bag
├── e3_50rpm/e3_50rpm_run1.bag
...
└── e20_320rpm/e20_320rpm_run1.bag
```

### Bag Contents (per bag, confirmed from e0 and e1)
| Topic | Messages | Type |
|-------|----------|------|
| `/sony_cam1/camera_info` | ~1830 | `sensor_msgs/CameraInfo` |
| `/sony_cam1/image_raw/compressed` | ~1830 | `sensor_msgs/CompressedImage` |
| `/sony_cam2/camera_info` | ~1830 | `sensor_msgs/CameraInfo` |
| `/sony_cam2/image_raw/compressed` | ~1830 | `sensor_msgs/CompressedImage` |
| `/sony_cam3/camera_info` | ~1830 | `sensor_msgs/CameraInfo` |
| `/sony_cam3/image_raw/compressed` | ~1830 | `sensor_msgs/CompressedImage` |

**Total: ~5490 frames per bag across 3 cameras. No AprilTag detection topics recorded — offline processing required.**

### RPM-to-Condition Mapping
| e# | RPM | Approx U (m/s) using Tunnel A formula |
|----|-----|--------------------------------------|
| e0 | 0 | 0 (static) |
| e1 | 20 | 0.109 |
| e2 | 40 | 0.478 |
| e3 | 50 | 0.663 |
| e4 | 60 | 0.847 |
| e5 | 70 | 1.032 |
| e6 | 80 | 1.214 |
| e7 | 90 | 1.399 |
| e8 | 100 | 1.580 |
| e9 | 110 | 1.761 |
| e10 | 120 | 1.943 |
| e11 | 140 | 2.314 |
| e12 | 160 | 2.673 |
| e13 | 180 | 3.042 |
| e14 | 200 | 3.399 |
| e15 | 220 | 3.761 |
| e16 | 240 | 4.162 |
| e17 | 260 | 4.519 |
| e18 | 280 | 4.879 |
| e19 | 300 | 5.245 |
| e20 | 320 | 5.605 |

*(Formula: U ≈ RPM × 0.01845 − 0.26077 from 2024 Windspeed.xlsx linear fit)*

### Processing Status
**RAW ONLY — NOT YET PROCESSED.** To generate displacement data from these bags:
1. Play each bag through the offline AprilTag detection pipeline
2. Run `april_marker.py` node to detect poses
3. Save CSV with same format as 2024 (25-col with timestamp + 3 × cam pose)
4. Apply `BRID2D1_choi.m` (with pvolt=100, dside=10, dp=2.0) to get bending/torsion statistics

### No Simultaneous LDV
The 2025 WTT bags have NO simultaneous LDV reference. The closest valid reference is the 2024 Experiment 2 LDV data — same tunnel, same model, same RPM range, just 1 year apart.

---

## 5. Two Wind Tunnels — Summary Table

| Feature | Tunnel A | Tunnel B |
|---------|---------|---------|
| Experiments | 2 (2024), 4 (2025 bags) | 3 (2025 LDV) |
| Model dside | 10 cm | 13 cm |
| Model dp | 2.0 | 1.538 |
| Condition count | 38–39 (2024), 21 (2025) | 21 |
| Duration/condition | 30s | 20s |
| Max tested speed | ~5.5 m/s (310–320 RPM) | ~? (D20 = flutter onset) |
| Natural frequencies | ~1.43 Hz / ~3.11 Hz (2024) | To be determined from fq.m |
| Naming convention | D-series with RPM table | Korean descriptive |
| Data file format | Space-delimited ASCII | Space-delimited ASCII |
| Camera data exists | Yes (2024) + bags (2025) | No |

---

## 6. What to Use for Your Paper

### For fastest publication (Sensors MDPI, ~6–8 weeks):
**Use Experiment 2 exclusively.** Simultaneous camera + LDV, 37 wind conditions, already partially processed.

### For the strongest claim:
**Combine Experiments 2 and 4.** Experiment 2 provides LDV validation; Experiment 4 demonstrates the updated offline pipeline on the same tunnel. But Experiment 4 needs processing first (~2 weeks additional work).

### Do NOT use Experiment 3 (2025 LDV) as a camera reference:
Different model geometry, no paired camera data, different tunnel. Set aside for a separate aerodynamic characterization paper if TESolution permits.

---

## 7. Key Questions Still Open

1. **Natural frequency discrepancy:** 2024 MATLAB scripts use 1.43/3.11 Hz; 2016 paper says 1.95/5.15 Hz. Same model? Confirm with TESolution.
2. **Tunnel B context:** What study was the 2025 LDV campaign for? TMD effectiveness? Different bridge section? Get TESolution's description.
3. **2025 Windspeed calibration:** Does the 2024 Windspeed.xlsx apply directly to the 2025 Tunnel A bags? Confirm RPM→m/s formula unchanged.
4. **Data use agreement:** Required from TESolution before any submission. Get this first.
5. **Camera hardware documentation:** MindVision camera model/specs needed for paper Methods section. See codebase analysis file for serial numbers.
