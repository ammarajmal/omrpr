# TESolution LDV — Geometry, Calibration, and Complete Results

**Source files:**  
- MATLAB: `RAW_Data/laser_displacement/2D_WTT/BRID2D1_choi.m` (Ver 2.1, 2024-11-11 CHOI)  
- Raw data: `RAW_Data/laser_displacement/2D_WTT/D0`–`D38`  
- Results Excel: `Video Measurement_Test_1_4 Section_Smooth Flow_Attack Angle 00.xlsx`, sheet `0°_laser`

---

## 1. Sensor Identity

**Sensor model:** KEYENCE LB-1201/301 (laser displacement sensor)  
**Range:** ±10 cm  
**Sampling rate:** 360 Hz (confirmed in `fqB.m` and `fqT.m`: `fs=360`)  
**Signal conditioning:** Low-pass filter 9B02 (NEC), 1 Hz – 1 kHz  
**Output format:** Voltage; DAQ records 3 columns (center V, side V, Pitot V)

---

## 2. LDV Sensor Geometry

Confirmed from MATLAB `BRID2D1_choi.m` lines 14–19:

```matlab
pvolt  = [2.7, 2.7];   % calibration: cm/V for [center, side] sensors
dside  = 10;           % side sensor distance from deck centerline [cm]
db     = 20.0;         % reference lever arm for torsion output [cm]
dp     = db/dside;     % = 2.0 — scale factor (dimensionless)
```

**Physical layout:**
- **Center sensor:** positioned at the bridge deck centerline (reference = 0)
- **Side sensor:** positioned at dside = **10 cm = 100 mm** from centerline
- **Torsion output reference position:** db = **20 cm = 200 mm** from centerline

**Bending formula (line 53):**
```matlab
bending = (dat1(:,1) + dat1(:,2)) / 2     % average(center, side) [cm]
```

**Torsion formula (lines 53, 58–61):**
```matlab
torsion_raw  = dat1(:,2) - dat1(:,1)      % side - center [cm at 10 cm position]
torsion_out  = torsion_raw * dp           % scaled to 200 mm reference position
torsion_rms  = std(torsion_raw) * dp
```

**Output interpretation:**
> All LDV torsion values represent **differential vertical displacement at 200 mm from the bridge deck centerline** — NOT a torsion angle. Units: cm. Multiply × 10 for mm.

### Equivalence to Camera Measurement

Camera MATLAB uses (video BRID2D1_choi.m line 56):
```matlab
torsion_video = (Cam3_Y - Cam1_Y) / 2    % /2 because cameras at ±L/2 (symmetric)
torsion_out   = torsion_video * dp        % same dp = 2.0
```

The `/2` in the video formula compensates for symmetric camera placement (both cameras at ±L/2 from centerline, vs LDV where center sensor is at 0 and side sensor at dside). After applying dp=2.0, both formulas produce displacement at the same 200 mm reference position — they are **dimensionally equivalent**.

---

## 3. Bias Subtraction

Static baseline D0 (10 s, 3600 samples) used for bias:
- Bias center: **+0.01156 V** → 0.0312 cm offset removed
- Bias side: **+0.00443 V** → 0.0120 cm offset removed

All subsequent measurements are bias-corrected before calibration.

---

## 4. Complete LDV Results Table

**All values in cm. Multiply × 10 for mm.**  
**Formula:** B_rms = std(bending) × scale; T_rms = std(torsion_raw × dp)  

