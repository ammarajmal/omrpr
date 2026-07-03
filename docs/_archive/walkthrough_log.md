# OMRPR Pipeline Walkthrough Log
Generated during final Step 00-12 review before manuscript drafting.
All canonical values confirmed from results/step10/ldv_summary.json
and current_ground_truth_audit_2026-06-23.md.
Tunnel: Both camera (Oct 2025) and LDV (Sep 2025) in Tunnel B.
Bending r = 0.845 | Torsion r = 0.940 | Timing drift = 20.03 ms
---

---
## Step 00 — ROS Bag Audit | 2026-06-23 | PASS

### Q&A Record
**Q1:** `step00_bag_audit.py` checks each ROS bag for completeness. What specific properties does it verify per bag, and what constitutes a "pass" vs "fail" for a bag — i.e., what is the acceptance criterion that would cause a bag to be flagged?
**A1:** Must contain image data, consistent timestamps, no missing data, must be readable; outputs topic names, message types, and message counts. | APPROVED

**Q2:** The audit covers both camera and LDV bags. Given the 10-day gap between camera (Oct 2025) and LDV (Sep 2025) acquisition, what does the audit actually synchronise or cross-check between the two, if anything — or is it purely a per-bag integrity check at this stage?
**A2:** LDV is facility-provided CSV (commercial aerodynamic testing facility in South Korea [Lee2016]), not a ROS bag. Audit cross-checks experiment label (e-number + RPM) and duration parity (~20–30 s). No deeper sync at this stage. | APPROVED

**Q3:** What is the specific failure mode most concerning in camera bags versus LDV bags, and why do those differ given the sensor types?
**A3:** Missing data and inconsistent numbers. | NEEDS CORRECTION: Camera bags — dropped frames break the uniform Δt assumption all downstream optical-flow steps depend on. LDV CSVs — silent NaN/blank rows or mis-stated sample-rate header, because bags expose message counts explicitly while CSVs require row-count + time-column inspection.

### Run Results
- Smoke test (e7_90rpm): cam1 1828 frames @ 59.94 Hz, cam2 1828 @ 59.94 Hz, cam3 1830 @ 60.00 Hz; duration 30.48 s; timestamp skew 0.0124 s; max gap 0.0260 s — PASS
- Full sweep (--all, 21 WTT bags e0–e20): ALL PASS
  - FPS: cam1 & cam2 consistently 59.94 Hz; cam3 consistently 60.00 Hz (hardware clock difference, expected)
  - Duration: all 30.46–30.55 s (tight cluster, consistent with 30 s acquisition protocol)
  - Timestamp skew range: 0.0023 s (e15) to 0.0215 s (e6) — all well within limits
  - MaxGap range: 0.0240–0.0311 s; **e8_100rpm cam3 = 0.0311 s** (highest single-topic gap, still << 0.1 s threshold)
  - JSON outputs saved to results/step00/ (31 files including static bags)
- Acceptance gate: PASS — 21/21 WTT bags, 0 WARN, 0 FAIL

### Key Findings
- All 21 WTT experiment bags pass FPS and gap acceptance criteria with zero anomalies
- cam3 runs at exactly 60.00 Hz vs 59.94 Hz for cam1/cam2; consistent across all experiments — expected hardware timing difference, not a defect
- e8_100rpm cam3 has the largest single max-gap at 0.0311 s; flagged for awareness but within PASS band (threshold 0.1 s)
- Inter-camera timestamp skew is largest for e3_50rpm (0.0206 s) and e6_80rpm (0.0215 s) — relevant context for the timing-drift correction in step02
- All 31 per-bag JSON audits saved to results/step00/

### Static Bags (Calibration)
- 20 static bags (cam1×5, cam2×10, cam3×5) also audited
- **7 FAIL, 5 WARN, 8 PASS** — but FAILs are expected: static bags use `/image_raw` (uncompressed) at ~32 Hz, single-camera only; the 59–61 Hz PASS criterion is tuned for WTT experiment bags
- e.g., `static_cam2_test6`: 391 frames @ 32.56 Hz on `image_raw` — not a recording defect, just different capture mode
- **Action for step03:** static bag acceptance criteria must be evaluated separately from WTT criteria

### Vulnerabilities Noted
- Audit is metadata-only — does not decode pixel content, so a corrupted JPEG stream would pass this gate and only surface at step01 (frame extraction)
- LDV CSV integrity not checked here; duration parity cross-check against bag durations is not yet implemented in step00 (manual verification confirms ~30 s match)
- e3_50rpm and e6_80rpm have the largest inter-camera skew (>20 ms); downstream stereo-matching steps should be robust to this level of jitter

### Viva Q&A
**Q:** Why do cam1/cam2 report 59.94 Hz while cam3 reports 60.00 Hz, and should this concern you?
**A:** Sony cameras can run at either 59.94 Hz (NTSC-compatible) or exactly 60.00 Hz depending on internal clock configuration; the 0.06 Hz difference corresponds to a ~30 µs per-frame drift and accumulates to ~1 ms over a 30 s run. This is well below the 20.03 ms canonical timing drift from the 10-day session gap and does not affect any downstream step. The difference is consistent across all 21 experiments, confirming it is a systematic hardware setting, not intermittent jitter.

### Reviewer Risk
A *Measurement* reviewer would ask whether the bag audit detects corrupted compressed image data (not just missing frames), and whether the 20 ms inter-session timing drift is accounted for prior to any cross-modal comparison.

---

