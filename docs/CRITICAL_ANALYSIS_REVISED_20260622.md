# CRITICAL ANALYSIS: OMRPR VALIDATION RESULTS

**Date:** 2026-06-22  
**Status:** Historical analysis note; not the active source-of-truth layer

This document is retained as a supporting critique from an earlier review pass.
It should be read as historical analysis, not as the controlling manuscript
baseline. The active canonical layer for the current repo sync is:

- `README.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/claim_boundary.md`
- `docs/OMRPR_SUPERVISOR_GUIDELINE.md`
- `results/step10/step10_summary.json`
- `results/step10/ldv_summary.json`

---

## Active Canonical Interpretation

For the current documentation sync, use these values and framing:

| Metric | Active canonical value | Interpretation |
|--------|------------------------|----------------|
| Torsion Pearson r | **0.940** | Robust stable-regime result |
| Bending Pearson r | **0.845** | Stable-regime value; below gate but physically explained |
| Bending ratio | **1.339x** | Characterised physical limitation, not an accuracy claim |
| Torsion ratio | **0.599x** | Geometry-sensitive but stable after correction |
| Recording context | **Tunnel B, separate sessions, NOT simultaneous** | Condition-level comparison only |

The bending result is interpreted as a documented physical limitation driven by
cross-axis sensitivity from the ~9.8 degree inter-camera misalignment. It is not
treated as a code or processing defect.

---

## Superseded Historical Framing

Earlier analysis variants in this file referenced a `0.833` bending result and an
above-floor subset as the manuscript-facing center. That framing is preserved only
as an example of the repo's transition state before the final documentation sync.

If those older numbers are cited at all, they must be labeled as:

- retired historical subset analysis,
- not the active canonical documentation baseline,
- not the value to propagate into README or manuscript-grounding docs.

---

## Supporting Critique That Still Holds

The following review points remain useful:

1. Torsion is the strongest validation result and should be emphasized.
2. Bending requires an up-front explanation of regime-dependent leakage.
3. The comparison must be framed as condition-level only because the recordings are
   separate-session and non-simultaneous.
4. The Step 05 gap-aware interpolation guard remains a documented pending design,
   not a live implementation.
