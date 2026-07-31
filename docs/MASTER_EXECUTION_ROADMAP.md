# Master Execution Roadmap

| Step | Stage | Exit gate |
|---:|---|---|
| 00 | Source inventory and bag audit | Canonical bags classified; timing report reviewed |
| 01 | Calibration-input audit | Target dimensions and image suitability documented |
| 02 | Calibration limitation and sensitivity | Image-plane primary observable locked; intrinsic scenarios bounded; metric claims gated |
| 03 | Official AprilTag verification | Upstream v3.4.5+ import and tag36h11 fixture pass |
| 04 | Static precision | Timing, detection, RMS, PSD, and axis-specific noise documented |
| 05 | WTT detection and pose export | Per-camera/per-tag outputs with rejection reasons |
| 06 | Timestamp matching and per-tag fusion | No positional truncation; raw/aligned disagreement saved |
| 07 | Response construction | Bending and torsion-proxy definitions frozen |
| 08 | LDV processing | Units, mapping, geometry, filtering, and provenance verified |
| 09 | Condition benchmarking | Primary and diagnostic analyses separated |
| 10 | Frequency and uncertainty | Correct model frequencies and uncertainty components used |
| 11 | Manuscript outputs | Every value generated and consistency-checked |
| 12 | Submission readiness | Claims, anonymization, files, and reproducibility package audited |

A stage is approved only by writing a reviewed JSON gate with
`uv run omrpr pipeline approve --step N --evidence <path>`.
