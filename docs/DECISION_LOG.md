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
| 2026-08-01 | Treat generated analysis outputs as reproducible working products and Graphify as a disposable navigation index | Scientific evidence requires input/config/code/result provenance; generated indexes are not primary evidence | `docs/GENERATED_ARTIFACT_POLICY.md` |
| 2026-08-01 | Invoke pytest and mypy through the locked Python interpreter | Non-executable virtual-environment entry points caused `uv run` to fall through to system Python/ROS plugins on this mounted workspace | G0 quality audit; `Makefile`; `scripts/06_project_readiness.sh` |
| 2026-08-01 | Preserve remote `ammarajmal/omrpr` history without importing its tree into the clean-room baseline | Remote `master` is the historical pipeline/results lineage and has no common ancestor with the reconstructed repository; its claims and implementations cannot silently become production code | remote `master` at `1cc2cba`; local stabilization at `7e0bc23`; G0 remote audit |
| 2026-08-01 | Freeze image-plane observation control before clean-room WTT detection | Fresh calibration is unavailable; camera/tag identities, campaign separation, admissibility, and special-condition handling must not drift in response to downstream LDV agreement | `configs/observation-control.yaml`; `configs/observation-manifest.csv`; `configs/dataset-identity-manifest.csv` |
