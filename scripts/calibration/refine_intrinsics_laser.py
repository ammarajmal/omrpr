#!/usr/bin/env python3
"""PROVISIONAL laser-corrected intrinsics from WTT CameraInfo priors.

This is not physical Step 02 calibration. It fits fx, fy, cx, cy per camera using
official-AprilTag corner reprojection and scale-invariant, non-simultaneous
condition-level benchmarking against the Tunnel A laser series. Distortion is fixed.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import apriltag
import cv2
import numpy as np
import numpy.typing as npt
import yaml
from rosbags.highlevel import AnyReader
from scipy.optimize import differential_evolution, minimize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from omrpr_analysis.paths import ProjectPaths  # noqa: E402
from scripts.camera.estimate_displacement import (  # noqa: E402
    CAMS,
    TAG_OBJECT_POINTS,
    MarkerTrack,
    ProvisionalIntrinsics,
    amplitude_3d_rms,
    axis_deviation_mm,
    find_condition_bags,
    load_provisional_intrinsics,
    pca_dominant_axis,
    solve_tag_pose,
)

VIV_ANOMALY_RPM = 60.0
WEIGHTS = {"reprojection": 0.35, "laser_agreement": 0.55, "prior_drift": 0.10}
REPROJECTION_SCALE_PX = 0.5
MAX_REPROJECTION_FRAMES_PER_CONDITION = 24


def detect_and_cache(conditions: list[tuple[str, float, Path]], output: Path) -> None:
    arrays: dict[str, npt.NDArray] = {}
    for condition, _rpm, bag in conditions:
        for cam in CAMS:
            detector = apriltag.apriltag("tag36h11")
            timestamps: list[int] = []
            corners: list[npt.NDArray[np.float64]] = []
            with AnyReader([bag]) as reader:
                conns = [
                    c for c in reader.connections if c.topic == f"/sony_{cam}/image_raw/compressed"
                ]
                for conn, timestamp_ns, raw in reader.messages(connections=conns):
                    msg = reader.deserialize(raw, conn.msgtype)
                    image = cv2.imdecode(
                        np.frombuffer(bytes(msg.data), dtype=np.uint8), cv2.IMREAD_GRAYSCALE
                    )
                    if image is None:
                        continue
                    detections = detector.detect(image)
                    if not detections:
                        continue
                    best = max(detections, key=lambda d: d["margin"])
                    timestamps.append(timestamp_ns)
                    corners.append(np.asarray(best["lb-rb-rt-lt"], dtype=np.float64))
            prefix = f"{cam}__{condition}"
            arrays[f"{prefix}__timestamps_ns"] = np.asarray(timestamps, dtype=np.int64)
            arrays[f"{prefix}__corners"] = np.asarray(corners, dtype=np.float64)
            print(f"detected {cam} {condition}: n={len(corners)}", flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **arrays)


def load_laser(path: Path) -> dict[float, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {float(r["rpm"]): float(r["bending_rms_mm"]) for r in csv.DictReader(handle)}


def make_intrinsics(params: npt.ArrayLike, seed: ProvisionalIntrinsics) -> ProvisionalIntrinsics:
    fx, fy, cx, cy = np.asarray(params, dtype=np.float64)
    k = np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])
    return ProvisionalIntrinsics(k=k, d=seed.d.copy(), distortion_model=seed.distortion_model)


def pose_for_corners(
    corners: npt.NDArray[np.float64], intrinsics: ProvisionalIntrinsics
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]] | None:
    pts = corners.reshape(-1, 1, 2).astype(np.float64)
    undistorted = cv2.undistortPoints(pts, intrinsics.k, intrinsics.d, P=intrinsics.k)
    # ITERATIVE is deliberate here: IPPE_SQUARE requires a different strict object-
    # point order than the detector's lb-rb-rt-lt convention. The displacement
    # pipeline retains its already-established solver for comparability, while this
    # reprojection-only nuisance pose must minimize the four observed corner residuals.
    ok, rvec, tvec = cv2.solvePnP(
        TAG_OBJECT_POINTS, undistorted, intrinsics.k, None, flags=cv2.SOLVEPNP_ITERATIVE
    )
    return (rvec, tvec) if ok else None


def reprojection_errors(
    sample: npt.NDArray[np.float64], intrinsics: ProvisionalIntrinsics
) -> npt.NDArray[np.float64]:
    errors: list[float] = []
    for corners in sample:
        pose = pose_for_corners(corners, intrinsics)
        if pose is None:
            errors.extend([10.0] * 4)
            continue
        projected, _ = cv2.projectPoints(
            TAG_OBJECT_POINTS, pose[0], pose[1], intrinsics.k, intrinsics.d
        )
        errors.extend(np.linalg.norm(projected.reshape(-1, 2) - corners, axis=1))
    return np.asarray(errors)


def tracks_and_correlation(
    cam: str,
    intrinsics: ProvisionalIntrinsics,
    condition_rows: list[tuple[str, float, Path]],
    cache: np.lib.npyio.NpzFile,
    laser: dict[float, float],
) -> tuple[float, dict[str, MarkerTrack], npt.NDArray[np.float64], str]:
    tracks: dict[str, MarkerTrack] = {}
    for condition, _rpm, _bag in condition_rows:
        prefix = f"{cam}__{condition}"
        ts = cache[f"{prefix}__timestamps_ns"]
        corners = cache[f"{prefix}__corners"]
        positions: list[npt.NDArray[np.float64]] = []
        kept: list[int] = []
        for timestamp, frame_corners in zip(ts, corners, strict=True):
            tvec = solve_tag_pose(frame_corners, intrinsics)
            if tvec is not None:
                kept.append(int(timestamp))
                positions.append(tvec)
        tracks[condition] = MarkerTrack(
            np.asarray(kept, dtype=np.int64), np.asarray(positions, dtype=np.float64)
        )
    best = max(tracks, key=lambda name: amplitude_3d_rms(tracks[name]))
    axis = pca_dominant_axis(tracks[best])
    camera_values: list[float] = []
    laser_values: list[float] = []
    for condition, rpm, _bag in condition_rows:
        if rpm == VIV_ANOMALY_RPM or rpm not in laser:
            continue
        camera_values.append(float(axis_deviation_mm(tracks[condition], axis).std()))
        laser_values.append(laser[rpm])
    correlation = float(np.corrcoef(camera_values, laser_values)[0, 1])
    return correlation, tracks, axis, best


def sampled_corners(
    cam: str, condition_rows: list[tuple[str, float, Path]], cache: np.lib.npyio.NpzFile
) -> npt.NDArray[np.float64]:
    samples = []
    for condition, _rpm, _bag in condition_rows:
        corners = cache[f"{cam}__{condition}__corners"]
        if len(corners):
            idx = np.linspace(
                0, len(corners) - 1, min(len(corners), MAX_REPROJECTION_FRAMES_PER_CONDITION)
            ).astype(int)
            samples.append(corners[idx])
    return np.concatenate(samples)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-cache", action="store_true")
    parser.add_argument("--maxiter", type=int, default=18)
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    output_dir = paths.root / "outputs/calibration/step02b_laser_corrected_intrinsics"
    cache_path = output_dir / "official_apriltag_corner_cache.npz"
    conditions = find_condition_bags(paths.raw / "camera/rosbag", "wtt-main")
    if not conditions:
        raise RuntimeError("No WTT bags found")
    if not (args.reuse_cache and cache_path.exists()):
        detect_and_cache(conditions, cache_path)
    laser = load_laser(paths.interim / "condition-matched/laser_tunnel_a_2024.csv")
    summary: dict[str, dict] = {}
    with np.load(cache_path) as cache:
        for cam in CAMS:
            seed = load_provisional_intrinsics(cam, paths.root)
            x0 = np.array([seed.k[0, 0], seed.k[1, 1], seed.k[0, 2], seed.k[1, 2]])
            bounds = [
                (0.75 * x0[0], 1.25 * x0[0]),
                (0.75 * x0[1], 1.25 * x0[1]),
                (max(0.0, x0[2] - 120), min(1919.0, x0[2] + 120)),
                (max(0.0, x0[3] - 100), min(1079.0, x0[3] + 100)),
            ]
            reproj_sample = sampled_corners(cam, conditions, cache)
            before_corr, _tracks, before_axis, before_best = tracks_and_correlation(
                cam, seed, conditions, cache, laser
            )
            before_err = reprojection_errors(reproj_sample, seed)
            eval_count = 0

            def objective(
                params: npt.NDArray[np.float64],
                seed: ProvisionalIntrinsics = seed,
                reproj_sample: npt.NDArray[np.float64] = reproj_sample,
                cam: str = cam,
                x0: npt.NDArray[np.float64] = x0,
            ) -> float:
                nonlocal eval_count
                candidate = make_intrinsics(params, seed)
                reproj = float(np.mean(reprojection_errors(reproj_sample, candidate)))
                corr, _tracks, _axis, _best = tracks_and_correlation(
                    cam, candidate, conditions, cache, laser
                )
                normalized_drift = (params - x0) / np.array([0.25 * x0[0], 0.25 * x0[1], 120, 100])
                cost = (
                    WEIGHTS["reprojection"] * (reproj / REPROJECTION_SCALE_PX)
                    + WEIGHTS["laser_agreement"] * (1.0 - corr)
                    + WEIGHTS["prior_drift"] * float(np.mean(normalized_drift**2))
                )
                eval_count += 1
                if eval_count % 10 == 0:
                    print(
                        f"{cam} eval={eval_count} cost={cost:.6f} "
                        f"reproj={reproj:.4f}px r={corr:.4f}",
                        flush=True,
                    )
                return cost

            global_result = differential_evolution(
                objective,
                bounds=bounds,
                seed=20260803,
                maxiter=args.maxiter,
                popsize=5,
                polish=False,
                workers=1,
                updating="immediate",
            )
            result = minimize(
                objective,
                global_result.x,
                method="Powell",
                bounds=bounds,
                options={"maxiter": 80, "xtol": 1e-5, "ftol": 1e-7},
            )
            refined = make_intrinsics(result.x, seed)
            after_corr, _tracks, after_axis, after_best = tracks_and_correlation(
                cam, refined, conditions, cache, laser
            )
            after_err = reprojection_errors(reproj_sample, refined)
            record = {
                "status": "PROVISIONAL_LASER_CORRECTED",
                "camera": cam,
                "rationale": (
                    "Provisional-only intrinsics correction seeded exclusively from this project's "
                    "WTT CameraInfo prior. Per-camera fx, fy, cx, cy minimize a documented joint "
                    "AprilTag reprojection / scale-invariant non-simultaneous condition-level "
                    "benchmarking objective; D is fixed. This is not a substitute for real Step 02 "
                    "physical target calibration and is not the manuscript's Tunnel B LDV "
                    "reference."
                ),
                "distortion_model": refined.distortion_model,
                "K": refined.k.reshape(-1).tolist(),
                "D": refined.d.tolist(),
                "fx": float(refined.k[0, 0]),
                "fy": float(refined.k[1, 1]),
                "cx": float(refined.k[0, 2]),
                "cy": float(refined.k[1, 2]),
                "optimization": {
                    "method": "differential_evolution_then_bounded_Powell",
                    "success": bool(result.success),
                    "message": str(result.message),
                    "evaluations": eval_count,
                    "objective_weights": WEIGHTS,
                    "laser_term": "1 - Pearson r; per-camera PCA-projected RMS; rpm=60 excluded",
                    "reprojection_sampling": (
                        f"up to {MAX_REPROJECTION_FRAMES_PER_CONDITION} stratified frames "
                        "per condition"
                    ),
                },
                "metrics": {
                    "before_mean_reprojection_error_px": float(before_err.mean()),
                    "after_mean_reprojection_error_px": float(after_err.mean()),
                    "before_max_reprojection_error_px": float(before_err.max()),
                    "after_max_reprojection_error_px": float(after_err.max()),
                    "before_laser_bending_pearson": before_corr,
                    "after_laser_bending_pearson": after_corr,
                    "before_pca_axis": before_axis.tolist(),
                    "after_pca_axis": after_axis.tolist(),
                    "before_pca_condition": before_best,
                    "after_pca_condition": after_best,
                },
            }
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / f"{cam}.yaml").write_text(
                yaml.safe_dump(record, sort_keys=False), encoding="utf-8"
            )
            summary[cam] = record
            print(
                f"wrote {cam}: reproj {before_err.mean():.4f}->{after_err.mean():.4f}px, "
                f"r {before_corr:.4f}->{after_corr:.4f}",
                flush=True,
            )
    (output_dir / "optimization_summary.yaml").write_text(
        yaml.safe_dump(
            {"status": "PROVISIONAL_LASER_CORRECTED", "cameras": summary}, sort_keys=False
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