| D# | RPM | Wind (m/s) | B_rms (cm) | B_rms (mm) | T_rms (cm) | T_rms (mm) | Regime |
|----|-----|-----------|-----------|-----------|-----------|-----------|--------|
| D1 | 10 | 0.048 | 0.00266 | 0.027 | 0.01073 | 0.107 | Ambient/noise floor |
| D2 | 20 | 0.139 | 0.00264 | 0.026 | 0.01083 | 0.108 | Ambient |
| D3 | 30 | 0.229 | 0.00268 | 0.027 | 0.01077 | 0.108 | Ambient |
| D4 | 40 | 0.319 | 0.00279 | 0.028 | 0.01067 | 0.107 | Ambient |
| D5 | 50 | 0.409 | 0.00303 | 0.030 | 0.01072 | 0.107 | Ambient |
| D6 | 55 | 0.648 | 0.00303 | 0.030 | 0.01058 | 0.106 | Pre-VIV |
| D7 | 55 | 0.741 | 0.00492 | 0.049 | 0.01096 | 0.110 | Pre-VIV onset |
| D8 | 60 | 0.846 | 0.22134 | 2.213 | 0.02312 | 0.231 | **Vertical VIV onset** |
| D9 | 65 | 0.939 | 0.27583 | 2.758 | 0.02242 | 0.224 | **Vertical VIV peak** |
| D10 | 70 | 1.031 | 0.27392 | 2.739 | 0.02211 | 0.221 | Vertical VIV peak |
| D11 | 75 | 1.123 | 0.14766 | 1.477 | 0.02715 | 0.272 | Vertical VIV decay |
| D12 | 80 | 1.215 | 0.04928 | 0.493 | 0.17845 | 1.785 | **Torsional VIV onset** |
| D13 | 85 | 1.306 | 0.05814 | 0.581 | 0.21557 | 2.156 | **Torsional VIV peak** |
| D14 | 90 | 1.397 | 0.05436 | 0.544 | 0.20435 | 2.044 | Torsional VIV |
| D15 | 95 | 1.488 | 0.03147 | 0.315 | 0.11941 | 1.194 | Torsional VIV decay |
| D16 | 100 | 1.579 | 0.01493 | 0.149 | 0.01506 | 0.151 | Post-VIV |
| D17 | 105 | 1.670 | 0.01687 | 0.169 | 0.01278 | 0.128 | Turbulent buffeting |
| D18 | 110 | 1.760 | 0.01339 | 0.134 | 0.01271 | 0.127 | Turbulent |
| D19 | 120 | 1.940 | 0.01628 | 0.163 | 0.02246 | 0.225 | Turbulent |
| D20 | 130 | 2.129 | 0.03595 | 0.360 | 0.11278 | 1.128 | Turbulent |
| D21 | 140 | 2.316 | 0.05860 | 0.586 | 0.18999 | 1.900 | Turbulent |
| D22 | 145 | 2.402 | 0.07386 | 0.739 | 0.26377 | 2.638 | Turbulent |
| D23 | 155 | 2.584 | 0.08423 | 0.842 | 0.31738 | 3.174 | Turbulent |
| D24 | 160 | 2.674 | 0.09578 | 0.958 | 0.36688 | 3.669 | Turbulent |
| D25 | 180 | 3.043 | 0.09750 | 0.975 | 0.38038 | 3.804 | Turbulent (flutter buildup) |
| D26 | 185 | 3.126 | 0.09389 | 0.939 | 0.39059 | 3.906 | Turbulent |
| D27 | 195 | 3.297 | 0.09555 | 0.956 | 0.37992 | 3.799 | Turbulent |
| D28 | 200 | 3.380 | 0.07186 | 0.719 | 0.30101 | 3.010 | Turbulent |
| D29 | 210 | 3.547 | 0.06265 | 0.627 | 0.14268 | 1.427 | Turbulent |
| D30 | 230 | 3.994 | 0.07561 | 0.756 | 0.02807 | 0.281 | Turbulent |
| D31 | 235 | 4.075 | 0.06712 | 0.671 | 0.04292 | 0.429 | High wind |
| D32 | 240 | 4.156 | 0.06756 | 0.676 | 0.03332 | 0.333 | High wind |
| D33 | 250 | 4.317 | 0.09064 | 0.906 | 0.03262 | 0.326 | High wind |
| D34 | 270 | 4.815 | 0.07856 | 0.786 | 0.04289 | 0.429 | High wind |
| D35 | 275 | 4.905 | 0.07866 | 0.787 | 0.05226 | 0.523 | High wind |
| D36 | 290 | 5.179 | 0.08469 | 0.847 | 0.08137 | 0.814 | **Flutter onset** |
| D37 | 300 | 5.281 | 0.25924 | 2.592 | 1.59691 | **15.97** | **FLUTTER** |
| D38 | 310 | 5.475 | 0.26277 | 2.628 | 1.70761 | **17.08** | **FLUTTER** |

