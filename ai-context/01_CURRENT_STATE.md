# Current State

**As of:** 2026-07-31

**Lifecycle:** active clean-room reconstruction, before production WTT replay

**Current gate:** G0 — repository/worktree stabilization (draft PR review pending)

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
- Draft PR #6 proposes that preservation merge and clean-room working tree. G0
  may close after its history strategy and tree replacement are reviewed and
  merged.
- The locked Python 3.12 suite passes 10 tests with third-party pytest plugin
  autoload disabled. Ruff passes all 99 Python files and strict mypy passes the
  production package. Direct virtual-environment tool entry points are not
  executable on this mounted workspace, so pytest/mypy are invoked with
  `uv run python -m ...`; the Ruff binary was verified from uv's locked cache.
- No new physical calibration can be collected.
- Kalman/RTS and KLT have not passed preregistered physical-data validation.
- The final metric-displacement and torsion-proxy claim boundaries remain gated.

## Next action

Review and merge draft PR #6 to close G0. Then freeze the observation
manifest/config schema and run Step 00/01 reproducibly before implementing the
primary image-plane detector branch.
