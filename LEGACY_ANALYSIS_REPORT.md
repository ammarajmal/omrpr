# OMRPR Legacy Codebase Analysis — Report Before Rewrite

**Date:** 2026-07-21
**Purpose:** Full-pipeline audit of `/mnt/data/DEV/shm-displacement-project` (188GB) and `/mnt/data/DEV/shm-displacement-project-backup` (97GB), plus the ffix Logseq PhD notes (`/mnt/space/ffix/pages/LifeOS/Realms/PhD/OMRPR*`), conducted before writing any new code in this repo. Nothing in the legacy directories or ffix notes was modified — read-only survey. This document is the single reference to consult while designing and writing the new pipeline.

**Scope covered:** bag capture → bag audit → AprilTag detection → calibration → multi-camera fusion → sync/resampling → motion decomposition (bending/torsion) → frequency analysis → uncertainty quantification → LDV condition-level comparison → RTS smoothing. I.e. the full legacy pipeline, not just the bag-reading stage, per the "full pipeline, everything" scope decision.

---

## 0. Top-Level Verdict

The legacy implementation is **empirically productive but methodologically inconsistent** — it produced real, non-trivial results (static noise floor ~0.02mm, condition-level LDV Pearson correlation up to 0.96, a genuine VIV physical finding at 60RPM) but arrived there through three different AprilTag detector stacks, at least three disagreeing camera-intrinsics sources, two different wind-tunnel LDV geometry conventions silently mixed together, and a frequency-validation reference constant borrowed from an unrelated bridge model. None of this invalidates the underlying experiment — the raw bag data and the wind-tunnel/LDV hardware are fine — but it means **no single legacy script or config file should be trusted as ground truth without cross-checking against this report**, and the new pipeline should re-derive camera intrinsics and re-confirm LDV geometry from scratch rather than importing any legacy YAML.

The most consequential, load-bearing finding is **§1 — camera intrinsics are almost certainly wrong across every legacy source**, because everything downstream (pixel-to-mm conversion, uncertainty budget, noise floor, LDV comparison) depends on it.

---

## 1. CRITICAL: Camera Intrinsics — Confirmed Broken, Recalibrate From Scratch

Three independent research agents converged on the same finding via different files:

| Source | cam1 fx/fy | cam2 fx/fy | cam3 fx/fy |
|---|---|---|---|
| `sony_camN_info.yaml` / `camera_info.yaml` (**actually used in every production run and export**) | 20327.9 / 20240.8 | 25749.5 / 25819.0 | 25630.9 / 25590.6 |
| `data/calib_data/camN/ost.yaml` (raw `camera_calibration` output) | 34519.98 / 34244.11 | 28089.76 / 28016.08 | 38189.99 / 37888.57 |
| `data/calib_data/camN/sony_camN_recalib.yaml` (recalibration attempt) | 36498.25 / 36154.0 | 23006.95 / 22100.87 | 30497.53 / 30178.10 |

**All nine numbers are physically implausible.** A 1920×1080 sensor with any normal lens should show fx/fy in roughly the 1500–3500 px range (Sony RX10 IV at 600mm-equivalent zoom, ~5.4° FoV, could plausibly reach a few thousand px — but not 20,000–38,000). This is consistent across three independently-computed sources, which rules out a one-off typo and points to a systematic calibration bug — most likely a checkerboard **square-size unit error**: `calibcheckper.py` hardcodes `square_size = 0.006` (6mm) with a 6×7 inner-corner board; if the physical squares were actually a different size (a very plausible mix-up, e.g. cm vs mm, or wrong board entirely), the solver would converge on a degenerate huge-focal-length solution that still reprojects "acceptably" on the calibration images while being physically wrong.

Additional hygiene problems found in the recalibration files: `sony_cam2_recalib.yaml` internally mislabels itself `camera_name: sony_cam3`. `cam1` has three separate calibration attempt folders (`cam1`, `cam1_old`, `cam1_try1`) — repeated failed recalibration. `docs/archive/calibration_protocol.md` describes an aspirational protocol with no actual numbers/dates, clearly not what was followed.

A fourth number was flagged in the ffix Logseq "Critical Revision Roadmap" note: a claim that `step09_uncertainty.py` hardcodes `fx=fy=2108` px while `pipeline_config.yaml` has the ~20k-25k values above. **This specific file pair does not exist anywhere in the 188GB tree** (confirmed by exhaustive `find`/`grep`, including a full-text search for `2108`) — either it refers to a different/deleted script, or the reviewer who wrote that roadmap note was working from a state of the repo not present in this snapshot. Do not chase this specific number further; the broader problem (intrinsics are wrong) is independently proven without it.