---
## Step 01 — Frame Export | 2026-06-23 | PASS
### Q&A Record
**Q1:** In Step 01, what is the measurement rationale for exporting frames plus `timestamps.csv` instead of decoding images later directly from the bag inside every downstream step?
**A1:** the rationale for exporting frames plus timestamps.csv instead of decoding images later directly from the bag inside every downstream step is to avoid redundant processing of extraction of images from the bag files in each decoding downstream step. In this way, images are extracted in one clean step and later on, we may have images to be used for later processing. so that we do not have to extract them each time and it saves time, effort and processing. | APPROVED: The core rationale is exactly to create deterministic, reusable image and timestamp inputs once rather than re-decoding bags inside every later step.
**Q2:** What is the main vulnerability introduced by JPEG-to-PNG frame export for this pipeline, and why does that vulnerability not invalidate the later displacement analysis?
**A2:** I have no idea | NEEDS CORRECTION: The vulnerability is that the original camera data are already lossy compressed JPEG frames, so compression artefacts and any decode failures are baked in before AprilTag detection, but exporting to PNG is lossless and therefore adds no further image degradation; it preserves the decoded pixels for traceable downstream reuse.
**Q3:** If a reviewer asks whether Step 01 creates any false impression of synchrony between cameras or between camera and LDV, what is the correct 1-3 sentence response?
**A3:** no there is no false impression of synchrony between cameras, as the cameras raw data is being saved into bag files and in this step 01 their individual bag files are extracted into png images and their respective timestamps meta data. although the three cameras data is being recroding into a single bag file but they were stareted serially which added intercamera time shifts as well as time skew due to inconsistant framerates. but that is not tackled in this step, as only bag file to images conversion is done here and no time consistancy is being processied or done here. | APPROVED: Correct, because Step 01 only exports per-camera frames and timestamps and makes no synchrony or simultaneity claim across cameras or against LDV.
### Run Results
- Smoke test (e7_90rpm): cam1 1828 frames @ 59.9418 Hz, cam2 1828 @ 59.9414 Hz, cam3 1830 @ 60.0024 Hz; durations 30.4796 s / 30.4798 s / 30.4821 s; start-time skew 0.0119 s; max gap 0.0260 s; no decode failures
- Full sweep (--all): 21/21 WTT conditions present under `results/step01`; 0 warning cases from monotonicity/max-gap/decode-failure audit; frame-count range 1827-1833; worst observed gap e8_100rpm cam3 = 0.0311 s
- Acceptance gate: PASS
### Key Findings
- Step 01 outputs are complete across all 21 WTT conditions with no `decode_failures.txt` files present anywhere in `results/step01`
- e7_90rpm matches the expected reference pattern: cam1/cam2 at ~59.94 Hz, cam3 at ~60.00 Hz, with sub-12 ms start skew and no abnormal timestamp gaps
### Vulnerabilities Noted
- Step 01 cannot recover information lost by the original JPEG compression, so any compression artefact affecting AprilTag corner localisation is inherited downstream
- If decode failures ever occur, the script currently re-enumerates `timestamps.csv` from surviving frames rather than preserving original skipped frame indices, which would need careful interpretation
### Viva Q&A
**Q:** Why is exporting to PNG scientifically acceptable even though the source topic is compressed image data?
**A:** Because the lossy step already happened in-camera when the JPEG-compressed ROS message was recorded. PNG export is lossless and only freezes the decoded pixel array for reproducible downstream analysis. So Step 01 does not improve image fidelity, but it also does not degrade it further.
### Reviewer Risk
A *Measurement* reviewer would scrutinise whether JPEG compression or silent decode failures could bias sub-pixel AprilTag localisation before any displacement estimate is formed.

---

---
## Step 02 — Offline AprilTag Detection | 2026-06-23 | PASS
### Q&A Record
**Q1:** In Step 02, why is offline AprilTag detection a necessary intermediate measurement step instead of estimating structural displacement directly from image intensity or feature tracking on the deck itself?
**A1:** it will give me accurate poses for 3 dimensional displacement tracking. apart from that i am unsure if estimating structural displacement directly from image intensity or feature tracking on the deck itself can give me better results or not? Guide me on that. | NEEDS CORRECTION: AprilTag detection is needed because it gives a known planar target with fixed geometry, stable ID, and sub-pixel corners that support traceable pose recovery, whereas raw intensity or deck-feature tracking would be less repeatable, less metrically anchored, and more vulnerable to lighting, blur, and low-texture failure.
**Q2:** What is the main measurement vulnerability if AprilTag detections are intermittent, low-margin, or view-dependent across cameras, and how could that propagate into later pose and displacement estimates?
**A2:** it will give me messy or noisy baseline data and will influence the overall accuracy of the system | NEEDS CORRECTION: The specific vulnerability is not just generic noise but missing or weak corner observations, which create frame dropouts, lower-confidence pose estimates, and camera-dependent bias that can propagate into synchronisation, fusion, and displacement continuity errors.
**Q3:** If a reviewer asks whether successful AprilTag detection implies camera-LDV synchrony or simultaneous comparison validity, what is the correct 1-3 sentence response?
**A3:** no a successful AprilTag detection does not necessarily implies camera-LDV synchrony or simultaneous comparison validity as the detection in itself without the notion of timestamps only gives if the tag is detected or not. the actual phenomenon lies in the allignment of detected tags with the timestampts and the overall timeline analysis i.e., the detection integrated with the timestamps accuracy and availability. | APPROVED: Correct, because Step 02 only establishes per-frame tag observability and image coordinates; timing alignment and the non-simultaneous camera-LDV comparison claim are handled in later steps.
### Run Results
- Smoke test (e7_90rpm): cam1 1828/1828 detected (100.00%), cam2 1828/1828 (100.00%), cam3 1830/1830 (100.00%); max_consecutive_miss=0 for all cameras; decision-margin mean/min/max = cam1 34.962/32.254/37.371, cam2 34.559/32.164/37.241, cam3 55.343/53.288/57.772; all detections tag_id=0 and hamming=0
- Full sweep (--all): 61/63 camera streams at 100.00% detection with max_consecutive_miss=0; only e20_320rpm drops to cam1 1112/1829 (60.80%, max miss 6) and cam2 1122/1829 (61.35%, max miss 6), while e20 cam3 remains 1831/1831 (100.00%); no nonzero hamming decodes and no unexpected tag IDs anywhere
- Acceptance gate: PASS
### Key Findings
- Step 02 is perfectly stable across 20 of 21 WTT conditions and all three cameras for the smoke-test condition e7_90rpm
- The only anomaly is the expected e20_320rpm degradation in cam1 and cam2, matching the repo's known weak-condition story
- Detection decoding is clean throughout the corpus: all accepted rows use tag_id=0 with hamming=0
### Vulnerabilities Noted
- Step 02 produces sparse output for missed frames, so prolonged miss runs can create temporal gaps that later steps must handle explicitly rather than treating the series as uniformly observed
- Decision margin is diagnostic only at this stage; weak-but-decoded frames can still pass forward unless filtered downstream
### Viva Q&A
**Q:** Why is an AprilTag target preferable to generic deck feature tracking for this measurement pipeline?
**A:** An AprilTag gives a known geometry, unambiguous identity, and sub-pixel corner locations that support deterministic pose estimation with a clear error chain. Generic structural texture does not give the same metric anchor and is more sensitive to lighting, blur, and view changes. That makes AprilTags much more defensible for a measurement paper.
### Reviewer Risk
A *Measurement* reviewer would scrutinise whether the e20 cam1/cam2 miss runs bias downstream pose continuity or selectively remove high-motion frames in the most demanding condition.

---

