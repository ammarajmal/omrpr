# OMRPR Publication Readiness Assessment

## Overall judgment

Based on the project brief you provided, **this is potentially publishable work in a peer-reviewed impact-factor journal, but it is not yet submission-ready in its current state**. My strongest view is that it is **well positioned for a measurement-and-instrumentation journal such as *Measurement*** if you write it as a **metrology paper first** and a structural-health-monitoring application paper second. That journal’s official scope explicitly invites work on measurement science, estimation techniques, data processing and fusion, and performance evaluation of measurement systems, while also warning that papers centered mainly on image processing with little measurement-science content are likely out of scope. It also explicitly requires disciplined use of metrological terminology and expects authors to show how the work advances measurement science rather than merely applying existing tools. citeturn22view0turn22view1

So the answer to your practical question is:

**Yes, the work is strong enough in principle for an impact-factor journal.**  
**No, it is not yet strong enough in its present documented state to submit without targeted revision.**

The decisive reason is not that the core idea is weak. It is that your **publication risk lies in framing, metrology, and validation language**, not in the raw pipeline architecture. Right now the brief already shows a technically interesting contribution: offline multi-camera displacement reconstruction from asynchronous camera streams, deterministic processing, explicit uncertainty accounting, and careful comparison to a reference instrument. Those are all live topics in the field. Recent literature continues to address camera-motion compensation, non-overlapping or multi-camera displacement measurement, and uncertainty quantification for vision-based structural displacement monitoring, which means your topic is current and relevant rather than stale. citeturn13search9turn7search5turn21search10

My mentor-level verdict is therefore:

- **For *Measurement***: promising and realistic, if revised.
- **For *Engineering Structures***: borderline at best, unless the structural-dynamics contribution becomes much stronger.
- **For *Mechanical Systems and Signal Processing***: not yet competitive, because the methodological novelty in signal processing appears incremental rather than field-shifting. The official scopes of those journals support exactly that distinction: *Engineering Structures* wants stronger structural mechanics and dynamics contributions, while *MSSP* expects a demonstrably significant original advance in signal/information processing. citeturn22view2turn22view3

## What is genuinely strong and publishable

The project stands on a sound and relevant scientific problem. Modern reviews of computer-vision-based SHM consistently describe the field as important, active, and still constrained by calibration, feature extraction/tracking, practical field conditions, and measurement accuracy issues. That makes your focus on deterministic offline reconstruction, practical synchronization, and uncertainty not merely cosmetic but aligned with recognized technical pain points in the literature. citeturn21search1turn7search0turn21search18

Your **best contribution is not “we used cameras on a bridge model.”** Your best contribution is this:

> **A reproducible offline measurement pipeline for dynamic displacement reconstruction from asynchronous multi-camera data, with explicit quality gating, physically bounded claim language, and a nontrivial uncertainty/accountability chain.**

That is a publishable contribution in *Measurement* **if** you protect it from overclaiming.

Several parts of the brief are particularly strong.

First, the **offline-only design choice is academically defensible**. It is not a weakness to give up real-time capability when the scientific objective is measurement quality, non-causal estimation, and reproducibility. Fixed-interval smoothing belongs exactly in that category: the Rauch–Tung–Striebel smoother uses information from both past and future observations over a fixed interval, unlike a forward-only Kalman filter. That is an established and legitimate state-estimation framework, originating in the classic 1965 Rauch–Tung–Striebel work. citeturn12search1turn12search8turn12search12

Second, your **pose-estimation backbone is technically credible**. OpenCV’s official documentation states that `solvePnP` solves the 3D-to-2D pose problem by minimizing reprojection error, and that `SOLVEPNP_IPPE_SQUARE` is specifically intended for square-marker pose estimation with four coplanar points given in a strict point order. That makes the choice itself correct in principle for planar square fiducials. citeturn4view0

