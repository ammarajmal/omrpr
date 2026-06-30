# OMRPR Paper 2 — Critical Review
**Reviewer role:** Adversarial pre-submission audit  
**Date:** 2026-06-10  
**Scope:** Coherency, consistency, claim accuracy across all merged sections

---

## SEVERITY KEY
- 🔴 **CRITICAL** — Will cause rejection or retraction. Must fix before submission.
- 🟠 **HIGH** — Reviewer will flag. Must fix or formally justify.
- 🟡 **MEDIUM** — Weakens credibility. Should fix.
- 🟢 **LOW** — Cosmetic / minor. Fix if time allows.

---

## ISSUE 1 🔴 CRITICAL — LDV Geometry Contradiction in Torsion Sections

**Location:** Section 2.3 vs Section 2.5 (original METHODS_RESULTS_DRAFT.md)

**What was found:** Section 2.3 correctly stated the document-confirmed Paper 2 LDV geometry: d_side = 130 mm, d_b = 200 mm, d_p = 1.538 (Tunnel B, from BRID2D1.m). Section 2.5 in the same file stated: "d_p = 2.0 (= d_b / d_side = 200 mm / 100 mm)" — which is the Tunnel A geometry (wrong). Section 4.4 also referenced "d_side = 100 mm, d_p = 2.0" for the torsion proxy comparison.

**RESOLVED (2026-06-10):** dp=1.538 was confirmed used throughout. Tunnel B geometry (dside=130mm, dp=1.538) applied correctly in BRID2D1.m. Reported numbers verified against reference_comparisons_common60 report. No recomputation needed.

**Action taken in merge:** Sections 2.5 and 4.4 were corrected to d_side = 130 mm, d_p = 1.538 throughout the merged draft.

**Status: CLOSED.** dp=1.538 confirmed. Numbers (Pearson 0.968, ratio 0.785) are correct as reported.

---

## ISSUE 2 🔴 CRITICAL — Condition Count Inconsistency (Abstract vs Results vs Conclusion)

**Locations:** Abstract, Section 4.3, Section 5.1, Section 6 Conclusion

**What was found:**

| Location | Stated count | Conditions referred to |
|---|---|---|
| Abstract (original) | "20 stable-regime conditions" | Ambiguous — could include 60 RPM |
| Section 4.3 (METHODS_RESULTS) | "19 stable RPM conditions" | Unclear — 320 RPM status ambiguous |
| Section 5.1 (Discussion) | "20 stable-regime conditions" | Different from 4.3's "19" |
| Table 2 | 18 rows | 20–300 RPM excl. 60 |

**Correct count:** 21 total conditions (e0–e20). Minus e0 (baseline) = 20 dynamic. Minus 60 RPM (excluded) and 320 RPM (reported separately) = **18 comparison conditions** in the LDV analysis.

