# Current State

**As of:** 2026-07-31

**Lifecycle:** active clean-room reconstruction, before production WTT replay

**Current gate:** G0 — repository/worktree stabilization

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
- The worktree inherited 21 modified/untracked paths at authorization time.
  They must be preserved in the stabilization snapshot and reviewed before
  overlapping edits.

## Current blockers

- No Git remote is configured, so commits cannot yet be pushed.
- The current `uv run pytest` resolves contaminated system/ROS pytest plugins
  and fails collection with `ModuleNotFoundError: omrpr_analysis`; environment
  isolation must be repaired before test status can be called green.
- The preservation pre-commit run reports 20 remaining Ruff violations in
  inherited camera/comparison/laser and packaged Step-00 scripts.
- No new physical calibration can be collected.
- Kalman/RTS and KLT have not passed preregistered physical-data validation.
- The final metric-displacement and torsion-proxy claim boundaries remain gated.

## Next action

Complete G0: snapshot the inherited worktree, restore isolated testing, freeze
the observation manifest/config schema, and run Step 00/01 reproducibly before
implementing the primary image-plane detector branch.
