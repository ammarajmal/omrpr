# Roadmap

The unit of progress is an evidence-backed gate, not the existence of a script.

| Gate | Work package | Required exit evidence | Status |
|---|---|---|---|
| G0 | Repository stabilization | dirty-work snapshot, remote configured, isolated tests/lint green | IN PROGRESS |
| G1 | Data and observation control | immutable dataset hashes, reviewed condition/channel manifest, go/no-go rules | PARTIAL |
| G2 | Image-plane primary measurement | official AprilTag detections, corner/centroid tracks, stationary-reference compensation, rejection reasons | NOT STARTED |
| G3 | Precision and admissibility | static noise/PSD, per-camera/per-condition quality, no averaging through failed streams | NOT STARTED |
| G4 | KLT independent branch | AprilTag-anchored bounded KLT, hidden-frame/synthetic tests, return-anchor drift gates | QUARANTINED |
| G5 | State-estimation ablation | raw vs CV-KF vs oscillator-KF vs non-causal RTS; preregistered Q/R and acceptance metrics | QUARANTINED |
| G6 | Response/modal analysis | bending and torsion-proxy definitions, FDD + SSI-Cov consensus, uncertainty | NOT STARTED |
| G7 | LDV reconstruction | corrected D/RPM mapping, units, channel identity, geometry provenance, affected-result rebuild | PARTIAL/EXTERNAL PATCH |
| G8 | Condition-level benchmark | non-concurrent comparison, proportional-bias and small-N diagnostics, separate 320 RPM result | NOT STARTED |
| G9 | Robustness and reproducibility | bootstrap preserving adjacency, calibration sensitivity, config/result hashes, full rerun | PARTIAL |
| G10 | Publication package | figures/tables generated from locked results, claim audit, reviewer-response matrix | BLOCKED BY G1--G9 |

## Implementation order

1. Stabilize Git and Python isolation.
2. Freeze the observation manifest and derived-output contract.
3. Produce the official-AprilTag image-plane baseline.
4. Establish static and per-condition admissibility.
5. Add bounded KLT as an independent diagnostic, never silent gap filling.
6. Run the preregistered filter ablation; retain raw data as the primary result.
7. Add FDD/SSI-Cov modal consensus and valid block uncertainty.
8. Rebuild the corrected LDV branch and perform condition-level benchmarking.
9. Lock provenance, run the complete matrix, and generate publication outputs.

## Scope control

- EKF is conditional: use it only for a genuinely nonlinear observation model
  such as tag-corner projection. Scalar displacement does not require EKF.
- DIC/full-field phase methods and Bayesian SSI are optional extensions after
  the core gates, not prerequisites.
- No filter, calibration scenario, or admissibility threshold may be selected
  by maximizing camera--LDV agreement.