Third, your use of **AprilTags is reasonable and mainstream**, and AprilTag remains one of the most important fiducial systems in robotics and measurement-oriented vision work. The AprilTag literature emphasizes robustness to false positives through coding design and minimum Hamming-distance guarantees under rotation. citeturn23view1turn16search11

Fourth, you are already thinking in a way that many papers do not: **you are separating what the system measures from what it does not measure**. The distinction between bending displacement and a torsion-proxy, rather than a direct torsion angle, is absolutely the kind of restraint that reviewers respect when it is maintained consistently.

Fifth, the **uncertainty-aware posture** is a major asset. This matters more than many early-career authors realize. Measurement science does not reward only a low RMSE or a high correlation coefficient; it rewards a defensible account of the measurement result, the uncertainty attached to it, and the conditions under which the claim holds. That is exactly the language used in the Guide to the Expression of Uncertainty in Measurement and NIST guidance. citeturn20search1turn20search7turn20search4

In short, the project has the bones of a good paper.

## Critical technical issues that could hurt peer review

The most important thing I can tell you is that **your biggest technical vulnerabilities are not fatal, but they must be handled explicitly**.

The first issue is a **terminology problem** in the very motivation section. The brief groups LDVs with “contact sensors.” That is technically incorrect. Laser Doppler vibrometers are optical, non-contact vibration instruments, and manufacturers and technical sources consistently describe LDV as a non-contact measurement technology. This sounds small, but in a metrology journal it matters because it signals whether the authors are using instrumentation language carefully. Fix this everywhere. citeturn19search0turn19search1turn19search8

The second issue is that the AprilTag discussion is **slightly overconfident in the wrong places**. The brief states or implies that `tag36h11` is effectively the standard or best family. That is too strong. AprilTag 3’s own project documentation recommends `tagStandard41h12` for the vast majority of applications, not `tag36h11`. Also, the naming of `tag36h11` corresponds to a minimum Hamming distance of **11**, not 10. None of this means your choice is wrong; it means your language must change from “best” or “standard” to something like **“widely used, appropriate, and empirically validated for this setup.”** citeturn23view0turn15search0turn15search6

A closely related point is the **quality score**. Your `B0 = dm × √(area_px²)` is usable as an internal heuristic, but you should not present it as though it were a validated metrological quantity. The reason is important: official AprilTag API documentation describes decision margin as a rough measure of binary decoding quality, but also warns that it is a reasonable surrogate for detection accuracy **only for very small tags** and is not effective as a universal indicator for larger tags. Since your score multiplies decision margin by tag area, you are effectively engineering a practical quality heuristic, not deriving a physically established uncertainty model. That is fine, but the manuscript must call it exactly that. citeturn24view0

The third issue is **pose ambiguity in planar markers**. This is a subtle but serious point. IPPE is well suited to planar pose estimation, but its own documentation emphasizes that planar pose can be ambiguous and that IPPE conceptually provides two candidate pose solutions. The ambiguity becomes especially important when the projection is close to affine, such as when the marker is far away or seen nearly frontally. OpenCV also notes that `solvePnPGeneric()` can return multiple solutions for `SOLVEPNP_IPPE_SQUARE`. If the manuscript does not explain how you handled or ruled out this ambiguity, a well-informed reviewer can poke a hole in your pose-estimation story. citeturn17view0turn4view0

The fourth issue is **synchronization language**. Resampling onto a common 60 Hz grid is a reasonable processing step. But resampling by itself is not equivalent to true synchronization. It regularizes time stamps; it does not create simultaneous exposure acquisition. If the three cameras were started sequentially, reviewers will want to know exactly what the ROS time stamps represent: hardware exposure time, driver callback time, transport time, or bag write time. That distinction is crucial. Your own brief is already honest that the method is not equivalent to hardware triggering. Keep that honesty. In the paper, I would strongly prefer the phrase **“software time-base alignment”** or **“timestamp-based temporal alignment”** unless you can prove exposure-level synchronization. This is especially important because the literature on vision-based structural displacement still treats practical deployment factors—camera calibration, image quality, hardware behavior, and timing—as fundamental accuracy determinants. citeturn7search0turn7search15turn7search18

