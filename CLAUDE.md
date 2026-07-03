# OMRPR Codebase Context — fin_phd

## Active Paths
- Codebase: /media/ammar/phd/fin_phd/omrpr_fin
- Manuscript: /media/ammar/phd/fin_phd/omrpr_manuscript
- Private data: /media/ammar/phd/fin_phd/omrpr_private_data
- Literature: /media/ammar/phd/fin_phd/omrpr_literature
- AI memory: /media/ammar/phd/fin_phd/omrpr_ai_memory
- Canonical claims: /media/ammar/phd/fin_phd/omrpr_fin/docs/claim_boundary.md

## Operating Strategy
- Ubuntu 24.04 host for analysis, plotting, writing, AI tools, and Git.
- ROS1 Noetic only inside Ubuntu 20.04 Docker/devcontainer.
- Do not recommend OS switching.
- Do not recommend native ROS Noetic on Ubuntu 24.04 unless explicitly requested as an experiment.

## Data Policy
- Code/scripts can be public.
- Raw experimental data is private.
- Do not commit raw data, videos, ROS bags, or huge image dumps.

## Claim Rules
- Read `docs/claim_boundary.md` before changing any manuscript claim or number.
- Never invent metrics.
- Never convert `torsion_diff_y_mm` into a torsion angle.
- Timing mitigation value is 20.03 ms max pairwise drift (cam1-cam3), software common-grid only.

## Ground Truth — Option B Canonical (LOCKED 2026-07-01)
docs/claim_boundary.md holds the full table; headline numbers only here:
- Bending Pearson r (stable, 19 cond.) = 0.9598 (report ≈0.960), RMSE = 0.2930 mm (≈0.293 mm)
- Torsion proxy Pearson r (stable) = 0.9676 (report ≈0.968), mean ratio 0.7853× (≈0.785×)
- LDV geometry: 2024 paired session (Tunnel A facility), dside=100mm, dp=2.0, pvolt=2.7 cm/V, fs=360 Hz
  — vendor-verified (2026-07-03) via TESolution's own `BRID2D1_choi.m` (Ver 2.1, 2024.11.11) and
  `Displacement Measurement System_V2.pdf`; see docs/RESULTS_LOG.md "2026-07-03 RESOLVED" entry.
- Superseded: B0 values (2025 standalone LDV session, same facility, dp=1.538, dside=130mm — physical
  sensor repositioning between sessions, NOT a different tunnel/lab) — DO NOT USE
- "Tunnel A"/"Tunnel B" naming in older docs was a facility mislabel, corrected 2026-07-03 — there is
  only ONE physical wind tunnel facility across all 2024/2025 sessions.
