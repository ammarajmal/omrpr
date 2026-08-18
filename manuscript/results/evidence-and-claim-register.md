# Evidence and claim register

Date assembled: 2026-08-04

| Manuscript topic | Reviewed source | Permitted claim | Required boundary |
|---|---|---|---|
| Runtime readiness | `outputs/reports/project-readiness-latest.txt` | The configured project checks pass | One warning is the known dirty working tree |
| Detector | Step 05 review and import metadata | Official AprilRobotics v3.4.5, `tag36h11`, 20 mm | Do not mention OpenCV ArUco or pupil_apriltags as the production detector |
| WTT markers | Owner confirmation; `configs/project.yaml` | Two physical markers both decode as ID 0; marker A is viewed by cam1+cam2 and marker B by cam3 | Preserve camera and marker-group identity; never pool the two physical markers |
| Detection coverage | `outputs/reports/step_05_review.md` | 115,276 audit rows; 75,404 valid; 21 conditions; 3 cameras | Invalid rows were retained for traceability |
| Fusion | `outputs/reports/step_06_review.md` | Timestamp matching and marker-group fusion were applied | Do not claim hardware synchronization |
| Response channels | `outputs/reports/step_07_review.md` | Bending and torsion-proxy channels are separated | Torsion-proxy is not a validated physical angle |
| LDV | `outputs/reports/step_08_review.md` | 38 processed Tunnel A condition rows from D1-D38 | LDV is a benchmark from a separate campaign |
| Benchmark | `outputs/reports/step_09_review.md` | Stable joined conditions show positive condition-level association | Do not describe LDV as ground truth; exclude 60/70/80 and 320 RPM from stable fit |
| Static precision | `outputs/reports/step_04_static_precision.md` | No-wind and low-speed response is separated from 60 RPM onset | Metric values are provisional and calibration-sensitive |
| Frequency | `outputs/reports/step_10_review.md` | 60 RPM camera peak near 1.406 Hz is close to the 1.430 Hz bending mode | Do not use the unrelated 1.95/5.15 Hz reference pair |
| 320 RPM | Steps 04, 07, 09, and 12 reviews | Diagnostic-only high-response condition | No LDV counterpart; exclude from stable summaries |

## Transferred artifacts

| Manuscript file | Upstream source | Transfer rule |
|---|---|---|
| `figures/step04_static_precision_rms.png` | `outputs/figures/step04_static_precision_rms.png` | Byte-for-byte copy |
| `tables/step04_static_admissibility_thresholds.md` | `outputs/tables/step04_static_admissibility_thresholds.md` | Byte-for-byte copy |

## Resolved consistency issue

On 2026-08-04, the project owner confirmed that both physical WTT markers
decode as tag ID 0. Marker A is covered by cam1+cam2 and marker B by cam3, so
camera coverage and explicit marker-group identity must distinguish them
throughout processing and manuscript reporting.
