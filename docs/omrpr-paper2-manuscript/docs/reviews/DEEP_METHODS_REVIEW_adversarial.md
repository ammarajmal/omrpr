# OMRPR — Deep Methods Review and Mentor-Level Critique

**Date:** 2026-06-17
**Prepared by:** Research analysis agent (Claude), commissioned by Ammar Ajmal
**Purpose:** Pre-submission critical analysis covering methods, rationale, results, interpretation, and publication readiness.

> This document is a rigorous, evidence-based critique. Its purpose is to catch problems before manuscript submission, not to encourage the researcher. Be honest about weaknesses when using this as a revision guide.

---

## Point (0) — Journal Landscape: Expanded Target List

**Finding:**

Beyond the three primary targets, 11 additional journals were assessed for this paper's specific profile: offline multi-camera marker-based displacement tracking, non-simultaneous LDV comparison, wind tunnel bridge section, explicit uncertainty chain. Impact factors approximate from JCR 2023/2024.

| Journal | Publisher | IF (approx.) | Scope Fit (1–5) | Realistic Bar | Non-simultaneous validation precedent |
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
| Journal of Bridge Engineering (ASCE) | ASCE | ~3.5 | 3 | Low-medium — very strong bridge physics expected; markers seen as "toy" | No precedent for non-simultaneous |
| Journal of Civil Structural Health Monitoring (JCSHM) | Springer | ~3.8 | 4 | Low-medium — open to lab studies; smaller reach | Moderate |

**Critical Assessment:**

The paper's profile fits **IEEE TIM** and **Measurement (Elsevier)** better than any other journals on this list. IEEE TIM explicitly publishes multi-sensor comparison papers where condition-level RMS correlation against a reference instrument is the primary result. Papers in TIM regularly present camera-vs-LDV or camera-vs-LVDT at condition-level without waveform comparison. The bar is: measurement uncertainty must be rigorously quantified, and the claim boundary must be sharp. TIM also has an expedited review track ("express letters").

**Structural Health Monitoring (SAGE)** would require the paper to frame itself as a monitoring system rather than a measurement pipeline. The reviewers there expect deployed-sensor contributions, not laboratory wind-tunnel characterisation. This is a positioning challenge, not a technical one.

**JSV** is plausible if the aeroelastic regime characterisation (the three-regime finding and VIV at 60 RPM) is elevated to being the primary result, with the camera system as a tool to produce it. That would require significant reframing.

**Reviewer risk (for all targets):** Every high-IF journal will ask why this is not a simultaneous validation. The answer ("the LDV was physically in a different tunnel at a different time") is true but will be challenged as a fundamental limitation. The paper must pre-empt this on page one, not bury it in the limitations section.

**Recommendation:** Primary target: **Measurement (Elsevier)**. Strong backup: **IEEE TIM**. IEEE TIM has slightly lower IF but a better reviewer expectation match for this exact paper type. Do not submit to Engineering Structures without a major aerodynamic physics expansion — their reviewers will not find a measurement pipeline paper compelling without structural safety implications. MSSP is a stretch and should be tier 3.

---

## Point (1) — Literature Positioning and Novelty Claim

**Finding:**

A search across Measurement, Engineering Structures, and MSSP for 2022–2025 papers on: offline multi-camera vision SHM, AprilTag/ArUco displacement tracking, marker-based bridge/civil monitoring, non-simultaneous sensor validation.

Key papers found:
- ArUco marker displacement uncertainty analysis (2022–2023): covers single-camera setups only
- Vision-based multi-plane bridge displacement monitoring (Automation in Construction, 2024): uses ArUco, but simultaneous accelerometer comparison, single camera per plane
- Robust monocular vision monitoring (MSSP, 2024): targets moving background, no marker-based approach
- Computer vision bridge displacement under operational conditions (Engineering Structures area): uses homography without uncertainty chain
- Non-contact vibration using UAV (2025): single UAV camera, AprilTag for positioning only, not displacement measurement

**Critical Assessment:**

There is **no paper** in the literature that combines all four of: (a) offline multi-camera marker tracking with (b) explicit 4-component uncertainty chain (noise floor + camera agreement + bootstrap CIs + timing audit), (c) condition-level cross-sensor comparison as an explicit stated protocol, and (d) an aerodynamically rich dataset with regime characterisation. The non-simultaneous validation protocol is the clearest novelty claim.