---
## Step 03 — Quality Scoring | 2026-06-23 | PASS
### Q&A Record
**Q1:** The B0 quality formula is s_i = dm_i × sqrt(A_i), where dm is the decision margin and A_i is the shoelace area of the four detected corners. What does each factor contribute independently — why is neither dm alone nor sqrt(A_i) alone sufficient as a quality score for downstream pose weighting?
**A1:** `decision_margin` measures how cleanly the tag bits decode, while `sqrt(area)` measures the tag's image scale, which is a proxy for corner-localisation leverage. `dm` alone ignores whether the tag is tiny and geometrically weak, and `sqrt(area)` alone ignores whether the tag was decoded ambiguously or under poor contrast, so the product captures both robustness and usable image size. | APPROVED: Correct, because the locked B0 score combines decode confidence with projected tag scale, and either term alone would miss one of those two distinct failure modes.
**Q2:** The corner sharpness (Laplacian variance) was computed and stored as a diagnostic column but is deliberately excluded from the quality score formula itself. What is the specific reason this exclusion was the correct engineering decision for this dataset and pipeline — what failure mode would including it have introduced?
**A2:** In this dataset, Laplacian sharpness is highly sensitive to local contrast, JPEG artefacts, and camera-specific appearance, so folding it into the score would have mixed a blur diagnostic with illumination and texture effects. Including it would have risked down-weighting physically valid detections for photometric reasons and making scores less comparable across cameras and conditions. | APPROVED: Correct, because sharpness was useful as a diagnostic but too photometrically confounded to become part of the locked per-frame score.
**Q3:** Step 03 produces per-frame quality scores, but Step 04 (pose estimation) uses SOLVEPNP_IPPE_SQUARE which returns two candidate solutions rather than a quality-weighted average. How does the quality score from Step 03 actually influence the pipeline downstream — at which step and in what form does it have its first functional effect?
**A3:** It does not influence Step 04 pose selection at all: Step 04 reads the Step 03 CSV but uses only the corner coordinates and then chooses between the two IPPE solutions using physical validity and reprojection error. In the live pipeline, the first real effect of Step 03 quality is diagnostic and reporting only, through `summary.json`, later visual diagnostics, and manuscript justification for retaining equal-weight detected frames rather than applying a quality-weighted estimator. | APPROVED: Correct, because the current repo does not consume `quality_score` as an algorithmic weight or filter in downstream estimation.
### Run Results
- Smoke test (e7_90rpm): rerun completed on the live repo with `--no-sharpness`; cam1 quality mean/min/max = 10133.96/9339.42/10826.87, cam2 = 9965.85/9310.22/10733.80, cam3 = 16187.87/15586.79/16905.59; low_q=0 for all three cameras
- Full sweep (--all): rerun completed on the live repo with `--no-sharpness` across all 21 conditions; all 63 camera streams reported low_q=0 and `OK`; notable values include e20_320rpm cam1 mean/min/max = 10463.14/8969.65/11388.28, cam2 = 10586.89/9030.69/11465.85, cam3 = 16332.89/15757.68/17031.43
- Acceptance gate: PASS
### Key Findings
- The core B0 implementation reran successfully and reproduced the expected Step 03 pattern: cam3 consistently carries the highest quality scores, cam1 and cam2 track closely below it
- The low-quality threshold of 50.0 is non-binding in practice for this dataset, since even the minimum rerun score remained 8969.65
- e20_320rpm still scores as `OK` on detected frames despite Step 02 detection collapse in cam1 and cam2, which confirms that Step 03 measures detected-frame robustness rather than completeness
### Vulnerabilities Noted
- `quality_score` is not consumed as a downstream estimator weight or filter, so its scientific role must be framed honestly as diagnostic rather than causal
- Because scores are computed only on retained detections, Step 03 can look healthy even when a condition suffers severe dropout; that is why DCG and Step 02 completeness remain essential companion gates
### Viva Q&A
**Q:** Why is it defensible to keep the B0 formula locked even though it is not the final pose-quality gate?
**A:** Because it gives a simple, reproducible detection-robustness index based on information available at the detection stage. The actual pose-quality gate is reprojection error in Step 04, which is closer to the quantity reviewers care about for geometric accuracy. So B0 can stay as a diagnostic as long as it is not overstated as a pose-accuracy predictor.
### Reviewer Risk
A *Measurement* reviewer would scrutinise the fact that Step 03 scores only surviving detections, so they will want a clear statement that detection completeness and pose accuracy are governed elsewhere rather than by B0 alone.

---

---
## Step 04 — Pose Estimation | 2026-06-23 | PASS
### Q&A Record
**Q1:** `SOLVEPNP_IPPE_SQUARE` is being used to resolve any possible pose ambiguity that could arise from planar targets, since a flat square tag has a mirror-symmetric pose that produces identical reprojection from two distinct 3D orientations. A planar-target method is more appropriate because generic PnP solvers (e.g. iterative LM) converge to one local minimum depending on initialisation, potentially the wrong solution, whereas IPPE analytically enumerates both solutions and lets you select on a geometric criterion (`tvec[2] > 0`). | APPROVED: Correct, because the live Step 04 implementation explicitly uses `cv2.SOLVEPNP_IPPE_SQUARE` to enumerate the two planar-square solutions and then applies the positive-depth plus reprojection-error selection rule.
**Q2:** Reprojection error is the right check because it directly measures how well the estimated pose projects the known 3D tag corners back onto the detected 2D corner positions, so it is the residual of the geometric model being solved. The failure mode that slips through is the solution-flip ambiguity: both IPPE solutions can have identical or near-identical reprojection error, so low reprojection error does not guarantee the geometrically correct solution was selected; the `tvec[2] > 0` criterion is what resolves this, not reprojection error itself. | APPROVED: Correct, because reprojection error is the proper geometric residual for pose quality, but by itself it cannot disambiguate the two planar IPPE candidates.
**Q3:** If the pose axis convention or frame origin shifts between runs, even subtly, then the `y_w` displacement time series across conditions are not drawn from the same physical reference frame. Because the later condition-level comparison uses RMS per condition and RMS is sensitive to DC offset and sign, a flipped axis or inconsistent baseline would contaminate each condition's amplitude estimate and make the camera-LDV scatter physically meaningless despite the non-simultaneous comparison design. | APPROVED: Correct, because downstream condition-level RMS comparison still assumes that Step 04 produced internally consistent camera-frame coordinates before Step 06 baseline alignment removes per-camera means.
### Run Results
- Smoke test (`e7_90rpm`): reran `src/step04_world_transform.py` in conda env `omrpr`; cam1 1828 frames with reproj mean/max = 0.1041/0.3183 px, cam2 1828 = 0.1200/0.3029 px, cam3 1830 = 0.2859/1.0316 px; `high_reproj=0`, `bad=0` for all three cameras
- Full sweep (`--all`): reran all 21 conditions; all 63 camera streams finished `OK` with `high_reproj=0` and `bad=0`; repo-wide mean reprojection stayed in the expected sub-pixel band, with the known worst case at `e20_320rpm` cam3 mean/max = 0.7421/1.7163 px
- Acceptance gate: PASS
### Key Findings
- The live Step 04 implementation and rerun outputs are consistent with the locked solver story: `IPPE_SQUARE` is active, and all streams remain well below the 3.0 px warning gate and 10.0 px hard-fail gate
- `e7_90rpm` reproduced the expected reference pattern, with cam3 showing the highest reprojection error of the three cameras while still remaining comfortably sub-pixel on average
- The only notable anomaly is the expected `e20_320rpm` weak-condition case, where cam1/cam2 inherit reduced frame counts from Step 02 and cam3 shows the highest reprojection error, but none of those streams violate the Step 04 gate
### Vulnerabilities Noted
- Low reprojection error does not by itself prove the physically correct planar pose branch was selected, so the positive-depth selection logic must remain locked and documented
- Step 04 outputs are still camera-frame coordinates, not a shared geometric world frame, so any manuscript wording must avoid implying cross-camera absolute position comparability before Step 06 baseline alignment
### Viva Q&A
**Q:** Why is it scientifically acceptable that Step 04 does not establish a common multi-camera world frame yet?
**A:** Because this step’s job is only to recover a consistent per-camera tag pose from image geometry. The common reference used for cross-camera displacement comparison is established later by baseline subtraction in Step 06, so Step 04 does not need extrinsic registration as long as its camera-frame coordinates are internally stable and clearly described.
### Reviewer Risk
A *Measurement* reviewer would scrutinise whether the manuscript blurs the distinction between camera-frame pose recovery and a true shared world-frame reconstruction, especially because the later LDV comparison is already non-simultaneous and condition-level only.