**Noise floor** (D1–D5, < 0.5 m/s): bend RMS ≈ 0.027 mm, tors RMS ≈ 0.107 mm  
**Vertical VIV** (D8–D10, 0.85–1.03 m/s): bend RMS up to 2.76 mm; tors low (< 0.27 mm)  
**Torsional VIV** (D12–D15, 1.21–1.49 m/s): tors RMS up to 2.16 mm; bend low (< 0.58 mm)  
**Flutter** (D37–D38, > 5.28 m/s): tors RMS **15.97–17.08 mm** — catastrophic torsional instability  
**Note on D38:** Not in original Excel but raw file exists; processed from raw data (Python, 2026-06-09)

---

## 5. Structural Model Properties (from Lee 2016 PDF, Table 3)

| Property | Value |
|----------|-------|
| Model width | 34.4 cm |
| Model length | 2.54 m (test section: 1 m W × 1.5 m H × 6.0 m L) |
| Bending natural frequency | 1.95 Hz (PDF Table 3) |
| Torsion natural frequency | 5.15 Hz (PDF Table 3) |
| Frequency ratio (T/B) | 2.64 |
| Bending damping | 0.28% |
| Torsion damping | 0.13% |
| Scale factor | 1:50 |

**⚠️ Caveat:** Free-vibration MATLAB scripts (`fqB.m`, `fqT.m`) use bandpass at 1.43 Hz and 3.11 Hz — different from the PDF values (1.95/5.15 Hz). Either:
1. A different spring/mass configuration was used in the 2024 test, or
2. The free-vibration scripts used preliminary calibration data

**Before publication:** Confirm with TESolution whether the 2024 bridge model retained the same natural frequencies as the 2016 RINO paper specs.

---

## 6. Aerodynamic Regime Summary

| Regime | Wind (m/s) | D# range | Key characteristics |
|--------|-----------|----------|---------------------|
| Ambient / noise floor | < 0.65 | D1–D6 | Background vibration only |
| Vertical VIV | 0.84–1.12 | D8–D11 | Bending lock-in; torsion low |
| Torsional VIV | 1.21–1.49 | D12–D15 | Torsion lock-in; bending drops |
| Post-VIV / turbulent | 1.58–5.18 | D16–D36 | Broadband excitation, growing |
| Flutter | > 5.28 | D37–D38 | Catastrophic torsion; test stopped |

---

## 7. Usage Notes for Paper

- LDV bending and torsion values are **condition-level statistics** (RMS, peak over 30 s)
- **NOT** same-run, time-synchronized waveforms — compare as condition-level statistics only
- Always note: "torsion_diff_y_mm is differential vertical displacement at 200 mm from centerline, not validated torsion angle"
- D36 (flutter onset) and D37–D38 (full flutter) provide the most dramatic dynamic range
- D38 LDV data was processed from raw file but has no video counterpart

---

## 8. 2025 LDV Campaign — Tunnel B (Different Geometry)

**⚠️ This is a DIFFERENT facility from the 2024 data above. Sensor geometry changed. Do NOT compare values directly.**

**Source:** `context_data/TESolution/Video Measurement/laser_displacement/등류/영각00/BRID2D1.m`  
**Date:** September 2025

### 8.1 Geometry Parameters (Tunnel B)

```matlab
pvolt  = [2.7, 2.7];   % same calibration as Tunnel A
dside  = 13;           % ch2 (side sensor) distance from deck centerline [cm]
db     = 20;           % reference lever arm (half-chord) for torsion output [cm]
dp     = db/dside;     % = 1.538 — scale factor
```

**Sensor layout — center+side configuration (NOT symmetric):**
- ch1 (center sensor): at deck centerline, 0 cm from center
- ch2 (side sensor): 13 cm from deck centerline, to the right of center
- `센서간격 = 13 cm` = total gap between sensors (confirmed from setup sheet `설계속도 및 모형Setup_영상계측.xlsx`)
- Bridge half-chord: db = 20 cm (교폭 40 cm ÷ 2)

