# Task Queue

> OMRPR-NS-001 controls ordering and progress. This file is an implementation
> view; checked boxes do not independently earn score.

## Now — G0

- [x] Record bounded write authorization in both repositories.
- [x] Preserve the knowledge-system evidence in a local commit.
- [x] Configure the registered remote, push the preservation branch, and open
  draft PR #6; merge remains human-reviewed.
- [x] Commit the inherited `omrpr-analysis` worktree as a named stabilization
  snapshot before feature edits.
- [x] Repair `uv`/pytest isolation from system ROS plugins and prove package
  import, tests, Ruff, and mypy from the locked environment.
- [x] Classify generated `outputs/` and `graphify-out/` retention policy.

## Next — G1 to G3

- [x] Import/freeze the reviewed expected-observation manifest as runtime
  configuration.
- [x] Freeze the 21 canonical `wtt-main` bag identities by SHA-256.
- [x] Populate the manifest with measured per-camera/per-condition gate records;
  schema validation and deterministic pass/warning/fail decisions are implemented.
- [x] Run Step 00 structural/timing and static-gap audit reproducibly.
- [x] Run bounded Step 01 decode sampling across all 146 streams with zero
  decode failures.
- [x] Human-review all Step 01 contact sheets and complete the 146-row manual
  review ledger before approving image content.
- [x] Verify official AprilRobotics binary/version at runtime.
- [x] Implement image-plane AprilTag observation export with provenance and
  explicit rejection reasons.
- [ ] Complete raw pixel-domain tracks and stationary-background compensation.
- [ ] Rebuild static precision/PSD without promoting provisional metric results.
- [ ] Produce the signed admitted-observation manifest required by S05.

## Then — G4 to G6

- [ ] Port bounded AprilTag-anchored KLT behind a feature flag.
- [ ] Preregister KLT hidden-frame and physical-data acceptance tests.
- [ ] Implement constant-velocity and oscillator-aware linear Kalman filters.
- [ ] Keep causal KF and non-causal RTS outputs separately labelled.
- [ ] Run raw/KF/RTS ablation across conditions and fixed Q/R sensitivity grid.
- [ ] Implement FDD and SSI-Cov modal-consensus outputs.

## Later — G7 to G10

- [ ] Integrate corrected D-file/RPM mapping through the authorized `omrpr_fin`
  workflow and rebuild affected LDV results.
- [ ] Implement non-concurrent condition-level benchmark and small-N/proportional
  bias diagnostics.
- [ ] Run calibration-scenario sensitivity without selecting against LDV.
- [ ] Generate locked figures, tables, provenance bundle, and claim audit.

## Parking lot

- EKF tag-corner projection experiment.
- DIC/full-field cross-check.
- Bayesian modal identification.
- Automated knowledge-graph/RAG layer after schemas and provenance stabilize.
