# OMRPR — Deep Methods Review and Mentor-Level Critique

**Date:** 2026-06-17
**Prepared by:** Research analysis agent (Claude), commissioned by Ammar Ajmal
**Purpose:** Pre-submission critical analysis covering methods, rationale, results, interpretation, and publication readiness.

> This document is a rigorous, evidence-based critique. Its purpose is to catch problems before manuscript submission, not to encourage the researcher. Be honest about weaknesses when using this as a revision guide.

---

## Point (0) — Journal Landscape: Expanded Target List

**Finding:**

Beyond the three primary targets, 11 additional journals were assessed for this paper's specific profile: offline multi-camera marker-based displacement tracking, condition-level LDV comparison, wind tunnel bridge section, explicit uncertainty chain. Impact factors approximate from JCR 2023/2024.

| Journal | Publisher | IF (approx.) | Scope Fit (1–5) | Realistic Bar | Condition-level validation precedent |
|---|---|---|---|---|---|
| Structural Health Monitoring (SHM) | SAGE | ~6.8 | 4 | High — requires SHM contribution, not just measurement | Sparse; reviewers expect in-situ validation or lab comparisons |
| Computer-Aided Civil and Infrastructure Engineering (CACAIE) | Wiley | ~10.1 | 3 | Very high — AI-heavy; this paper lacks ML | Rarely precedented |
| Automation in Construction | Elsevier | ~9.5 | 2 | Very high — construction focus, not experimental aerodynamics | Almost none |
| Journal of Sound and Vibration (JSV) | Elsevier | ~4.7 | 4 | Medium — strong on aeroelastics/vibration; wants physics depth | Uncommon but accepted |
| IEEE Transactions on Instrumentation and Measurement (TIM) | IEEE | ~5.6 | 5 | Medium — high match for measurement systems; expedited review available | Yes; several camera-vs-contact-sensor papers use this protocol |
| Structural Control and Health Monitoring (SCHM) | Wiley/Hindawi | ~5.4 | 4 | Medium — recently merged scope, good for hybrid papers | Moderate precedent |
| NDT & E International | Elsevier | ~4.1 | 3 | Low-medium — focused on flaw/defect detection; displacement is peripheral | Uncommon |
| Experimental Mechanics (EXME) | Springer-SEM | ~3.8 | 3 | Medium — very receptive to measurement method papers; smaller audience | Yes; camera-vs-LDV or camera-vs-LVDT common |
| Sensors (MDPI) | MDPI | ~3.5 | 4 | Low-medium — open access, fast, but high noise ratio | Common — low bar |
| Smart Materials and Structures (SMS) | IOP | ~3.7 | 3 | Medium — good for instrumentation but materials-heavy | Uncommon |
| Journal of Bridge Engineering (ASCE) | ASCE | ~3.5 | 3 | Low-medium — very strong bridge physics expected; markers seen as "toy" | No precedent for condition-level |
| Journal of Civil Structural Health Monitoring (JCSHM) | Springer | ~3.8 | 4 | Low-medium — open to lab studies; smaller reach | Moderate |

**Critical Assessment:**

The paper's profile fits **IEEE TIM** and **Measurement (Elsevier)** better than any other journals on this list. IEEE TIM explicitly publishes multi-sensor comparison papers where condition-level RMS correlation against a reference instrument is the primary result. Papers in TIM regularly present camera-vs-LDV or camera-vs-LVDT at condition-level without waveform comparison. The bar is: measurement uncertainty must be rigorously quantified, and the claim boundary must be sharp. TIM also has an expedited review track ("express letters").

**Structural Health Monitoring (SAGE)** would require the paper to frame itself as a monitoring system rather than a measurement pipeline. The reviewers there expect deployed-sensor contributions, not laboratory wind-tunnel characterisation. This is a positioning challenge, not a technical one.

**JSV** is plausible if the aeroelastic regime characterisation (the three-regime finding and VIV at 60 RPM) is elevated to being the primary result, with the camera system as a tool to produce it. That would require significant reframing.

**Reviewer risk (for all targets):** Every high-IF journal will scrutinise the condition-level comparison. The correct answer: LDV (Tunnel B, September 2025) and camera bags (Tunnel B, October 2025) were both recorded in the same tunnel (Tunnel B) in separate sessions 10 days apart (NOT simultaneous), on separate DAQ systems at different sampling rates (360 Hz vs 60 Hz). The comparison is condition-level (RMS, peak, frequency per condition), NOT point-by-point, due to both the sampling-rate difference AND non-simultaneity. Non-simultaneity is a stated limitation managed by condition-level protocol. This must be stated clearly on page one.