**Action for rewrite:** Do not import any legacy intrinsics file. Recalibrate all three cameras from scratch with a verified, correctly-measured checkerboard/Charuco pattern, sanity-check that fx/fy land in the 1000–4000px range for the actual lens/zoom setting used, and gate on reprojection error (legacy docs disagree on the threshold — one says <0.25px, another says <1.0px good / >3.0px suspicious — pick one deliberately and document it, don't inherit either blindly).

---

## 2. CRITICAL: Two Wind Tunnels Were Silently Conflated

This is the single most consequential documentation-mining finding, and it explains several downstream numeric puzzles.

- **Tunnel A** (2024 campaign — this is where the **camera/WTT bag data actually came from**, confirmed via wind-speed calibration formula `U = RPM × 0.01845 − 0.26077` matching the bag metadata): LDV files `D0–D38`, non-uniform RPM steps, 30s/run, LDV geometry `dside=10cm, db=20cm, dp=db/dside=2.0`.
- **Tunnel B** (2025 campaign — this is where the **LDV reference values actually came from**, confirmed by exact value match to `D01=0.112mm, D03=0.114mm, D05=2.908mm`): LDV files `D00–D20`, uniform 20-RPM steps, 20s/run, LDV geometry `dside=13cm, db=20cm, dp=1.538`.

The torsion-proxy formula also differs structurally between the two tunnels (Tunnel A does not divide by 2 before pvolt conversion; Tunnel B does). **Using one tunnel's formula/geometry on the other tunnel's data silently produces wrong torsion numbers.** This was correctly resolved once (2026-06-10, documented in `memory/ldv_geometry_facts.md` and `memory/ldv_results_table.md`, both using the correct Tunnel B `dp=1.538`) — but the offline-processing audit script `audit_torsion_geometry_and_ldv_proxy.py` and the newest planning document `OMRPR_SUPERVISOR_PROMPT.md` (written *after* the resolution date) **both still use the wrong Tunnel A value `dp=2.0`**. The fix did not fully propagate.

**Action for rewrite:** use `dside=13cm, db=20cm, dp=1.538` for any LDV torsion-proxy geometry calculation. Treat `memory/ldv_geometry_facts.md` as authoritative over `OMRPR_SUPERVISOR_PROMPT.md` on this specific number.

---

## 3. CRITICAL: Frequency-Validation Reference Constants Are From a Different Bridge

`phase3_frequency_analysis.py` and `analyze_dominant_frequency_behavior.py` both validate detected dominant frequencies against a hardcoded reference: **bending 1.95Hz, torsion 5.15Hz** (from the Lee2016 SPIE paper describing the wind-tunnel facility class). But that paper's bridge-deck model has a **34.4cm chord**, while this project's actual model has a **confirmed 40cm chord** — a different physical specimen. The real measured natural frequencies for *this* model, cross-confirmed by 6 independent legacy sources to within 0.001Hz, are:

**f_h (bending) = 1.430 Hz, f_α (torsion) = 3.103 Hz, frequency ratio 2.17, damping ≈1.9%**

(vs. Lee2016's model: 1.95Hz / 5.15Hz / ratio 2.64 / damping 0.28–0.13% — visibly a stiffer, more lightly-damped different structure). Every "dominant frequency vs reference" pass/fail check in the legacy paper2 results was silently checking against the wrong structure's modes. Interestingly, the actual measured dominant frequencies in the real data (median stable bending 2.262Hz, median stable torsion-proxy 3.046Hz) sit closer to the *correct* torsion reference (3.103Hz) than to the wrong one (5.15Hz) — so the underlying signal was likely fine, but the automated "does it match reference" labeling logic was working from the wrong yardstick throughout.

**Action for rewrite:** if reintroducing a reference-frequency sanity check, use 1.430Hz / 3.103Hz (this model's confirmed natural frequencies), not the Lee2016 values, unless deliberately comparing against Lee2016's paper as external literature.

---

## 4. AprilTag Detection — Three Different Stacks Were Used, None Is the Official C Library

Confirmed across all four research agents — **the official AprilRobotics `apriltag` C library was never used anywhere in the legacy codebase**, despite this being the user's explicit requirement for the new pipeline:

| Code path | Detector | Notes |
|---|---|---|
| `scripts/static_tests/**` (all current, cam2_working, and old/ variants) | `cv2.aruco`, `DICT_APRILTAG_36h11` | No confidence/decision-margin filtering anywhere — accepts any detection where `ids is not None`. Only `tvec` saved; `rvec` computed but discarded everywhere. |
| `scripts/dynamic_test/**` (WTT pipeline, production) | `cv2.aruco`, `DICT_APRILTAG_36h11`, with a runtime API-compat shim | Same tag family/size, but has a real historical bug trail (see §7) around the OpenCV 4.7 API break (`estimatePoseSingleMarkers` removed). |
| `offline_processing/scripts/detect_apriltag.py` | `pupil_apriltags` | Params: `quad_decimate=1.0, quad_sigma=0.8, refine_edges=True, decode_sharpening=0.25` — useful as a reference point for equivalent official-`apriltag` C-library flags, but this exact library is the one the user has explicitly ruled out. |

Tag family is consistently `tag36h11` everywhere. **Tag size is consistently `0.020m (20mm)` in every code path that actually runs** — a separate, real bug existed only in *documentation* (an early manuscript draft and `TESolution_Critical_Data_Analysis.md` inherited Paper 1's 80mm tag size and applied it to Paper 2's actual 20mm tags; this was caught and corrected 2026-06-10, and never actually reached the code).

`cv2.aruco`'s `DetectorParameters_create()` (old API) / `ArucoDetector` (new API) has **no equivalent to `apriltag`'s `decision_margin` confidence score** — false-positive detections were never filterable in the legacy pipeline. This is a genuine capability gap that switching to the official `apriltag` C library will fix, and is a good concrete justification for the migration already underway in this repo (before the nuclear reset) via `environment/build_apriltag.sh`.

One tuned-but-never-adopted parameter set exists in a debug-only script (`old/detect_one_bagfile.py`): `cornerRefinementMethod=CORNER_REFINE_SUBPIX, adaptiveThreshWinSizeMin=3, Max=23, Step=10, minMarkerPerimeterRate=0.01, maxMarkerPerimeterRate=4.0, polygonalApproxAccuracyRate=0.03`.

---

## 5. WTT Two-Marker Setup — Confirmed Details and a Real Production Bug

Confirmed: **Marker A** (tag ID 0) viewed by cam1+cam2 (stereo-capable), **Marker B** (tag ID 1) viewed by cam3 (monocular). Marker spacing ≈200mm (operator-confirmed, not independently measured — the torsion-geometry audit explicitly calls this out as `BLOCKED_BY_GEOMETRY_UNCERTAINTY`, an unconfirmed provisional assumption). Recording distance is inconsistently documented as "~2.5m" (one doc) vs "3–4m target" (another doc, possibly an aspirational spec rather than as-built) — worth re-measuring and documenting precisely in the new project.

**Production bug, confirmed by direct code read:** `fuse_detections_wtt.py`, which is what `run_full_pipeline_wtt.py` (the actual end-to-end driver script) calls, **does not filter fused detections by tag ID at all** — it timestamp-matches and averages whatever tag any camera detected into one `fused_detections.csv` per run, regardless of which physical marker it came from. This is only safe because in practice cam1/cam2 apparently never see tag 1 and cam3 never sees tag 0 — but it's an implicit, unenforced assumption, not a designed guarantee. A proper two-marker-aware code path exists (`extract_motion_modes.py --phaseb-base-dir` with explicit `--marker1-tag-id`/`--marker2-tag-id`) but **was never wired into the production full-replay run.**

**Consequence — torsion is not what it sounds like in the actual results.** `run_step5_full_replay.py`'s own quality metadata records `"torsion_source": "single_marker_z_proxy"` for the full 21-condition sweep — i.e. the shipped "torsion" numbers are a proxy derived from a *single* marker's z-displacement via `arctan2(Δz, lever_arm=0.10m)`, filtered/normalized, **not** a true two-marker differential angle, even though the two-marker code path (`z_signal = marker2_z − marker1_z`) exists and is documented elsewhere as the intended approach. This matches and is independently confirmed by the `BLOCKED_BY_GEOMETRY_UNCERTAINTY` decision in the offline-processing torsion audit, and by every claim-boundary document insisting "torsion is a proxy, not a validated angle."

**Action for rewrite:** always fuse per tag ID explicitly, never pool across tags. Decide up front whether the new pipeline computes true two-marker differential torsion (now that both markers' setup is well understood) or continues with a documented single-marker proxy — but make the choice explicit and traceable in code, not implicit.

---

## 6. Bag Capture Protocol

**Static tests:** topics `/sony_{cam}/image_raw` (**raw, uncompressed** — different from WTT) + `/sony_{cam}/camera_info`. Bag naming `static_{cam}_test{N}.bag`. Current script: `num_runs=5, duration=10s`; an earlier `gen_.sh`-based version used `num_runs=10, duration=10s` — inconsistent across iterations, pick one for the new project. Plain `rospy.Subscriber` writes to `rosbag.Bag`, keyed on `msg.header.stamp`.

**WTT tests:** topics `/sony_cam{1,2,3}/image_raw/compressed` + `/sony_cam{1,2,3}/camera_info` (**compressed**, unlike static). 21 conditions `e0_0rpm` through `e20_320rpm` (RPM sweep 0→320 in mostly-20-RPM steps, full list in the bag-naming table below), `DURATION=31s`, `NUM_RUNS=1`/condition, `SAVE_MODE="grouped"` (single combined bag per run via `rosbag record`, all 3 cameras). Capture tool is a bare interactive CLI (`input("Press ENTER...")` + `subprocess.Popen(["rosbag","record",...])`), **not** a CustomTkinter GUI as one ffix note claimed — an exhaustive grep across both legacy directories found zero references to `customtkinter`; treat that specific ffix claim as unconfirmed/likely misremembered from an even earlier iteration not present in this snapshot.

**Bag-naming → physical meaning table (WTT, 21 conditions):**
```
e0_0rpm, e1_20rpm, e2_40rpm, e3_50rpm, e4_60rpm, e5_70rpm, e6_80rpm, e7_90rpm, e8_100rpm,
e9_110rpm, e10_120rpm, e11_140rpm, e12_160rpm, e13_180rpm, e14_200rpm, e15_220rpm,
e16_240rpm, e17_260rpm, e18_280rpm, e19_300rpm, e20_320rpm
```
RPM→wind-speed calibration (Tunnel A, matches the actual bag data): `U = RPM × 0.01845 − 0.26077` m/s. A separate hardcoded lookup table (20 discrete points, 0.0–5.648 m/s) also appears in analysis scripts — prefer the formula, cross-check against the table.

`e20_320rpm` is the flutter/near-instability regime and is **always excluded from stable-regime statistics** in the legacy analysis — carry this convention forward.

A distinct, unrelated older dataset (`data/micrometer_bags`, naming `1e50rmp`...`7e300rmp` — note the "rmp" typo) predates the `e{N}_{RPM}rpm` convention and uses different scripts (PlanA/PlanB/rest) — do not confuse with the main WTT sweep.

---

## 7. Bag Audit / Integrity Checking — Exact Thresholds to Reuse

The ffix Logseq notes contain a fully worked, paper-ready algorithm spec for this stage (Step 00) — reproduced here since it's the most directly reusable artifact found in the entire investigation:

```
bag_start_ns = min timestamp across ALL topics across ALL messages   (global min, not per-topic)
t_normalized[i] = (timestamp_ns[i] - bag_start_ns) / 1e9
fps = (count - 1) / duration        # interval-based: N frames = N-1 intervals
max_gap_s = max(consecutive timestamp differences)
skew = max(first_s across topics) - min(first_s across topics)

Acceptance:
  FAIL if fps < 55 or max_gap > 0.5s   → return immediately, no further topics checked
  WARN if fps outside [59,61] or max_gap > 0.1s   → accumulate, do NOT return early
  else PASS
```
Two documented bugs to avoid repeating: (1) don't trust library-exposed start/end-time attributes for `bag_start_ns` — compute it directly from message timestamps, since the `rosbags` API isn't guaranteed to expose those attributes consistently; (2) don't `return` on the first WARN — a later topic could still be FAIL, and an early WARN return would mask it. Only FAIL short-circuits.

The actual production WTT integrity script (`STEP2_CHECT_WTTBAGS.py`) has additional concrete thresholds:
- `EXPECTED_DT = 1/60s`, `DROP_THRESH = 1.5 × EXPECTED_DT` ≈ **25ms** — any gap exceeding this counts as a dropped frame.
- Reports FPS two ways (`fps_ros` from message timestamps vs `fps_bag` from bag metadata) — divergence flags a bag-metadata inconsistency.
- **Weakness to fix in the rewrite:** cross-camera sync in this script uses **naive positional truncation** (`stamps_c1[:min_len]` vs `stamps_c2[:min_len]`), not real timestamp-based nearest-neighbor matching — this silently misaligns everything downstream of the truncation point if cameras drop different frame counts.

Static-test integrity checking (`step2_check_integrity.py`) is purely descriptive — computes `fps_mean/std/min/max` per bag via `1/diff(timestamps)`, no pass/fail gate at all. A more complete variant (`old/capture_bags_step1.py`, cam2) computed `frames_expected` vs `frames_dropped` at capture time — **this drop-accounting logic regressed and is absent from the "current" production capture script**, worth restoring.

Real captured example (from ffix notes, `e7_90rpm_run1.bag`): all 3 cameras 59.94–60.00Hz, all gaps <0.03s, timestamp skew 12.4ms (cam2 starts 12.4ms after cam1/cam3 due to serial launch order — a deterministic, correctable offset, not a hardware fault). Result: PASS.

---

## 8. Calibration Reprojection Check

`calibcheckper.py` (byte-identical copy-paste across `cam1/cam1_old/cam1_try1/cam2/cam3` — never parameterized) hardcodes `square_size=0.006m` (6mm), board `(6,7)` inner corners — this is the suspected root cause of the intrinsics bug in §1. **Critically, the actual static-test detection scripts don't even load intrinsics from `data/calib_data/` — they load from an external path (`/home/ammar/tesol_ws/src/sony_cam/config/sony_{cam}_info.yaml`) not present in this disk snapshot, meaning the intrinsics actually used during real detection runs can't be independently verified from this repo at all.** This reinforces §1's recommendation: don't trust any legacy calibration artifact, redo it.

Legacy docs disagree on calibration methodology itself: one doc says checkerboard, two others say Charuco-based — another sign this process was not tightly version-controlled or documented consistently.

Camera extrinsics (`multi_cam_extrinsics.yaml`, used for world-frame transforms) look internally sane by contrast — no obvious inconsistency found: `cam2→cam1` translation ≈ `[0.247, 0.052, −0.242]`m, `cam3→cam1` translation ≈ `[−0.110, 0.024, −0.073]`m, near-identity rotation blocks.

---

## 9. Multi-Camera Fusion — Actual Algorithm (Not True Triangulation)

Despite naming (`weighted_triangulation`, `fuse_multiview.py`), the production fusion method is **not** geometric multi-view triangulation from 2D pixel correspondences. Each camera independently computes a full monocular 3D pose via `solvePnP` (using the known tag size for metric depth), transforms it into cam1's world frame via the 4×4 extrinsics, and then the multiple per-camera world-frame estimates are combined by a **quality-weighted arithmetic mean** (`score = decision_margin × sqrt(tag_area_px²)` as weight). A true stereo-triangulation variant (`cv2.triangulatePoints` on 2D pixel centroids) exists only in superseded debug scripts (`analyze_wtt.py`, `debug_cam12_wtt*.py`), never adopted into production.

A **baseline-alignment correction** is applied before fusion: the first 120 synchronized frames establish a per-camera median position bias relative to cam1, which is then subtracted from every subsequent frame. This step is important and effective — raw cross-camera Z disagreement was 106–115mm (looks catastrophic) but is actually a fixed per-camera extrinsic bias; after baseline alignment it drops to 1–15mm (a ~61× improvement, 20/21 runs pass a <10mm gate; the one failure is the high-wind `e20_320rpm` condition). **Always report both raw and aligned numbers — the contrast is itself meaningful evidence, not noise to hide.**

Sync tolerance for matching frames across cameras during fusion is **inconsistent across script generations**: 25ms in the final `fuse_detections_wtt.py`, 5ms in an older `step3a_extract_and_fuse.py`. 25ms ≈ 1.5 frames at 60Hz is the more permissive, final choice — pick one deliberately for the rewrite rather than inheriting whichever script you happen to copy from.

---

## 10. Sync / Resampling to Common Grid

The full per-run alignment pipeline (`sync_and_interp.py`, current/active) does, in order: (1) per-camera RTS smoothing first (see §11), (2) timestamp normalization to bag-start, (3) build a master 60Hz grid from the reference camera's own timestamps, (4) windowed cross-correlation drift/offset estimation (5s windows, 2s hop) fit to a linear `a·t+b` correction, (5) `np.interp` resample onto the master grid, (6) sub-sample fractional-delay refinement via parabolic peak interpolation.

**A live bug exists in `sync_and_interp_backup.py`** (the non-active variant): its `_load_and_smooth` signature was refactored to drop the `process_var`/`meas_var`/`auto_normalize` parameters, but `main()` was never updated to match — calling it would raise `TypeError`. Don't port this file as-is; it's a stale half-finished refactor. Its normalization approach (independent per-camera `t0`, rather than shared epoch-scale detection) is also a subtly worse design than the active version's — another reason to base the rewrite on `sync_and_interp.py`, not the backup.

`fractional_delay.py` has a **dead-code trap**: `apply_fractional_delay` uses plain `np.interp` on a shifted index, while the module also defines `lagrange_fd_coeffs()` (a proper Lagrange-FIR fractional-delay filter) that is **never actually called**. The "fractional delay correction" in the real pipeline is really just shifted linear interpolation, not the bandlimited filter the function name implies — decide deliberately whether the new pipeline needs true fractional-delay filtering or whether linear interpolation is sufficient, don't assume the legacy name reflects the legacy behavior.

`offline_processing/configs/default.yaml` is a decoy — contains only `default_config: true`, no real parameters; every legacy script's actual defaults live in its own CLI argument definitions, scattered and undocumented centrally.

An independent, separately-built common-grid layer also exists (`audit_timing_and_resampling_consistency.py`, Paper2 Step 04b) that resamples directly from detection timestamps onto both 60Hz and 100Hz grids and applies FFT low-pass (10Hz cutoff) + baseline detrending — this script's conclusion was that plain nearest-neighbor timestamp matching was nearly as good as full common-grid resampling for this project's purposes (bending/torsion RMS differences stayed small). Worth knowing this was empirically tested and didn't need to be over-engineered.

---

## 11. RTS Smoother — Exact Parameters to Reuse or Re-Justify

Constant-velocity 1D-per-axis Rauch–Tung–Striebel smoother (state = [position, velocity], block-diagonal across x/y/z axes):
```
F(dt) = [[1, dt], [0, 1]]
Q(dt, q) = [[dt³/3, dt²/2], [dt²/2, dt]] × q          # process noise, spectral density q
R = diag(meas_var)                                     # measurement variance per axis

Defaults: process_var (q) = 1e-3, meas_var (R) = 1e-2
```
Handles non-uniform `dt` (falls back to median positive `dt`, then `1/60s`, if `dt≤0`) and missing/NaN measurements via predict-only steps. Initial velocity variance is set uninformatively large (`1e3`) since there's no prior on starting velocity. These process/measurement noise values were never re-derived from actual sensor noise characteristics in any doc found — they read as reasonable defaults, not empirically justified constants. **Recommend re-deriving `meas_var` directly from the new pipeline's own static noise-floor measurement** (§12) rather than reusing `1e-2` blindly.

---

## 12. Static Noise Floor — Actual Numbers (Useful as Target Benchmarks)

From the legacy no-wind baseline run (`e0_0rpm_run1`):
- Cross-camera **bending baseline RMS = 0.017mm**; **torsion-proxy baseline RMS = 0.033mm**.
- Fused camera-agreement spread on the response axis: mean `y_std` **0.037mm**, max **0.090mm**.
- In-plane (tx/ty) jitter std: **0.012–0.059mm** — depth-axis (tz) jitter is far noisier: **0.985–12.046mm** (camera depth estimation is inherently much less precise than in-plane position — expect this in the new pipeline too, don't be alarmed if tz noise looks 100× worse than tx/ty).
- Static camera timing quality varied: cam1 max gap 19.7ms (0 gaps>25ms, best), cam2 max gap **134.5ms** (2 gaps>25ms, worst), cam3 max gap 37.9ms (1 gap>25ms).
- A PSD/Welch-based jitter-vs-frequency analysis (`scipy.signal.welch`, `fs=60, nperseg=min(256,len)`) existed in one older script (`old/static_bags_fps_and_jitter_analysis_step5.py`) but was **dropped from the current production step5** — worth reinstating; useful for spotting mechanical resonance contaminating what should be a pure-noise stationary signal.

These noise-floor numbers (0.017mm bending / 0.033mm torsion-proxy) are a reasonable target/sanity-check for the new pipeline's own static-precision measurement — if the new detector (official `apriltag` C library, with proper `decision_margin` filtering) is genuinely more precise than the old `cv2.aruco`/`pupil_apriltags` stack, the new noise floor should beat these numbers, not just match them.

---

## 13. Frequency Analysis — Method and Actual Results

Method: Hann-windowed single-sided FFT amplitude spectrum after mean removal, on the common-60Hz basis, band 0.25–30Hz. Peak reliability gate: prominence ratio ≥1.5, spectral concentration ≥0.18, normalized prominence ≥0.35.

**Reminder: the reference constants used in this analysis (1.95Hz/5.15Hz) are wrong — see §3. Use 1.430Hz/3.103Hz instead if reintroducing this check.**

Actual results (21 runs × 2 channels): median stable-regime dominant bending frequency **2.262Hz**, median stable torsion-proxy dominant frequency **3.046Hz** (24/30 reliable stable rows). Interestingly, all 24 reliable rows had the *wrong* reference bin technically present in-band, but the dominant peak located elsewhere — the automated pass/fail logic conflated "reference frequency exists somewhere in spectrum" with "reference frequency is the dominant peak," which are different claims; keep these separate in the rewrite.

**Real physical finding worth preserving**: the 60RPM condition shows a genuine Vortex-Induced Vibration (VIV) anomaly — camera-measured resonance amplitude at 60RPM is **1/37.8×** the amplitude seen at 70RPM (PSD power ratio 70RPM/60RPM = **1427×**), even though the resonance frequency itself (1.406Hz camera vs 1.4358Hz true natural frequency) is correctly detected. Root cause: non-simultaneous camera/LDV capture sessions plus VIV lock-in hysteresis right at the onset boundary (reduced velocity Vr≈1.54) — not a measurement fault. Frame-rate/timing and detection quality were both explicitly ruled out as causes (FPS 59.94±0.01Hz, jitter ≤0.87ms, 100% 3-tag detection, reprojection error 0.31–0.34px, all unchanged vs the clean 70RPM run). This is a legitimate, interesting result for the manuscript's discussion section — carry the finding forward even though the underlying pipeline had other flaws.

---

## 14. Uncertainty Budget — Components and Numbers

Staged across multiple audit scripts rather than one unified budget:
- **Camera-agreement (aligned)**: mean Z disagreement improves from raw 107.3mm to aligned 2.363mm (61.1× median improvement). Stable-regime response-axis agreement mean 0.353mm (≈9.5× the no-wind noise floor of 0.037mm — motion signal is real and well above the noise floor). Cam1/Cam2 marker-A correlation mean 0.804, differential RMS 0.120mm.
- **Bootstrap CIs**: moving-block bootstrap, 1000 replicates, seed `20260516`, block length 60 samples (1.0s) preferred after testing 30/60/120. Stable non-near-floor relative CI width ≈13.3% (bending RMS), ≈15.0% (torsion-proxy RMS).
- **Processing sensitivity**: near-floor thresholds defined as `max(2× static_rms, fixed_floor)` — bending 0.035mm, torsion-proxy 0.067mm. Baseline-removal and filter-choice variants stayed within ~2.62% of each other, **except** first-1-second-mean baseline removal, which shifted results by ~38.70% and was explicitly rejected — because each RPM condition is an independently recorded bag *after* the operator already set the target RPM, so the first second is not actually a static/zero-wind baseline. **Do not use first-1s-mean as a baseline-removal method in the new pipeline; use full-run mean or median instead.**
- **Torsion-geometry uncertainty is unresolved**: marker spacing (200mm) is only an operator-confirmed estimate, never independently measured — status `BLOCKED_BY_GEOMETRY_UNCERTAINTY`. If the new pipeline wants a quantitative camera-vs-LDV torsion comparison, this measurement needs to be done properly first.

---

## 15. Condition-Level LDV Comparison — Actual Results

Unit note: LDV native workbook units are **centimeters**, not millimeters as some legacy `_mm`-labeled columns implied — a real historical unit bug (10× error) fixed by an explicit `_mm_corrected` column. Watch for this exact mistake in the rewrite.

Stable regime (n=19, excludes e20_320rpm): bending RMS Pearson **0.898**, Spearman **0.902**, mean ratio 1.434 (camera reads higher than LDV on average), mean absolute %diff 57.2%. Bending peak Pearson **0.935**. A separate ablation cross-check on a slightly different subset reports higher correlations (bending Pearson 0.960, torsion-proxy Pearson 0.968) — both numbers are legitimate but computed on different subsets/conditions, so don't quote one without specifying which.

Largest RMS gaps cluster at mid-RPM (e11_140rpm worst, 172.2% diff) — not a smooth error-vs-windspeed trend, suggesting condition-specific effects (possibly related to VIV/resonance proximity) rather than a simple linear calibration bias. 60RPM is a severe, separately-explained outlier (§13) and should stay excluded from summary statistics with its cause documented, not silently dropped.

Torsion vs LDV was never quantitatively compared in the final results — blocked by the geometry uncertainty in §14. Only exploratory, non-validated numbers exist (high-wind torsion-proxy RMS 11.08mm camera vs 17.08mm LDV, ratio 0.649).

RPM-to-LDV-row mapping used an unresolved assumption (`actual Dn → workbook D(n+1)` offset) — 21 rows included, 18 excluded from the LDV workbook (which covers more RPM steps than the WTT bag sweep does). Re-verify this mapping independently in the new project rather than inheriting the assumption.

---

## 16. Dataset Inventory (What Raw Data Actually Exists)

62 total bag-like files across 13 tracked candidate datasets. Three are the ones that matter:
- **`data/WTT`** (INCLUDE_MAIN): 21 full grouped bags, one per RPM condition, ~850–915MB each, ~1828–1833 frames/camera, ~59.97–60.03fps, ~30.5s duration. This is the canonical dataset.
- **`data/static_bags`** (INCLUDE_SUPPORTING): 20 static no-motion bags, split by camera, used only for noise-floor/timing characterization.
- **`data/WTT_5sec`** (EXCLUDE_FOR_NOW): 21 shorter/partial repeats of the same RPM sweep — noted in an earlier project memory as linked to a "5sec repeat dataset" but the legacy inclusion decision explicitly excludes it as partial/short.

Everything else (a legacy `data/export/rpm75_all_cams_10s`, prior-study 3D-video-system outputs, `static_bags/cam2/old`) is inventory-only/provenance-only — do not treat as usable data. Note: these bag files live in the legacy directories only for provenance reference — the actual dataset this new project should use is already symlinked in at `/mnt/space/adev/datasets/omrpr/*` (confirmed in an earlier session), so there's no need to re-copy anything from the legacy tree.

Per-run capture-time inter-camera sync drift is comparable in magnitude across all 21 WTT bags (tens of milliseconds, e.g. e0_0rpm: cam1–cam2 16.2ms, cam1–cam3 31.8ms, cam2–cam3 17.9ms max) — this is baked into the raw hardware capture and is independent of any later software resync; expect to see numbers in this range and don't treat them as a processing bug.

---

## 17. Claim-Boundary / Manuscript Constraints (Carry Forward As-Is)

These aren't pipeline bugs — they're hard constraints on what the eventual manuscript is allowed to claim, consistently enforced across nearly every legacy doc, and should inform how the new pipeline's outputs get labeled/reported even at the code level (e.g. output field names, report headers):

- Facility must always be referred to as "a commercial wind-tunnel facility in South Korea" — never name it or any staff.
- LDV comparison is "non-simultaneous condition-level benchmarking," never "validation" or "ground truth."
- "Synchronization" must be described as "timestamp-based/software temporal alignment," never "hardware synchronized."
- Torsion is a "torsion-proxy" (differential/single-marker displacement), never "true torsion angle," unless the geometry uncertainty (§14) is resolved and a genuine angle is derived.
- `e20_320rpm` (high-wind) is always reported separately from stable-regime statistics, never pooled in.
- Accuracy claims must distinguish static precision/noise-floor from dynamic operating uncertainty — never blend the two into one "sub-millimeter accuracy" statement.
- One planning doc additionally flags "no C1/C2 same-marker fusion claim" without a bias audit, and "60RPM is a VIV outlier, must be explained not hidden" — both consistent with findings in this report (§9 baseline-alignment bias, §13 VIV finding).

---

## 18. Recommendations Summary for the Rewrite

1. **Recalibrate all three cameras from scratch.** Do not import any legacy intrinsics/distortion file. Sanity-check fx/fy land in a physically plausible range before trusting anything downstream.
2. **Use the official AprilRobotics `apriltag` C library** (per explicit user requirement) — the legacy codebase never actually used it (only `cv2.aruco` and `pupil_apriltags`), so there's no legacy detector code to port, only parameter references (`quad_decimate`, `quad_sigma`, `refine_edges` from the `pupil_apriltags` script) to translate to the official library's equivalent flags. Take advantage of `decision_margin` filtering, which no legacy detector had.
3. **Fuse strictly per tag ID** — never pool detections across tag IDs the way the legacy `fuse_detections_wtt.py` did.
4. **Use `dside=13cm, dp=1.538`** for any LDV torsion-proxy geometry (Tunnel B, the confirmed correct source for Paper 2's actual LDV reference data) — not the `dp=2.0` value still floating around in the newest planning doc.
5. **Use 1.430Hz / 3.103Hz** as this bridge model's real natural frequencies if reintroducing a frequency-reference sanity check — not Lee2016's 1.95Hz/5.15Hz (different bridge).
6. **Reuse the Step-00 bag-audit algorithm as specified in §7 almost verbatim** — it's well-designed, paper-ready, and its two known bugs (trusting library start/end-time attributes; early-return on WARN) are already documented; just don't repeat them.
7. **Reuse the baseline-alignment-before-fusion pattern (§9)** — median-position bias over the first ~120 synchronized frames, subtracted before displacement is computed — it's a large, real, well-validated improvement (~61×).
8. **Do not use first-1-second-mean as a baseline-removal method** (§14) — proven invalid, each condition bag starts mid-condition, not at rest.
9. **Match cross-camera frames by timestamp, not positional truncation** — the legacy `STEP2_CHECT_WTTBAGS.py` sync check used naive truncation, which silently misaligns if drop counts differ per camera.
10. **Treat the legacy static/torsion noise-floor numbers (0.017mm / 0.033mm) as a target to beat**, not a number to reproduce — the new detector should be more precise given proper confidence filtering.
11. **Pick one sync tolerance deliberately** (legacy used both 25ms and 5ms in different script generations) and document the choice.
12. **Decide explicitly whether torsion is single-marker-proxy or true two-marker-differential** for the new pipeline, and label it accordingly in every output — don't let this drift implicitly the way it did in the legacy full-replay run.

---

## Appendix: Full Source File Inventory (What Was Read)

**Static-test / calibration pipeline:**
`shm-displacement-project-backup/scripts/static_tests/{bagfiles,images}/**` (current, cam2_working, and old/ variants), `shm-displacement-project/data/calib_data/cam{1,1_old,1_try1,2,3}/calibcheckper.py` + `ost.yaml` + `sony_camN_recalib.yaml`, `scripts/dynamic_test/multi_cam_extrinsics.yaml`, `ros_ws/src/bag_exporter/scripts/export_from_bag.py`, `offline_processing/scripts/export_from_rosbag.py`, `audit.sh`.

**WTT dynamic-test pipeline:**
`shm-displacement-project-backup/scripts/dynamic_test/{PlanA,PlanB,rest}/**`, `shm-displacement-project/scripts/dynamic_test/{Recorder_WTT,STEP2_CHECT_WTTBAGS,fuse_detections_wtt,run_full_pipeline_wtt,run_step5_full_replay,run_phase3_full_replay,phase3_frequency_analysis,extract_motion_modes,batch_phase3,report_phase3_summary,validate_against_ldv,analyze_wtt,debug*}.py`, `scripts/{tag_pixel_coverage,analyze_experiments,process_all.sh}`, `offline_processing/scripts/detect_apriltag.py`.

**Offline processing + paper2 audits:**
`offline_processing/scripts/{sync_and_interp,sync_and_interp_backup,fuse_multiview,rts_smoother,fractional_delay,poses_to_world,compute_metrics,compare_ldv,run_Steps.sh}`, `offline_processing/configs/default.yaml`, `scripts/paper2/*.py` (15+ audit/analysis scripts), `data/results/paper2/{PAPER2_CURRENT_STATUS.md, ablation/, uncertainty/, frequency_audit/, torsion_geometry_audit/, condition_level_ldv/, dataset_inventory/}`.

**Docs / memory / claim-boundary:**
`memory/*.md` (all), `docs/{project_manager,PROJECT_TRUTH_CONTEXT,claim_language_rules,paper2_validation_hierarchy,paper2_claim_boundary,paper2_facility_anonymization_note,paper2_figure_table_index,paper2_ldv_unit_and_mapping_audit,paper2_publication_plan,paper2_tesolution_reference_context,paper2_tesolution_style_torsion_plan,measurement_timing_limitations,walkthrough_log,INVESTIGATION_REPORT_2026_06_10,OMRPR_SUPERVISOR_PROMPT,TESolution_Critical_Data_Analysis,ANALYSIS_REPORT_TESOLUTION,ROS Migration}.md`, `docs/archive/project_plan_old/paper2_hybrid_framework/*.md`, `CLAUDE.md`, `USER_GUIDE.md`.

**ffix Logseq PhD notes:**
`OMRPR.md`, `OMRPR___Algorithm - Step 00 Bag Audit.md`, `OMRPR___Step 00 - Bag Audit.md`, `OMRPR___Concepts.md`, `OMRPR___Decisions Log.md`, `OMRPR___Questions and Answers.md`, `OMRPR___Claim Boundary.md`, `OMRPR___Step 01-12*.md` (stubs, mostly empty templates), `OMRPR_Critical_Revision_Roadmap_Logseq.md`.

**Not read (out of scope for this report):** raw image/bag binary content, `.venv`/`venv*` package internals, `paper1_published/` LaTeX source, `__pycache__` compiled bytecode.