The fifth issue is **the meaning of your internal-agreement numbers**. The dramatic reduction from a raw ~106 mm Z disagreement to ~1.757 mm after full-run mean removal can indeed be publishable, but only if you define the measurand properly. If your measurand is **dynamic displacement relative to an operating mean**, then subtracting the run mean is physically justified. If your manuscript ever sounds as if you are making a claim about **absolute 3D position accuracy**, subtracting means will look like hiding extrinsic bias. You cannot let that ambiguity exist. In metrological terms, the post-alignment agreement is evidence of **internal reproducibility/consistency** under your chosen coordinate treatment, not evidence of absolute trueness. Official metrology guidance distinguishes repeatability, reproducibility, trueness, bias, and accuracy very carefully, and *Measurement* explicitly demands disciplined use of those terms. citeturn26search6turn26search4turn22view0

The sixth issue is that your **external benchmark is condition-level, not instantaneous ground truth**. This is probably the single largest scientific limitation in the whole study. If the camera bags and LDV measurements are non-simultaneous and even taken in different tunnels or sessions, then Pearson correlation and RMSE against LDV are not demonstrating time-synchronous waveform accuracy. They are demonstrating **condition-level agreement in trend and scale**, which is still useful, but weaker. This does not kill the paper. It simply defines the claim boundary. You must stop every sentence that drifts toward “validated against LDV” unless it is immediately qualified as **non-simultaneous condition-by-condition benchmarking**.

The seventh issue is a **novelty-risk issue relative to Paper 1**. From a reviewer’s perspective, the question will not be “is this pipeline good?” but “is this paper materially different from the previous publication?” Your answer must be sharp and non-negotiable: the new paper contributes **offline deterministic processing, asynchronous multi-camera alignment, fixed-interval smoothing, quality-gated reconstruction, and an explicit uncertainty framework**. If that delta is not made explicit in the introduction and related-work section, the manuscript may be dismissed as a larger but incremental reprocessing of the same experiment.

## Metrology, statistics, and validation standards you should meet

You are targeting a journal that explicitly invokes the VIM and GUM worldview, so the paper should be written accordingly. The GUM frames uncertainty as a property of the reported measurement result, and NIST guidance separates Type A evaluations based on statistical analysis from Type B evaluations based on other information. *Measurement* explicitly tells authors to use internationally approved terminology for concepts such as accuracy, uncertainty, and propagation of uncertainty. citeturn20search1turn20search7turn22view0

In practice, that means your uncertainty section should stop being a collection of “good checks” and become a **structured uncertainty model**. Right now, from the briefing, you have at least four real components:

- **Type A repeatability/precision terms**, such as static noise floor and repeat measurements under the same condition.
- **Inter-camera reproducibility terms**, such as post-alignment Cam1–Cam2 agreement on the same marker.
- **Timing-related terms**, including stamp provenance, frame-rate stability, resampling effects, and the phase consequences of temporal misalignment.
- **Reference-comparison terms**, which should be treated carefully because the LDV comparison is non-simultaneous and therefore mixes sensor disagreement with inter-session aerodynamic variability.

That structure is publishable. But it must be stated clearly and the terminology must be correct.

The statistical treatment also needs sharpening. Pearson correlation is acceptable, but in your setup it will be easy for a reviewer to say, correctly, that a high condition-level correlation across 21 operating points is **not the same thing as waveform agreement**. I would therefore recommend that the paper emphasize three different layers of evidence:

**Internal precision evidence.**  
This is where the static noise floor, Cam1–Cam2 agreement, tag detection quality, and re-projection error belong.

**Physics-consistency evidence.**  
This is where the modal frequencies and condition-dependent aerodynamic response belong.

**External benchmarking evidence.**  
This is where the LDV comparison belongs, but with careful wording: not “truth validation,” but “non-simultaneous reference benchmarking.”

