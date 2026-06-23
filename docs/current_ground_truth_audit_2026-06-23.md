# OMRPR Current Ground-Truth Audit

Date: 2026-06-23

Status: historical/supporting audit note. This file is not the active manuscript
source of truth. Use `docs/PROJECT_CONTEXT.md`, `docs/claim_boundary.md`,
`docs/OMRPR_SUPERVISOR_GUIDELINE.md`, `README.md`, and the live Step 10 JSONs as
the active canonical layer.

---

## Historical Context

This audit was created during a transition period when the repo still contained
mixed framing from multiple cleanup passes. It remains useful as a record of what
had to be reconciled, but its earlier recommendation to center the manuscript on
`0.833` is superseded for the present sync pass.

Current controlling decision for documentation sync:

- Canonical bending Pearson r: **0.845** (stable regime, 18 conditions)
- Canonical torsion Pearson r: **0.940** (stable regime)
- Recording context: **Tunnel B**, same facility, separate sessions ~10 days apart,
  **NOT simultaneous**
- Step 05 guard wording: **derived/proposed, not implemented in live code**

---

## Confirmed Active Canonical Values

These are the values the repo-facing docs should present after synchronization:

- Bending Pearson r: **0.845**
- Bending Spearman rho: **0.864**
- Bending MAE: **0.484 mm**
- Bending RMSE: **0.719 mm**
- Bending ratio: **1.339x**
- Torsion Pearson r: **0.940**
- Torsion Spearman rho: **0.928**
- Torsion MAE: **0.549 mm**
- Torsion RMSE: **0.771 mm**
- Torsion ratio: **0.599x**
- Timing drift: **20.03 ms**
- Natural frequencies: **1.4323 Hz** bending, **3.0827 Hz** torsion
- Natural period: **0.698 s**
- Conservative manuscript noise floor: **0.017 mm** bending, **0.033 mm** torsion

Primary supporting files:

1. `docs/PROJECT_CONTEXT.md`
2. `docs/claim_boundary.md`
3. `docs/OMRPR_SUPERVISOR_GUIDELINE.md`
4. `results/step10/step10_summary.json`
5. `results/step10/ldv_summary.json`

---

## Still-Useful Audit Findings

- The live Step 05 script still has no implemented gap-length guard.
- Any wording that suggests waveform-level or concurrent-session validation should
  be removed from canonical docs.
- Older `0.833` language should be treated as retired historical framing unless
  explicitly labeled as superseded analysis.

---

## Superseded Historical Note

Earlier versions of this audit argued for `0.833` as the single manuscript-facing
bending value. That recommendation is retained only as historical context about the
cleanup process. It is not the controlling choice for the current documentation sync.