**Python pipeline torsion formula (correct for center+side):**
```python
torsion_cm = (ch2 - ch1) * dp    # dp = 20/13 = 1.538
```
For center+side, ch2 displacement = δ + θ×13, ch1 = δ (pure bending). So `(ch2-ch1) = θ×13`, and `(ch2-ch1) × (20/13) = θ×20` — displacement at the 20 cm reference position. No `/2` factor.

**The MATLAB `/2` formula (wrong for this geometry):**
The original `BRID2D1_choi.m` uses `(ch2-ch1)/2 × dp` with `dside=10`, designed for symmetric ±10 cm sensors. For center+side (ch1=0, ch2=13), the `/2` halves the signal without physical justification. The Python code correctly drops the `/2`.

**Python Tunnel A and Tunnel B give the same reference displacement:**
- Tunnel A: ch2 at 10 cm → `(θ×10) × (20/10) = θ×20` ✓
- Tunnel B: ch2 at 13 cm → `(θ×13) × (20/13) = θ×20` ✓

Both pipelines are dimensionally equivalent and produce displacement at the 20 cm reference. The 0.769× scaling difference applies only to the MATLAB `(ch2-ch1)/2 × dp` outputs, not the Python pipeline.

**Torsion ratio 0.599 — physical explanation (confirmed 2026-06-24):**
Camera torsion proxy = `y_cam3 − bending_avg` = differential displacement at Marker B arm ≈ 13–14 cm.
LDV torsion proxy = `(ch2-ch1) × dp` = displacement scaled to 20 cm (deck half-chord).
Expected ratio = 13/20 ≈ 0.65; observed stable mean 0.599, torsional VIV range 0.61–0.76 — physically consistent.
Manuscript: "Camera torsion proxy, measured at marker arm ~13 cm, underestimates the LDV torsion proxy (scaled to deck half-chord, 20 cm) by factor ~13/20 ≈ 0.65, consistent with the observed ratio of 0.599."

**Bending contamination (center+side geometry):**
For center+side LDV: `bending = (ch1+ch2)/2 = δ + θ×6.5` — the LDV bending channel contains a torsion contribution of θ×6.5 mm. In the torsional VIV regime (90–220 RPM), this independently explains why bending comparison is noisier (both LDV bending and camera bending are contaminated, in different ways).

### 8.2 Data Structure (Tunnel B)

| File | Rows | Duration | Notes |
|------|------|----------|-------|
| D00 | 7200 | 20 s | Static baseline |
| D01–D20 | 7200 each | 20 s each | Wind conditions |

Compared to Tunnel A (10800 rows = 30 s per condition), Tunnel B records 20 s per condition.

### 8.3 Free Vibration Parameters (Tunnel B)

```matlab
cal1 = 27; cal2 = 27;   % DAQ calibration factor
fs   = 360;              % same sampling rate
```

Free vibration files: `Bd1` (72000 rows = 200 s bending), `Td1` (72000 rows = 200 s torsion).

### 8.4 Results Summary (D01–D20, Tunnel B)

| D# | B_rms (mm) | T_rms (mm) | Regime |
|----|-----------|-----------|--------|
| D01–D03 | 0.112–0.114 | 0.133–0.135 | Ambient noise floor |
| D04–D05 | 1.766–2.908 | 0.145–0.154 | Bending VIV |
| D06–D10 | 0.620–0.748 | 1.024–1.132 | Torsional VIV onset |
| D11–D14 | 0.726–1.359 | 1.356–2.175 | Torsional VIV / turbulent |
| D18–D19 | 1.756–2.893 | 3.342–5.471 | Flutter buildup |
| D20 | 3.575 | **8.684** | Flutter onset |

**Note:** Bending VIV peak at D05 = 2.908 mm; torsional VIV starts around D06. This regime sequence (bending VIV first, then torsional VIV, then flutter) matches the Tunnel A 2024 data pattern.

### 8.5 Publication Use

- **Do NOT use** as a camera system reference (no camera data; different model geometry)
- Potentially useful as a second aerodynamic dataset in a broader study
- If TESolution confirms this is a TMD effectiveness study (j/m variants), it belongs in a different publication scope
- For full context, see `TESolution_2025_datasets.md` Part 1