However, the novelty argument is currently weak on one axis: the paper does not position itself against existing literature with enough specificity. Sentences like "previous work lacks uncertainty quantification" are commonly made and rarely proven. The paper needs to cite 3–5 specific papers and state exactly what they do NOT report.

The strongest novelty arguments, in order:
1. Explicit condition-level comparison protocol — no precedent found in any marker-based SHM paper
2. Four-component uncertainty chain including derived (not directly measured) noise floor with explicit independence assumption
3. Three-regime aerodynamic characterisation derived entirely from camera data without ground truth
4. No hardware trigger + moving-block bootstrap as a formal treatment of measurement uncertainty

**The weakest argument:** sub-millimeter accuracy. This is routinely claimed and rarely means the same thing across papers. The paper does not actually achieve sub-millimeter accuracy at the condition level (bending MAE = 0.484 mm, RMSE = 0.719 mm versus LDV). The noise floor (0.017 mm) and the condition-level accuracy (0.484–0.719 mm MAE/RMSE) are very different things and must not be conflated in the manuscript.

**Reviewer risk:** "What does sub-millimeter precision mean when your condition-level MAE against the reference is 0.484 mm?" The noise floor characterises the measurement system's precision in a static context; the condition-level MAE reflects a cross-tunnel non-simultaneous comparison and cannot be called an accuracy number.

**Recommendation:** Add a literature comparison table in the introduction with 6–8 papers, explicitly tabulating: marker type, number of cameras, uncertainty quantification method, validation protocol (simultaneous vs. non-simultaneous), and noise floor reported. This table makes the novelty visually undeniable to reviewers and editors.

---

## Point (2) — AprilTag Pose Estimation Validity

**Finding:**

**Pixel coverage calculation:** At 2.5 m standoff with fx ≈ 20,328 px (cam1) and a 20 mm marker, the tag subtends approximately 163 px per side, covering ~26,500 px² at nominal distance. This is excellent coverage.

**IPPE_SQUARE validity:** IPPE_SQUARE is the correct and optimal choice for square planar markers. OpenCV documentation explicitly designates it for this use case. It is analytically faster than SOLVEPNP_ITERATIVE and was designed for exactly the 4-point planar case. The choice is sound.

**Sub-millimeter plausibility:** At ~8 px/mm resolution at 2.5 m, with sub-pixel corner refinement (`refine_edges=1`), theoretical corner localisation precision is 0.1–0.3 px, giving ~0.025 mm in the lateral (Y) plane. Depth (Z) uncertainty is larger but does not affect bending or torsion channels, which are extracted from Y.

**B0 quality score assessment:** The formula `s_i = dm_i × sqrt(area_px2)` combines AprilTag's decision_margin (decoding confidence) with tag area. **This is the weakest methodological piece in the entire pipeline.** `decision_margin` is a binarization/decoding confidence metric — it reflects how cleanly the bit pattern was decoded, not how accurately the corner locations were estimated. Pose accuracy is dominated by corner localisation precision, which is affected by motion blur, defocus, and local contrast. High `decision_margin` can coexist with motion-blurred corners. The corner_sharpness metric (Laplacian) added in step03 is actually a better pose accuracy predictor than decision_margin.

**Critical bug identified — intrinsics discrepancy:**
`pipeline_config.yaml` shows fx = 20,328 (cam1), 25,750 (cam2), 25,631 (cam3).
`step09_uncertainty.py` hardcodes fx = fy = 2,108 px for all three cameras.
**This is a factor of 10–12 discrepancy.** The uncertainty step uses completely wrong intrinsics. Either the config intrinsics are wrong (from a long-telephoto lens setup), or step09 uses placeholder values. At fx = 2,108 (wrong), pixel-to-mm resolution would be ~12× coarser, and the noise floor would be correspondingly wrong. This discrepancy must be resolved before any noise floor numbers are reported in the manuscript.

**Reviewer risk:** "How does decision_margin correlate with pose estimation error? Have you validated that low-quality frames have higher reprojection error?"

**Recommendation:** (a) Resolve intrinsics discrepancy in step09 immediately — this is a potential rejection-level issue. (b) Either validate B0 empirically (show scatter of B0 vs. reprojection error) or demote B0 to a detection robustness metric. State explicitly: "All detected frames are retained; B0 serves as a post-hoc diagnostic, not a filter." The paper uses reprojection error (step04) as the actual pose quality gate, which is the more defensible approach.

