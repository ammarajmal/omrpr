# OMRPR-Analysis — Agent Instructions

PhD research repo: multi-camera AprilTag displacement tracking of a bridge-deck
model in wind-tunnel testing, benchmarked non-simultaneously against LDV.

## Governing plan and progress authority

Scientific progress, score, deviations, and publication-stage status are
controlled by the sibling research hub:

- `/mnt/space/adev/projects/active/structural-vision-research/10_PROJECT_MANAGEMENT/RESEARCH_NORTH_STAR_SUPERVISORY_SYSTEM.md`
- `/mnt/space/adev/projects/active/structural-vision-research/10_PROJECT_MANAGEMENT/RESEARCH_MASTER_PLAN.json`
- its progress, deviation, and decision ledgers.

This repository owns implementation and reproducible derived outputs. Its
legacy Step 00--12 documents are engineering crosswalks only and cannot approve
scientific progress independently.

**Read `LEGACY_ANALYSIS_REPORT.md` first, in full, before writing any code.**
It is a full-pipeline audit of a prior 188GB implementation of this same
project (`/mnt/data/DEV/shm-displacement-project`) and documents concrete
bugs already found and fixed once — recalibration, LDV-geometry mixup,
wrong frequency-reference constants, untagged fusion, etc. Repeating any of
those bugs is a regression, not a fresh mistake.

## Hard constraints

### Write authorization and boundary (2026-07-31)

The project owner explicitly authorizes bounded pipeline development in this
repository. Codex may modify pipeline source, tests, configuration,
reproducibility/provenance records, project-management documentation, and
derived outputs. Raw datasets, legacy repositories, and manuscript repositories
remain read-only. Preserve and classify the dirty worktree that existed at the
time of authorization; do not overwrite unrelated or uncertain changes.

- **AprilTag detection must use the official AprilRobotics `apriltag` C
  library** (built from source, v3.4.5+), never `pupil_apriltags` and never
  `cv2.aruco`. This is an explicit, non-negotiable user requirement — every
  detector in the legacy codebase used one of the two forbidden options,
  which is part of why this rewrite exists.
- Tag family `tag36h11`, tag size `0.020 m` (20mm) — confirmed correct in
  all working legacy code (only documentation drafts had a wrong 80mm
  value inherited from a different, earlier paper).
- Static tests: 1 AprilTag shared by all 3 cameras. WTT tests: 2 physical
  AprilTags, both decoding as tag ID 0 — marker A viewed by cam1+cam2
  (stereo-capable), marker B viewed by cam3 (monocular). Camera coverage and
  explicit marker-group identity distinguish the two physical markers. Always
  fuse within the declared marker group; never pool observations across marker
  groups (see report §5 for the exact legacy bug this avoids).
- Do not treat any legacy camera-intrinsics/calibration file as valid production
  calibration. Fresh physical calibration is currently unavailable. The
  approved workaround is to keep image-plane displacement as the primary
  defensible observable, quarantine absolute metric/pose claims, and run a
  declared calibration-sensitivity analysis when metric results are explored.
  Legacy intrinsic families may be used only as labelled sensitivity scenarios,
  never selected by maximizing agreement with LDV. See report §1 for why the
  historical intrinsics cannot be adopted as ground truth.
- Raw dataset lives externally, symlinked in under `data/{raw,interim,
  processed,metadata}/source` → `/mnt/space/adev/datasets/omrpr/*`. Never
  copy from the legacy directories at `/mnt/data/DEV/shm-displacement-project*`
  — those are read-only reference material for this report, not a data
  source.

## Repo state

This repo was nuclear-reset on 2026-07-21 (see git log) — only `.git`,
`.venv`, and `LEGACY_ANALYSIS_REPORT.md`/`AGENTS.md` exist. No scaffolding,
no `pyproject.toml`, no `ai-context/` docs. All of that needs rebuilding as
part of this work, informed by the report rather than copied from the old
`ai-context/` files (which are gone, preserved only in git history at
commit `341e7f6` if ever needed for reference).

Use `uv` for the Python environment. PEP 723 inline-script dependencies
(`#!/usr/bin/env -S uv run` + `# /// script ... ///`) are the preferred
style for standalone pipeline-step scripts, consistent with how the
previous iteration of this repo (before the reset) was structured.

## Tooling session record

For what commit-hook/CI infrastructure exists in this repo and why
(number-ledger pre-commit gate, `core.hooksPath` setup), see
`structural-vision-research/10_PROJECT_MANAGEMENT/TOOLING_SESSION_2026-08-02.md`
(sibling repo at `/mnt/space/adev/projects/active/structural-vision-research`).