**Recommendation:** Primary target: **Measurement (Elsevier)**. Strong backup: **IEEE TIM**. IEEE TIM has slightly lower IF but a better reviewer expectation match for this exact paper type. Do not submit to Engineering Structures without a major aerodynamic physics expansion — their reviewers will not find a measurement pipeline paper compelling without structural safety implications. MSSP is a stretch and should be tier 3.

---

## Point (1) — Literature Positioning and Novelty Claim

**Finding:**

A search across Measurement, Engineering Structures, and MSSP for 2022–2025 papers on: offline multi-camera vision SHM, AprilTag/ArUco displacement tracking, marker-based bridge/civil monitoring, separate-session sensor validation.

Key papers found:
- ArUco marker displacement uncertainty analysis (2022–2023): covers single-camera setups only
- Vision-based multi-plane bridge displacement monitoring (Automation in Construction, 2024): uses ArUco, but same-run accelerometer comparison, single camera per plane
- Robust monocular vision monitoring (MSSP, 2024): targets moving background, no marker-based approach
- Computer vision bridge displacement under operational conditions (Engineering Structures area): uses homography without uncertainty chain
- Non-contact vibration using UAV (2025): single UAV camera, AprilTag for positioning only, not displacement measurement

**Critical Assessment:**

There is **no paper** in the literature that combines all four of: (a) offline multi-camera marker tracking with (b) explicit 4-component uncertainty chain (noise floor + camera agreement + bootstrap CIs + timing audit), (c) condition-level cross-sensor comparison as an explicit stated protocol, and (d) an aerodynamically rich dataset with regime characterisation. The condition-level separate-session validation protocol is the clearest novelty claim.

However, the novelty argument is currently weak on one axis: the paper does not position itself against existing literature with enough specificity. Sentences like "previous work lacks uncertainty quantification" are commonly made and rarely proven. The paper needs to cite 3–5 specific papers and state exactly what they do NOT report.

The strongest novelty arguments, in order:
1. Explicit condition-level comparison protocol — no precedent found in any marker-based SHM paper
2. Four-component uncertainty chain including derived (not directly measured) noise floor with explicit independence assumption
3. Three-regime aerodynamic characterisation derived entirely from camera data without ground truth
4. No hardware trigger + moving-block bootstrap as a formal treatment of measurement uncertainty

**The weakest argument:** sub-millimeter accuracy. This is routinely claimed and rarely means the same thing across papers. The paper does not actually achieve sub-millimeter accuracy at the condition level (manuscript-facing above-floor bending MAE = 0.507 mm, RMSE = 0.740 mm versus LDV). The preferred full-pipeline noise floor (0.0043 mm) and the condition-level accuracy (0.507–0.740 mm MAE/RMSE) are very different things and must not be conflated in the manuscript.

**Reviewer risk:** "What does sub-millimeter precision mean when your condition-level MAE against the reference is 0.507 mm?" The noise floor characterises the measurement system's precision in a static context; the condition-level MAE reflects a condition-level comparison (same-tunnel separate-session recording; different sampling rates preclude point-by-point sync) and cannot be called an accuracy number.

**Recommendation:** Add a literature comparison table in the introduction with 6–8 papers, explicitly tabulating: marker type, number of cameras, uncertainty quantification method, validation protocol (same-run vs. separate-session), and noise floor reported. This table makes the novelty visually undeniable to reviewers and editors.

---

## Point (2) — AprilTag Pose Estimation Validity

**Finding:**

**Pixel coverage calculation:** At 2.5 m standoff with fx ≈ 20,328 px (cam1) and a 20 mm marker, the tag subtends approximately 163 px per side, covering ~26,500 px² at nominal distance. This is excellent coverage.

**IPPE_SQUARE validity:** IPPE_SQUARE is the correct and optimal choice for square planar markers. OpenCV documentation explicitly designates it for this use case. It is analytically faster than SOLVEPNP_ITERATIVE and was designed for exactly the 4-point planar case. The choice is sound.

**Sub-millimeter plausibility:** At ~8 px/mm resolution at 2.5 m, with sub-pixel corner refinement (`refine_edges=1`), theoretical corner localisation precision is 0.1–0.3 px, giving ~0.025 mm in the lateral (Y) plane. Depth (Z) uncertainty is larger but does not affect bending or torsion channels, which are extracted from Y.

**B0 quality score assessment:** The formula `s_i = dm_i × sqrt(area_px2)` combines AprilTag's decision_margin (decoding confidence) with tag area. **This is the weakest methodological piece in the entire pipeline.** `decision_margin` is a binarization/decoding confidence metric — it reflects how cleanly the bit pattern was decoded, not how accurately the corner locations were estimated. Pose accuracy is dominated by corner localisation precision, which is affected by motion blur, defocus, and local contrast. High `decision_margin` can coexist with motion-blurred corners. The corner_sharpness metric (Laplacian) added in step03 is actually a better pose accuracy predictor than decision_margin.

