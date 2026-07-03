# Claude Code Session Summary — 2026-07-03

**Scope:** Wire manuscript figures into `04_results.tex`; investigate and fix everything
that turned out to block that cleanly. Session spanned both `omrpr_fin` (pipeline code)
and `omrpr_manuscript` (LaTeX + claim_boundary.md mirror).

**Bottom line:** the five manuscript figures are now generated from a pipeline that
independently reproduces `claim_boundary.md`'s locked numbers, wired into the LaTeX with
verified captions, and the manuscript compiles cleanly. Three additional stale-number
problems were found and fixed along the way (bootstrap CI width, a retired ratio
explanation, and a wrong noise-floor value that also affected the DCG gate equation).
Nothing has been committed — see `git diff` before deciding what to keep.

---

## 1. Why this went further than "add \includegraphics"

Checking Fig. 3/5's embedded numbers against `claim_boundary.md` before inserting them
surfaced that `omrpr_fin/results/step12/` figures were built from a pipeline that no
longer matched the locked v2.1 numbers:

- `step07_motion_decompose.py` computed `bending_avg_y_mm` as the **2-camera** average
  `(cam1+cam2)/2`. The locked r=0.960 depends on the **3-camera cross-bridge average**
  `((cam1+cam2)/2 + cam3)/2` — confirmed from `omrpr_manuscript/scripts/verify_option_b.py`'s
  own docstring, which documents this exact formula change as the fix that took r from
  0.845 → 0.960.
- `step09_uncertainty.py` and `step10_ldv_comparison.py` both still hardcoded `e4_60rpm`
  as an excluded "VIV outlier" condition — the exact exclusion `claim_boundary.md`'s
  2026-07-02 changelog says was retracted.
- `step10_ldv_comparison.py` additionally pointed at the wrong LDV dataset entirely: the
  retracted 2025 standalone session (`dside=130mm`, `dp=1.538`), not the vendor-verified
  2024 paired session (`dside=100mm`, `dp=2.0`) that the manuscript's numbers are locked
  to.

## 2. Fixes applied (in order)

1. **`step07_motion_decompose.py`** — bending formula corrected to the cross-bridge
   average. Torsion (`torsion_diff_y_mm`) deliberately kept on the *original* 2-camera
   reference (`cam3 - (cam1+cam2)/2`), not the new bending average, so the already-correct
   torsion proxy (r=0.968) wasn't silently changed by reusing a column that now includes
   cam3 twice.
2. **`step09_uncertainty.py`** — `e4_60rpm` removed from the hardcoded VIV exclusion;
   added to `stable_conditions`. Made the `rosbags` import lazy (only needed for Section A
   static-bag noise floor, which wasn't rerun this session — no `rosbags` package
   installed in this environment).
3. **`step10_ldv_comparison.py`** — rewritten to the correct 2024 paired-session LDV path,
   geometry (`dside=10cm`, `dp=2.0`), and RPM→D-file mapping (matching
   `verify_option_b.py`'s already-validated `CONDITIONS` dict); removed the 60RPM
   exclusion; updated gate targets and all prose to v2.1 numbers.
4. Reran **steps 07→11** across all 21 conditions. Verified against
   `option_b_verified_table.csv`: LDV values match byte-identical; camera RMS matches
   within ~1-4% for every condition 70 RPM and above. The only large relative deviations
   are at 20/40/50 RPM (already-documented near-floor conditions where tiny absolute
   differences swing the ratio disproportionately) — explained, not a bug.
5. **`step12_figures_tables.py`** — removed the retired "y_leak ≈ α·sin(9.8°) torsion
   coupling" bending-ratio explanation (hardcoded `BENDING_RATIO_MEAN_STABLE=1.339`,
   `BENDING_STABLE_PEARSON_R=0.845`, `BENDING_STABLE_N=18` — all B0-era numbers) from
   Fig. 3's caption/annotation and Table 2. Removed the "VIV (60 RPM)" scatter category
   from Fig. 3/5. Fixed Fig. 1's title/caption ("Camera 1 & 2 mean" → "cross-bridge
   average, Camera 1, 2 & 3") to match the new formula. Fig. 3 itself was rewritten to
   load `option_b_verified_table.csv` directly (not the in-repo pipeline output) so it
   stays numerically identical to the manuscript's own Table 1, which is built from that
   same file.
6. **`omrpr_manuscript/scripts/gen_fig03_ldv_scatter.py`** — a second, independent fig03
   generator (already correct on the ratio/VIV front) was found writing to the same
   output path. Fixed it to stop reporting torsion Spearman ρ/MAE/RMSE, which
   `claim_boundary.md` explicitly says are not reported for the torsion proxy. This
   script's output is the one actually used (more polished, correct off-axis handling of
   the 320 RPM torsion outlier).
7. Regenerated all 5 figures, verified visually, copied into
   `omrpr_manuscript/manuscript/figures/` and `omrpr_outputs_review/final_figures/`
   (checksums match).
8. Wired all 5 figures into `omrpr_manuscript/manuscript/sections/04_results.tex` with
   captions cross-checked against `claim_boundary.md`. Manuscript compiles cleanly via
   `latexmk` (28 pages, no errors, only benign overfull-hbox warnings).

## 3. Three follow-on fixes (found while closing out the above)

**Bootstrap CI width.** Re-including 60 RPM as stable shifted the mean relative CI width
(stable, non-near-floor, n=18): bending 13.3%→14.3%, torsion 15.0%→16.3%. Updated
`claim_boundary.md` (changelog + claim line) and `04_results.tex`.