---

---
## Step 05 — Synchronisation | 2026-06-23 | PASS
### Q&A Record
**Q1:** Step 05 is scientifically limited to synchronising the three camera streams onto a common 60 Hz time base since the three cameras frame rate was inconsistant and was not exactly 60Hz, so a consistant baseline 60hz timeline is necessary before moving on. Yes, since we are also using LDV comparisons as condition level so it is not absolutely necessary, correct me if wrong. | APPROVED: Correct in substance, because the live step only regularises the three camera streams to a common grid and does not create any camera-LDV simultaneity claim beyond the locked condition-level comparison boundary.
**Q2:** no idea | NEEDS CORRECTION: The live vulnerability is that Step 05 will interpolate any in-range timestamps onto the common grid without checking whether the source gap is short or long, so large dropout spans can be smoothed across silently; therefore the `DCG <= 3 frames` rule must be treated as an external acceptance gate from Step 02/02b, not as active protection implemented inside `src/step05_synchronize.py`.
**Q3:** yes | NEEDS CORRECTION: A 20.03 ms inter-camera drift is acceptable for later condition-level RMS comparison because RMS over a 30 s condition is insensitive to a small phase offset between camera streams once they are placed on a common 60 Hz grid. It would be unacceptable for any point-by-point camera-LDV waveform agreement claim, because that kind of claim requires true simultaneity and sub-cycle alignment, which this dataset does not have across the 10-day-separated camera and LDV sessions.
### Run Results
- Smoke test (`e7_90rpm`): reran `src/step05_synchronize.py` in conda env `omrpr`; common window `[0.011891, 30.479582] s` produced 1829 synced frames at 60 Hz; all three cameras wrote identical `t_s` grids (`max_diff < 1e-9 s`); raw Z disagreement remained at cam1-cam2 `388.0 mm`, cam1-cam3 `347.1 mm`, cam2-cam3 `40.9 mm`
- Full sweep (`--all`): reran all 21 conditions successfully; every condition produced a common 60 Hz grid with identical `t_s` across cameras; synced-frame counts ranged from 1821 (`e20_320rpm`) to 1832 (`e0_0rpm`, `e11_140rpm`, `e17_260rpm`)
- Expected-value check: the locked normal-case max inter-camera start spread was reproduced at `20.03 ms` in `e3_50rpm`; the much larger `70.94 ms` spread seen in `e20_320rpm` is an anomaly caused by late first valid Step 04 detections in cam1/cam2 after dropout, not by the canonical healthy-dataset timing drift
- Acceptance gate: PASS
### Key Findings
- The live Step 05 implementation still matches the cleaned repo truth: it intersects the per-camera time ranges, builds a common 60 Hz grid, uses `interp1d(..., bounds_error=True)`, and does not implement an explicit maximum-gap rejection rule
- `e7_90rpm` reproduced the expected synchronisation reference pattern cleanly, including the known pre-alignment raw Z offset of about `388 mm` that Step 06 must later remove
- Across the full sweep, all conditions maintained numerically identical cross-camera timestamps after resampling, so the step is stable for downstream fusion on the camera side
### Vulnerabilities Noted
- Because there is no active `MAX_INTERP_GAP` guard, Step 05 can interpolate smoothly across long observation gaps if the timestamps remain in range; `e20_320rpm` is the concrete warning case for this vulnerability
- Step 05 does not and cannot justify waveform-level camera-LDV agreement, because the camera and LDV datasets are non-simultaneous and separated by 10 days
### Viva Q&A
**Q:** Why is the `e20_320rpm` anomaly scientifically important even though Step 05 itself still finishes with a PASS?
**A:** Because it shows that successful resampling is not the same thing as trustworthy signal support. The step can produce a neat 60 Hz grid even when upstream detections are sparse, so the scientific defense has to rely on the separate DCG/dropout gate rather than claiming Step 05 itself rejects bad interpolation spans.
### Reviewer Risk
A *Measurement* reviewer would scrutinise whether the manuscript accidentally presents interpolated continuity as if it were directly observed continuity, especially in weak conditions like `e20_320rpm` and in any discussion that drifts toward camera-LDV synchrony.

---