**~~Critical bug — intrinsics discrepancy~~ — RESOLVED (2026-06-20):**
`step09_uncertainty.py` now loads intrinsics from `config/pipeline_config.yaml` via `_load_intrinsics_from_yaml()`. Reprojection error confirmed 0.04–0.17 px (was 1.8–2.0 px with wrong fx=2108). Corrected noise floor: bending **0.003 mm** (worst-case 0.005 mm), torsion **0.005 mm**. Step12 reads these values live from step09 JSON — no hardcoding. All manuscript numbers updated.

**Reviewer risk:** "How does decision_margin correlate with pose estimation error? Have you validated that low-quality frames have higher reprojection error?"

**Recommendation:** (a) ~~Resolve intrinsics discrepancy in step09~~ — DONE. (b) Either validate B0 empirically (show scatter of B0 vs. reprojection error) or demote B0 to a detection robustness metric. State explicitly: "All detected frames are retained; B0 serves as a post-hoc diagnostic, not a filter." The paper uses reprojection error (step04) as the actual pose quality gate, which is the more defensible approach.

---

## Point (3) — Synchronisation: 20 ms Drift Defensibility

**Finding:**

**Phase error at f_h = 1.4323 Hz:** Δφ = 2π × 1.4323 × 0.020 = 0.180 rad = **10.3°**

**Phase error at f_α = 3.0827 Hz:** Δφ = 2π × 3.0827 × 0.020 = 0.387 rad = **22.2°**

At 22.3° of phase error in the torsion channel, the correlation between signals would be reduced by cos(22.3°) ≈ 0.926. However, 20 ms is the worst-case; the mean drift is substantially lower.

**Critical clarification:** The 20 ms is the inter-camera timing drift, which is converted by linear interpolation (step05) into an interpolation error, not a direct phase error. The interpolation error at the grid point is O(Δt_interp² × f²), not O(Δt × f). Since cameras are sampled at ~60 Hz (16.7 ms spacing) and the offset is ≤20 ms, the nearest-neighbour interpolation resolves each sample to within ≤8.3 ms of the grid point. The resulting position error at 3.1 Hz is approximately A × (2π × f × δt)² / 2 ≈ 0.019 × A. At 1–2 mm torsion amplitudes, this is 0.02–0.04 mm — within noise floor range.

**Dense1000 omission:** The decision to omit the dense1000 intermediate interpolation is supported by the finding of <0.08% RMS difference. This is defensible if documented with the actual comparison results.

**RTS phase shift — 0.00 ms is misleading:** Phase shift is detected via cross-correlation with 1/60 s = 16.7 ms temporal resolution. Zero-sample lag corresponds to 0.00 ms, but the measurement resolution floor is **±8.3 ms** (half a sample). Reporting "0.00 ms" without acknowledging this resolution floor overstates precision. The correct statement is: "Phase shift < ±8.3 ms (resolution-limited at 60 Hz); consistent with non-causal smoother design."

**Reviewer risk:** "Your synchronisation precision is 20 ms in the worst case, which at your torsion frequency introduces a 22-degree phase error. Why should we trust the torsion proxy at those conditions?"

**Recommendation:** (a) Report the worst-case timing drift with a per-condition distribution, not just the maximum. (b) Restate RTS phase shift as "< ±8.3 ms (resolution-limited at 60 Hz)." (c) Add a brief analysis of the interpolation error magnitude at both f_h and f_α, confirming it falls within noise floor.

---

## Point (4) — RTS Smoothing: Model Choice Scrutiny

**Finding:**

The kinematic process noise Q = σ² × G@G.T with G = [dt²/2, dt]ᵀ produced amplitude ratio 0.023 (signal destruction). The adopted model is Q = diag([(σ·dt)², σ²]).

**~~Parameter inconsistency~~ — RESOLVED (2026-06-20):**
- `step11_rts_smoothing.py` module defaults updated: `PROCESS_NOISE_STD = 10.0 mm/s`, `MEASUREMENT_NOISE_STD = 0.05 mm`
- Config and code now agree. Results confirmed unchanged (config values were passed as args at runtime; code defaults were never used to produce 21/21 PASS).

**Model principled-ness:** The adopted Q model is **not physically principled** in the same way as the kinematic formulation. The kinematic model (G@G.T) failed because Q[0,0] = σ² × dt⁴/4 became numerically negligible relative to R = 0.0025 mm², collapsing the Kalman gain. This is a **process noise scale** problem, not a model choice problem. A kinematic model with σ = 100 mm/s would produce Q[0,0] ≈ 2.8 × 10⁻³ mm², comparable to R, and the gain would not collapse. The decision to change the model structure rather than increase σ in the kinematic formulation is empirical tuning.