---

## Point (3) — Synchronisation: 20 ms Drift Defensibility

**Finding:**

**Phase error at f_h = 1.430 Hz:** Δφ = 2π × 1.430 × 0.020 = 0.180 rad = **10.3°**

**Phase error at f_α = 3.103 Hz:** Δφ = 2π × 3.103 × 0.020 = 0.390 rad = **22.3°**

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

**Parameter inconsistency identified:**
- `step11_rts_smoothing.py` module defaults: `PROCESS_NOISE_STD = 0.5`, `MEASUREMENT_NOISE_STD = 0.1` mm
- `pipeline_config.yaml`: `process_noise_std: 10.0` mm/s, `measurement_noise_std: 0.05` mm
- `PROJECT_CONTEXT.md` (locked values): 10.0 mm/s and 0.05 mm

Which values actually produced the 21/21 PASS results? This must be verified before the manuscript quotes specific σ values.

**Model principled-ness:** The adopted Q model is **not physically principled** in the same way as the kinematic formulation. The kinematic model (G@G.T) failed because Q[0,0] = σ² × dt⁴/4 became numerically negligible relative to R = 0.0025 mm², collapsing the Kalman gain. This is a **process noise scale** problem, not a model choice problem. A kinematic model with σ = 100 mm/s would produce Q[0,0] ≈ 2.8 × 10⁻³ mm², comparable to R, and the gain would not collapse. The decision to change the model structure rather than increase σ in the kinematic formulation is empirical tuning.

**Physical justification for σ = 10 mm/s:** At f_h = 1.430 Hz and amplitude ~1 mm, peak velocity ≈ 2π × 1.430 × 1 ≈ 9 mm/s ≈ 10 mm/s. This is a legitimate physical argument that should be stated explicitly in the manuscript — it turns empirical tuning into physical calibration.

**Amplitude ratio 0.957–1.000:** The lower bound 0.957 occurs at near-floor conditions where RMS ≈ measurement noise. This is physically expected — the smoother cannot add energy that isn't there. This is a sound result.

**Reviewer risk:** "Your process noise model is not the standard kinematic formulation. How was the noise level selected, and is your smoother physically motivated?"

**Recommendation:** (a) Resolve step11 parameter discrepancy between code defaults and pipeline_config.yaml. (b) Add the peak-velocity physical justification for σ = 10 mm/s in the manuscript. (c) Frame the 0.00 ms phase result as "resolution-limited; consistent with non-causal design."

---

## Point (5) — LDV Validation: Three Compounding Problems

**Finding:**

Three issues compound: (a) cross-tunnel comparison, (b) bending r = 0.845 below gate, (c) torsion dp = 1.538 "operator-confirmed" geometry.

**Critical Assessment:**

**(a) Cross-tunnel, 1-month-apart comparison:** The reviewer objection is: "What systematic differences could exist between Tunnel A and Tunnel B?" These include different turbulence intensity, mean flow profiles, blockage ratios, model mounting stiffness, temperature/humidity effects on structural damping, and wind speed calibration differences. None of these are quantified. The 1.339× bending ratio could partially reflect different excitation levels between tunnel runs, not a camera bias. Without simultaneous data, this cannot be decomposed.

**(b) Bending r = 0.845, explained by 9.8° inter-camera misalignment — internally inconsistent:**
The 9.8° angle is "from an audit of old extrinsics YAML" — not an independent measurement of the current physical geometry. The claim is that torsional motion leaks into the bending channel via the misalignment. The stated consequence is 0.038 mm bias at 5 mm amplitude. But the observed camera/LDV ratio in the torsion-dominated regime is ~2× — implying far larger coupling than 0.038 mm can explain. **These two numbers are inconsistent by approximately two orders of magnitude.** The correct coupling formula is: torsional motion of amplitude α contributes `y_leak ≈ α × sin(9.8°) ≈ 0.170α` to the bending channel. At α = 5 mm torsional amplitude, y_leak ≈ 0.85 mm — which could plausibly inflate a 1 mm bending signal to ~1.85 mm, approaching the ~2× factor. The 0.038 mm figure quoted in the documentation is wrong for this mechanism; it describes something different (perhaps the averaging bias, not the coupling). This needs to be recomputed correctly.

