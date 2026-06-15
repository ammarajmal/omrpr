"""
Step 03 — Quality Scoring
==========================
Purpose:  Compute per-frame quality scores for AprilTag detections.
          Enriches step02 detections.csv with quality metrics.
          Does NOT filter frames — all detected frames are kept.
          Quality score is used downstream as a confidence diagnostic
          and to justify equal-weight frame inclusion in the manuscript.

Inputs:   results/step02/{condition}/{cam}/detections.csv
          results/step01/{condition}/{cam}/frame_XXXXXX.png  (for corner sharpness)
          config/pipeline_config.yaml

Outputs:  results/step03/{condition}/{cam}/detections_with_quality.csv
          results/step03/{condition}/{cam}/summary.json

Schema (detections_with_quality.csv):
    All columns from step02 detections.csv, plus:
        area_px2         float  — tag area in pixels², shoelace formula on 4 corners
        quality_score    float  — B0 formula: decision_margin × sqrt(area_px2)
        corner_sharpness float  — mean Laplacian gradient magnitude in 11×11 window
                                  around each of the 4 corners (optional, see --no-sharpness)

Quality score formula (B0 — locked, do not change):
    s_i = dm_i × sqrt(A_i)
    where A_i = shoelace area of the four detected corners in pixels²

Corner sharpness:
    For each corner, extract an 11×11 pixel window from the grayscale frame.
    Compute the absolute Laplacian (cv2.Laplacian, ksize=3).
    corner_sharpness = mean of the 4 per-corner Laplacian mean values.
    Higher = sharper = more reliable sub-pixel localization.

Low-quality threshold:
    Defined in pipeline_config.yaml as quality.low_quality_threshold.
    Frames below this threshold are counted in summary.json but NOT removed.

Limits:
    Corner sharpness requires re-reading PNG frames from step01.
    Use --no-sharpness to skip this (faster bulk runs).
    Requires step02 detections.csv to exist.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import cv2
import yaml


SHARPNESS_WINDOW = 11   # 11×11 pixel window around each corner
SHARPNESS_HALF   = SHARPNESS_WINDOW // 2


def parse_args():
    parser = argparse.ArgumentParser(description="Step 03 — Quality Scoring")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Condition name — e.g. e7_90rpm")
    group.add_argument("--all", action="store_true",
                       help="Process all conditions found in results/step02/")
    parser.add_argument("--config", default="config/pipeline_config.yaml")
    parser.add_argument("--no-sharpness", action="store_true",
                       help="Skip corner sharpness computation (faster, no PNG reads)")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def shoelace_area(corners: np.ndarray) -> float:
    """
    Compute the area of a polygon using the shoelace formula.
    corners: shape (4, 2), ordered TL → TR → BR → BL (pupil_apriltags convention).
    Returns area in pixels².
    Always returns a positive value (abs of signed area).
    """
    x = corners[:, 0]
    y = corners[:, 1]
    # Shoelace: 0.5 * |sum(x_i * y_{i+1} - x_{i+1} * y_i)|
    n = len(x)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += x[i] * y[j]
        area -= x[j] * y[i]
    return abs(area) / 2.0


def corner_sharpness_score(img_gray: np.ndarray, corners: np.ndarray) -> float:
    """
    Compute mean Laplacian magnitude in an 11×11 window around each corner.
    img_gray: (H, W) uint8 grayscale image.
    corners: shape (4, 2) float corner pixel coordinates.
    Returns the mean sharpness across all 4 corners.
    Corners near the image border are clamped to valid coordinates.
    """
    H, W = img_gray.shape
    scores = []

    for cx, cy in corners:
        # Clamp window to image bounds
        x0 = max(0, int(round(cx)) - SHARPNESS_HALF)
        x1 = min(W, int(round(cx)) + SHARPNESS_HALF + 1)
        y0 = max(0, int(round(cy)) - SHARPNESS_HALF)
        y1 = min(H, int(round(cy)) + SHARPNESS_HALF + 1)

        patch = img_gray[y0:y1, x0:x1]
        if patch.size == 0:
            scores.append(0.0)
            continue

        lap = cv2.Laplacian(patch, cv2.CV_64F, ksize=3)
        scores.append(float(np.mean(np.abs(lap))))

    return float(np.mean(scores))


def condition_from_arg(arg: str) -> str:
    p = Path(arg)
    if p.suffix == ".bag":
        return p.parent.name
    return p.name


def process_condition(condition: str, config: dict, compute_sharpness: bool) -> None:
    results_dir  = Path(config["paths"]["results_dir"])
    cam_config   = config["cameras"]
    low_q_thresh = config.get("quality", {}).get("low_quality_threshold", 50.0)

    step01_root  = results_dir / "step01" / condition
    step02_root  = results_dir / "step02" / condition
    step03_root  = results_dir / "step03" / condition

    print(f"\n=== QUALITY SCORING: {condition} ===\n")
    if compute_sharpness:
        print(f"  Corner sharpness: ON  (11×11 window, Laplacian ksize=3)")
    else:
        print(f"  Corner sharpness: OFF (--no-sharpness flag set)")
    print()

    for cam_name in cam_config:
        cam02_dir   = step02_root / cam_name
        cam01_dir   = step01_root / cam_name
        cam03_dir   = step03_root / cam_name
        cam03_dir.mkdir(parents=True, exist_ok=True)

        det_csv = cam02_dir / "detections.csv"
        if not det_csv.exists():
            raise FileNotFoundError(
                f"Step02 detections missing for {condition}/{cam_name}. "
                f"Run step02 first."
            )

        # ── Read step02 detections ────────────────────────────────────────────
        with open(det_csv) as f:
            reader = csv.DictReader(f)
            step02_rows = list(reader)

        # ── Compute quality metrics ───────────────────────────────────────────
        enriched_rows   = []
        quality_scores  = []
        sharpness_vals  = []

        for row in step02_rows:
            frame_idx = int(row["frame_idx"])

            # Four corners as (4, 2) array
            corners = np.array([
                [float(row["c0x"]), float(row["c0y"])],
                [float(row["c1x"]), float(row["c1y"])],
                [float(row["c2x"]), float(row["c2y"])],
                [float(row["c3x"]), float(row["c3y"])],
            ], dtype=np.float64)

            # B0 quality score: dm × sqrt(area)
            area_px2      = shoelace_area(corners)
            dm            = float(row["decision_margin"])
            quality_score = dm * np.sqrt(area_px2)

            quality_scores.append(quality_score)

            new_row = dict(row)
            new_row["area_px2"]      = round(area_px2, 4)
            new_row["quality_score"] = round(quality_score, 4)

            # Corner sharpness (optional — requires PNG read)
            if compute_sharpness:
                png_path = cam01_dir / f"frame_{frame_idx:06d}.png"
                img_gray = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
                if img_gray is not None:
                    sharpness = corner_sharpness_score(img_gray, corners)
                else:
                    sharpness = 0.0
                new_row["corner_sharpness"] = round(sharpness, 4)
                sharpness_vals.append(sharpness)

            enriched_rows.append(new_row)

        # ── Write detections_with_quality.csv ────────────────────────────────
        base_fields = [
            "frame_idx", "tag_id",
            "cx", "cy",
            "c0x", "c0y", "c1x", "c1y", "c2x", "c2y", "c3x", "c3y",
            "decision_margin", "hamming",
        ]
        extra_fields = ["area_px2", "quality_score"]
        if compute_sharpness:
            extra_fields.append("corner_sharpness")
        fieldnames = base_fields + extra_fields

        out_csv = cam03_dir / "detections_with_quality.csv"
        with open(out_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched_rows)

        # ── Build summary ─────────────────────────────────────────────────────
        qs_arr         = np.array(quality_scores)
        low_q_count    = int(np.sum(qs_arr < low_q_thresh))

        summary = {
            "condition":            condition,
            "cam":                  cam_name,
            "total_detected":       len(enriched_rows),
            "low_quality_threshold": low_q_thresh,
            "low_quality_count":    low_q_count,
            "quality_score": {
                "mean":  round(float(np.mean(qs_arr)), 4),
                "min":   round(float(np.min(qs_arr)),  4),
                "max":   round(float(np.max(qs_arr)),  4),
                "std":   round(float(np.std(qs_arr)),  4),
            },
        }

        if compute_sharpness and sharpness_vals:
            sh_arr = np.array(sharpness_vals)
            summary["corner_sharpness"] = {
                "mean": round(float(np.mean(sh_arr)), 4),
                "min":  round(float(np.min(sh_arr)),  4),
                "max":  round(float(np.max(sh_arr)),  4),
            }

        with open(cam03_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # ── Print per-camera line ─────────────────────────────────────────────
        status = "OK" if low_q_count == 0 else "WARN"
        sharpness_str = ""
        if compute_sharpness and sharpness_vals:
            sharpness_str = f" | sharpness_mean={round(float(np.mean(sharpness_vals)),2)}"
        print(f"  {cam_name}: quality mean={round(float(np.mean(qs_arr)),2)} "
              f"min={round(float(np.min(qs_arr)),2)} "
              f"max={round(float(np.max(qs_arr)),2)} "
              f"| low_q={low_q_count}{sharpness_str} | {status}")

    print()


def main():
    args             = parse_args()
    config           = load_config(args.config)
    compute_sharpness = not args.no_sharpness

    if args.all:
        results_dir = Path(config["paths"]["results_dir"])
        step02_root = results_dir / "step02"
        conditions  = sorted([d.name for d in step02_root.iterdir() if d.is_dir()])
        if not conditions:
            raise FileNotFoundError(f"No step02 results found under {step02_root}")
        print(f"Found {len(conditions)} condition(s) — processing all.")
    else:
        conditions = [condition_from_arg(args.bag)]

    for condition in conditions:
        process_condition(condition, config, compute_sharpness)


if __name__ == "__main__":
    main()