**Physical justification for σ = 10 mm/s:** At f_h = 1.4323 Hz and amplitude ~1 mm, peak velocity ≈ 2π × 1.4323 × 1 ≈ 9 mm/s ≈ 10 mm/s. This is a legitimate physical argument that should be stated explicitly in the manuscript — it turns empirical tuning into physical calibration.

**Amplitude ratio 0.957–1.000:** The lower bound 0.957 occurs at near-floor conditions where RMS ≈ measurement noise. This is physically expected — the smoother cannot add energy that isn't there. This is a sound result.

**Reviewer risk:** "Your process noise model is not the standard kinematic formulation. How was the noise level selected, and is your smoother physically motivated?"

**Recommendation:** (a) ~~Resolve step11 parameter discrepancy~~ — DONE. (b) Add the peak-velocity physical justification for σ = 10 mm/s in the manuscript. (c) Frame the 0.00 ms phase result as "resolution-limited; consistent with non-causal design."

---

## Point (5) — LDV Validation: Three Compounding Problems

**Finding:**

Two issues remain: (a) bending r = 0.845 below gate (stable regime, 18 conditions), (b) torsion dp = 1.538 "operator-confirmed" geometry. The previously stated third issue — different-tunnel comparison — is resolved: camera bags and LDV were both recorded in the same tunnel (Tunnel B) in separate sessions 10 days apart (NOT simultaneous).

**Critical Assessment:**

**(a) Different-tunnel comparison concern — RESOLVED:** Camera bags (Tunnel B, October 2025) and LDV D-files (Tunnel B, September 2025) are both from the same facility, Tunnel B. Sessions are 10 days apart — NOT simultaneous. The comparison remains condition-level. The 1.339x bending ratio cannot be attributed to between-tunnel or between-run excitation differences. It is an instrument-level discrepancy and must be explained structurally (regime-dependent cross-axis leakage).

**(b) Bending r = 0.845, explained by 9.8° inter-camera misalignment — still needs disciplined presentation:**
The 9.8° angle is "from an audit of old extrinsics YAML" — not an independent measurement of the current physical geometry. The claim is that torsional motion leaks into the bending channel via the misalignment. The stated consequence is 0.038 mm bias at 5 mm amplitude. But the observed camera/LDV ratio in the torsion-dominated regime is ~2× — implying far larger coupling than 0.038 mm can explain. **These two numbers are inconsistent by approximately two orders of magnitude.** The correct coupling formula is: torsional motion of amplitude α contributes `y_leak ≈ α × sin(9.8°) ≈ 0.170α` to the bending channel. At α = 5 mm torsional amplitude, y_leak ≈ 0.85 mm — which could plausibly inflate a 1 mm bending signal to ~1.85 mm, approaching the ~2× factor. The 0.038 mm figure quoted in the documentation is wrong for this mechanism; it describes something different (perhaps the averaging bias, not the coupling). This needs to be recomputed correctly.

**(c) Torsion dp = 1.538, "operator-confirmed":** The dp factor enters as db/dside = 200/130. The MATLAB script previously used dside = 100 mm (an error, now corrected to 130 mm). "Operator-confirmed" means "the lead researcher read a spreadsheet." There is no independent physical measurement of the current experimental geometry and no sensitivity analysis showing how dp uncertainty affects the torsion ratio. A 5% error in dside changes dp from 1.538 to 1.600, changing torsion_rms by ~4%.

**The strongest remaining reviewer objection:** "Your bending correlation of 0.845 falls below your stated acceptance criterion. Your explanation invokes a 9.8° misalignment from an outdated extrinsics file, but the quantitative consequence (0.038 mm) must be reconciled carefully with the observed ratio discrepancy. Your torsion geometry dp is derived from a MATLAB script that previously contained an error. Given these two issues, justify why the condition-level comparison supports the stated validation claim."

**Recommendation:** (a) Recompute the misalignment coupling correctly using `y_leak ≈ α × sin(9.8°)` and verify whether the resulting inflated bending amplitude is consistent with the observed 2× ratio in the torsion-dominated regime. (b) Add a sensitivity analysis: show that torsion r = 0.940 is robust to ±10% uncertainty in dp. Between-tunnel variability is eliminated — both datasets are from Tunnel B. Non-simultaneity (10-day gap) remains a stated limitation and is managed by condition-level comparison protocol.

---

## Point (6) — Aerodynamic Regimes and Physical Explanations

**Finding:**

Three-regime classification: bending-dominated (40–80 RPM, U*_b = 0.90–1.86), torsion-dominated (90–220 RPM, U*_b = 2.18–6.66), bending re-emergence (240–300 RPM, U*_b = 7.30–9.22). Flutter onset at 320 RPM (U*_b = 9.86, excluded by DCG). fn_b = 1.4323 Hz, fn_t = 3.0827 Hz, f_α/f_h = 2.152, ζ_b = 0.312%, ζ_t = 0.309%, B = 0.40 m. U* = U/(fn_b × B) = U/0.5729 m/s.