**(c) Torsion dp = 1.538, "operator-confirmed":** The dp factor enters as db/dside = 200/130. The MATLAB script previously used dside = 100 mm (an error, now corrected to 130 mm). "Operator-confirmed" means "the lead researcher read a spreadsheet." There is no independent physical measurement of the current experimental geometry and no sensitivity analysis showing how dp uncertainty affects the torsion ratio. A 5% error in dside changes dp from 1.538 to 1.600, changing torsion_rms by ~4%.

**The strongest combined reviewer objection:** "Your bending correlation of 0.845 falls below your stated acceptance criterion. Your explanation invokes a 9.8° misalignment from an outdated extrinsics file, but the quantitative consequence (0.038 mm) is inconsistent with the observed 2× ratio discrepancy. Your torsion geometry dp is derived from a MATLAB script that previously contained an error. Your cross-tunnel comparison does not control for run-to-run excitation differences. Given these three compounding issues, the LDV comparison provides insufficient evidence to support the condition-level validation claim."

**Recommendation:** (a) Recompute the misalignment coupling correctly using `y_leak ≈ α × sin(9.8°)` and verify whether the resulting inflated bending amplitude is consistent with the observed 2× ratio in the torsion-dominated regime. If it matches, you have a quantitative argument. (b) Add a sensitivity analysis: show that torsion r = 0.940 is robust to ±10% uncertainty in dp. (c) Add a brief discussion of between-tunnel variability as a quantified (or acknowledged unquantifiable) contribution to the bending ratio.

---

## Point (6) — Aerodynamic Regimes and Physical Explanations

**Finding:**

Three-regime classification: bending-dominated (40–80 RPM), torsion-dominated (90–220 RPM), bending re-emergence (240–300 RPM). f_α/f_h = 2.17, structural damping ≈ 1.9%.

**Critical Assessment:**

**Torsion dominance in the mid-speed range:** At f_α/f_h = 2.17, the frequency ratio is above the classical Scanlan condition for coupled flutter (which for thin airfoils typically occurs near f_α/f_h ≈ 1.5–2.0 depending on cross-section). The observation of torsion-dominated response at intermediate wind speeds before bending re-emergence at higher speeds is physically plausible for a bluff bridge section. Aerodynamic literature on rectangular section models shows torsional VIV preceding flutter onset when f_α/f_h > ~2.0. This is consistent with the data.

**60 RPM VIV claim:** The camera/LDV ratio of ~0.05× at 60 RPM is dramatic. VIV intermittency is a legitimate physical mechanism: during lock-in, response amplitude is highly sensitive to small differences in wind speed, turbulence level, or structural damping. If the LDV run happened at a slightly different wind speed (±5% of lock-in speed), the amplitude could differ by 20×. The ~0.05× ratio is plausible but requires a quantitative argument — calculate the VIV lock-in bandwidth at 60 RPM in terms of reduced velocity and show that cross-tunnel wind speed differences of [X]% could produce the observed collapse.

**320 RPM flutter onset:** B = 0.40 m, f_α = 3.103 Hz. For a flat plate, flutter reduced velocity U_cr/(f_α × B) ≈ 3.5–6.0. At U_cr ≈ 5 m/s: reduced velocity = 5 / (3.103 × 0.40) ≈ 4.0 — consistent with flutter susceptibility for this cross-section.

**The physical explanations are qualitatively sound but lack quantitative bridge.** The three-regime identification is the strongest physical result of the paper, but it is presented as observation (frequency vs. RPM plot) without linking to published aerodynamic data for comparable rectangular section models (Scanlan, Simiu, or Larsen references). Aerodynamics reviewers will want reduced-velocity axes and regime boundary citations.

**Reviewer risk:** "At what reduced velocities do these regimes occur? Are they consistent with published flutter derivative data for this cross-section?"

**Recommendation:** (a) Add a reduced-velocity axis to the frequency-vs-RPM figure if the wind speed/RPM calibration is available from facility records. (b) Cite 2–3 aerodynamics references for rectangular section models with f_α/f_h ≈ 2 to contextualise the three-regime observation. (c) For 60 RPM VIV: calculate the lock-in bandwidth and show that cross-tunnel differences of X% wind speed could produce the ratio collapse.

---

