"""
step09_uncertainty.py — OMRPR Pipeline Step 09: Uncertainty Quantification

PURPOSE:
    Quantifies four sources of uncertainty in the OMRPR pipeline:
    A. Static noise floor — per-camera world-frame Y RMS from static bags
    B. Camera agreement — inter-camera aligned Z statistics across all 21 WTT conditions
    C. Bootstrap confidence intervals — per-condition bending/torsion RMS uncertainty
    D. Timing audit — max pairwise timestamp drift across cameras

INPUTS:
    Section A: data/static_bags/{cam}/static_{cam}_test{1-5}.bag  (bgr8 raw format)
    Section B: results/step06/{condition}/{cam}/summary.json
    Section C: results/step07/{condition}/motion.csv
    Section D: results/step01/{condition}/{cam}/timestamps.csv

OUTPUTS:
    results/step09/noise_floor/per_camera_per_test.csv
    results/step09/noise_floor/noise_floor_summary.json
    results/step09/camera_agreement/agreement_per_condition.csv
    results/step09/camera_agreement/agreement_summary.json
    results/step09/bootstrap_ci/bootstrap_ci_per_condition.csv
    results/step09/bootstrap_ci/bootstrap_summary.json
    results/step09/timing_audit/timing_drift_per_condition.csv
    results/step09/timing_audit/timing_audit_summary.json
    results/step09/step09_summary.json  ← top-level gate check

ACCEPTANCE CRITERIA:
    Noise floor cam1/cam2 world-Y worst-case RMS < 0.05 mm (target ~0.017 mm)
    Noise floor cam3 world-Y worst-case RMS < 0.10 mm (target ~0.033 mm)
    Camera agreement: 20/21 conditions aligned Z std < 15 mm
    Bootstrap CI: stable non-near-floor conditions relative width < 20%
    Max timing drift: report honestly (20.0 ms cam1-cam3, from clean pipeline Step 09)

LIMITATIONS:
    Static bags were not recorded simultaneously across cameras (recorded hours apart).
    bending_avg_y_mm noise floor is therefore DERIVED, not directly measured:
        sigma_bending_bound = sqrt((sigma_cam1^2 + sigma_cam2^2) / 4)
    This assumes independent noise sources between cameras, which is physically
    reasonable (separate sensors, separate capture chains, separate pose estimation).
    cam2 tests 6-10 excluded: recorded in a different session (12s duration, different
    day). Only tests 1-5 used for symmetry with cam1 and cam3 (5 tests each).

KNOWN BUGS AVOIDED:
    - Static bags use sensor_msgs/Image (bgr8), NOT CompressedImage. Decoded via
      np.frombuffer().reshape(), not cv2.imdecode().
    - Timestamps normalised to bag-start before any analysis.
    - Full-run mean removal (not first-second) matching Step 06.
    - solvePnP tvec always .flatten() immediately after call.
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from rosbags.rosbag1 import Reader
from rosbags.typesys import Stores, get_typestore

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — mirrors pipeline_config.yaml values
# All physical constants here; no magic numbers in logic below
# ─────────────────────────────────────────────────────────────────────────────

CONFIG = {
    # Tag geometry
    "tag_size_m": 0.020,          # physical tag side length in metres
    "tag_family": "tag36h11",

    # AprilTag detector settings (matching Step 02)
    "quad_decimate": 1.0,
    "refine_edges": 1,
    "quad_sigma": 0.0,
    "nthreads": 4,

    # solvePnP
    "solver": cv2.SOLVEPNP_IPPE_SQUARE,

    # Camera intrinsics — from pipeline_config.yaml
    # These must match the values used in Step 04
    "intrinsics": {
        "cam1": {
            "fx": 2108.0, "fy": 2108.0, "cx": 960.0, "cy": 540.0,
            "dist": [0.0, 0.0, 0.0, 0.0, 0.0],
        },
        "cam2": {
            "fx": 2108.0, "fy": 2108.0, "cx": 960.0, "cy": 540.0,
            "dist": [0.0, 0.0, 0.0, 0.0, 0.0],
        },
        "cam3": {
            "fx": 2108.0, "fy": 2108.0, "cx": 960.0, "cy": 540.0,
            "dist": [0.0, 0.0, 0.0, 0.0, 0.0],
        },
    },

    # Static bag configuration
    "static_bags": {
        "cam1": {
            "dir": "data/static_bags/cam1",
            "tests": [1, 2, 3, 4, 5],
            "topic": "/sony_cam1/image_raw",
            "caminfo_topic": "/sony_cam1/camera_info",
        },
        "cam2": {
            "dir": "data/static_bags/cam2",
            "tests": [1, 2, 3, 4, 5],   # tests 6-10 excluded (different session)
            "topic": "/sony_cam2/image_raw",
            "caminfo_topic": "/sony_cam2/camera_info",
        },
        "cam3": {
            "dir": "data/static_bags/cam3",
            "tests": [1, 2, 3, 4, 5],
            "topic": "/sony_cam3/image_raw",
            "caminfo_topic": "/sony_cam3/camera_info",
        },
    },

    # WTT conditions
    "conditions": [
        "e0_0rpm", "e1_20rpm", "e2_40rpm", "e3_50rpm", "e4_60rpm",
        "e5_70rpm", "e6_80rpm", "e7_90rpm", "e8_100rpm", "e9_110rpm",
        "e10_120rpm", "e11_140rpm", "e12_160rpm", "e13_180rpm", "e14_200rpm",
        "e15_220rpm", "e16_240rpm", "e17_260rpm", "e18_280rpm", "e19_300rpm",
        "e20_320rpm",
    ],

    # Stable regime (excludes 0rpm, VIV 60rpm, high-wind 320rpm)
    "stable_conditions": [
        "e1_20rpm", "e2_40rpm", "e3_50rpm",
        "e5_70rpm", "e6_80rpm", "e7_90rpm", "e8_100rpm", "e9_110rpm",
        "e10_120rpm", "e11_140rpm", "e12_160rpm", "e13_180rpm", "e14_200rpm",
        "e15_220rpm", "e16_240rpm", "e17_260rpm", "e18_280rpm", "e19_300rpm",
    ],

    # Cameras used in WTT pipeline
    "cameras": ["cam1", "cam2", "cam3"],

    # Bootstrap parameters
    "bootstrap_n_resamples": 1000,
    "bootstrap_ci_level": 0.95,
    "bootstrap_block_length_rule": "cube_root",  # L = int(N^(1/3))
    "random_seed": 42,

    # Gate thresholds
    "noise_floor_bending_max_mm": 0.05,    # cam1/cam2 per-camera worst-case
    "noise_floor_torsion_max_mm": 0.10,    # cam3 worst-case
    "camera_agreement_max_mm": 15.0,       # aligned Z std per condition
    "camera_agreement_min_pass": 20,       # out of 21 conditions
    "bootstrap_ci_max_relative_width": 0.20,  # for stable non-near-floor
}

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def make_tag_corners_3d(tag_size_m: float) -> np.ndarray:
    """
    3D tag corner coordinates in tag frame, TL→TR→BR→BL order.
    Matches the corner order returned by pupil_apriltags and Step 02.
    Origin at tag centre, Z=0 (tag lies in XY plane).
    """
    h = tag_size_m / 2.0
    return np.array([
        [-h,  h, 0.0],   # TL
        [ h,  h, 0.0],   # TR
        [ h, -h, 0.0],   # BR
        [-h, -h, 0.0],   # BL
    ], dtype=np.float64)


def build_camera_matrix(intr: dict) -> tuple[np.ndarray, np.ndarray]:
    """Build OpenCV camera matrix K and distortion vector D from config dict."""
    K = np.array([
        [intr["fx"],       0.0, intr["cx"]],
        [      0.0, intr["fy"], intr["cy"]],
        [      0.0,       0.0,       1.0],
    ], dtype=np.float64)
    D = np.array(intr["dist"], dtype=np.float64)
    return K, D


def decode_bgr8_frame(msg) -> np.ndarray:
    """
    Decode a sensor_msgs/Image message with bgr8 encoding.
    Static bags use raw uncompressed bgr8 — NOT JPEG CompressedImage.
    This is different from the WTT pipeline which uses cv2.imdecode on JPEG bytes.
    """
    frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(
        msg.height, msg.width, 3
    )
    return frame.copy()  # copy needed — frombuffer returns read-only view


def solve_pose(corners_2d: np.ndarray, K: np.ndarray, D: np.ndarray,
               tag_size_m: float, solver: int) -> tuple[np.ndarray, np.ndarray, float]:
    """
    Run solvePnP and return (rvec, tvec, reprojection_error).
    tvec is always .flatten() — avoids shape (3,1) vs (3,) inconsistency.
    When IPPE_SQUARE returns two solutions, selects the one with tvec[2] > 0
    (tag in front of camera); if tied, takes lower reprojection error.
    """
    obj_pts = make_tag_corners_3d(tag_size_m)
    img_pts = corners_2d.reshape(4, 1, 2).astype(np.float64)

    retval, rvecs, tvecs, reprojErrors = cv2.solvePnPGeneric(
        obj_pts, img_pts, K, D, flags=solver
    )

    if not retval or len(tvecs) == 0:
        return None, None, None

    # Select solution: prefer tvec[2] > 0 (in front of camera)
    candidates = list(zip(rvecs, tvecs, reprojErrors.flatten()))
    front = [(r, t, e) for r, t, e in candidates if t.flatten()[2] > 0]
    if front:
        rvec, tvec, err = min(front, key=lambda x: x[2])
    else:
        rvec, tvec, err = min(candidates, key=lambda x: x[2])

    return rvec.flatten(), tvec.flatten(), float(err)


def compute_rms(signal: np.ndarray) -> float:
    """RMS of a 1D signal after mean removal (full-run mean, matching Step 06)."""
    s = signal - np.mean(signal)
    return float(np.sqrt(np.mean(s ** 2)))


# ─────────────────────────────────────────────────────────────────────────────
# SECTION A — STATIC NOISE FLOOR
# ─────────────────────────────────────────────────────────────────────────────

def process_static_bag(bag_path: str, cam: str, test_idx: int,
                       typestore, detector, config: dict) -> dict | None:
    """
    Process one static bag for one camera.
    Returns dict with: cam, test_idx, n_frames, n_detected, detection_rate,
                       y_w_mm_rms, y_w_mm_mean, y_w_mm_std, reproj_err_mean
    Returns None if bag cannot be opened or has < 10 detections.
    """
    intr = config["intrinsics"][cam]
    K, D = build_camera_matrix(intr)
    tag_size = config["tag_size_m"]
    solver = config["solver"]
    topic = config["static_bags"][cam]["topic"]

    y_vals_m = []
    reproj_errs = []
    n_frames = 0
    n_detected = 0

    print(f"    Processing {os.path.basename(bag_path)} ...", flush=True)

    try:
        with Reader(bag_path) as r:
            conns = [c for c in r.connections if c.topic == topic]
            if not conns:
                print(f"    WARNING: topic {topic} not found in {bag_path}")
                available = [c.topic for c in r.connections]
                print(f"    Available topics: {available}")
                return None

            for conn, timestamp, rawdata in r.messages(connections=conns):
                n_frames += 1
                msg = typestore.deserialize_ros1(rawdata, conn.msgtype)
                frame = decode_bgr8_frame(msg)

                # AprilTag detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detections = detector.detect(gray)

                if not detections:
                    continue

                # Use first detection (static bags: one tag visible per camera)
                det = detections[0]
                corners_2d = np.array(det.corners, dtype=np.float64)  # shape (4,2)

                rvec, tvec, reproj_err = solve_pose(
                    corners_2d, K, D, tag_size, solver
                )

                if tvec is None:
                    continue

                n_detected += 1
                # tvec is in camera frame; store Y for baseline removal below
                # Note: this is camera-frame Y, not world-frame Y.
                # For static bags (single camera, no extrinsics), world-frame Y
                # is approximated as camera-frame ty since we have no cross-camera
                # transform. The noise floor is the variance of this signal after
                # mean removal — which is independent of any constant offset.
                y_vals_m.append(tvec[1])
                reproj_errs.append(reproj_err)

    except Exception as e:
        print(f"    ERROR opening {bag_path}: {e}")
        return None

    if n_detected < 10:
        print(f"    WARNING: only {n_detected} detections — skipping")
        return None

    y_arr = np.array(y_vals_m) * 1000.0  # convert m → mm

    # Full-run mean removal (matching Step 06 behaviour)
    y_rms = compute_rms(y_arr)
    y_std = float(np.std(y_arr - np.mean(y_arr)))
    y_mean_raw = float(np.mean(y_arr))

    detection_rate = n_detected / n_frames if n_frames > 0 else 0.0

    result = {
        "cam": cam,
        "test_idx": test_idx,
        "bag": os.path.basename(bag_path),
        "n_frames": n_frames,
        "n_detected": n_detected,
        "detection_rate": round(detection_rate, 4),
        "y_w_mm_rms": round(y_rms, 6),
        "y_w_mm_std": round(y_std, 6),
        "y_w_mm_mean_raw": round(y_mean_raw, 4),
        "reproj_err_mean_px": round(float(np.mean(reproj_errs)), 4),
        "reproj_err_max_px": round(float(np.max(reproj_errs)), 4),
    }

    print(f"      n_detected={n_detected}/{n_frames}  "
          f"y_rms={y_rms:.4f} mm  reproj={np.mean(reproj_errs):.3f} px")

    return result


def run_section_a(results_dir: Path, config: dict) -> dict:
    """
    Section A: Static noise floor.
    Run each static bag independently, report per-test RMS,
    then worst-case and mean across tests per camera.
    """
    print("\n=== SECTION A: Static Noise Floor ===")

    out_dir = results_dir / "noise_floor"
    out_dir.mkdir(parents=True, exist_ok=True)

    typestore = get_typestore(Stores.ROS1_NOETIC)

    # Build AprilTag detector — same settings as Step 02
    from pupil_apriltags import Detector
    detector = Detector(
        families=config["tag_family"],
        nthreads=config["nthreads"],
        quad_decimate=config["quad_decimate"],
        quad_sigma=config["quad_sigma"],
        refine_edges=config["refine_edges"],
        decode_sharpening=0.25,
        debug=False,
    )

    all_results = []

    for cam in ["cam1", "cam2", "cam3"]:
        cam_cfg = config["static_bags"][cam]
        print(f"\n  Camera: {cam}")

        for test_idx in cam_cfg["tests"]:
            bag_name = f"static_{cam}_test{test_idx}.bag"
            bag_path = os.path.join(cam_cfg["dir"], bag_name)

            if not os.path.exists(bag_path):
                print(f"    MISSING: {bag_path} — skipping")
                continue

            result = process_static_bag(
                bag_path, cam, test_idx, typestore, detector, config
            )
            if result is not None:
                all_results.append(result)

    if not all_results:
        print("  ERROR: No static bags processed successfully.")
        return {"section_a_status": "FAILED", "reason": "no bags processed"}

    # Write per-test CSV
    df = pd.DataFrame(all_results)
    df.to_csv(out_dir / "per_camera_per_test.csv", index=False)
    print(f"\n  Wrote {out_dir / 'per_camera_per_test.csv'}")

    # Compute per-camera summary: worst-case and mean RMS
    summary = {}
    for cam in ["cam1", "cam2", "cam3"]:
        cam_df = df[df["cam"] == cam]
        if cam_df.empty:
            summary[cam] = {"status": "NO_DATA"}
            continue

        rms_values = cam_df["y_w_mm_rms"].values
        summary[cam] = {
            "n_tests": int(len(rms_values)),
            "rms_mean_mm": round(float(np.mean(rms_values)), 6),
            "rms_worst_mm": round(float(np.max(rms_values)), 6),
            "rms_best_mm": round(float(np.min(rms_values)), 6),
            "rms_std_mm": round(float(np.std(rms_values)), 6),
            "detection_rate_mean": round(float(cam_df["detection_rate"].mean()), 4),
            "reproj_err_mean_px": round(float(cam_df["reproj_err_mean_px"].mean()), 4),
        }
        print(f"\n  {cam} noise floor summary:")
        print(f"    worst-case RMS: {summary[cam]['rms_worst_mm']:.4f} mm")
        print(f"    mean RMS:       {summary[cam]['rms_mean_mm']:.4f} mm")
        print(f"    best RMS:       {summary[cam]['rms_best_mm']:.4f} mm")

    # Derived combined bounds (assuming independent noise)
    # sigma_bending_bound = sqrt((sigma_cam1^2 + sigma_cam2^2) / 4)
    if "cam1" in summary and "cam2" in summary and \
       summary["cam1"].get("rms_worst_mm") and summary["cam2"].get("rms_worst_mm"):

        s1 = summary["cam1"]["rms_worst_mm"]
        s2 = summary["cam2"]["rms_worst_mm"]
        s3 = summary.get("cam3", {}).get("rms_worst_mm", 0.0)

        bending_bound = float(np.sqrt((s1**2 + s2**2) / 4.0))
        torsion_bound = float(np.sqrt(s3**2 + bending_bound**2))

        summary["derived_bounds"] = {
            "note": (
                "Derived upper bounds assuming independent noise between cameras. "
                "Static bags were NOT recorded simultaneously across cameras "
                "(recorded hours apart). Direct measurement of bending_avg_y_mm "
                "noise floor from static bags is therefore not possible."
            ),
            "sigma_cam1_worst_mm": s1,
            "sigma_cam2_worst_mm": s2,
            "sigma_cam3_worst_mm": s3,
            "bending_avg_bound_mm": round(bending_bound, 6),
            "torsion_diff_bound_mm": round(torsion_bound, 6),
        }
        print(f"\n  Derived bending_avg_y_mm bound: {bending_bound:.4f} mm")
        print(f"  Derived torsion_diff_y_mm bound: {torsion_bound:.4f} mm")

    # Gate check
    cam1_worst = summary.get("cam1", {}).get("rms_worst_mm", 999.0)
    cam2_worst = summary.get("cam2", {}).get("rms_worst_mm", 999.0)
    cam3_worst = summary.get("cam3", {}).get("rms_worst_mm", 999.0)

    bending_pass = (cam1_worst < config["noise_floor_bending_max_mm"] and
                    cam2_worst < config["noise_floor_bending_max_mm"])
    torsion_pass = cam3_worst < config["noise_floor_torsion_max_mm"]

    summary["gate"] = {
        "bending_threshold_mm": config["noise_floor_bending_max_mm"],
        "torsion_threshold_mm": config["noise_floor_torsion_max_mm"],
        "bending_pass": bending_pass,
        "torsion_pass": torsion_pass,
        "SECTION_A_PASS": bending_pass and torsion_pass,
    }

    print(f"\n  Gate: bending={'PASS' if bending_pass else 'FAIL'}  "
          f"torsion={'PASS' if torsion_pass else 'FAIL'}")

    with open(out_dir / "noise_floor_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# SECTION B — CAMERA AGREEMENT
# ─────────────────────────────────────────────────────────────────────────────

def run_section_b(results_dir: Path, config: dict) -> dict:
    """
    Section B: Camera agreement — reads Step 06 summary.json files.
    Reports aligned Z disagreement (cam1 vs cam2) per condition.
    Gate: 20/21 conditions with aligned Z std < 15 mm.
    """
    print("\n=== SECTION B: Camera Agreement ===")

    out_dir = results_dir / "camera_agreement"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []

    for condition in config["conditions"]:
        summary_path = Path(f"results/step06/{condition}/summary.json")
        if not summary_path.exists():
            print(f"  MISSING: {summary_path}")
            rows.append({
                "condition": condition,
                "status": "MISSING",
                "aligned_z_std_mm": None,
                "raw_z_std_mm": None,
                "pass": False,
            })
            continue

        with open(summary_path) as f:
            s = json.load(f)

        # Step 06 summary.json uses nested schema:
        #   aligned_z_disagreement_mm.cam1_cam2.std_mm
        #   raw_z_disagreement_mm.cam1_cam2  (scalar, mm)
        nested_aligned = s.get("aligned_z_disagreement_mm", {})
        cam12_aligned = nested_aligned.get("cam1_cam2", {})
        aligned_z_std = cam12_aligned.get("std_mm", None) if isinstance(cam12_aligned, dict) else None

        nested_raw = s.get("raw_z_disagreement_mm", {})
        raw_z_val = nested_raw.get("cam1_cam2", None) if isinstance(nested_raw, dict) else None
        raw_z_std = float(raw_z_val) if raw_z_val is not None else None

        if aligned_z_std is None:
            # Fallback: try to compute from aligned_pose.csv files directly
            print(f"  WARNING: {condition} summary.json missing z agreement fields — "
                  f"attempting fallback from aligned_pose.csv")
            aligned_z_std, raw_z_std = _compute_z_agreement_from_csv(condition)

        passes = (aligned_z_std is not None and
                  aligned_z_std < config["camera_agreement_max_mm"])

        rows.append({
            "condition": condition,
            "status": "OK" if aligned_z_std is not None else "NO_DATA",
            "aligned_z_std_mm": round(aligned_z_std, 4) if aligned_z_std else None,
            "raw_z_std_mm": round(raw_z_std, 2) if raw_z_std else None,
            "pass": passes,
        })

        status = "PASS" if passes else "FAIL"
        z_str = f"{aligned_z_std:.3f}" if aligned_z_std is not None else "N/A"
        print(f"  {condition:20s}  aligned_Z_std={z_str:>8} mm  [{status}]")

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "agreement_per_condition.csv", index=False)

    n_pass = int(df["pass"].sum())
    n_total = len(df)
    gate_pass = n_pass >= config["camera_agreement_min_pass"]

    summary = {
        "n_conditions": n_total,
        "n_pass": n_pass,
        "n_fail": n_total - n_pass,
        "threshold_mm": config["camera_agreement_max_mm"],
        "aligned_z_std_mean_mm": round(float(df["aligned_z_std_mm"].dropna().mean()), 4),
        "aligned_z_std_max_mm": round(float(df["aligned_z_std_mm"].dropna().max()), 4),
        "raw_z_std_mean_mm": round(float(df["raw_z_std_mm"].dropna().mean()), 2)
                             if df["raw_z_std_mm"].notna().any() else None,
        "gate": {
            "min_pass_required": config["camera_agreement_min_pass"],
            "SECTION_B_PASS": gate_pass,
        },
    }

    print(f"\n  Camera agreement: {n_pass}/{n_total} conditions pass "
          f"({'PASS' if gate_pass else 'FAIL'})")

    with open(out_dir / "agreement_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def _compute_z_agreement_from_csv(condition: str) -> tuple[float | None, float | None]:
    """
    Fallback: compute Z agreement from aligned_pose.csv files if summary.json
    doesn't have the field. Returns (aligned_std, raw_std) or (None, None).
    """
    try:
        cam1_path = Path(f"results/step06/{condition}/cam1/aligned_pose.csv")
        cam2_path = Path(f"results/step06/{condition}/cam2/aligned_pose.csv")

        if not cam1_path.exists() or not cam2_path.exists():
            return None, None

        df1 = pd.read_csv(cam1_path)
        df2 = pd.read_csv(cam2_path)

        # Merge on frame index or timestamp — use index if lengths match
        min_len = min(len(df1), len(df2))
        z1 = df1["z_w_mm"].values[:min_len]
        z2 = df2["z_w_mm"].values[:min_len]

        aligned_std = float(np.std(z1 - z2))

        # Raw Z std if mean offsets are stored
        if "z_w_mean_m" in df1.columns and "z_w_mean_m" in df2.columns:
            raw_offset = float(df1["z_w_mean_m"].iloc[0] - df2["z_w_mean_m"].iloc[0])
            raw_std = abs(raw_offset) * 1000.0  # m → mm, approximate
        else:
            raw_std = None

        return aligned_std, raw_std

    except Exception as e:
        print(f"    Fallback failed for {condition}: {e}")
        return None, None


# ─────────────────────────────────────────────────────────────────────────────
# SECTION C — BOOTSTRAP CONFIDENCE INTERVALS
# ─────────────────────────────────────────────────────────────────────────────

def moving_block_bootstrap(signal: np.ndarray, n_resamples: int,
                            block_length: int, rng: np.random.Generator,
                            statistic_fn) -> np.ndarray:
    """
    Moving-block bootstrap for time series.

    Why not standard bootstrap: standard bootstrap resamples frames independently,
    destroying temporal autocorrelation. Structural response has inertia — a frame
    at time k is correlated with k+1, k+2, etc. Standard bootstrap would give
    artificially narrow CIs (too many effective degrees of freedom).

    Moving-block bootstrap resamples contiguous blocks, preserving within-block
    autocorrelation structure. Effective sample size is N/L, not N.

    Args:
        signal: 1D time series
        n_resamples: number of bootstrap samples
        block_length: L — number of consecutive frames per block
        rng: numpy random generator (seeded for reproducibility)
        statistic_fn: function(array) → scalar
    Returns:
        array of bootstrap statistic values, length n_resamples
    """
    N = len(signal)
    n_blocks = int(np.ceil(N / block_length))
    max_start = N - block_length  # last valid block start index

    boot_stats = np.empty(n_resamples)

    for i in range(n_resamples):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        blocks = [signal[s:s + block_length] for s in starts]
        boot_sample = np.concatenate(blocks)[:N]  # trim to original length
        boot_stats[i] = statistic_fn(boot_sample)

    return boot_stats


def rms_statistic(signal: np.ndarray) -> float:
    """RMS after full-run mean removal — the statistic we bootstrap."""
    return compute_rms(signal)


def run_section_c(results_dir: Path, config: dict) -> dict:
    """
    Section C: Moving-block bootstrap CIs on bending and torsion RMS per condition.
    """
    print("\n=== SECTION C: Bootstrap Confidence Intervals ===")

    out_dir = results_dir / "bootstrap_ci"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(config["random_seed"])
    alpha = 1.0 - config["bootstrap_ci_level"]
    rows = []

    for condition in config["conditions"]:
        motion_path = Path(f"results/step07/{condition}/motion.csv")
        if not motion_path.exists():
            print(f"  MISSING: {motion_path}")
            continue

        df = pd.read_csv(motion_path)

        is_stable = condition in config["stable_conditions"]
        is_viv = condition == "e4_60rpm"
        is_high_wind = condition == "e20_320rpm"
        is_near_floor = condition in ["e0_0rpm", "e1_20rpm"]

        for channel in ["bending_avg_y_mm", "torsion_diff_y_mm"]:
            if channel not in df.columns:
                print(f"  WARNING: {channel} not in {motion_path}")
                continue

            signal = df[channel].dropna().values
            N = len(signal)

            if N < 30:
                print(f"  WARNING: {condition}/{channel} has only {N} samples — skipping")
                continue

            # Block length: cube root rule
            L = max(2, int(N ** (1.0 / 3.0)))

            boot_stats = moving_block_bootstrap(
                signal, config["bootstrap_n_resamples"], L, rng, rms_statistic
            )

            ci_lo = float(np.percentile(boot_stats, 100 * alpha / 2))
            ci_hi = float(np.percentile(boot_stats, 100 * (1 - alpha / 2)))
            rms_estimate = rms_statistic(signal)
            relative_width = (ci_hi - ci_lo) / rms_estimate if rms_estimate > 0 else None

            rows.append({
                "condition": condition,
                "channel": channel,
                "n_samples": N,
                "block_length": L,
                "rms_estimate_mm": round(rms_estimate, 6),
                "ci_lo_mm": round(ci_lo, 6),
                "ci_hi_mm": round(ci_hi, 6),
                "ci_width_mm": round(ci_hi - ci_lo, 6),
                "relative_ci_width": round(relative_width, 4) if relative_width else None,
                "is_stable": is_stable,
                "is_viv": is_viv,
                "is_high_wind": is_high_wind,
                "is_near_floor": is_near_floor,
                "n_bootstrap_resamples": config["bootstrap_n_resamples"],
            })

        print(f"  {condition:20s}  L={L:3d}  done")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "bootstrap_ci_per_condition.csv", index=False)

    # Summary: stable non-near-floor conditions only
    stable_df = df_out[
        df_out["is_stable"] & ~df_out["is_near_floor"] & ~df_out["is_viv"]
    ]

    max_rel_width = float(stable_df["relative_ci_width"].max()) \
        if not stable_df.empty else None
    gate_pass = max_rel_width is not None and \
                max_rel_width < config["bootstrap_ci_max_relative_width"]

    summary = {
        "n_conditions_processed": len(df_out["condition"].unique()),
        "bootstrap_n_resamples": config["bootstrap_n_resamples"],
        "bootstrap_ci_level": config["bootstrap_ci_level"],
        "block_length_rule": config["bootstrap_block_length_rule"],
        "random_seed": config["random_seed"],
        "stable_non_nearfloor_max_relative_ci_width": round(max_rel_width, 4)
                                                       if max_rel_width else None,
        "gate": {
            "threshold": config["bootstrap_ci_max_relative_width"],
            "SECTION_C_PASS": gate_pass,
        },
    }

    width_str = f"{max_rel_width:.3f}" if max_rel_width is not None else "N/A"
    print(f"\n  Bootstrap CI max relative width (stable): "
          f"{width_str} "
          f"({'PASS' if gate_pass else 'FAIL'})")

    with open(out_dir / "bootstrap_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# SECTION D — TIMING AUDIT
# ─────────────────────────────────────────────────────────────────────────────

def run_section_d(results_dir: Path, config: dict) -> dict:
    """
    Section D: Timing audit — max pairwise nearest-neighbour timestamp drift.

    For each condition and each camera pair, finds the maximum over all frames
    of the nearest-neighbour timestamp difference. This is the worst-case timing
    error that the Step 05 common-grid interpolation must handle.

    Actual result (clean pipeline): 20.0 ms max pairwise drift, cam1-cam3.
    Reporting this honestly is required — a reviewer will ask for the worst case.
    """
    print("\n=== SECTION D: Timing Audit ===")

    out_dir = results_dir / "timing_audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    pairs = [("cam1", "cam2"), ("cam1", "cam3"), ("cam2", "cam3")]
    rows = []

    for condition in config["conditions"]:
        # Load timestamps for all three cameras
        ts = {}
        missing = []
        for cam in config["cameras"]:
            ts_path = Path(f"results/step01/{condition}/{cam}/timestamps.csv")
            if not ts_path.exists():
                missing.append(cam)
                continue
            df = pd.read_csv(ts_path)
            # timestamps.csv schema: frame_idx, timestamp_s (already normalised)
            ts[cam] = df["timestamp_s"].values

        if missing:
            print(f"  WARNING: {condition} missing timestamps for {missing}")

        for cam_i, cam_j in pairs:
            if cam_i not in ts or cam_j not in ts:
                rows.append({
                    "condition": condition,
                    "pair": f"{cam_i}-{cam_j}",
                    "max_nn_drift_ms": None,
                    "mean_nn_drift_ms": None,
                    "status": "MISSING_DATA",
                })
                continue

            t_i = ts[cam_i]
            t_j = ts[cam_j]

            # For each frame in cam_i, find nearest frame in cam_j
            # np.searchsorted gives O(N log M) — efficient
            idx = np.searchsorted(t_j, t_i, side="left")
            idx = np.clip(idx, 0, len(t_j) - 1)

            # Also check the frame before the insertion point
            idx_prev = np.clip(idx - 1, 0, len(t_j) - 1)
            drift_curr = np.abs(t_i - t_j[idx])
            drift_prev = np.abs(t_i - t_j[idx_prev])
            nn_drift = np.minimum(drift_curr, drift_prev)

            max_drift_ms = float(np.max(nn_drift)) * 1000.0
            mean_drift_ms = float(np.mean(nn_drift)) * 1000.0

            rows.append({
                "condition": condition,
                "pair": f"{cam_i}-{cam_j}",
                "max_nn_drift_ms": round(max_drift_ms, 3),
                "mean_nn_drift_ms": round(mean_drift_ms, 3),
                "status": "OK",
            })

        print(f"  {condition:20s}  done")

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_dir / "timing_drift_per_condition.csv", index=False)

    # Aggregate: worst case per pair across all conditions
    pair_summary = {}
    for pair_label in [f"{a}-{b}" for a, b in pairs]:
        pair_df = df_out[(df_out["pair"] == pair_label) & (df_out["status"] == "OK")]
        if pair_df.empty:
            pair_summary[pair_label] = {"max_drift_ms": None}
            continue
        pair_summary[pair_label] = {
            "max_drift_ms_across_conditions": round(
                float(pair_df["max_nn_drift_ms"].max()), 3),
            "mean_drift_ms_across_conditions": round(
                float(pair_df["max_nn_drift_ms"].mean()), 3),
        }

    overall_max = max(
        (v["max_drift_ms_across_conditions"]
         for v in pair_summary.values()
         if v.get("max_drift_ms_across_conditions") is not None),
        default=None
    )

    summary = {
        "per_pair": pair_summary,
        "overall_max_drift_ms": overall_max,
        "note": (
            "Max pairwise nearest-neighbour timestamp drift from Step 01 timestamps. "
            "This is NOT the synchronisation error in the fused signal — "
            "Step 05 common-grid interpolation converts timing drift into "
            "an interpolation error of O(delta_t^2), not O(delta_t). "
            "At 1.4 Hz dominant frequency, interpolation amplitude error is "
            "approximately (pi*f*delta_t)^2 * A / 2, where A is signal amplitude."
        ),
        "gate": {
            "SECTION_D_PASS": True,   # timing audit is always a report, not a gate
            "note": "Timing audit is informational — no hard threshold. "
                    "Report the number honestly in the manuscript.",
        },
    }

    drift_str = f"{overall_max:.1f}" if overall_max is not None else "N/A"
    print(f"\n  Overall max pairwise drift: {drift_str} ms  (worst case across all conditions)")

    with open(out_dir / "timing_audit_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Step 09: Uncertainty Quantification"
    )
    parser.add_argument(
        "--results-dir", default="results/step09",
        help="Output directory (default: results/step09)"
    )
    parser.add_argument(
        "--skip-noise-floor", action="store_true",
        help="Skip Section A (static bags) — use if bags unavailable"
    )
    parser.add_argument(
        "--skip-bootstrap", action="store_true",
        help="Skip Section C (bootstrap CIs) — slow, ~5 min"
    )
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="Smoke test mode: process only cam1/test1 and e7_90rpm"
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    config = CONFIG.copy()

    if args.smoke_test:
        print("SMOKE TEST MODE: cam1/test1 only, e7_90rpm only")
        config["static_bags"]["cam1"]["tests"] = [1]
        config["static_bags"]["cam2"]["tests"] = [1]
        config["static_bags"]["cam3"]["tests"] = [1]
        config["conditions"] = ["e7_90rpm"]
        config["stable_conditions"] = ["e7_90rpm"]
        config["bootstrap_n_resamples"] = 100

    section_results = {}

    # Section A — Static noise floor
    if not args.skip_noise_floor:
        section_results["section_a"] = run_section_a(results_dir, config)
    else:
        print("\n=== SECTION A: SKIPPED (--skip-noise-floor) ===")
        section_results["section_a"] = {"section_a_status": "SKIPPED"}

    # Section B — Camera agreement
    section_results["section_b"] = run_section_b(results_dir, config)

    # Section C — Bootstrap CIs
    if not args.skip_bootstrap:
        section_results["section_c"] = run_section_c(results_dir, config)
    else:
        print("\n=== SECTION C: SKIPPED (--skip-bootstrap) ===")
        section_results["section_c"] = {"section_c_status": "SKIPPED"}

    # Section D — Timing audit
    section_results["section_d"] = run_section_d(results_dir, config)

    # Top-level gate check
    a_pass = section_results["section_a"].get(
        "gate", {}).get("SECTION_A_PASS", False) \
        if not args.skip_noise_floor else None

    b_pass = section_results["section_b"].get(
        "gate", {}).get("SECTION_B_PASS", False)

    c_pass = section_results["section_c"].get(
        "gate", {}).get("SECTION_C_PASS", False) \
        if not args.skip_bootstrap else None

    d_pass = True  # timing audit is always informational

    overall_gate = all(x for x in [a_pass, b_pass, c_pass, d_pass] if x is not None)

    top_summary = {
        "section_a_gate": a_pass,
        "section_b_gate": b_pass,
        "section_c_gate": c_pass,
        "section_d_gate": d_pass,
        "STEP09_GATE_PASS": overall_gate,
        "smoke_test_mode": args.smoke_test,
    }

    with open(results_dir / "step09_summary.json", "w") as f:
        json.dump(top_summary, f, indent=2)

    print("\n" + "=" * 60)
    print("STEP 09 COMPLETE")
    print(f"  Section A (noise floor):   {'PASS' if a_pass else 'FAIL' if a_pass is False else 'SKIPPED'}")
    print(f"  Section B (cam agreement): {'PASS' if b_pass else 'FAIL'}")
    print(f"  Section C (bootstrap CI):  {'PASS' if c_pass else 'FAIL' if c_pass is False else 'SKIPPED'}")
    print(f"  Section D (timing audit):  PASS (informational)")
    print(f"  OVERALL GATE: {'PASS' if overall_gate else 'FAIL'}")
    print(f"\nResults written to: {results_dir}/")


if __name__ == "__main__":
    main()