The frequency analysis is not optional. It is essential. A Hann window is a standard and defensible choice for reducing spectral leakage in FFT-based harmonic analysis, and that should be stated cleanly. But the paper should also report the frequency resolution, the window used, whether zero-padding was used only for visualization or also for peak estimation, and how dominant peaks were selected in low-SNR conditions. citeturn18search0turn18search3

I would go further: your frequency section should become one of the paper’s strongest parts, because it can do something the non-simultaneous LDV benchmark cannot. If your reconstructed motion repeatedly produces peaks near the known bending and torsional-reference frequencies for the model under appropriate regimes, that is **independent physics-based validation**. Given your stated modal frequencies, the 60 Hz common grid is in principle adequate for those low-order modes: it gives roughly 42 samples per cycle at 1.430 Hz and about 19 samples per cycle at 3.103 Hz. That is enough for dominant-frequency identification, provided you report the estimation method rigorously.

The smoothing section also needs stricter validation language. RTS smoothing is methodologically legitimate, but “no phase lag” should not be asserted loosely. Because your grid spacing at 60 Hz is about 16.7 ms, any claim of sub-10 ms phase shift effectively implies sub-sample estimation or cross-spectral analysis, not merely visual overlap. Show the method. Report the actual pre/post dominant frequency, amplitude ratio, and lag-estimation procedure. Cite RTS as fixed-interval smoothing, not as some exotic novelty. citeturn12search1turn12search12

Finally, the paper should use metrology language correctly when discussing performance:

- **Static noise floor** is not the same as **dynamic operating uncertainty**.
- **Internal agreement** is not the same as **external accuracy**.
- **Bias relative to LDV** is not automatically **camera measurement error**, because your experimental design confounds sensor disagreement with inter-session aerodynamic variability.
- **Torsion-proxy** should remain a proxy unless you derive an angle from a clearly stated baseline and justified geometry.

If you make these distinctions explicit, reviewers will read your manuscript as careful and serious. If you blur them, they will read it as overclaimed.

## Journal fit and likely peer-review outcome

For *Measurement*, the fit is real, but only if the manuscript is framed in explicitly measurement-science terms. The journal says it wants advances in measurement science, estimation, data processing, fusion, and performance evaluation, and warns against papers that are mostly image processing without a strong instrumentation or metrology contribution. That wording matters enormously for your paper. You should therefore present OMRPR not as a clever computer-vision pipeline, but as a **deterministic optical measurement system for dynamic displacement reconstruction under asynchronous acquisition constraints**. citeturn22view0turn22view1

If written that way, I would assess your chances as follows:

| Submission target | Fit | My assessment |
|---|---|---|
| *Measurement* | Strong if reframed as a measurement-system paper | **Yes, realistic** |
| *Engineering Structures* | Needs stronger contribution to structural dynamics, aeroelastic interpretation, or structural mechanics | **Possible but weaker fit** |
| *Mechanical Systems and Signal Processing* | Needs materially stronger signal-processing novelty and methodological advancement | **Not recommended right now** |

That assessment aligns with the stated journal scopes. *Engineering Structures* explicitly seeks advances in structural engineering, structural dynamics, wind engineering, and SHM with strong structural relevance, while *MSSP* explicitly asks for a significant original contribution in signal and information processing. citeturn22view2turn22view3

What will likely happen in peer review?

If the paper is submitted now, without Step 08 completed and without the terminology fixes, the likely reviewer criticisms would be:

- the LDV comparison is non-simultaneous and therefore too weakly framed,
- the uncertainty section is not yet fully metrological,
- the tag-quality score is heuristic rather than validated,
- the IPPE ambiguity is not fully discussed,
- the contribution over Paper 1 is insufficiently differentiated,
- and the paper still reads too much like an image-processing workflow rather than a measurement paper.

If those points are addressed, I think the paper becomes much stronger. In that case, the likely reviewer response changes from “overclaimed and incomplete” to “limited but carefully bounded and methodologically useful.” That is a very different outcome.

## What must be fixed before submission