**Retired ratio explanation still in `claim_boundary.md`.** Its "What We CAN Claim"
section still listed the "torsion coupling y_leak ≈ 0.170α, ~2× bending-ratio inflation"
explanation — the same B0-era mechanism the manuscript's actual Discussion (Sec. 5.2)
deliberately does *not* use (per `FINALIZATION_PLAN.md`'s existing Phase 4 note). Removed
it; replaced with the current 3-factor explanation (non-simultaneity, spatial-averaging
geometry, residual timing) that Discussion and the figures now consistently use. The
separate, still-valid 0.038mm/13.0%/9.8° fixed-bias claim (Limitations Sec. 6.6) was
retained unchanged — it's a distinct, correct claim that happened to be bundled in the
same old bullet.

**Noise floor was stale, and it cascaded into the DCG gate equation.** The manuscript
(abstract, Methods, Results, Table 1 caption) stated noise floor = 0.017mm bending /
0.033mm torsion. Confirmed via `pipeline_config.yaml`'s camera intrinsics (fx values
match the documented post-fix values) and `noise_floor_summary.json`'s reprojection error
(0.035–0.17px, in the correct range) that this was a **pre-2026-06-20-intrinsics-fix**
value that had never propagated into manuscript-facing text, even though the pipeline
itself has computed and gate-checked against the corrected ~0.004mm/0.005mm value ever
since. Fixing the number meant the Methods section's own interpolation-error derivation
(`Eq. dcg-threshold`, comparing ε against the noise floor to justify the `n_miss,max ≤ 2`
frame criterion) no longer held arithmetically — ε(2 frames)=0.0141mm is *not* below the
corrected 0.004mm floor. Re-derived: the threshold is `N ≤ 1` frame, not `N ≤ 2`.
**Verified this changes zero reported results**: every stable condition
(`results/step02/*/summary.json`) has `max_consecutive_miss = 0` on every camera, so the
N=1-vs-N=2 choice has no practical effect on which conditions pass the DCG or on the
19-stable-condition sample. Updated: `abstract.tex`, `01_introduction.tex` (Contribution
2), `02_methods.tex` (Eq. dcg + derivation), `04_results.tex` (noise floor values, Table 1
caption, Frequency section), `07_conclusion.tex`, `claim_boundary.md`, `RESULTS_LOG.md`.

## 4. Files touched

**Code (`omrpr_fin/src/`):** `step07_motion_decompose.py`, `step09_uncertainty.py`,
`step10_ldv_comparison.py`, `step12_figures_tables.py`

**Docs (`omrpr_fin/docs/`):** `claim_boundary.md` (multiple changelog entries),
`RESULTS_LOG.md`

**Scripts (`omrpr_manuscript/scripts/`):** `gen_fig03_ldv_scatter.py`

**Manuscript (`omrpr_manuscript/manuscript/`):** `abstract.tex`,
`sections/01_introduction.tex`, `sections/02_methods.tex`, `sections/04_results.tex`,
`sections/07_conclusion.tex`, `figures/fig0{1..5}_*.pdf` (regenerated)

**Mirrors:** `omrpr_manuscript/docs/source_of_truth/claim_boundary.md` (kept
byte-identical to `omrpr_fin/docs/claim_boundary.md`)

**Review copies:** `omrpr_outputs_review/final_figures/fig0{1..5}_*.pdf`,
`omrpr_outputs_review/FINALIZATION_PLAN.md` (checklist updated)

## 5. Verification performed

- `verify_option_b.py`-style tolerance check: regenerated r/RMSE/MAE/ρ all within ±0.03 of
  `claim_boundary.md` targets (ratio has a known, explained near-floor residual).
- Fig. 3 stats recomputed directly from `option_b_verified_table.csv`: r=0.9598,
  ρ=0.9439, torsion r=0.9676, ratio=1.2607 — matches `claim_boundary.md` to 4 decimal
  places.
- `latexmk -pdf -halt-on-error` on the full manuscript: clean compile, 28 pages, after
  every substantive edit in this session.
- Forbidden-phrase gate (`step12_figures_tables.py`'s `check_forbidden_phrases`) and the
  same gate in `gen_fig03_ldv_scatter.py`: both PASS.
- Cross-checked figure checksums between `omrpr_manuscript/manuscript/figures/` and
  `omrpr_outputs_review/final_figures/`: identical.

## 6. Open items for next session

- `results/step09/noise_floor/noise_floor_summary.json` was **not regenerated** this
  session (Section A needs the `rosbags` package, not installed in this environment, and
  a system-wide pip install was avoided as out of scope). Its numbers were already
  consistent with the corrected noise floor before this session, so nothing is currently
  wrong, but a future session with `rosbags` available should rerun Section A once for a
  clean, fully-current artifact.
- `omrpr_fin/docs/RESULTS_LOG.md`'s Step 00-08 historical entries (and several other docs
  under `omrpr_fin/docs/` and `omrpr_manuscript/docs/`) still reference retracted B0-era
  numbers (r=0.845, "Tunnel B" naming, etc.) as historical record — intentionally left
  untouched per those files' own "historical record, not rewritten in place" convention,
  but worth being aware of if searching the repo for current numbers.
- `FINALIZATION_PLAN.md` Phase 4 Steps 3–4 (Opus/ChatGPT adversarial critique of
  Discussion) are still open; a Sonnet-run equivalent of Step 3 was delivered earlier in
  this session (structural critique of Discussion/Conclusion) but not yet saved to
  `reviewer_risk_reports/discussion_critique_log.md` or acted on.
- Phases 1 (literature comparison table), 5 (diagrams), 6 (adversarial review), 7 (Fable
  pass), 8 (submission package) are unstarted, per `FINALIZATION_PLAN.md`.