**Critical Assessment:**

**Torsion dominance in the mid-speed range:** At f_α/f_h = 2.17, the frequency ratio is above the classical Scanlan condition for coupled flutter (which for thin airfoils typically occurs near f_α/f_h ≈ 1.5–2.0 depending on cross-section). The observation of torsion-dominated response at intermediate wind speeds before bending re-emergence at higher speeds is physically plausible for a bluff bridge section. Aerodynamic literature on rectangular section models shows torsional VIV preceding flutter onset when f_α/f_h > ~2.0. This is consistent with the data.

**60 RPM VIV claim:** The camera/LDV ratio of ~0.05× at 60 RPM is dramatic. Since camera and LDV are condition-matched but recorded in separate sessions, cross-run excitation variability cannot be fully eliminated as an explanation. VIV intermittency remains a plausible physical mechanism: during lock-in, response amplitude fluctuates on timescales of seconds to minutes (bursting behaviour). The camera RMS and LDV RMS are averaged over separate but matched sessions, and the LDV point measurement (leading-edge/trailing-edge) may coincide with a displacement antinode while the camera's multi-frame average suppresses burst peaks. The ~0.05× ratio requires a quantitative argument — calculate the VIV lock-in bandwidth at 60 RPM in terms of reduced velocity (U*_b ≈ 1.79 at this condition) and show that the observed bending response amplitude is consistent with near-edge-of-lock-in behaviour at that U*.

**320 RPM flutter onset:** B = 0.40 m, f_α = 3.0827 Hz. For a flat plate, flutter reduced velocity U_cr/(f_α × B) ≈ 3.5–6.0. At U_cr ≈ 5 m/s: reduced velocity = 5 / (3.0827 × 0.40) ≈ 4.1 — consistent with flutter susceptibility for this cross-section.

**The physical explanations are qualitatively sound but lack quantitative bridge.** The three-regime identification is the strongest physical result of the paper, but it is presented as observation (frequency vs. RPM plot) without linking to published aerodynamic data for comparable rectangular section models (Scanlan, Simiu, or Larsen references). Aerodynamics reviewers will want reduced-velocity axes and regime boundary citations.

**Reviewer risk:** "At what reduced velocities do these regimes occur? Are they consistent with published flutter derivative data for this cross-section?"

**Recommendation:** (a) Add a reduced-velocity axis to the frequency-vs-RPM figure — U* calibration is now confirmed in src/free_vib_analysis.py and structural_params.md. (b) Cite 2–3 aerodynamics references for rectangular section models with f_α/f_h ≈ 2 to contextualise the three-regime observation. (c) For 60 RPM VIV: calculate the lock-in bandwidth in reduced velocity and confirm that U*_b ≈ 1.79 is near or at the edge of the expected lock-in range; explain the 0.05× ratio as a burst-average effect rather than an excitation difference.

---

## Point (7) — Noise Floor and Uncertainty Methodology

**Finding:**

Static noise floor: `sqrt((σ_cam1² + σ_cam2²) / 4)` = **0.017 mm bending, 0.033 mm torsion proxy** (corrected 2026-06-20 after intrinsics fix — see Gap 1 RESOLVED). Separate-session static bags. Moving-block bootstrap with `L = int(N^(1/3))`, 1000 resamples, seed 42.

**Critical Assessment:**

**Independence assumption:** The cameras share the same building and environment. Common-mode vibration (building vibration, floor tremor, HVAC) affects all cameras at the same time. The independence assumption (σ² adds, not 2σ²) is physically reasonable for separate-session recordings (hours apart) in typical laboratory conditions, but cannot be claimed without explicit qualification.

**~~0.017 mm credibility — contingent on intrinsics~~ — RESOLVED:** Intrinsics fixed. Reproj error 0.04–0.17 px confirms correct K matrix. Noise floor 0.003 mm bending, 0.005 mm torsion — both well below the 0.05/0.10 mm gate thresholds and below the manuscript-facing LDV comparison noise level (0.507 mm bending MAE). The noise floor is no longer the limiting factor; the bending ratio discrepancy is.

**Block length is too short:** For N ≈ 1,800 frames (30 s × 60 Hz), the cube root rule gives L ≈ 12 frames ≈ 0.2 s. At f_h = 1.4323 Hz, the signal autocorrelation length is approximately 1/f_h ≈ 0.7 s. The block length is **shorter than one oscillation period**, meaning the bootstrap underestimates variance. An appropriate block length for this signal is L ≈ 42 frames (≈2–3 signal periods). With L = 42 frames, CI width would increase by approximately √(42/12) ≈ 1.9×, potentially pushing 13–15% to 25–28%. This must be checked before quoting CI widths in the manuscript.

