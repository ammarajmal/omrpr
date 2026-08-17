# Paper 2 North Star — progress, working tree, and bigger picture

Date: 2026-08-02

This document is the quick orientation layer for Paper 2 / OMRPR analysis.
It explains:

- what the project is trying to do;
- what is finished;
- what is still pending;
- how the repository is currently arranged;
- what the active working tree contains right now.

It is meant to be readable from top to bottom without already knowing the
history.

## 1) The project in one paragraph

Paper 2 is a source-grounded, non-simultaneous camera-vs-LDV study of a
bridge-deck wind-tunnel experiment. The camera side is built around official
AprilTag image-plane tracking, conservative admissibility rules, and explicit
static-precision gating. The LDV side is a condition-level benchmark, not
ground truth. The whole point of the pipeline is to keep the camera evidence,
the laser evidence, and the manuscript language separated until each claim is
actually supported.

## 2) The core architecture

The project is organized as a staged pipeline:

| Step | Stage | Meaning |
|---:|---|---|
| 00 | Source inventory and bag audit | Classify the raw WTT/static corpus and timing quality |
| 01 | Calibration-input audit | Confirm what target geometry and image inputs are usable |
| 02 | Calibration limitation and sensitivity | Lock the image-plane-first rule and quarantine metric claims |
| 03 | Official AprilTag verification | Verify the official AprilRobotics detector path |
| 04 | Static precision | Measure noise floor, timing quality, and first-pass thresholds |
| 05 | WTT detection and pose export | Produce per-camera/per-tag outputs with rejection reasons |
| 06 | Timestamp matching and per-tag fusion | Match streams by timestamp and fuse by marker group |
| 07 | Response construction | Freeze bending and torsion-proxy channel definitions |
| 08 | LDV processing | Parse and normalize the laser benchmark tables |
| 09 | Condition benchmarking | Compare camera and LDV by condition |
| 10 | Frequency and uncertainty | Interpret resonance, noise floor, and uncertainty |
| 11 | Manuscript outputs | Check that all numbers are internally consistent |
| 12 | Submission readiness | Audit claims, anonymization, files, and reproducibility |

The key design idea is simple:

1. the camera pipeline is the primary observable;
2. the LDV pipeline is the benchmark side;
3. the manuscript only gets written after the evidence chain is stable.

## 3) What is already finished

The pipeline is not just scaffolded anymore; the main scientific stages have
been reviewed and approved through submission readiness.

Completed outcomes:

- the raw WTT corpus and static corpus have been inventoried;
- observation control is frozen in configuration and code;
- the official AprilRobotics AprilTag detector is the required runtime;
- static precision has been measured and turned into first-pass thresholds;
- WTT image-plane tracks have been imported and checked;
- timestamp matching and marker-group fusion are in place;
- response channels are defined as bending and torsion-proxy;
- LDV data have been imported and normalized;
- camera-vs-LDV benchmarking has been summarized;
- frequency and uncertainty have been reviewed;
- manuscript consistency has been checked;
- the readiness script passes with no failures.

Current readiness snapshot:

- PASS = 31
- WARN = 1
- FAIL = 0

The single warning is the expected dirty working tree, not a scientific
failure.

## 4) What is still pending

The science pipeline is ready; the manuscript package is not yet assembled.

Pending work:

- populate the manuscript folders;
- move reviewed figures and tables into manuscript-ready form;
- write the actual paper text;
- finalize claim language and captions;
- do the final author-level review;
- package the submission artifacts.

Also still pending in a broader sense:

- final manuscript wording on torsion-proxy vs true torsion angle;
- any future re-derivation of geometry if the project owner reopens that
  question;
- any later cleanup of the active worktree into commits or a release branch.

## 5) The working tree right now

The repo is intentionally not clean. That is because there are active edits and
new files that were created while moving the pipeline forward.

Current `git status --short` snapshot:

| State | File |
|---|---|
| modified | `AGENTS.md` |
| modified | `ai-context/01_CURRENT_STATE.md` |
| modified | `ai-context/06_TASK_QUEUE.md` |
| modified | `ai-context/PROJECT_STATE.yaml` |
| modified | `configs/observation-control.yaml` |
| modified | `configs/observation-manifest.csv` |
| modified | `configs/project.yaml` |
| modified | `src/omrpr_analysis/observation_control.py` |
| modified | `tests/python/test_observation_control.py` |
| untracked | `scripts/camera/import_official_image_plane_tracks.py` |
| untracked | `src/omrpr_analysis/official_tracks.py` |
| untracked | `tests/python/test_official_tracks.py` |

What that means in plain English:

- the config files were updated to lock thresholds and gate behavior;
- the observation-control code was updated to enforce the thresholds;
- tests were added/updated to protect that behavior;
- the official-tracks import code was added as a new helper path;
- the working tree still needs to be committed or otherwise organized by the
  user when they are ready.

Nothing in the repo was reset or wiped.

## 6) What the manuscript folder means

The `manuscript` directory exists, but it is still mostly structural.
Its purpose is to become the final paper package area, not the pipeline
working area.

Current layout:

- `manuscript/drafts/`
- `manuscript/figures/`
- `manuscript/generated/figures/`
- `manuscript/generated/results/`
- `manuscript/generated/tables/`
- `manuscript/results/`
- `manuscript/submission/`
- `manuscript/tables/`

At the moment, these folders are not yet populated with the actual paper text.
That is normal for the current state of the project.

## 7) The project theory in plain language

The paper is built on a careful distinction between evidence types:

- raw bags and records are the source layer;
- the official detector gives image-plane measurements;
- static precision tells us how much we can trust the camera noise floor;
- fusion turns camera tracks into response channels;
- LDV provides a condition-level benchmark;
- frequency and uncertainty explain whether the observed signals are
  physically meaningful;
- the manuscript is the final communication layer.

The project avoids three common mistakes:

1. treating provisional camera geometry as final truth;
2. treating LDV as ground truth instead of a benchmark;
3. blending stable-regime evidence with diagnostic resonance evidence.

For the WTT setup, both physical AprilTags decode as tag ID 0. Marker A is
viewed by cam1+cam2 and marker B by cam3; camera coverage and explicit
marker-group identity, rather than differing decoded IDs, keep them separate.

That is why the pipeline uses explicit gates and why the project keeps saying
“provisional” when the evidence really is provisional.

## 8) How to read the results

If you want to understand the whole story quickly, read in this order:

1. `CURRENT_STATE.md`
2. `docs/MASTER_EXECUTION_ROADMAP.md`
3. `docs/DECISION_LOG.md`
4. `outputs/reports/step_04_static_precision.md`
5. `outputs/reports/step_10_review.md`
6. `outputs/reports/step_11_review.md`
7. `outputs/reports/step_12_review.md`

That sequence gets you from the governing architecture to the actual
results and the current readiness state.

## 9) What this means for next actions

The next real work is not more gate logic.

The next work is:

- assemble the manuscript package;
- move the reviewed figures/tables into the manuscript folders;
- write the introduction, methods, results, and discussion around the
  approved evidence chain;
- keep the language aligned with the claim boundaries already frozen in the
  repo.

## 10) Short summary

- The pipeline is finished through submission readiness.
- The paper itself is not yet drafted into the manuscript area.
- The active repo is intentionally dirty because the work is in progress.
- The next step is manuscript assembly, not more core pipeline debugging.
