# TESolution RINO Paper — Citation, Novelty Analysis, and Anonymization Rules

**Date:** 2026-06-09

---

## 1. Full Citation

### APA format
Lee, S.-W., Jeong, J.-H., Knez, K. P., Min, J.-H., & Jo, H. (2016). Practical application of RINO, smartphone-based dynamic displacement sensing application, for wind tunnel tests. *Proceedings of SPIE, 9803*, 98032X. https://doi.org/10.1117/12.2219404

### IEEE format
[Lee2016] S.-W. Lee, J.-H. Jeong, K. P. Knez, J.-H. Min, and H. Jo, "Practical application of RINO, smartphone-based dynamic displacement sensing application, for wind tunnel tests," *Proc. SPIE, Sensors and Smart Structures Technologies for Civil, Mechanical, and Aerospace Systems 2016*, vol. 9803, p. 98032X, Apr. 2016.

### Short key used in this project
`[Lee2016]`

### File location
`context_data/TESolution/TE SOLUTION RESULTS PAPER.pdf`

---

## 2. What the RINO Paper Is

A 10-page conference paper presented at SPIE Smart Structures + Nondestructive Evaluation, Las Vegas, NV, April 2016.

**Authors:**
- Sang-Won Lee (TESolution Co., Ltd., Anseong-si, South Korea)
- Jeong-Hyun Jeong (TESolution Co., Ltd.)
- Kyle P. Knez (Univ. of Illinois Urbana-Champaign, advised by H. Jo)
- Jae-Hong Min (TESolution Co., Ltd.)
- Hongki Jo (Univ. of Illinois Urbana-Champaign)

**Core contribution:** Validated the RINO iOS smartphone app for real-time dynamic displacement measurement in a wind tunnel test on a bridge section model. Compared smartphone displacement against LDV (KEYENCE laser sensors) across a series of wind speeds.

**RINO system characteristics:**
- iOS real-time app (iPhone 6s used in the paper)
- Color-blob tracking (red/blue circular markers on bridge model)
- Image processing in real-time on iPhone CPU
- Output: pixel coordinates in camera image frame
- Single-phone setup (two phones for two measurement points)
- No ROS, no multi-camera synchronization framework, no AprilTag

---

## 3. Facility and Model Specifications (from PDF)

| Property | Value |
|----------|-------|
| Tunnel type | Eiffel type |
| Test section | 1.0 m (W) × 1.5 m (H) × 6.0 m (L) |
| Wind speed range | 0.3–21.0 m/s |
| Turbulence intensity | < 0.7% |
| Bridge model width | 34.4 cm |
| Model scale | 1:50 |
| Bending natural frequency | 1.95 Hz |
| Torsion natural frequency | 5.15 Hz |
| Frequency ratio (T/B) | 2.64 |
| Bending damping | 0.28% |
| Torsion damping | 0.13% |
| LDV sensor | KEYENCE LB-1201/301, ±10 cm range |
| LDV sampling | 360 Hz |

**⚠️ Important caveat:** These specs are from the 2016 paper. The 2024 experiments used the same facility. The MATLAB free-vibration scripts from 2024 (`fqB.m`, `fqT.m`) bandpass at 1.43 Hz and 3.11 Hz — different from 1.95/5.15 Hz in the PDF. **Confirm with TESolution whether the bridge model configuration was identical in 2024 before citing Table 3 from [Lee2016] for the 2024 dataset.**

---

## 4. Novelty Threat Assessment

### Does [Lee2016] threaten your novelty?

**Verdict: LOW THREAT — but must be explicitly addressed.**

| Aspect | [Lee2016] | Your system (Paper 1 + WTT) |
|--------|-----------|------------------------------|
| Sensing method | Color-blob tracking (iOS) | AprilTag fiducial (ROS) |
| Platform | iPhone 6s, real-time | PC + cameras, offline ROS bag |
| Cameras | 1–2 iPhones | 3 Sony RX10 IV cameras via AverMedia capture cards |
| Synchronization | No multi-camera sync framework | ApproximateTime + software timestamps (no Chrony in WTT deploy) |
| Reference | LDV | LDV (same sensors) |
| Output | Pixel displacement | Metric displacement (meters, ROS) |
| 3D capability | 2D only (image plane) | 3D pose estimation |
| Dropout handling | None mentioned | Explicit dropout detection + recovery |
| Open source | No | ROS stack (open source) |
| Test conditions | VIV + turbulent | VIV + turbulent + flutter |

