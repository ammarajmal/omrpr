# Current State

**As of:** 2026-08-08

**Lifecycle:** active OMRPR-NS-001-controlled reconstruction

**Current gate:** S04 — primary official-AprilTag image-plane measurement

**Authoritative score:** 24/100. Read it from the sibling research hub with
`python3 scripts/research_supervisor.py status`; do not infer completion from
the presence of review reports or legacy Step JSON files.

## Established

- Raw datasets remain external and read-only.
- Official AprilRobotics detector is mandatory; tag family `tag36h11`, size
  20 mm.
- The camera and LDV campaigns are parallel, non-concurrent condition-level
  observations, not a joint synchronized measurement.
- Governing facility labels and speed conditions are controlled by the reviewed
  observation manifest; 320 RPM is excluded from stable summaries and retained
  as cam3-only diagnostic evidence where admissible.
- TESolution historically presented an unspecified Kalman-filtered comparison,
  but supplied no reproducible filter specification.
- Fresh physical calibration is unavailable. Image-plane results are primary;
  absolute metric/pose claims remain gated and calibration-sensitive.
- `omrpr-knowledge-system` contains the Phase 2--4 registers, primary-evidence
  decisions, calibration sensitivity, RTS ablation, KLT decision, and methods
  boundaries at commit `27f6c5c`.

## Existing implementation

- Step 00 bag audit and Step 01 image sampling/audit have implementation and
  derived review material.
- Steps 02--12 are primarily scaffold interfaces and documentation, not a
  validated end-to-end production pipeline.
- A Graphify snapshot exists, but it is generated navigation material rather
  than scientific evidence.
- The inherited worktree is preserved in commit `7e0bc23`; subsequent G0
  quality repairs are being reviewed as a separate bounded change.

## Current blockers

- `origin` now points to `ammarajmal/omrpr`. Its historical `master` has no
  common ancestor with this clean-room reconstruction and contains the prior
  pipeline/results lineage. It must be joined by a preservation-only ancestry
  merge on a review branch; its tree must not be imported as production code.
- PR #6 merged the preservation ancestry and clean-room working tree at
  `f605a05`. G0 is complete.
- The 21 canonical `wtt-main` bag identities are frozen by size and SHA-256 in
  `configs/dataset-identity-manifest.csv`. The expected 63 camera-condition
  observations and their camera/tag/location identities are frozen in
  `configs/observation-manifest.csv`.
- Observation gates are executable in `configs/observation-control.yaml` and
  `omrpr_analysis.observation_control`. They enforce campaign separation,
  image-plane primacy, per-stream decisions, 60 RPM diagnostic treatment, and
  the cam3-only 320 RPM boundary.
- The fresh Step 00 review run `20260801_022002` completed successfully using
  the hashed canonical audit CSV plus newly computed static gap/segment
  diagnostics. All 126 WTT topic rows passed; the 12 non-pass rows are confined
  to static streams. Static decisions are 8 accept-as-recorded, 5 segment
  selection, 5 lower-rate pending image review, and 2 long-gap review.
- The fresh bounded Step 01 run `20260801_022229` sampled 1,752 frames from 146
  streams with zero decode failures. Automated image checks mark 37 PASS and
  109 REVIEW because of near-duplicate samples; this is not automatic failure.
  All contact sheets and 146 manual-review rows remain human-gated.
- The locked Python 3.12 suite passes 10 tests with third-party pytest plugin
  autoload disabled. Ruff passes all 99 Python files and strict mypy passes the
  production package. Direct virtual-environment tool entry points are not
  executable on this mounted workspace, so pytest/mypy are invoked with
  `uv run python -m ...`; the Ruff binary was verified from uv's locked cache.
- No new physical calibration can be collected.
- Kalman/RTS and KLT have not passed preregistered physical-data validation.
- The final metric-displacement and torsion-proxy claim boundaries remain gated.

## Next action

Complete the S04 primary pixel-domain track and stationary-background-
compensation chain. Treat existing metric static-precision, LDV comparison,
frequency, and manuscript artifacts as provisional evidence until their
OMRPR-NS-001 checkpoints are accepted.
