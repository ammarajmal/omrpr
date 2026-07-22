# Decision Log

| Date | Decision | Rationale | Evidence |
|---|---|---|---|
| 2026-07-21 | Recalibrate all cameras from scratch | Legacy intrinsics are inconsistent and implausible | LEGACY_ANALYSIS_REPORT.md §1 |
| 2026-07-21 | Use official AprilRobotics detector only | Legacy detector stacks violate project constraint | AGENTS.md; report §4 |
| 2026-07-21 | Preserve tag IDs through fusion | Prevent cross-marker pooling regression | report §5 |