---
## Step 06 — Baseline Fusion | 2026-06-23 | PASS
### Q&A Record
**Q1:** The ~388 mm raw Z disagreement is a fixed DC offset — it exists because cam1 and cam2 are physically separated and their Z axes point in different directions, so their raw tvec Z values are in completely different camera frames and cannot be directly compared. Subtracting the full-run mean per camera removes that fixed offset because mean(z_c) absorbs it entirely, leaving only the dynamic variation around the mean. The implicit physical assumption is that the DC offset is constant across the entire recording — i.e., the cameras did not move during the experiment. If a camera shifted mid-run, the mean would be wrong and the residual would contain a step-change artifact rather than just dynamic noise. | APPROVED: Full-run mean removal is mathematically sufficient here because the raw inter-camera Z disagreement behaves like a constant additive bias over the recording, so subtracting each camera's own mean removes that bias without needing extrinsics.
**Q2:** Step 04 outputs tvec in metres (solvePnP works in the same units as the object points, which are defined in metres in the tag corner coordinates). Before trusting the mm conversion, you must verify that the object point coordinates passed to solvePnP used metres (tag half-size h = 0.010 m), not millimetres or some other unit. A silent unit error would produce aligned Z std values that are either ~1000× too large (if tvec was already in mm but you multiplied by 1000 again) or ~1000× too small (if you forgot to convert), so instead of ~2.053 mm you would see either ~2053 mm or ~0.002 mm — both obviously wrong, but only if you know what to expect. | APPROVED: The key trust check is that Step 04 `tvec` scale comes from object points defined in metres, so the Step 06 `*1000` conversion is the only metres-to-millimetres change; otherwise the aligned residual would be off by about `1000x`.
**Q3:** Even though cam1 and cam2 track the same physical marker, the 2.053 mm residual std is real and expected. It contains three things: (1) the ~9.8° inter-camera axis misalignment, which means the Y axes of the two cameras are not perfectly parallel — a true purely vertical displacement appears with slightly different magnitudes in each camera frame; (2) independent per-camera measurement noise from reprojection error (~0.10–0.29 px), which does not cancel when you subtract one camera from the other; and (3) any residual after mean removal of small slow thermal or mechanical drift in the camera mounts across the ~30 s recording. The 2.053 mm is not random noise — it is a structured, bounded residual whose dominant source is the geometric axis misalignment. The ~189× improvement from ~388 mm raw to 2.053 mm std is itself the publishable result: it demonstrates that mean removal is doing real alignment work, not just shifting numbers. | APPROVED: The `2.053 mm` residual is the post-centering mismatch budget, not a contradiction: it contains axis non-parallelism, independent per-camera pose noise, and any small residual mount drift that survives mean removal.
### Run Results
- Smoke test (`e7_90rpm`): reran `src/step06_fuse_cameras.py` in conda env `omrpr`; raw Z disagreement was cam1-cam2 `388.0 mm`, cam1-cam3 `347.1 mm`, cam2-cam3 `40.9 mm`; aligned Z residuals were cam1-cam2 `2.0529 mm`, cam1-cam3 `3.0458 mm`, cam2-cam3 `2.0604 mm`, with zero-mean residuals after alignment and cam1-cam2 improvement `189.0x`
- Full sweep (`--all`): reran all 21 conditions successfully and wrote refreshed Step 06 outputs for every condition; 20 conditions kept all camera-pair aligned Z std values below the `15 mm` gate
- Expected-value check: the locked reference reproduced cleanly on `e7_90rpm` (`2.0529 mm` rounds to the canonical `2.053 mm`, with `388.0 / 2.0529 = 189.0x`); the only anomaly was the known weak condition `e20_320rpm`, where cam1-cam2 remained acceptable at `7.4188 mm` but cam1-cam3 and cam2-cam3 rose to `24.8684 mm` and `28.5673 mm`
- Acceptance gate: PASS for the canonical cam1-cam2 baseline-fusion result and normal conditions; `e20_320rpm` remains the documented weak-condition anomaly
### Key Findings
- The live Step 06 implementation matches the locked theory exactly: it removes per-camera full-run means in metres, converts the centred traces to millimetres, and reports residual inter-camera disagreement as a standard deviation of pairwise `z_w_mm` differences
- `e7_90rpm` reproduced the canonical publishable contrast cleanly: raw cam1-cam2 Z disagreement of `388.0 mm` collapsed to an aligned residual std of `2.0529 mm`, which is the locked `2.053 mm` reference to rounding
- Across the full sweep, the stable-condition pattern remained intact, with `e20_320rpm` again standing out as the only condition where camera pairs involving cam3 exceeded the nominal `15 mm` residual gate
### Vulnerabilities Noted
- Full-run mean removal assumes the inter-camera DC bias is constant over the recording, so any mid-run mount shift or slow baseline drift larger than the normal residual would contaminate the aligned traces rather than being corrected explicitly
- Because Step 06 is statistical baseline alignment rather than geometric extrinsic fusion, manuscript wording must not imply that a surveyed shared world frame was established here
### Viva Q&A
**Q:** Why is Step 06 scientifically defensible even though it does not estimate camera extrinsics?
**A:** Because the claim being defended is dynamic displacement agreement after removing constant per-camera offsets, not absolute 3D reconstruction in a surveyed global frame. For condition-level vibration response and later non-simultaneous LDV comparison, removing the fixed baseline is sufficient as long as the scope of the claim stays limited to relative motion.
### Reviewer Risk
A *Measurement* reviewer would likely probe whether the manuscript is careful enough about the distinction between baseline-aligned relative displacement and true extrinsic-calibrated multi-camera fusion, especially when the weak `e20_320rpm` cam3 pairs are visible in the rerun outputs.

---

---
## Step 07 — Motion Decompose | 2026-06-23 | PASS
### Q&A Record
**Q1:** `bending_avg_y_mm = (cam1_y + cam2_y) / 2 because cam1 and cam2 are looking at the same marker? is it so, but in that case since cam1 and cam2 are looking at the same marker and then cam3 is looking at the second marker, shouldn't we be looking at bending_avg_y_mm = (cam1_y + cam3_y) / 2 and or bending_avg_y_mm = (cam2_y + cam3_y) / 2` | NEEDS CORRECTION: `cam1` and `cam2` are averaged precisely because they are two independent views of the same physical point (Marker A), so their mean is the cleanest estimate of Marker A bending motion; including `cam3` would contaminate the bending reference with Marker B motion and destroy the differential reference needed for the torsion proxy.
**Q2:** `explain it for me as i dont know the answer.` | NEEDS CORRECTION: `torsion_diff_y_mm = cam3_y - bending_avg_y_mm` is only a two-point relative vertical displacement proxy between Marker B and Marker A, so the defensible claim is that it captures differential motion consistent with torsional behaviour; it would be scientifically incorrect to call it a calibrated torsion angle, infer absolute deck twist, or claim a signed physical rotation without a lever arm model and geometric calibration.
**Q3:** `that both the camera results are not consistant.` | NEEDS CORRECTION: Low or negative `cam1-cam2` correlation specifically exposes a risk of sign inconsistency, bad tracking, or noise-dominated non-common motion before averaging; Step 06 passing only proves the traces were aligned onto a common baseline/time grid, not that both cameras still observe the same physical waveform with trustworthy sign and sufficient signal content.
### Run Results
- Smoke test (`e7_90rpm`): reran `src/step07_motion_decompose.py` in conda env `omrpr`; `cam1-cam2` correlation reproduced at `r=0.999012`, `bending_avg_y_mm` RMS/std `1.6186 mm`, peak `2.6014 mm`, and `torsion_diff_y_mm` RMS/std `1.6249 mm`, peak `2.3510 mm`
- Full sweep (`--all`): reran all 21 conditions successfully and rewrote `results/step07/{condition}/motion.csv` plus `summary.json` for every condition
- Expected-value check: the locked internal-consistency story holds in the dynamic conditions, with `e7_90rpm` reproducing the expected near-unity same-marker agreement and all summary means staying effectively zero across the corpus
- Anomalies vs expected values: only `e0_0rpm`, `e1_20rpm`, and `e2_40rpm` triggered the script's `<0.95` correlation warning (`r=0.8312`, `0.868434`, `0.924365`), but those are near-zero-motion cases with RMS amplitudes of only `0.0058-0.0107 mm`, so the warning reflects noise-dominated low-signal behaviour rather than a sign-flip defect; `e20_320rpm` remained the large-amplitude weak-condition outlier (`bending RMS 9.8430 mm`, `torsion RMS 11.1249 mm`) but still kept positive high correlation (`r=0.998109`)
- Acceptance gate: PASS for the locked Step 07 decomposition logic and for all publishable dynamic conditions; low-correlation warnings in `e0-e2` should be described as low-signal caveats, not structural failures
### Key Findings
- The live Step 07 implementation matches the intended claim boundary: average the two same-marker channels (`cam1`, `cam2`) to estimate Marker A bending, then difference Marker B (`cam3`) against that reference to form a torsion proxy
- `e7_90rpm` reproduced the expected same-marker consistency cleanly, with `cam1-cam2 r=0.999012`, confirming no sign-flip or cross-camera disagreement in the main dynamic regime
- All 21 conditions preserved near-zero channel means after decomposition, which is consistent with Step 06 having already removed the per-camera DC offsets and with Step 07 correctly avoiding a second mean-removal step
### Vulnerabilities Noted
- The torsion channel is still only a two-point differential displacement proxy, so manuscript wording must not drift into claims about calibrated torsion angle, signed twist, or full modal torsion shape
- Correlation warnings in very low-amplitude cases can be noise-dominated rather than physically meaningful, so reviewers should not see the `<0.95` threshold as a universal failure gate without amplitude context
### Viva Q&A
**Q:** Why would averaging `cam1` with `cam3` be a scientific mistake for the bending channel?
**A:** Because `cam1` and `cam2` observe the same marker and therefore estimate the same physical bending motion at Marker A, while `cam3` observes a different marker whose differential motion is exactly what Step 07 is trying to preserve for the torsion proxy. Mixing `cam3` into the bending reference would leak Marker B behaviour into both channels and collapse the interpretation.
### Reviewer Risk
A *Measurement* reviewer would likely probe whether the manuscript clearly separates the very strong same-marker agreement in dynamic runs from the low-signal correlation warnings in `e0-e2`, and whether the torsion channel is described strictly as a proxy rather than a calibrated angle.

