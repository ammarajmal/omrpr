"""
Step 04 — Pose Estimation (World-Frame Transform)
==================================================
Purpose:  Estimate 6-DOF pose of the AprilTag in each frame using solvePnP.
          Produces per-frame translation (x, y, z) and quaternion rotation
          in the camera's own coordinate frame.

          IMPORTANT: "world frame" here means camera-frame output from solvePnP.
          There are no geometric extrinsic transforms between cameras —
          extrinsics.yaml is empty by design. The common reference frame is
          established in Step 06 via baseline alignment (subtracting each
          camera's mean position), not via a rotation/translation matrix here.

Inputs:   results/step03/{condition}/{cam}/detections_with_quality.csv
          results/step01/{condition}/{cam}/timestamps.csv
          config/pipeline_config.yaml  (intrinsics, tag_size_m)

Outputs:  results/step04/{condition}/{cam}/world_pose.csv
          results/step04/{condition}/{cam}/summary.json

Schema (world_pose.csv):
    frame_idx       int     — links back to step01/step02/step03
    timestamp_s     float   — from step01 timestamps.csv (bag-normalised)
    x_w             float   — tvec[0] in metres (camera frame, lateral)
    y_w             float   — tvec[1] in metres (camera frame, vertical)
    z_w             float   — tvec[2] in metres (camera frame, depth)
    qx,qy,qz,qw    float   — rotation as unit quaternion (from rvec via Rodrigues)
    reproj_err      float   — mean reprojection error in pixels (quality gate)

Solver:   cv2.SOLVEPNP_IPPE_SQUARE — optimal for square planar markers.
          Returns two solutions; we select the one with tvec[2] > 0
          (tag in front of camera) confirmed by lower reprojection error.

Object points (tag corners, tag frame, Z=0 plane):
    TL = (-h, +h, 0)   TR = (+h, +h, 0)
    BR = (+h, -h, 0)   BL = (-h, -h, 0)
    where h = tag_size_m / 2 = 0.010 m

Limits:
    - Pose is in each camera's own frame, NOT a unified world frame.
    - Do NOT cross-compare absolute x/y/z values between cameras.
    - Cross-camera comparison happens in Step 06 after baseline alignment.
    - Frames with reproj_err > 3.0 px are flagged WARN in summary but kept.
    - Requires step03 detections_with_quality.csv and step01 timestamps.csv.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import cv2
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Step 04 — Pose Estimation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Condition name — e.g. e7_90rpm")
    group.add_argument("--all", action="store_true",
                       help="Process all conditions found in results/step03/")
    parser.add_argument("--config", default="config/pipeline_config.yaml")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def condition_from_arg(arg: str) -> str:
    p = Path(arg)
    if p.suffix == ".bag":
        return p.parent.name
    return p.name


def build_object_points(tag_size_m: float) -> np.ndarray:
    """
    3D object points for a square AprilTag centred at origin, Z=0 plane.
    Order matches pupil_apriltags corner convention: TL → TR → BR → BL.
    """
    h = tag_size_m / 2.0
    return np.array([
        [-h, +h, 0.0],   # TL
        [+h, +h, 0.0],   # TR
        [+h, -h, 0.0],   # BR
        [-h, -h, 0.0],   # BL
    ], dtype=np.float64)


def build_camera_matrix(intr: dict) -> np.ndarray:
    """Build 3×3 camera intrinsic matrix from config dict."""
    return np.array([
        [intr["fx"],       0.0,  intr["cx"]],
        [      0.0, intr["fy"],  intr["cy"]],
        [      0.0,       0.0,        1.0  ],
    ], dtype=np.float64)


def rvec_to_quaternion(rvec: np.ndarray) -> tuple[float, float, float, float]:
    """
    Convert OpenCV rotation vector (Rodrigues) to unit quaternion (qx, qy, qz, qw).
    Uses cv2.Rodrigues to get the 3×3 rotation matrix, then converts.
    """
    R, _ = cv2.Rodrigues(rvec.flatten())
    # Shepperd's method for R → quaternion
    trace = R[0, 0] + R[1, 1] + R[2, 2]
    if trace > 0:
        s  = 0.5 / np.sqrt(trace + 1.0)
        qw = 0.25 / s
        qx = (R[2, 1] - R[1, 2]) * s
        qy = (R[0, 2] - R[2, 0]) * s
        qz = (R[1, 0] - R[0, 1]) * s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s  = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s  = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s  = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    return float(qx), float(qy), float(qz), float(qw)


def reprojection_error(obj_pts: np.ndarray,
                       rvec: np.ndarray,
                       tvec: np.ndarray,
                       K: np.ndarray,
                       dist: np.ndarray,
                       img_pts: np.ndarray) -> float:
    """
    Project 3D object points back into the image and compute mean
    Euclidean distance to the detected 2D corners (in pixels).
    """
    projected, _ = cv2.projectPoints(obj_pts, rvec, tvec, K, dist)
    projected = projected.reshape(-1, 2)
    errors = np.linalg.norm(projected - img_pts, axis=1)
    return float(np.mean(errors))


def load_timestamps(ts_csv: Path) -> dict[int, float]:
    """Load step01 timestamps.csv → {frame_idx: timestamp_s}."""
    ts_map = {}
    with open(ts_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_map[int(row["frame_idx"])] = float(row["timestamp_s"])
    return ts_map


def process_condition(condition: str, config: dict) -> None:
    results_dir = Path(config["paths"]["results_dir"])
    cam_config  = config["cameras"]
    intr_config = config["intrinsics"]
    tag_size_m  = config["apriltag"]["tag_size_m"]
    obj_pts     = build_object_points(tag_size_m)

    # Reprojection error thresholds
    REPROJ_WARN  = 3.0   # px — flag in summary
    REPROJ_BAD   = 10.0  # px — hard flag, physically implausible

    print(f"\n=== POSE ESTIMATION: {condition} ===\n")

    for cam_name in cam_config:
        cam03_dir = results_dir / "step03" / condition / cam_name
        cam01_dir = results_dir / "step01" / condition / cam_name
        cam04_dir = results_dir / "step04" / condition / cam_name
        cam04_dir.mkdir(parents=True, exist_ok=True)

        # ── Load inputs ───────────────────────────────────────────────────────
        det_csv = cam03_dir / "detections_with_quality.csv"
        if not det_csv.exists():
            raise FileNotFoundError(
                f"Step03 output missing for {condition}/{cam_name}. "
                f"Run step03 first."
            )

        ts_map = load_timestamps(cam01_dir / "timestamps.csv")

        # ── Build camera matrix and distortion coefficients ───────────────────
        intr = intr_config[cam_name]
        K    = build_camera_matrix(intr)
        dist = np.array(intr["dist"], dtype=np.float64)

        # ── Pose estimation loop ──────────────────────────────────────────────
        pose_rows      = []
        reproj_errors  = []
        high_reproj    = []   # frame_idx where reproj_err > REPROJ_WARN
        bad_reproj     = []   # frame_idx where reproj_err > REPROJ_BAD

        with open(det_csv) as f:
            reader = csv.DictReader(f)
            for row in reader:
                frame_idx = int(row["frame_idx"])

                # 2D image points — must match OBJ_PTS order TL→TR→BR→BL
                img_pts = np.array([
                    [float(row["c0x"]), float(row["c0y"])],  # TL
                    [float(row["c1x"]), float(row["c1y"])],  # TR
                    [float(row["c2x"]), float(row["c2y"])],  # BR
                    [float(row["c3x"]), float(row["c3y"])],  # BL
                ], dtype=np.float64)

                # IPPE_SQUARE returns exactly 2 solutions
                retval, rvecs, tvecs, reproj_errs = cv2.solvePnPGeneric(
                    obj_pts, img_pts, K, dist,
                    flags=cv2.SOLVEPNP_IPPE_SQUARE
                )

                # Select solution with tvec[2] > 0 (tag in front of camera)
                # and lower reprojection error — these should agree; if not,
                # reprojection error wins.
                rvec1, tvec1 = rvecs[0].flatten(), tvecs[0].flatten()
                rvec2, tvec2 = rvecs[1].flatten(), tvecs[1].flatten()
                
                err1 = float(np.squeeze(reproj_errs[0]))
                err2 = float(np.squeeze(reproj_errs[1]))

                # Primary criterion: tvec[2] > 0 (physically valid solution)
                sol1_valid = tvec1[2] > 0
                sol2_valid = tvec2[2] > 0

                if sol1_valid and sol2_valid:
                    # Both valid — pick lower reprojection error
                    rvec, tvec, err = (rvec1, tvec1, err1) if err1 <= err2 else (rvec2, tvec2, err2)
                elif sol1_valid:
                    rvec, tvec, err = rvec1, tvec1, err1
                elif sol2_valid:
                    rvec, tvec, err = rvec2, tvec2, err2
                else:
                    # Both solutions have tvec[2] < 0 — physically impossible
                    # Fall back to lower reprojection error and flag it
                    rvec, tvec, err = (rvec1, tvec1, err1) if err1 <= err2 else (rvec2, tvec2, err2)
                    print(f"  [WARN] {cam_name} frame {frame_idx:06d}: "
                          f"both IPPE solutions have z<0 — reproj_err={err:.3f}px")

                # Recompute reprojection error with selected solution
                # (IPPE_SQUARE's returned reproj_err is per-solution — use our own
                #  computation for consistency with the metric reported downstream)
                reproj = reprojection_error(obj_pts, rvec, tvec, K, dist, img_pts)
                reproj_errors.append(reproj)

                if reproj > REPROJ_BAD:
                    bad_reproj.append(frame_idx)
                elif reproj > REPROJ_WARN:
                    high_reproj.append(frame_idx)

                # Convert rvec → quaternion
                qx, qy, qz, qw = rvec_to_quaternion(rvec)

                # Timestamp from step01
                timestamp_s = ts_map.get(frame_idx, float("nan"))

                pose_rows.append({
                    "frame_idx":   frame_idx,
                    "timestamp_s": round(timestamp_s, 9),
                    "x_w":         round(float(tvec[0]), 8),
                    "y_w":         round(float(tvec[1]), 8),
                    "z_w":         round(float(tvec[2]), 8),
                    "qx":          round(qx, 8),
                    "qy":          round(qy, 8),
                    "qz":          round(qz, 8),
                    "qw":          round(qw, 8),
                    "reproj_err":  round(reproj, 6),
                })

        # ── Write world_pose.csv ──────────────────────────────────────────────
        fieldnames = [
            "frame_idx", "timestamp_s",
            "x_w", "y_w", "z_w",
            "qx", "qy", "qz", "qw",
            "reproj_err",
        ]
        with open(cam04_dir / "world_pose.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(pose_rows)

        # ── Summary ───────────────────────────────────────────────────────────
        err_arr = np.array(reproj_errors)
        summary = {
            "condition":          condition,
            "cam":                cam_name,
            "total_frames":       len(pose_rows),
            "reproj_err": {
                "mean":  round(float(np.mean(err_arr)), 4),
                "max":   round(float(np.max(err_arr)),  4),
                "min":   round(float(np.min(err_arr)),  4),
                "std":   round(float(np.std(err_arr)),  4),
            },
            "high_reproj_count":  len(high_reproj),   # > 3.0 px
            "bad_reproj_count":   len(bad_reproj),     # > 10.0 px
            "reproj_warn_thresh": REPROJ_WARN,
            "reproj_bad_thresh":  REPROJ_BAD,
        }

        with open(cam04_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # ── Print per-camera line ─────────────────────────────────────────────
        status = "OK"
        if len(bad_reproj) > 0:
            status = "BAD"
        elif len(high_reproj) > len(pose_rows) * 0.05:
            status = "WARN"

        print(f"  {cam_name}: {len(pose_rows)} frames | "
              f"reproj_err mean={summary['reproj_err']['mean']:.4f}px "
              f"max={summary['reproj_err']['max']:.4f}px | "
              f"high_reproj={len(high_reproj)} bad={len(bad_reproj)} | {status}")

    print()


def main():
    args   = parse_args()
    config = load_config(args.config)

    if args.all:
        results_dir = Path(config["paths"]["results_dir"])
        step03_root = results_dir / "step03"
        conditions  = sorted([d.name for d in step03_root.iterdir() if d.is_dir()])
        if not conditions:
            raise FileNotFoundError(f"No step03 results found under {step03_root}")
        print(f"Found {len(conditions)} condition(s) — processing all.")
    else:
        conditions = [condition_from_arg(args.bag)]

    for condition in conditions:
        process_condition(condition, config)


if __name__ == "__main__":
    main()