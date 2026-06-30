# OMRPR Project Progress Log

**Date:** 2026-06-23  
**Status:** Historical/supporting progress log; not the active source-of-truth layer

This file records the cleanup journey that led to the present documentation state.
It is intentionally kept shorter and non-authoritative so it does not compete with
the canonical docs.

Active source-of-truth layer:

1. `README.md`
2. `docs/PROJECT_CONTEXT.md`
3. `docs/claim_boundary.md`
4. `docs/OMRPR_SUPERVISOR_GUIDELINE.md`
5. `docs/pipeline_progress.md`
6. `results/step10/step10_summary.json`
7. `results/step10/ldv_summary.json`

---

## Final Sync Outcome

The current repo-facing documentation is aligned to:

- Bending Pearson r = **0.845**
- Torsion Pearson r = **0.940**
- Bending ratio = **1.339x**
- Torsion ratio = **0.599x**
- Timing drift = **20.03 ms**
- Tunnel context = **Tunnel B**, separate sessions ~10 days apart, **NOT simultaneous**
- Step 05 guard wording = **derived/proposed, not implemented in live code**

---

## Historical Notes

- Earlier cleanup passes experimented with a `0.833` manuscript-facing bending
  subset. That path is superseded for the present documentation sync.
- Some source files and generated outputs still contain older exploratory wording,
  but those are no longer treated as canonical manuscript-grounding material.
- The repo now distinguishes clearly between:
  - canonical docs for manuscript grounding, and
  - historical audit/critique notes retained for traceability.

---

## Remaining Non-Doc Technical Parity Item

The main unresolved code-vs-doc issue remains unchanged:

- `src/step05_synchronize.py` does not implement the documented 3-frame
  gap-aware interpolation guard.

That fact is now documented consistently as pending/proposed rather than as an
already-active feature.