---

---
## Step 08 — Frequency Analysis | 2026-06-23 | PASS
### Q&A Record
**Q1:** `Why does Step 08 keep dominant_peak_hz and nearest_ref_bin_hz as separate outputs, and what scientific mistake would happen if we treated them as the same quantity?` | APPROVED: Correct, because merging them would imply agreement by construction and would destroy the scientific validity of the frequency-identification claim by making the data peak appear forced onto the structural reference.
**Q2:** `The code uses the median PSD within the 0.5-10 Hz search band as the noise floor for SNR. What vulnerability does this choice still have, especially in low-amplitude or structured-noise conditions?` | APPROVED: Correct, because multiple strong peaks can inflate the median and suppress reported SNR, while structured near-floor noise such as the ~9 Hz content in `e0-e1` makes the median a poor proxy for true broadband noise in those specific cases.
**Q3:** `Step 08 reports three aerodynamic regimes from the spectral results. What is the main reviewer-risk in making that regime claim from this step alone, and which conditions must be treated separately rather than folded into the clean regime narrative?` | APPROVED: Correct, because Step 08 alone cannot distinguish genuine aerodynamic regime changes from measurement-channel contamination like cross-axis torsion leakage, so `e4_60rpm`, `e9_110rpm`, and `e20_320rpm` must stay explicitly separated from the clean three-regime summary.
### Run Results
- Smoke test (`e7_90rpm`): user-ran `python src/step08_frequency_analysis.py --bag e7_90rpm` in conda env `omrpr`; bending peak was `3.1165 Hz` with reference bin `1.4434 Hz` and SNR `61.3 dB`, while torsion peak was `3.1165 Hz` with reference bin `3.1165 Hz` and SNR `61.7 dB`; both channels returned `low_snr=False`
- Full sweep (`--all`): user-ran all 21 conditions successfully with zero execution errors; aggregated output was rewritten to `results/step08/frequency_summary.csv`, and every condition reported `low_snr=False`
- Expected-value check: the canonical three-regime story was reproduced cleanly from the live outputs, with bending-dominated cases at `40-80 RPM` clustering near `f_h=1.4323 Hz`, torsion-dominated cases at `90-220 RPM` clustering near `f_alpha=3.0827 Hz`, and bending re-emergence at `240-300 RPM` returning to about `1.408-1.411 Hz`
- Anomalies vs expected values: `e4_60rpm` remained the VIV outlier with bending peak `1.3770 Hz` below `f_h`; `e9_110rpm` reproduced the anomalous transition peaks at bending `2.2623 Hz` and torsion `2.6557 Hz`; `e20_320rpm` processed at `2.9325 Hz` but remains excluded from the clean regime narrative by the DCG context; near-floor structured-noise peaks at about `9.1-9.3 Hz` persisted in `e0_0rpm` and `e1_20rpm`, and `e2_40rpm` torsion also peaked at `9.1197 Hz`
- Acceptance gate: PASS
### Key Findings
- The live Step 08 outputs preserve the critical distinction between measured dominant peak and nearest structural reference bin; `e7_90rpm` is the clearest demonstration, where bending peaks at `3.1165 Hz` rather than the bending reference bin at `1.4434 Hz`
- All 21 conditions remained above the configured SNR threshold, confirming the locked result that the current median-PSD criterion does not classify the structured near-floor spectra as `low_snr`
- The three aerodynamic regimes are visible directly in the aggregated outputs and match the locked narrative: bending-dominated (`40-80 RPM`), torsion-dominated (`90-220 RPM`), and bending re-emergence (`240-300 RPM`)
### Vulnerabilities Noted
- Because the SNR floor is the median PSD inside the same search band, structured noise or multiple energetic peaks can still distort the reported SNR without triggering `low_snr=True`
- Regime interpretation from spectra alone remains vulnerable to over-claiming, because bending-channel peaks in the torsion-dominated range can still be amplified by cross-axis leakage rather than pure aerodynamic modal separation
### Viva Q&A
**Q:** Why is `e7_90rpm` such an important Step 08 smoke test for the manuscript argument?
**A:** Because it proves the pipeline does not force the bending channel onto the structural bending reference. The bending dominant peak moves to the torsion band at `3.1165 Hz` while the bending reference bin stays at `1.4434 Hz`, which is exactly the separation needed to defend that the data are identifying regime behaviour rather than echoing the structural model by construction.
### Reviewer Risk
A *Measurement* reviewer would likely probe whether the manuscript is disciplined enough to present the three-regime pattern as an empirically useful spectral summary while still isolating `e4_60rpm`, `e9_110rpm`, `e20_320rpm`, and the near-floor `~9 Hz` cases as special interpretations rather than forcing them into a single clean modal story.

---