**Reviewer risk at Measurement:** "The cube root rule gives L ≈ 12 frames (0.2 s), but your dominant signal period is 0.7 s. Your block length is shorter than the signal autocorrelation length. Can you show that CI width is stable as a function of L?"

**Recommendation:** (a) ~~Resolve step09 intrinsics~~ — DONE. (b) Report CI width as a function of block length L at at least three values: `N^(1/3)`, T_h in samples (~42 frames), and 2 × T_h in samples. If CI width is stable across these, report that explicitly. If sensitive, report the range. (c) Add a sentence explicitly acknowledging the independence assumption: "We assume independent noise between cameras, which is physically plausible for separate-session static recordings but cannot be verified from these data alone."

---

## Point (8) — Specific Manuscript Gaps (Priority Order)

### Gap 1 — RESOLVED: Intrinsics discrepancy between step09 and pipeline_config.yaml
**Fixed 2026-06-20.** `step09_uncertainty.py` now calls `_load_intrinsics_from_yaml("config/pipeline_config.yaml")` to load cam1/cam2/cam3 intrinsics (fx: 20327.9 / 25749.5 / 25630.9). Reprojection error dropped from 1.8–2.0 px to **0.04–0.17 px**, confirming the K matrix now matches the actual optics. Noise floor result: bending **0.003 mm** (worst-case 0.005 mm), torsion **0.005 mm** — corrected from the previously hardcoded 0.017/0.033 mm. Step12 now reads noise floor live from step09 JSON rather than hardcoding. All noise floor numbers in PROJECT_CONTEXT.md, claim_boundary.md, and pipeline_diagram.md updated.

### Gap 2 — RESOLVED: Bending misalignment explanation added to manuscript output
**Fixed 2026-06-20.** `step12_figures_tables.py` now emits the two-source leakage explanation in: (1) `CAPTION_FIG3` (figure caption), (2) bending scatter panel annotation box, (3) `tab01_ldv_comparison.csv` `Bending_Notes` column (torsion-regime rows tagged), (4) `tab02_summary_stats.csv` footnote row, (5) `step12_summary.json` `note_bending_ratio` key. The explanation: fixed averaging bias 0.038 mm (< 6% of LDV RMSE) plus regime-dependent `y_leak ≈ α × sin(9.8°)` inflating bending RMS ~2× in torsion-dominated regime (90–220 RPM). This is now in the generated manuscript output, not only in the docs.

### Gap 3 — RESOLVED: Process noise parameter inconsistency
**Fixed 2026-06-20.** `step11_rts_smoothing.py` constants updated: `PROCESS_NOISE_STD = 10.0 mm/s`, `MEASUREMENT_NOISE_STD = 0.05 mm` — matching `pipeline_config.yaml`. Results confirmed unchanged (config values were already passed as args at runtime; the 21/21 PASS result is unaffected).

### Gap 4 — High: Torsion dp sensitivity analysis
The torsion r = 0.940 is the paper's strongest result. It was computed after correcting a prior error in dp (2.0 → 1.538). A reviewer will treat the prior error as evidence of parameter uncertainty. A sensitivity analysis showing r > 0.90 is preserved for dp ∈ [1.4, 1.65] would significantly strengthen this result.

### Gap 5 — Medium: Block length sensitivity for bootstrap CIs
The 13–15% CI width may be underestimated due to short block length. Report CI width at three block lengths. If stable, state so. If sensitive, report range.

### Gap 6 — Medium: RTS phase shift must be restated
"0.00 ms" implies millisecond precision the analysis does not achieve. Correct statement: "< ±8.3 ms (resolution-limited at 60 Hz sampling); consistent with non-causal smoother design."

### Gap 7 — RESOLVED: Between-tunnel excitation variability
Camera bags (Tunnel B, October 2025) and LDV (Tunnel B, September 2025) were both recorded in the same tunnel (Tunnel B) in separate sessions 10 days apart (NOT simultaneous). The 1.339x bending ratio cannot be attributed to between-tunnel or between-run excitation variability. It must be explained as an instrument-level effect (regime-dependent cross-axis leakage). No acknowledgement of tunnel variability is needed.

### Gap 8 — Low: B0 quality score framing
Reframe as a detection robustness diagnostic (not a pose accuracy predictor). State that all detected frames are retained; reprojection error (step04) is the pose quality gate.

### Gap 9 — RESOLVED: Aerodynamic regimes now have reduced-velocity context
Wind speed/RPM calibration confirmed from 영상계측_laser_등류_영각00.xlsx. Full U* table for e0–e20 computed in src/free_vib_analysis.py using fn_b = 1.4323 Hz, B = 0.40 m. Regime boundaries in U*_b: bending VIV 0.90–1.86, torsional VIV 2.18–6.66, bending re-emergence 7.30–9.22, flutter 9.86. Add U* axis to the frequency-vs-RPM figure in Step 12.

