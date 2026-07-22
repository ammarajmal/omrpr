# OMRPR-Analysis — Agent Instructions

PhD research repo: multi-camera AprilTag displacement tracking of a bridge-deck
model in wind-tunnel testing, benchmarked non-simultaneously against LDV.

**Read `LEGACY_ANALYSIS_REPORT.md` first, in full, before writing any code.**
It is a full-pipeline audit of a prior 188GB implementation of this same
project (`/mnt/data/DEV/shm-displacement-project`) and documents concrete
bugs already found and fixed once — recalibration, LDV-geometry mixup,
wrong frequency-reference constants, untagged fusion, etc. Repeating any of
those bugs is a regression, not a fresh mistake.

## Hard constraints

- **AprilTag detection must use the official AprilRobotics `apriltag` C
  library** (built from source, v3.4.5+), never `pupil_apriltags` and never
  `cv2.aruco`. This is an explicit, non-negotiable user requirement — every
  detector in the legacy codebase used one of the two forbidden options,
  which is part of why this rewrite exists.
- Tag family `tag36h11`, tag size `0.020 m` (20mm) — confirmed correct in
  all working legacy code (only documentation drafts had a wrong 80mm
  value inherited from a different, earlier paper).
- Static tests: 1 AprilTag shared by all 3 cameras. WTT tests: 2 AprilTags
  — marker A (tag ID 0) viewed by cam1+cam2 (stereo-capable), marker B
  (tag ID 1) viewed by cam3 (monocular). Always fuse per tag ID explicitly;
  never pool detections across tag IDs (see report §5 for the exact legacy
  bug this avoids).
- Do not import any legacy camera-intrinsics/calibration file. Recalibrate
  from scratch — see report §1 for why every legacy intrinsics source is
  provably wrong.
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