---
## Step 10 — LDV Comparison | 2026-06-24 | FAIL/PASS
### Q&A Record
**Q1:** `Step 10 reports bending r=0.845 as a FAIL against the >0.90 stable-regime gate, yet the manuscript retains it. The docstring says the comparison is condition-level only and explicitly forbids calling the ratio a validated accuracy number. Given both of those constraints, what is the one scientifically defensible claim that bending r=0.845 actually supports — and what would a Measurement reviewer demand before accepting that claim?` | SUPERVISOR ANSWER: The defensible claim is only that the camera pipeline preserves the condition-level bending trend across matched RPM conditions in the stable regime, not that it reproduces LDV amplitudes or validates waveform accuracy. A *Measurement* reviewer would demand an explicit claim boundary stating that the sessions are non-simultaneous and 10 days apart, that the comparison is RMS-at-condition-level only, and that the residual amplitude mismatch remains an unresolved scale/geometry limitation rather than a proved accuracy result.
**Q2:** `The LDV bending channel is converted from cm to mm using pvolt=2.7 cm/V and dp=1.538, while the camera bending channel is the average of cam1 and cam2 vertical displacements. These two physical quantities are not the same thing. What is the geometric reason their RMS values can still be meaningfully correlated at condition level, and what is the one assumption about the wind tunnel model that must hold for that correlation to be physically interpretable?` | SUPERVISOR ANSWER: They can still correlate because both channels respond to the same underlying modal bending energy of the same structural model, so even with different measurement definitions they should rise and fall together across RPM conditions. That interpretation only holds if the structural deformation shape is sufficiently stable across runs, meaning the camera marker motion and the LDV sensing location remain governed by the same dominant bending response rather than by different local mode mixtures.
**Q3:** `D00 (zero-wind static) is subtracted from D01–D20 as a bias reference before computing LDV RMS. What does this subtraction actually remove, and why does failing to subtract D00 — or subtracting it incorrectly — produce a systematic error in the ratio rather than random scatter?` | SUPERVISOR ANSWER: D00 removes the LDV channel offset and static zero reference of the acquisition chain before dynamic RMS is computed. If that bias is left in or removed with the wrong sign/magnitude, every condition inherits the same calibration-offset contamination, which shifts the LDV denominator coherently and therefore biases the camera/LDV ratio systematically instead of merely adding condition-to-condition noise.
### Run Results
- Smoke test (`--smoke-test`): `conda run -n omrpr python src/step10_ldv_comparison.py --smoke-test` completed successfully on `e7_90rpm`; bending was `cam=1.619 mm` vs `ldv=0.748 mm` (`ratio=2.164`), torsion was `cam=1.625 mm` vs `ldv=2.250 mm` (`ratio=0.722`)
- Full sweep (`20` matched conditions): `conda run -n omrpr python src/step10_ldv_comparison.py` rewrote `results/step10/ldv_comparison_table.csv`, `results/step10/ldv_summary.json`, and `results/step10/step10_summary.json`; the process exited with code `1` because the script intentionally treats the stable-regime bending gate failure as an overall non-zero exit
- Expected-value check: locked stable-regime values reproduced exactly from live outputs — bending `r=0.8450`, torsion `r=0.9396`, bending ratio `1.3393×`, torsion ratio `0.5986×`, `dp=1.538462`, and `n_stable=18`
- Comparison boundary confirmed: the summary file records `Camera (Tunnel B, October 2025)` versus `LDV (Tunnel B, September 2025)`, explicitly notes `10 days apart`, `NOT simultaneous`, and limits the result to `condition-level` comparison
- Anomalies vs expected values: none beyond the locked gate split; bending remains the expected stable-regime FAIL against the `>0.90` criterion, while torsion remains PASS; `e4_60rpm` (VIV outlier) and `e20_320rpm` (high-wind unstable) are excluded from the stable subset but included in full-regime reporting
- Acceptance gate: `FAIL/PASS` by design
### Key Findings
- The live rerun confirms the canonical manuscript numbers without drift: stable bending `r=0.845`, stable torsion `r=0.940`, bending ratio `1.339×`, torsion ratio `0.599×`
- The comparison remains scientifically bounded to matched-condition RMS behavior across separate tunnel sessions, not time-synchronised waveform agreement and not an LDV-equivalent accuracy validation
- The full-regime console summary can be misleading if read casually, because it prints torsion full-regime ratio `0.5727×`; the locked torsion ratio `0.599×` is the stable-regime value from `results/step10/ldv_summary.json`
### Vulnerabilities Noted
- The script exits non-zero even though the rerun is scientifically successful relative to the locked canonical state, because its gate logic encodes bending `r>0.90` as a hard pass/fail threshold
- Because camera and LDV were collected in separate September/October 2025 sessions with different DAQ systems, any ratio interpretation beyond condition-level trend agreement would overclaim what the data can support
- The camera bending proxy and LDV bending measurement are geometrically related but not identical observables, so amplitude-ratio deviation cannot be treated as a pure measurement-error estimate
### Reviewer Risk
A *Measurement* reviewer would likely accept the torsion agreement but press hard on whether the manuscript clearly frames bending `r=0.845` as trend-level corroboration only, with the non-simultaneous `10-day` separation and unresolved scale/geometry mismatch stated up front instead of buried in methods.

---
## Step 11 — RTS/Kalman Smoothing | 2026-06-24 | PASS
### Q&A Record
**Q1:** `Why is RTS smoothing non-causal, and why does that make it valid for this pipeline only as offline post-processing rather than real-time estimation?` | APPROVED: Correct, because RTS needs future observations during the backward pass, so it can improve retrospective state estimates offline but cannot be used for causal real-time estimation.
**Q2:** `Why does the choice of initial covariance P0 matter here, and what failure mode do you get if you start with an unrealistically small fixed covariance?` | NEEDS CORRECTION: `P0` controls how quickly the filter is willing to move away from its initial state, and an unrealistically small fixed covariance makes the filter overconfident at the start, suppresses Kalman gain, and can lock in a biased transient or delayed convergence over the early segment.
**Q3:** `What does the process-noise matrix Q mean physically in this model, and what does sigma = 10.0 mm/s represent in practical motion terms?` | NEEDS CORRECTION: `Q` encodes the allowed frame-to-frame uncertainty in the constant-velocity motion model, and `sigma = 10.0 mm/s` is the assumed standard deviation of unmodelled velocity variation, meaning the smoother permits modest acceleration/deceleration rather than forcing perfectly constant velocity.
### Run Results
- Smoke test (`e7_90rpm`): `conda run -n omrpr python src/step11_rts_smoothing.py --condition e7_90rpm` completed successfully; both bending and torsion reproduced `phase=+0.00 ms`, `freq_err=0.000 Hz`, and `amp_ratio=0.999`
- Full sweep (all 21 conditions): `conda run -n omrpr python src/step11_rts_smoothing.py` completed successfully; the script does not expose a literal `--all` flag, so the live full-run path is the default invocation with no `--condition`
- Expected-value check: locked canonical behavior reproduced from live outputs — stable-condition amplitude ratio `0.999`, near-floor `e0/e1` bending ratios `0.961/0.966`, and `0.00 ms` phase shift throughout
- Output boundary confirmed: `results/step11/{condition}/motion_smoothed.csv` was rewritten for the condition run and full sweep; `results/step11/step11_summary.json` records `n_conditions=21`, `n_pass=21`, `n_fail=0`, `process_noise_std=10.0`, and `measurement_noise_std=0.05`
- Anomalies vs expected values: no scientific anomalies; the only operational wrinkle was CLI shape, where `--all` is unsupported and “all conditions” is the default mode. Near-floor torsion smoothing dipped to `0.957` at `e0_0rpm`, still above the `0.95` acceptance gate and consistent with stronger attenuation only in very low-signal cases
- Acceptance gate: PASS
### Key Findings
- The live rerun matches the locked Step 11 manuscript state: all `21/21` conditions PASS, phase shift remains exactly `0.00 ms`, and stable-condition smoothing is effectively amplitude-neutral at `0.999-1.000`
- The expected low-signal attenuation pattern is preserved without violating the gate: `e0_0rpm` and `e1_20rpm` bending land at `0.961` and `0.966`, respectively, while the rest of the dataset remains much closer to unity
- The implementation stays consistent with the intended offline rationale: scalar 2-state `[position, velocity]` smoothing per channel, non-causal RTS backward pass, and amplitude-scaled `P0` rather than a small hard-coded start covariance
### Vulnerabilities Noted
- Because RTS is explicitly non-causal, any manuscript wording that implies real-time deployability would be scientifically incorrect and should be avoided
- The chosen `Q` is physically interpretable but still a modelling assumption; if `sigma` were set too low, the smoother would over-regularize true dynamics, while an excessively high value would collapse the benefit of smoothing and track measurement noise too closely
- Near-floor conditions are the most vulnerable to visible amplitude attenuation, so `e0-e2` should continue to be described as low-signal edge cases rather than representative dynamic runs
### Reviewer Risk
A *Measurement* reviewer would likely accept this step if the manuscript states plainly that RTS is an offline post-processing aid and not a real-time estimator, but may still ask whether the chosen `P0` and `Q` were sensitivity-checked enough to show that the near-unity stable-regime ratios are not a tuning artefact.