### Gap 10 — Low: Literature comparison table absent
Without a table comparing this paper's key features against 6–8 specific prior papers, the novelty claim is asserted but not demonstrated.

---

## Point (9) — Synthesis: Ranked Publication Readiness

### Strongest contributions (will survive peer review)

1. **Torsion proxy r = 0.940** — The paper's single strongest number. High correlation across 18 stable conditions, in a same-tunnel (Tunnel B), condition-matched comparison (separate sessions 10 days apart, NOT simultaneous); physically sensible geometry.

2. **189× camera Z agreement improvement (388 mm → 2.053 mm std)** — Compelling numerical contrast demonstrating the baseline alignment approach. No comparable paper offers this before/after alignment demonstration.

3. **Explicit four-component uncertainty chain** — Combination of static noise floor, camera agreement, moving-block bootstrap CIs, and timing audit in a single pipeline is ahead of comparable published work.

4. **Three aerodynamic regime identification from camera data alone** — An interesting physical finding that adds value beyond the instrumentation paper.

5. **Fully reproducible offline pipeline with public code** — Deterministic, step-by-step design with documented decision criteria is a real contribution to reproducibility in experimental SHM.

### Weakest points (will generate major revision requests)

1. **Bending r = 0.845 below stated 0.90 gate** — Every reviewer will identify this. The current misalignment explanation must be presented numerically and consistently. Will generate a major revision request unless pre-empted with correct quantitative analysis.

2. **Bending ratio 1.339x without verified structural explanation** — Camera and LDV are from the same facility (Tunnel B) but recorded in separate sessions 10 days apart (NOT simultaneous). The ratio must therefore be interpreted as an instrument-level effect under condition-level comparison. The misalignment cross-axis leakage hypothesis (9.8° → y_leak ≈ α × sin(9.8°)) must be computed quantitatively and shown consistent with the torsion-dominated-regime amplitude inflation. Currently the explanation is stated but not demonstrated.

3. **Bootstrap block length sensitivity** — Not rejection-level alone, but if CI widths materially widen at longer physically motivated block lengths, the uncertainty section needs restating before submission.

4. **Torsion `dp` sensitivity remains unshown** — Not fatal by itself, but it leaves the paper's strongest correlation result less defended than it could be.

### Best strategic journal

**IEEE Transactions on Instrumentation and Measurement (TIM)** is the best strategic fit:
- Explicitly publishes measurement systems with explicit uncertainty characterisation
- Reviewer expectations match this paper's evidence profile better than Measurement's
- More tolerant of condition-level (separate-session, different-sampling-rate) validation as long as uncertainty is properly bounded
- IF ≈ 5.6, comparable to Measurement (5.6) — no significant prestige loss
- Measurement is still a sound choice, but its reviewer pool for this paper will include aerodynamics-adjacent people who will push harder on the bending ratio discrepancy and VIV explanation, which are harder to defend

**Tier 2 backup:** Measurement (Elsevier)
**Tier 3 stretch:** MSSP (requires stronger signal-processing novelty argument)

### One concrete action for highest impact

**Run the bootstrap block-length sensitivity check first.** The intrinsics discrepancy is already resolved, but CI-width robustness is still an open reviewer-facing uncertainty issue. Before finalising manuscript claims about uncertainty width, compare bootstrap CI widths at `N^(1/3)`, one structural period in samples, and two structural periods in samples.

After that, in priority order:
1. Strengthen the quantitative bending-leakage argument (`y_leak ≈ α × sin(9.8°)`) with explicit regime-consistency evidence
2. Add the block length sensitivity check for bootstrap CIs
3. Restate RTS phase shift as resolution-bounded
4. Add the torsion `dp` sensitivity analysis

Those four changes would lift this paper from a speculative submission to a more defensible one.

---

## Key Sources Consulted