## Point (7) — Noise Floor and Uncertainty Methodology

**Finding:**

Static noise floor: `sqrt((σ_cam1² + σ_cam2²) / 4)` = 0.017 mm bending, 0.033 mm torsion proxy. Non-simultaneous static bags. Moving-block bootstrap with `L = int(N^(1/3))`, 1000 resamples, seed 42.

**Critical Assessment:**

**Independence assumption:** The cameras share the same building and environment. Common-mode vibration (building vibration, floor tremor, HVAC) affects all cameras simultaneously. The independence assumption (σ² adds, not 2σ²) is physically reasonable for non-simultaneous recordings (hours apart) in typical laboratory conditions, but cannot be claimed without explicit qualification.

**0.017 mm credibility — contingent on intrinsics being correct:** If step09 ran with fx = 2,108 (wrong) instead of fx = 20,328 (correct), the noise floor numbers are not trustworthy. See Point (2). This is the same critical bug.

**Block length is too short:** For N ≈ 1,800 frames (30 s × 60 Hz), the cube root rule gives L ≈ 12 frames ≈ 0.2 s. At f_h = 1.430 Hz, the signal autocorrelation length is approximately 1/f_h ≈ 0.7 s. The block length is **shorter than one oscillation period**, meaning the bootstrap underestimates variance. An appropriate block length for this signal is L ≈ 42 frames (≈2–3 signal periods). With L = 42 frames, CI width would increase by approximately √(42/12) ≈ 1.9×, potentially pushing 13–15% to 25–28%. This must be checked before quoting CI widths in the manuscript.

**Reviewer risk at Measurement:** "The cube root rule gives L ≈ 12 frames (0.2 s), but your dominant signal period is 0.7 s. Your block length is shorter than the signal autocorrelation length. Can you show that CI width is stable as a function of L?"

**Recommendation:** (a) Resolve the step09 intrinsics discrepancy first. (b) Report CI width as a function of block length L at at least three values: `N^(1/3)`, T_h in samples (~42 frames), and 2 × T_h in samples. If CI width is stable across these, report that explicitly. If sensitive, report the range. (c) Add a sentence explicitly acknowledging the independence assumption: "We assume independent noise between cameras, which is physically plausible for non-simultaneous static recordings but cannot be verified from these data alone."

---

## Point (8) — Specific Manuscript Gaps (Priority Order)

### Gap 1 — Critical: Intrinsics discrepancy between step09 and pipeline_config.yaml
`step09_uncertainty.py` hardcodes `fx = fy = 2,108 px` for all three cameras. `pipeline_config.yaml` has `fx = 20,328` (cam1), `25,750` (cam2), `25,631` (cam3) — a factor of 10–12. The noise floor, timing audit, and camera agreement computations in step09 may all be based on wrong pixel-to-mm mapping. Verify and correct before any noise floor number enters the manuscript.

### Gap 2 — Critical: Bending misalignment explanation is internally inconsistent
The 0.038 mm bias (stated as the coupling consequence) is far too small to explain a ~2× amplitude ratio in the torsion-dominated regime. The correct coupling term is `y_leak ≈ α × sin(9.8°) ≈ 0.170α`. Recompute and verify consistency with the observed ratio. Without this fix, the bending r = 0.845 discussion will not survive peer review.

### Gap 3 — High: Process noise parameter inconsistency
`step11` code defaults differ from `pipeline_config.yaml` and `PROJECT_CONTEXT.md`. Verify which values were actually used to produce the 21/21 PASS results. The manuscript must quote the values that were actually used.

### Gap 4 — High: Torsion dp sensitivity analysis
The torsion r = 0.940 is the paper's strongest result. It was computed after correcting a prior error in dp (2.0 → 1.538). A reviewer will treat the prior error as evidence of parameter uncertainty. A sensitivity analysis showing r > 0.90 is preserved for dp ∈ [1.4, 1.65] would significantly strengthen this result.

### Gap 5 — Medium: Block length sensitivity for bootstrap CIs
The 13–15% CI width may be underestimated due to short block length. Report CI width at three block lengths. If stable, state so. If sensitive, report range.

### Gap 6 — Medium: RTS phase shift must be restated
"0.00 ms" implies millisecond precision the analysis does not achieve. Correct statement: "< ±8.3 ms (resolution-limited at 60 Hz sampling); consistent with non-causal smoother design."

