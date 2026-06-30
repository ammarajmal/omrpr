"""
Step 05 — Cross-Camera Synchronization
=======================================
Purpose:  Resample all three cameras onto a common 60 Hz time grid so that
          downstream steps can compare per-timestep values across cameras.

          The cameras were started sequentially (not hardware-triggered).
          cam1 starts at t=0.000000s, cam2 at t=0.011891s, cam3 at t=0.000075s
          (for e7_90rpm — varies slightly per condition).
          Step 01 already normalized timestamps to bag-start, so no raw epoch
          offsets exist here. The inter-camera offsets are small (< 15 ms).

Strategy:
          1. Load world_pose.csv per camera (from Step 04).
          2. Find the common time window: [max(t_min), min(t_max)] across cameras.
             This guarantees no extrapolation — every grid point is within every
             camera's data range.
          3. Build common grid: t_grid = np.arange(n_frames) / 60.0
             (NOT np.arange(0, dur, 1/60.0) — avoids float step accumulation drift)
             where n_frames = floor((t_end - t_start) * 60) + 1
          4. Interpolate x_w, y_w, z_w, qx, qy, qz, qw with scipy interp1d
             (bounds_error=True — fails loudly if grid escapes data range).
          5. Renormalize quaternions after interpolation.
          6. reproj_err is NOT interpolated — it is a per-detection metric,
             not a continuous signal.

Inputs:   results/step04/{condition}/{cam}/world_pose.csv
          config/pipeline_config.yaml

Outputs:  results/step05/{condition}/{cam}/synced_pose.csv
          results/step05/{condition}/summary.json

Schema (synced_pose.csv):
          t_s     float  — common grid time in seconds (identical across cameras)
          x_w     float  — interpolated lateral position (metres, camera frame)
          y_w     float  — interpolated vertical position (metres, camera frame)
          z_w     float  — interpolated depth (metres, camera frame)
          qx,qy,qz,qw  float  — interpolated + renormalized quaternion

Limits:
          Interpolation is linear. Acceptable because delta-t between frames (~16.7ms)
          is much smaller than the primary structural oscillation period (~0.7 s).
          Quaternion linear interpolation + renormalization is indistinguishable
          from SLERP at < 0.1 degree inter-frame rotation.
          MAX_INTERP_GAP guard: any consecutive-frame gap in the source camera data
          exceeding MAX_INTERP_GAP_FRAMES (3 frames = 50 ms) triggers a per-gap
          WARNING printed to stdout and is recorded in summary.json under
          "large_gaps".  Interpolation still proceeds — the guard is diagnostic,
          not a hard stop — so the caller can decide whether to discard the run.
          Per-camera files only — Step 06 is responsible for merging.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Step 05 — Synchronization")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Condition name — e.g. e7_90rpm")
    group.add_argument("--all", action="store_true",
                       help="Process all conditions found in results/step04/")
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


INTERP_COLS = ["x_w", "y_w", "z_w", "qx", "qy", "qz", "qw"]

MAX_INTERP_GAP_FRAMES = 3                          # warn if any source gap > this
MAX_INTERP_GAP_S      = MAX_INTERP_GAP_FRAMES / 60.0


def process_condition(condition: str, config: dict) -> None:
    results_dir = Path(config["paths"]["results_dir"])
    cam_names   = list(config["cameras"].keys())

    step04_root = results_dir / "step04" / condition
    step05_root = results_dir / "step05" / condition

    print(f"\n=== SYNCHRONIZATION: {condition} ===\n")

    # ── Load all cameras ──────────────────────────────────────────────────────
    cam_data = {}
    for cam in cam_names:
        pose_csv = step04_root / cam / "world_pose.csv"
        if not pose_csv.exists():
            raise FileNotFoundError(
                f"Step04 output missing for {condition}/{cam}. Run step04 first."
            )
        df = pd.read_csv(pose_csv)
        cam_data[cam] = df
        print(f"  {cam}: {len(df)} frames | "
              f"t=[{df.timestamp_s.iloc[0]:.6f}, {df.timestamp_s.iloc[-1]:.6f}]s")

    # ── Find common time window ───────────────────────────────────────────────
    # Intersection: latest start, earliest end — guarantees no extrapolation
    t_start = max(df.timestamp_s.iloc[0]  for df in cam_data.values())
    t_end   = min(df.timestamp_s.iloc[-1] for df in cam_data.values())

    if t_end <= t_start:
        raise RuntimeError(
            f"No overlapping time window for {condition}. "
            f"t_start={t_start:.6f} >= t_end={t_end:.6f}"
        )

    # ── Build common 60 Hz grid ───────────────────────────────────────────────
    # np.arange(n) / 60.0 avoids float step accumulation drift.
    # n_frames chosen so that last grid point <= t_end.
    n_frames = int(np.floor((t_end - t_start) * 60.0)) + 1
    t_grid   = t_start + np.arange(n_frames) / 60.0

    # Safety check — last grid point must not exceed t_end
    assert t_grid[-1] <= t_end + 1e-9, (
        f"Grid overrun: t_grid[-1]={t_grid[-1]:.9f} > t_end={t_end:.9f}"
    )

    print(f"\n  Common window: [{t_start:.6f}, {t_end:.6f}]s "
          f"-> {n_frames} frames at 60 Hz\n")

    # ── Interpolate each camera onto common grid ──────────────────────────────
    large_gap_counts = {}   # {cam: n_gaps} — populated in loop, saved to summary
    for cam in cam_names:
        df    = cam_data[cam]
        t_cam = df.timestamp_s.values

        # Verify monotonicity — interp1d requires it
        diffs = np.diff(t_cam)
        if not np.all(diffs > 0):
            raise RuntimeError(
                f"{cam} timestamps are not strictly monotonic. "
                f"Check step01 output."
            )

        # MAX_INTERP_GAP guard — warn on any source gap > 3 frames (50 ms)
        gap_mask    = diffs > MAX_INTERP_GAP_S
        gap_indices = np.where(gap_mask)[0]
        if len(gap_indices) > 0:
            for idx in gap_indices:
                gap_ms     = diffs[idx] * 1000.0
                gap_frames = diffs[idx] * 60.0
                print(f"  [WARN] {cam}: large source gap of {gap_ms:.1f} ms "
                      f"({gap_frames:.1f} frames) at t={t_cam[idx]:.4f}s — "
                      f"interpolation will bridge it")
        large_gap_counts[cam] = int(len(gap_indices))

        synced = {"t_s": t_grid}

        for col in INTERP_COLS:
            f_interp    = interp1d(t_cam, df[col].values,
                                   kind="linear", bounds_error=True)
            synced[col] = f_interp(t_grid)

        # Renormalize quaternions — linear interpolation does not preserve unit norm
        q = np.stack([synced["qx"], synced["qy"],
                      synced["qz"], synced["qw"]], axis=1)   # (N, 4)
        norms = np.linalg.norm(q, axis=1, keepdims=True)
        q    /= norms
        synced["qx"] = q[:, 0]
        synced["qy"] = q[:, 1]
        synced["qz"] = q[:, 2]
        synced["qw"] = q[:, 3]

        # Check quaternion norm after renormalization
        final_norms  = np.linalg.norm(q, axis=1)
        max_norm_err = float(np.max(np.abs(final_norms - 1.0)))
        if max_norm_err > 1e-6:
            print(f"  [WARN] {cam}: max quaternion norm error after renorm = "
                  f"{max_norm_err:.2e}")

        # Write synced_pose.csv
        cam05_dir = step05_root / cam
        cam05_dir.mkdir(parents=True, exist_ok=True)

        out_df = pd.DataFrame({
            "t_s": np.round(synced["t_s"], 9),
            "x_w": np.round(synced["x_w"], 9),
            "y_w": np.round(synced["y_w"], 9),
            "z_w": np.round(synced["z_w"], 9),
            "qx":  np.round(synced["qx"],  9),
            "qy":  np.round(synced["qy"],  9),
            "qz":  np.round(synced["qz"],  9),
            "qw":  np.round(synced["qw"],  9),
        })

        out_df.to_csv(cam05_dir / "synced_pose.csv", index=False)

        # Per-camera diagnostics
        y_std_mm = float(out_df["y_w"].std()) * 1000.0
        z_mean_m = float(out_df["z_w"].mean())
        print(f"  {cam}: {n_frames} synced frames | "
              f"y_w std={y_std_mm:.3f}mm | z_w mean={z_mean_m:.4f}m")

    # ── Condition-level summary ───────────────────────────────────────────────
    dfs = {cam: pd.read_csv(step05_root / cam / "synced_pose.csv")
           for cam in cam_names}

    # Verify t_s is identical across cameras
    t_arrays   = [dfs[cam]["t_s"].values for cam in cam_names]
    max_t_diff = float(np.max([
        np.max(np.abs(t_arrays[0] - t_arrays[i]))
        for i in range(1, len(t_arrays))
    ]))

    if max_t_diff > 1e-9:
        print(f"  [WARN] t_s mismatch across cameras: max_diff={max_t_diff:.2e}s")
    else:
        print(f"\n  t_s identical across all cameras (max_diff < 1e-9s)")

    # Raw inter-camera Z disagreement (before baseline alignment in Step 06)
    z_cam1 = dfs["cam1"]["z_w"].values
    z_cam2 = dfs["cam2"]["z_w"].values
    z_cam3 = dfs["cam3"]["z_w"].values
    raw_z12 = float(np.mean(np.abs(z_cam1 - z_cam2))) * 1000.0
    raw_z13 = float(np.mean(np.abs(z_cam1 - z_cam3))) * 1000.0
    raw_z23 = float(np.mean(np.abs(z_cam2 - z_cam3))) * 1000.0

    print(f"\n  Raw Z disagreement (before baseline alignment in Step 06):")
    print(f"    cam1-cam2: {raw_z12:.1f} mm")
    print(f"    cam1-cam3: {raw_z13:.1f} mm")
    print(f"    cam2-cam3: {raw_z23:.1f} mm")

    summary = {
        "condition":       condition,
        "n_frames_synced": n_frames,
        "t_start_s":       round(float(t_start), 9),
        "t_end_s":         round(float(t_end),   9),
        "duration_s":      round(float(t_end - t_start), 6),
        "grid_hz":         60,
        "t_s_max_diff":    float(max_t_diff),
        "large_gaps": {
            "threshold_frames": MAX_INTERP_GAP_FRAMES,
            "threshold_ms":     round(MAX_INTERP_GAP_S * 1000.0, 2),
            "counts":           large_gap_counts,
        },
        "raw_z_disagreement_mm": {
            "cam1_cam2": round(raw_z12, 2),
            "cam1_cam3": round(raw_z13, 2),
            "cam2_cam3": round(raw_z23, 2),
        },
        "cameras": {
            cam: {
                "y_w_std_mm": round(float(dfs[cam]["y_w"].std()) * 1000.0, 4),
                "z_w_mean_m": round(float(dfs[cam]["z_w"].mean()), 6),
            }
            for cam in cam_names
        },
    }

    with open(step05_root / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print()


def main():
    args   = parse_args()
    config = load_config(args.config)

    if args.all:
        results_dir = Path(config["paths"]["results_dir"])
        step04_root = results_dir / "step04"
        conditions  = sorted([d.name for d in step04_root.iterdir() if d.is_dir()])
        if not conditions:
            raise FileNotFoundError(f"No step04 results found under {step04_root}")
        print(f"Found {len(conditions)} condition(s) — processing all.")
    else:
        conditions = [condition_from_arg(args.bag)]

    for condition in conditions:
        process_condition(condition, config)


if __name__ == "__main__":
    main()