If you asked me whether I would allow one of my PhD students to submit this next week, my answer would be **no**. If you asked me whether I would allow submission after a focused revision round, my answer would be **yes**.

Here is the standard I would require before submission.

| Item | Status from your brief | Submission consequence |
|---|---|---|
| Full frequency-analysis section completed | Not yet complete | **Mandatory before submission** |
| Claim boundary rewritten in metrological language | Partly present, not yet publication-tight | **Mandatory** |
| LDV comparison reframed as non-simultaneous benchmarking | Needs stronger discipline | **Mandatory** |
| IPPE ambiguity handling documented | Not yet explicit in the brief | **Mandatory** |
| Uncertainty budget reorganized into clear components | Promising but incomplete | **Mandatory** |
| AprilTag-family and quality-score wording corrected | Needs revision | **Mandatory** |
| Distinction between torsion and torsion-proxy maintained everywhere | Present conceptually | **Mandatory to preserve** |
| KLT/B2 removed from main contribution | Correctly de-emphasized | **Keep out of the core paper** |

The highest-priority fixes are these.

**Complete the frequency section.**  
Without it, the manuscript is analytically incomplete. You need spectra, dominant peaks, nearest-reference-bin reporting, and a policy for low-SNR cases. This section can become a major strength because it anchors the camera measurements to known structural physics rather than only to a non-simultaneous external reference.

**Rewrite the measurement claim.**  
The paper should not claim “sub-millimeter accuracy” in the broad sense. It can claim **sub-millimeter static precision/noise floor**, strong internal consistency, and condition-level agreement with an external LDV benchmark under non-simultaneous conditions. That wording is defensible. “Accuracy” is not, unless tightly qualified.

**Clarify the time-base story.**  
State exactly what the timestamps are, how drift was characterized, whether the cameras were nominally constant-frame-rate, and what resampling does and does not solve.

**Explain why mean removal is physically legitimate.**  
You must define the measurand as dynamic displacement relative to the operating mean for a run that begins in an already excited state. Then the 106 mm to 1.757 mm result becomes a justified decomposition of fixed offset and dynamic disagreement, not a suspicious numerical cleanup.

**Turn the uncertainty section into a true uncertainty section.**  
Write it like a measurement paper: identify components, classify them, state how each is estimated, and be honest about what remains confounded. GUM-style language will help here. citeturn20search1turn20search4turn26search1

**State the paper’s genuine novelty over Paper 1 in one paragraph, early.**  
Do not assume the reviewer will infer it.

Once those are done, the paper becomes viable.

## Final mentor verdict

My professional assessment is:

**This work is enough for journal publication in an impact-factor venue, but only after one more serious revision cycle.**  
**It is appropriate for submission to *Measurement* after that revision cycle.**  
**It is not yet appropriate to submit in the exact state reflected by this brief.**

If I convert that into a plain decision:

- **Scientific value:** yes.
- **Novelty:** yes, but moderate and needs precise framing.
- **Technical rigor:** promising, but still incomplete.
- **Metrology maturity:** not yet sufficient for submission, but close.
- **Journal appropriateness:** good for *Measurement*, weaker for higher structural-dynamics or signal-processing venues.
- **Submission readiness today:** **not yet**.
- **Submission readiness after the fixes above:** **yes, likely**.

The paper can succeed because it does something many papers do not do well: it tries to measure carefully, not merely detect or track. That is the right instinct. But that same strength means you will be judged by measurement-science standards. *Measurement* explicitly requires that standard: strong measurement context, correctly used metrological terminology, and an advance beyond generic image processing. If you meet that bar, the project is defensible and publishable. citeturn22view0turn22view1

My most concise final advice is this:

**Do not submit the paper as “a camera pipeline validated against LDV.”**  
Submit it as **“a deterministic offline optical measurement system for dynamic displacement reconstruction under asynchronous acquisition, with bounded claims, internal reproducibility evidence, physics-consistency checks, and non-simultaneous external benchmarking.”**

That version has a real chance.