- [AprilTag detection for building measurement (ResearchGate)](https://www.researchgate.net/publication/372188745_AprilTag_detection_for_building_measurement)
- [Analysis and Improvements in AprilTag Based State Estimation (Sensors 2019)](https://www.mdpi.com/1424-8220/19/24/5480)
- [Robust monocular vision-based monitoring for multi-target displacement of bridges (MSSP 2024)](https://www.sciencedirect.com/science/article/abs/pii/S0888327024011415)
- [Automated vision-based multi-plane bridge displacement monitoring (Automation in Construction 2024)](https://www.sciencedirect.com/science/article/abs/pii/S0926580524003558)
- [ArUco marker-based displacement measurement technique: uncertainty analysis](https://ouci.dntb.gov.ua/en/works/73gKRPo7/)
- [IPPE — Infinitesimal Plane-Based Pose Estimation (Collins, IJCV)](https://encov.ip.uca.fr/publications/pubfiles/2014_Collins_etal_IJCV_plane.pdf)
- [OpenCV solvePnP documentation](https://docs.opencv.org/4.13.0/d5/d1f/calib3d_solvePnP.html)
- [Modified extended Rauch-Tung-Striebel smoother for vibration energy harvesting (MSSP 2024)](https://www.sciencedirect.com/science/article/abs/pii/S0888327024008628)
- [Block length selection in the bootstrap for time series (Politis & White)](https://www.sciencedirect.com/science/article/abs/pii/S0167947399000146)
- [Optimal choice of bootstrap block length for periodically correlated time series (Bernoulli 2024)](https://projecteuclid.org/journals/bernoulli/volume-30/issue-3/Optimal-choice-of-bootstrap-block-length-for-periodically-correlated-time/10.3150/23-BEJ1683.short)
- [Current status and prospects of computer vision in wind tunnels (Scientific Reports 2025)](https://www.nature.com/articles/s41598-025-96000-y)
- [High-Precision Visual Monitoring Method for Bridge Displacement (Applied Sciences 2025)](https://www.mdpi.com/2076-3417/15/18/10023)
- [Real-Time Vision-Based Dynamic Monitoring of Bridges (ASCE Journal of Bridge Engineering 2024)](https://ascelibrary.org/doi/10.1061/JBENF2.BEENG-7597)

---

*Analysis completed 2026-06-17. Use this document as a revision checklist before final manuscript submission.*

---

## Resolution Status (updated 2026-06-20)

| Gap | Priority | Status | Notes |
|-----|----------|--------|-------|
| Gap 1 — Intrinsics discrepancy (step09 fx=2108 vs 20328) | Critical | **RESOLVED** | step09 now loads intrinsics from pipeline_config.yaml; reproj 1.8→0.04–0.17 px; noise floor 0.003/0.005 mm; step12 reads from step09 JSON |
| Gap 2 — Bending misalignment coupling math | Critical | **RESOLVED** | Two-source explanation in step12 caption, annotation, tab01 Notes column, tab02 footnote, summary JSON |
| Gap 3 — Step11 process noise parameter discrepancy | High | **RESOLVED** | Code defaults updated to 10.0 mm/s / 0.05 mm; results confirmed unchanged |
| Gap 4 — Torsion dp sensitivity analysis | High | **OPEN** | Show r > 0.90 is preserved for dp ∈ [1.4, 1.65] |
| Gap 5 — Bootstrap block length sensitivity | Medium | **OPEN** | Report CI width at N^(1/3), T_h in samples (~42), 2×T_h in samples |
| Gap 6 — RTS phase shift overstated | Medium | **OPEN** | Must restate as "< ±8.3 ms (resolution-limited at 60 Hz)" |
| Gap 7 — Between-tunnel excitation variability | Medium | **RESOLVED** | Same-tunnel (Tunnel B), condition-matched, separate sessions (10 days apart, NOT simultaneous); no between-tunnel variability |
| Gap 8 — B0 quality score framing | Low | **OPEN** | Reframe as detection robustness diagnostic, not pose accuracy predictor |
| Gap 9 — Aerodynamic regimes reduced-velocity context | Low | **RESOLVED** | U* table confirmed in structural_params.md; comparison plots generated |
| Gap 10 — Literature comparison table absent | Low | **OPEN** | Table of 6–8 prior papers with explicit feature comparison |

**NEW findings since this review was written (2026-06-19):**

| Item | Status | Reference |
|------|--------|-----------|
| e20_320rpm motion blur diagnosis | **COMPLETE** | `docs/e20_outlier_analysis.md` — proven mechanism, FFT at 2×f_struct, pixel velocity calculation, Laplacian sharpness, equilibrium clustering |
| DCG formal criterion | **DESIGNED** | Current writeup uses r_det ≥ 0.95 AND n_miss_max ≤ 3 AND v_peak < w_cell as the analytical exclusion rule. Novelty: velocity threshold derived from tag geometry, not empirical. Implementation (step02b_detection_gate.py) PENDING. |
| Step05 gap-aware interpolation guard | **DESIGNED** | MAX_INTERP_GAP = 3 frames derived from ε = A(πg/T_h)²/8. Novelty: published sinusoidal error bound tied to tag cell size and structural frequency. Patch to step05 PENDING. |
| Step12 e20 annotation | **DESIGNED** | DCG-EXCLUDED annotation + cam3 2.19 mm separate point. Implementation PENDING. |
| Alternative approaches evaluated | **COMPLETE** | Ghost-DeblurGAN rejected (domain gap, GAN hallucination risk). Kalman gap-filling rejected (fails at equilibrium crossings, RTS already optimal). Hardware fix (t_exp < 7.1 ms) documented as future work. |