**Action taken in merge:**
- Abstract updated: "20 dynamic test conditions...with e20_320rpm reported separately" (counts correct, doesn't over-claim 20 as all stable)
- Section 4.3 header corrected to "18 stable RPM conditions (60 RPM excluded; 320 RPM reported separately)"
- Section 5.1 corrected to "18 stable-regime wind-tunnel conditions"
- Section 6 Conclusion corrected to "18 stable-regime conditions"

**Remaining action:** Re-verify that the Pearson 0.959 aggregate is indeed computed over exactly 18 conditions. If it includes or excludes different conditions, update accordingly.

---

## ISSUE 3 🟠 HIGH — Natural Frequency Inconsistency (f_h = 1.430 vs 1.436 Hz)

**Locations:** Section 2.1 states f_h = 1.430 Hz; Section 4.5 (V_r calculation) uses 1.436 Hz in the formula; Section 4.7 (original) stated "f_h = 1.436 Hz, f_α = 3.108 Hz"

**What is correct:** Memory and claim_boundary both confirm f_h = 1.430 Hz, f_α = 3.103 Hz (6 independent sources). Section 2.1 is correct.

**Action taken in merge:**
- Section 4.5 V_r calculation now uses f_h = 1.430 Hz: V_r = 0.882 / (1.430 × 0.40) = 1.54 ✓
- Section 4.7 reference frequencies corrected to f_h = 1.430 Hz, f_α = 3.103 Hz

**Remaining action:** Do a final text search for "1.436" and "3.108" anywhere in submission files — both are wrong and must be replaced.

---

## ISSUE 4 🟠 HIGH — Abstract Condition Count Phrasing Ambiguous

**Location:** Abstract

**Original phrasing:** "Experiments were conducted across 20 stable-regime conditions...with the high-wind unstable condition (e20_320rpm) reported separately."

**Problem:** This reads as 20 stable + 1 unstable = 21. But the Pearson 0.959 is over 18 conditions. A careful reader will ask: were 20 conditions or 18 conditions used for the correlation?

**Action taken in merge:** Revised to: "Experiments were conducted across 20 dynamic test conditions of a bridge section model...with the high-wind unstable condition (e20_320rpm) reported separately."

**Remaining action:** The abstract does not state the Pearson is over 18 conditions. The phrase "stable regime" in the Pearson sentence implicitly bounds it. This is borderline acceptable but consider adding: "(18 conditions, excluding the VIV onset boundary at 60 RPM)" to the correlation sentence for full transparency.

---

## ISSUE 5 🟠 HIGH — Section 4.7 Frequency Claim Requires the C_R2 Caveat

**Location:** Section 4.7

**Original problem (METHODS_RESULTS_DRAFT):** The text said "21/21 conditions within tolerance" without clearly distinguishing nearest-bin energy concentration from dominant-peak agreement. The flag C_R2 correctly identified this as a claim that would not survive review.

**Action taken in merge:** Section 4.7 now explicitly states "energy concentration" (not "dominant-peak agreement") and includes the caveat: "at low-amplitude near-noise-floor conditions the dominant peak may be noise-driven." The 21/21 claim is reframed as a weaker, accurate statement.

**Remaining action:** Verify this wording with Dr. Jongbin Won before submission. The 21/21 figure should be either (a) restricted to conditions where SNR justifies a dominant-peak interpretation, or (b) kept as "energy concentration" framing as written.

---

## ISSUE 6 🟡 MEDIUM — Torsion Proxy RMSE Not in Abstract

**Location:** Abstract reports bending RMSE (0.297 mm) and MAE (0.224 mm) but omits torsion proxy RMSE (0.501 mm) and MAE (0.338 mm).

**Assessment:** The abstract already notes the torsion proxy is not a validated torsion angle. Not reporting RMSE avoids a reviewer asking "RMSE of what, exactly?" and is arguably cleaner. However, for consistency and completeness, adding "MAE ≈ 0.338 mm" for the torsion proxy would be standard.

**Recommendation:** Low priority. Leave as-is unless journal requires balanced reporting.

---

## ISSUE 7 🟡 MEDIUM — "Document-Confirmed" Language Inconsistency

**Location:** Introduction Para 3 (Contribution 3), Section 2.5, Section 4.4, Section 5.4, claim_boundary.md

**Problem:** The claim_boundary.md still contains an entry saying "OPERATOR_CONFIRMED" for torsion geometry. The resolved flag C_R3 in the draft says this should be "document-confirmed." The merged manuscript correctly uses "document-confirmed" throughout, but claim_boundary.md is inconsistent with the manuscript.

**Action taken in merge:** Manuscript uses "document-confirmed" consistently.

**Remaining action:** Update claim_boundary.md to replace "OPERATOR_CONFIRMED" with "DOCUMENT_CONFIRMED" for the torsion geometry entry. This is an internal consistency fix, not submission-blocking.

---

## ISSUE 8 🟡 MEDIUM — Section 5.1 Discussion Does Not Reference Section 4.3 Table Numbers

**Location:** Section 5.1

**Problem:** The Discussion (5.1) discusses the 1.268× over-read in general terms but does not point the reader to Table 2 for the per-condition breakdown. This weakens the discussion's grounding in the results.

**Recommendation:** Add one sentence: "Per-condition ratios are provided in Table 2; the over-read is most pronounced in the 80–220 RPM range (ratios 1.30–2.21×) and approaches unity in the quiet-zone and high-speed regimes (100–120 RPM, 240–300 RPM)."

---

## ISSUE 9 🟡 MEDIUM — Section 2.4 Stage 5 "Statistics Extraction" is Vague

**Location:** Section 2.4, Stage 5

**Problem:** "For each condition, full-record RMS, peak, mean, and frequency-domain statistics were computed" — does not specify the window length, RMS definition (full record vs. subset), or how the "stable regime" subset was defined for aggregate statistics. Reviewers will ask.

**Recommendation:** Add: "Full-record statistics were computed over the complete 30-second recording window. The stable regime was defined as conditions with aligned Z agreement below 10 mm and bending RMS above the noise floor (0.017 mm); 18 conditions satisfied both criteria (20–300 RPM, excluding 60 RPM)."

---

## ISSUE 10 🟡 MEDIUM — 320 RPM Torsion Proxy Ratio Statement is Misleading

**Location:** Section 4.4

**Original text:** "camera torsion proxy RMS ≈ 17.1 mm vs. LDV torsion RMS ≈ 17.1 mm (ratio ≈ 1.00). This single-condition numerical equality should not be over-interpreted."

**Problem:** The parenthetical warning ("should not be over-interpreted") is correct but weak. A reviewer may still cite this as inconsistent with the 0.785× under-read in the stable regime and ask why the ratio is 1.00 at 320 RPM. No physical explanation is given.

**Recommendation:** Replace with: "At the flutter condition e20_320rpm, camera torsion proxy RMS ≈ 17.1 mm and LDV torsion RMS ≈ 17.1 mm (ratio ≈ 1.00). This apparent agreement at 320 RPM is not indicative of torsion proxy accuracy; at large flutter amplitudes, the dominant vertical displacement component dominates both signals and the relative contribution of the systematic geometry offset diminishes as a fraction of total amplitude."

---

## ISSUE 11 🟢 LOW — Missing Wind Speed for e0 (0 RPM) in Table 1

**Location:** Table 1, Baseline row

**Problem:** Wind speed listed as "0" but should explicitly state "0 (ambient)" to make clear this is zero-wind, not zero-rpm-with-residual-flow.

**Action:** Minor wording fix.

---

## ISSUE 12 🟢 LOW — Introduction Para 3 Says "21 conditions" but Conclusion Says "18 stable-regime conditions"

**Location:** Introduction 1.3 ("validated across 21 wind-tunnel test conditions") vs Conclusion ("18 stable-regime conditions")

**Assessment:** Not actually inconsistent — 21 is the total dataset size; 18 is the LDV comparison subset. But a reviewer reading quickly may flag this as a discrepancy.

**Recommendation:** In Intro Para 3, change to: "validated across 21 wind-tunnel test conditions (20 dynamic conditions plus zero-wind baseline; 18 stable-regime conditions used for LDV comparison)." Or simply ensure Section 4.3 makes the 18-vs-21 distinction clear, which it now does.

---

## COHERENCY ASSESSMENT

**Abstract ↔ Results:** After merge corrections, the abstract claim numbers (Pearson 0.959, RMSE 0.297, MAE 0.224, noise floor 0.017/0.033, camera agreement 1.757 ± 0.596) match the Results section exactly. ✓

**Introduction contributions ↔ Results sections:** All four contributions (C1 synchronization pipeline, C2 inter-camera uncertainty, C3 torsion proxy, C4 reproducible pipeline) are demonstrated in corresponding results sections (4.2, 4.2, 4.4, and pipeline description). ✓

**Methods ↔ Results:** Section 2.4 pipeline stages correspond directly to results reported in 4.1–4.4. ✓

**Results ↔ Discussion:** Discussion 5.1–5.4 maps directly onto results 4.3–4.5. Non-claims in 5.5 are grounded in limitations stated in Methods (2.3, 2.4). ✓

**Discussion ↔ Conclusion:** All four Conclusion paragraphs are supported by Discussion content. Future work (simultaneous acquisition, higher fps, geometry survey) follows logically from identified limitations. ✓

**Claim boundary compliance:** No claim in any section exceeds the B0 validated claim boundary. Non-claims (no same-run waveform, no LDV-equivalent accuracy, no hardware sync, torsion is proxy) appear explicitly in Abstract, Methods (2.3, 2.5), Results (4.4), Discussion (5.5), and are implicit in Conclusion framing. ✓

---

## SUMMARY OF REQUIRED ACTIONS (priority order)

| # | Priority | Action | Section |
|---|---|---|---|
| 1 | ✅ RESOLVED | Torsion B0 numbers verified (0.968, 0.785) were computed with dp=1.538 not dp=2.0 | Data integrity |
| 2 | 🔴 CRITICAL | Confirm Pearson 0.959 is over exactly 18 conditions; update if different | Abstract + 4.3 |
| 3 | 🟠 HIGH | Search+replace all instances of 1.436 Hz and 3.108 Hz → 1.430 and 3.103 | 4.5, 4.7 |
| 4 | 🟠 HIGH | Verify Table 2 values against B0 cross-camera package (C_R1) | 4.3 |
| 5 | 🟠 HIGH | Confirm Sony/AverMedia naming with supervisor (C_F2) | 2.2 |
| 6 | 🟡 MEDIUM | Add per-condition ratio context sentence to Discussion 5.1 (pointing to Table 2) | 5.1 |
| 7 | 🟡 MEDIUM | Clarify Stage 5 statistics window / stable-regime definition | 2.4 |
| 8 | 🟡 MEDIUM | Replace 320 RPM torsion ratio "should not be over-interpreted" with physical explanation | 4.4 |
| 9 | 🟡 MEDIUM | Update claim_boundary.md: OPERATOR_CONFIRMED → DOCUMENT_CONFIRMED | memory/ |
| 10 | 🟡 MEDIUM | Consider adding torsion MAE to abstract for completeness | Abstract |
| 11 | 🟢 LOW | Clarify 21 total vs 18 comparison conditions in Introduction 1.3 | 1.3 |
| 12 | 🟢 LOW | Add "ambient" qualifier to Table 1 baseline wind speed | Table 1 |