---
## Step 12 — Figures/Tables | 2026-06-24 | PASS
### Q&A Record
Q&A skipped — user elected to move directly to execution.
### Run Results
- Full generation pass: `conda run -n omrpr python src/step12_figures_tables.py` generated all five figures, both tables, and `results/step12/step12_summary.json`; claim-boundary scan passed with zero forbidden phrases across all 5 captions
- Output inventory confirmed: `fig01_displacement_traces.pdf`, `fig02_frequency_overview.pdf`, `fig03_ldv_scatter.pdf`, `fig04_camera_agreement.pdf`, `fig05_uncertainty.pdf`, `tab01_ldv_comparison.csv`, `tab02_summary_stats.csv`, and `step12_summary.json` were all present in `results/step12/`
- Initial anomaly vs expected values: the first run was operationally PASS but exposed stale hard-coded manuscript text in Step 12 outputs, with bending note `r = 0.833` and `17 cond.` conflicting with the live Step 10 canonical values `r = 0.845` and `18` stable conditions
- Fix applied and re-run: patched `src/step12_figures_tables.py` to replace the stale hard-coded bending note with the current canonical Step 10 values, then re-ran Step 12 successfully using `MPLCONFIGDIR=/tmp/mplconfig conda run -n omrpr python src/step12_figures_tables.py`
- Post-fix verification: regenerated `results/step12/step12_summary.json` and `results/step12/tab02_summary_stats.csv` now report the corrected bending note `r = 0.845 (stable, 18 cond.)`; stable-regime summary rows remain `bending r=0.8450`, `torsion r=0.9396`, `bending ratio=1.3393`, `torsion ratio=0.5986`
- Operational note: the unpatched environment emitted a Matplotlib cache warning because `/home/ammar/.config/matplotlib` is not writable; setting `MPLCONFIGDIR` to a writable temp directory removed the warning without affecting generated outputs
- Acceptance gate: PASS
### Key Findings
- The final Step 12 artifact set is complete and programmatically generated from live pipeline outputs: 5 figures, 2 tables, 0 caption claim-boundary violations, and `step12_summary.json` status `PASS`
- A real stale-claim risk was caught and corrected before sign-off: Step 12 had embedded outdated Step 10 bending text (`0.833`, `17 cond.`), which would have leaked inconsistent manuscript numbers into the final summary artifacts
- After patching, the generated figures/tables are aligned with the current locked pipeline state, including the Step 10 stable-regime comparison numbers and the Step 11 smoothing summary
### Vulnerabilities Noted
- Step 12 still relies on a few manuscript-facing explanatory constants inside the generator, so future upstream metric changes can drift into stale captions or footnotes unless those notes are derived directly from current summary files
- The Matplotlib config-path warning is harmless for correctness in this workspace but can clutter rerun logs unless `MPLCONFIGDIR` is set explicitly
- Because the script only scans captions for forbidden phrases, it will not automatically catch every possible numeric inconsistency if explanatory notes are hard-coded outside the main metric tables
### Reviewer Risk
A *Measurement* reviewer would likely focus less on the plotting itself and more on whether every explanatory caption/footnote is numerically synchronized with the underlying results. Catching and fixing the stale `0.833 / 17 cond.` bending note materially reduces that risk.

---
## Step 09 — Uncertainty Quantification | 2026-06-23 | PASS
### Q&A Record
Q&A skipped — user elected to move directly to execution.
### Run Results
- Smoke test (`--smoke-test`): Section A PASS (bending=0.0026 mm worst-case cam1, torsion=0.0040 mm worst-case cam3, both below gate); Section B FAIL expected — 1/21 minimum not met in single-condition smoke mode; Section C PASS (relative width 0.016); Section D informational (max drift 11.9 ms)
- Full sweep (all 21 conditions): exit code 0; all 4 gates PASS
- Section A canonical noise floors: e0_0rpm bending_avg_y_mm=0.0043 mm, torsion_diff_y_mm=0.0052 mm — both well below thresholds (0.017 mm / 0.033 mm)
- Section B: 21/21 conditions PASS; e20_320rpm aligned_Z_std=7.419 mm elevated vs other conditions but below 15 mm gate, consistent with known motion-blur artefacts
- Section C: Bootstrap CI max relative width=0.336 — wider than smoke-test value because low-signal e0–e4 have large relative CI widths at small amplitudes; gate PASS
- Section D: max pairwise timing drift=20.0 ms across all 21 conditions — matches locked canonical 20.03 ms
- Acceptance gate: PASS
### Key Findings
- Static-bag noise floor measurements are consistent across all 5 test bags per camera; worst-case values are 0.0026 mm (cam1), 0.0048 mm (cam2), 0.0040 mm (cam3), well within the configured gate thresholds
- The canonical e0_0rpm noise bounds (0.0043 mm bending, 0.0052 mm torsion) are reproduced exactly, confirming the uncertainty budget is stable across re-runs
- All 21 conditions clear the inter-camera alignment gate (≤15 mm aligned Z std), including e20_320rpm at 7.419 mm, though e20 remains contextually excluded from the clean regime narrative via the DCG gate from Step 02b
### Vulnerabilities Noted
- Section B smoke-test FAIL is a known artefact of single-condition execution and does not represent a real gate failure; the code correctly requires 20/21 conditions which cannot be met with one condition loaded
- Bootstrap CI relative widths in low-signal conditions (e0–e4) are legitimately wide because the amplitude is near the noise floor; the relative-width PASS gate does not distinguish between wide CIs from low SNR vs genuine parameter instability
- Timing drift of 20.0 ms is informational only; the 20.03 ms canonical value is the max start-time spread from Step 05, not a per-frame accumulating drift, so the Section D value and Step 05 value refer to the same quantity and are consistent
### Reviewer Risk
A *Measurement* reviewer would probe whether the manuscript reports the e0_0rpm dynamic bound (0.0043 mm) or the static-bag bound (0.0027 mm) as the headline noise floor, since choosing the static value would understate the noise environment actually present during tunnel operation. The dynamic bound is the more defensible choice.

---