### Gap 7 — Medium: Between-tunnel excitation variability not acknowledged
The 1.339× bending ratio could partially reflect different wind excitation levels between tunnel runs, not only camera bias. A sentence acknowledging this as an unresolved contribution is required for honest claim framing.

### Gap 8 — Low: B0 quality score framing
Reframe as a detection robustness diagnostic (not a pose accuracy predictor). State that all detected frames are retained; reprojection error (step04) is the pose quality gate.

### Gap 9 — Low: Aerodynamic regimes need reduced-velocity context
The frequency-vs-RPM plot is the most interesting physical result but lacks reduced-velocity axis. If the wind speed/RPM calibration exists in facility records, it must be included to allow contextualisation against published aerodynamic data.

### Gap 10 — Low: Literature comparison table absent
Without a table comparing this paper's key features against 6–8 specific prior papers, the novelty claim is asserted but not demonstrated.

---

## Point (9) — Synthesis: Ranked Publication Readiness

### Strongest contributions (will survive peer review)

1. **Torsion proxy r = 0.940** — The paper's single strongest number. High correlation across 18 stable conditions, robust to the non-simultaneous comparison, physically sensible geometry.

2. **189× camera Z agreement improvement (388 mm → 2.053 mm std)** — Compelling numerical contrast demonstrating the baseline alignment approach. No comparable paper offers this before/after alignment demonstration.

3. **Explicit four-component uncertainty chain** — Combination of static noise floor, camera agreement, moving-block bootstrap CIs, and timing audit in a single pipeline is ahead of comparable published work.

4. **Three aerodynamic regime identification from camera data alone** — An interesting physical finding that adds value beyond the instrumentation paper.

5. **Fully reproducible offline pipeline with public code** — Deterministic, step-by-step design with documented decision criteria is a real contribution to reproducibility in experimental SHM.

### Weakest points (will generate major revision requests)

1. **Bending r = 0.845 below stated 0.90 gate** — Every reviewer will identify this. The current misalignment explanation is internally inconsistent numerically. Will generate a major revision request unless pre-empted with correct quantitative analysis.

2. **Cross-tunnel comparison without excitation control** — Reviewers will ask how much of the 1.339× bending ratio is camera bias vs. different wind excitation. This is unanswerable from current data alone and needs honest framing.

3. **Intrinsics discrepancy in step09** — If this translates to wrong noise floor values in the manuscript, the uncertainty claims are invalidated. Potential rejection-level issue.

4. **Block length sensitivity** — Not rejection-level alone, but combined with other uncertainty concerns, it weakens the uncertainty methodology section.

### Best strategic journal

**IEEE Transactions on Instrumentation and Measurement (TIM)** is the best strategic fit:
- Explicitly publishes measurement systems with explicit uncertainty characterisation
- Reviewer expectations match this paper's evidence profile better than Measurement's
- More tolerant of condition-level (non-simultaneous) validation as long as uncertainty is properly bounded
- IF ≈ 5.6, comparable to Measurement (5.6) — no significant prestige loss
- Measurement is still a sound choice, but its reviewer pool for this paper will include aerodynamics-adjacent people who will push harder on the cross-tunnel comparison and VIV explanation, which are harder to defend

**Tier 2 backup:** Measurement (Elsevier)
**Tier 3 stretch:** MSSP (requires stronger signal-processing novelty argument)

### One concrete action for highest impact

**Resolve the step09 intrinsics discrepancy first.** This is the only issue that can invalidate the entire uncertainty section of the manuscript in a single reviewer comment. Before drafting a single manuscript sentence about the noise floor, verify whether step09 was run with `fx = 2,108` (hardcoded placeholder) or `fx = 20,328` (calibrated value from pipeline_config.yaml). If step09 used the wrong intrinsics, rerun it with the correct values and update all noise floor numbers. Only once the noise floor is confirmed correct should the manuscript uncertainty section be finalised.

After that, in priority order:
1. Fix the bending misalignment coupling math (`y_leak ≈ α × sin(9.8°)`)
2. Resolve the step11 process noise parameter discrepancy
3. Add the block length sensitivity check for bootstrap CIs
4. Restate RTS phase shift as resolution-bounded

Those four changes, plus the intrinsics fix, would lift this paper from a speculative submission to a defensible one.

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
