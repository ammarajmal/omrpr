"""
Step 02 — AprilTag Detection
=============================
Purpose:  Detect AprilTag corners in exported PNG frames.
Inputs:   results/step01/{condition}/{cam}/frame_XXXXXX.png
          results/step01/{condition}/{cam}/timestamps.csv
          config/pipeline_config.yaml
Outputs:  results/step02/{condition}/{cam}/detections.csv
          results/step02/{condition}/{cam}/summary.json
Schema (detections.csv):
    frame_idx       int     — links back to step01 PNG and timestamps.csv
    tag_id          int     — AprilTag ID (all cameras see tag_id=0)
    cx, cy          float   — pixel centroid
    c0x,c0y ..      float   — four corners, top-left going clockwise
    decision_margin float   — detector confidence (used by Step 03)
    hamming         int     — error-correction bits used (0 = perfect decode)
Contract:
    - Sparse CSV: frames with no detection produce no row.
    - Missed frames are recoverable by: set(step01 frame_idx) - set(step02 frame_idx)
    - summary.json carries total_frames, detected_frames, detection_rate,
      max_consecutive_miss for diagnostic purposes.
Limits:
    - Assumes tag family tag36h11, one tag visible per frame per camera.
    - Pose estimation is NOT done here — that is Step 04.
    - Requires pupil-apriltags >= 1.0.4
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import cv2
import yaml
import pupil_apriltags as ap


# ── Detector is created once at module level ─────────────────────────────────
# nthreads=1 is deliberate: we parallelise at the bag/camera level if needed,
# not inside the detector. More threads per detector causes contention.
DETECTOR = ap.Detector(
    families="tag36h11",
    nthreads=1,
    quad_decimate=1.0,   # no downscaling — full 1920×1080 resolution
    quad_sigma=0.0,      # no Gaussian blur pre-processing
    refine_edges=1,      # sub-pixel corner refinement — ON
    decode_sharpening=0.25,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Step 02 — AprilTag Detection")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Condition name or path — e.g. e7_90rpm or "
                                     "data/WTT/e7_90rpm/e7_90rpm_run1.bag")
    group.add_argument("--all", action="store_true",
                       help="Process all conditions found in results/step01/")
    parser.add_argument("--config", default="config/pipeline_config.yaml")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def condition_from_arg(arg: str) -> str:
    """
    Accept either a condition name ('e7_90rpm') or a bag path
    ('data/WTT/e7_90rpm/e7_90rpm_run1.bag') — return condition name either way.
    """
    p = Path(arg)
    if p.suffix == ".bag":
        return p.parent.name
    return p.name


def detect_condition(condition: str, config: dict) -> None:
    """
    Run detection on all cameras for one experimental condition.
    """
    results_dir  = Path(config["paths"]["results_dir"])
    cam_config   = config["cameras"]
    step01_root  = results_dir / "step01" / condition
    step02_root  = results_dir / "step02" / condition

    print(f"\n=== APRILTAG DETECTION: {condition} ===\n")

    for cam_name in cam_config:
        cam_in_dir  = step01_root / cam_name
        cam_out_dir = step02_root / cam_name
        cam_out_dir.mkdir(parents=True, exist_ok=True)

        # ── Load step01 timestamps to know total frame count ─────────────────
        ts_csv = cam_in_dir / "timestamps.csv"
        if not ts_csv.exists():
            raise FileNotFoundError(
                f"Step01 output missing for {condition}/{cam_name}. "
                f"Run step01 first."
            )

        with open(ts_csv) as f:
            reader = csv.DictReader(f)
            frame_indices = [int(row["frame_idx"]) for row in reader]

        total_frames = len(frame_indices)

        # ── Detection loop ────────────────────────────────────────────────────
        detections      = []   # list of dicts, one per detected frame
        detected_set    = set()

        for frame_idx in frame_indices:
            png_path = cam_in_dir / f"frame_{frame_idx:06d}.png"
            if not png_path.exists():
                # Should not happen if step01 ran cleanly, but guard anyway
                print(f"  [WARN] PNG missing: {png_path.name} — skipping")
                continue

            # Load as grayscale — detector requires single-channel uint8
            img = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                print(f"  [WARN] Could not read {png_path.name} — skipping")
                continue

            results = DETECTOR.detect(img)

            if not results:
                continue   # MISS — no row written, sparse CSV contract

            # Take the highest-margin detection if somehow >1 appears
            best = max(results, key=lambda r: r.decision_margin)

            corners = best.corners   # shape (4, 2), float64, TL→TR→BR→BL
            cx, cy  = best.center

            detections.append({
                "frame_idx":       frame_idx,
                "tag_id":          best.tag_id,
                "cx":              cx,
                "cy":              cy,
                "c0x": corners[0, 0], "c0y": corners[0, 1],  # top-left
                "c1x": corners[1, 0], "c1y": corners[1, 1],  # top-right
                "c2x": corners[2, 0], "c2y": corners[2, 1],  # bottom-right
                "c3x": corners[3, 0], "c3y": corners[3, 1],  # bottom-left
                "decision_margin": best.decision_margin,
                "hamming":         best.hamming,
            })
            detected_set.add(frame_idx)

        # ── Write detections.csv ──────────────────────────────────────────────
        fieldnames = [
            "frame_idx", "tag_id",
            "cx", "cy",
            "c0x", "c0y", "c1x", "c1y", "c2x", "c2y", "c3x", "c3y",
            "decision_margin", "hamming",
        ]
        det_csv = cam_out_dir / "detections.csv"
        with open(det_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in detections:
                # Round floats to 6 dp — sufficient for sub-pixel corners
                for key in ["cx","cy","c0x","c0y","c1x","c1y","c2x","c2y","c3x","c3y"]:
                    row[key] = round(float(row[key]), 6)
                row["decision_margin"] = round(float(row["decision_margin"]), 4)
                writer.writerow(row)

        # ── Compute summary stats ─────────────────────────────────────────────
        detected_frames   = len(detections)
        detection_rate    = detected_frames / total_frames if total_frames > 0 else 0.0
        missed_indices    = sorted(set(frame_indices) - detected_set)
        max_consec_miss   = _max_consecutive(missed_indices)

        summary = {
            "condition":           condition,
            "cam":                 cam_name,
            "total_frames":        total_frames,
            "detected_frames":     detected_frames,
            "missed_frames":       len(missed_indices),
            "detection_rate":      round(detection_rate, 6),
            "max_consecutive_miss": max_consec_miss,
        }

        with open(cam_out_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # ── Print per-camera line ─────────────────────────────────────────────
        status = "OK" if detection_rate >= 0.95 and max_consec_miss <= 5 else "WARN"
        print(f"  {cam_name}: {detected_frames}/{total_frames} detected "
              f"({detection_rate*100:.2f}%) | "
              f"max_consec_miss={max_consec_miss} | {status}")

    print()


def _max_consecutive(sorted_missed: list[int]) -> int:
    """
    Given a sorted list of missed frame indices, return the length of the
    longest consecutive run.  Returns 0 if the list is empty.
    """
    if not sorted_missed:
        return 0
    max_run = run = 1
    for i in range(1, len(sorted_missed)):
        if sorted_missed[i] == sorted_missed[i - 1] + 1:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    return max_run


def main():
    args   = parse_args()
    config = load_config(args.config)

    if args.all:
        results_dir  = Path(config["paths"]["results_dir"])
        step01_root  = results_dir / "step01"
        conditions   = sorted([d.name for d in step01_root.iterdir() if d.is_dir()])
        if not conditions:
            raise FileNotFoundError(f"No step01 results found under {step01_root}")
        print(f"Found {len(conditions)} condition(s) — processing all.")
    else:
        conditions = [condition_from_arg(args.bag)]

    for condition in conditions:
        detect_condition(condition, config)


if __name__ == "__main__":
    main()