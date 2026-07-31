# Changelog

## 1.0.1 — 2026-08-01

- Use the activated external runtime directly instead of invoking `uv run` and
  triggering an unintended environment synchronization.
- Validate the active Python executable rather than rejecting an inactive
  repository-local environment directory.

## 1.0.0 — 2026-07-28

- Added non-destructive Step 00 launcher.
- Added external-environment and bag-count preflight.
- Added full and reusable-audit modes.
- Added dataset summary and bag coverage reports.
- Added exact static-gap localization and contiguous-segment statistics.
- Added refined static acceptance decisions.
- Added Markdown final report, provenance, logs, script snapshot, and checksums.
