# Decision Log

| Date | Decision | Rationale | Evidence |
|---|---|---|---|
| 2026-07-21 | Recalibrate all cameras from scratch | Legacy intrinsics are inconsistent and implausible | LEGACY_ANALYSIS_REPORT.md §1 |
| 2026-07-21 | Use official AprilRobotics detector only | Legacy detector stacks violate project constraint | AGENTS.md; report §4 |
| 2026-07-21 | Preserve tag IDs through fusion | Prevent cross-marker pooling regression | report §5 |
| 2026-07-31 | Authorize bounded writes to `omrpr-analysis` | Continue the approved pipeline while retaining raw/legacy/manuscript protection | Owner instruction; AGENTS.md |
| 2026-07-31 | Use image-plane displacement as the primary observable | Fresh physical calibration is unavailable and historical intrinsics are not governing evidence | Knowledge-system calibration sensitivity and Phase 4 decisions |
| 2026-07-31 | Treat TESolution filtering as unspecified historical Kalman evidence | Presentation pages 18--23 show filtering but omit model, Q/R, code, and causal/smoother identity | `Displacement Measurement System_V2.pdf` |
| 2026-07-31 | Require raw/CV-KF/oscillator-KF/RTS ablation | Filtering must preserve physical amplitude/frequency and cannot be tuned to LDV agreement | State-estimation implementation plan |
| 2026-07-31 | Keep KLT and RTS quarantined pending physical validation | Synthetic success does not establish physical-data validity | Pre-Phase-5 validation report |