**Key differentiation statement for Related Work section:**
> "Lee et al. [Lee2016] demonstrated smartphone-based optical tracking in a wind tunnel bridge model test, achieving qualitative agreement with laser displacement sensors during VIV and turbulent conditions. The present work extends this approach using a multi-camera ROS-based AprilTag framework with explicit synchronization, offline reconstruction, and dropout recovery, enabling quantitative validation across VIV, turbulent buffeting, and flutter regimes."

### Why reviewers will still ask

Reviewers of a wind-engineering journal will cite [Lee2016] and ask: "How does your result differ from showing that cameras work in wind tunnels, which was already shown 8 years ago?"

**You must answer:**
1. Technology: AprilTag (scale-invariant, rotation-robust) vs color blob (sensitive to illumination, occlusion, blur)
2. Architecture: Distributed multi-camera ROS (any platform) vs single iOS device
3. Conditions: Extended dataset including flutter (D37–D38) — RINO paper did not capture flutter
4. Quantitative metrics: Sub-mm accuracy at noise floor vs qualitative agreement
5. Reproducibility: Open-source ROS stack vs proprietary iOS app

---

## 5. Other Relevant Citations

### For bridge section aerodynamics / VIV:
- Scanlan & Tomko (1971) — flutter derivatives (original paper)
- Larsen & Walther (1997) — aerodynamic VIV mechanisms
- Nakamura (1979) — torsional VIV of bridge girders

### For vision-based displacement measurement:
- Yoon et al. (2016) — camera-based SHM
- Feng & Feng (2018) — vision-based dynamic displacement
- Xu & Brownjohn (2018) — computer vision for civil SHM

### For ROS-based sensing:
- Cite your own Paper 1 (IEEE Access): Ajmal et al., "[Paper 1 title]"

### For AprilTag:
- Wang & Olson (2016) — AprilTag 2
- Krogius et al. (2019) — Flexible Layouts for AprilTag

---

## 6. Anonymization Rules (MANDATORY)

### NEVER write in any publication:
- "TESolution Co., Ltd."
- "Anseong-si, South Korea"
- Any institutional name visible on the PDF cover page
- The full names of the facility employees who adapted the MATLAB scripts

### Safe writing patterns:
- "A commercial wind tunnel testing facility" or "the wind tunnel operator"
- "The testing facility [Lee2016]" (cite the paper, not the company name)
- "Laser displacement sensors provided by the facility operator"
- "The experimental data was collected in collaboration with the facility operator"

### Why this rule exists:
The facility is named throughout the Lee et al. 2016 paper. Naming TESolution in your publication:
1. May violate data use agreements (if they restrict public identification)
2. Could complicate authorship and attribution negotiations
3. If the paper is ever in dispute, direct naming makes legal complications more serious

### Permitted:
- Citing [Lee2016] — the publication is public record
- Stating that the facility is a commercial wind tunnel testing company
- Stating that the structural model specifications match those in [Lee2016]
- Acknowledging "the facility operator" in the Acknowledgments section

---

## 7. Attribution and Authorship Considerations

Before submitting any paper using this dataset:

1. **Data use agreement:** Obtain written consent from TESolution to publish analysis results from their October 2024 wind tunnel test.
2. **Authorship:** "CHOI" adapted the MATLAB analysis scripts. Other TESolution researchers may have been involved in setting up the camera system. Standard academic practice would include them as co-authors or in the Acknowledgments.
3. **Hardware acknowledgment:** If TESolution provided the camera hardware (even temporarily), this should be disclosed.
4. **IP:** The raw data files are the intellectual property of TESolution unless otherwise agreed. The analysis code belongs to the user. A data sharing agreement clarifies this.
