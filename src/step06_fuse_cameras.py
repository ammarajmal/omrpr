"""
Step 06 — Baseline-Aligned Fusion
===================================
Purpose:  Remove per-camera DC offset (full-run mean) to convert absolute
          camera-frame positions into relative displacements. Compute the
          aligned inter-camera Z disagreement as a key publishable result.

          This is NOT geometric extrinsic fusion — no rotation/translation
          matrices are applied. Alignment is purely statistical: subtract
          each camera's full-run mean from each axis independently.

          After alignment:
            - Every camera's mean x/y/z = 0 by construction
            - Raw Z disagreement (DC offset, ~388 mm) is removed
            - Residual Z disagreement (std of z_diff) is the publishable metric
            - Target residual: ~2.053 mm std (from confirmed clean implementation, e7_90rpm reference)

          The ~189× improvement (388 mm raw → ~2.053 mm std aligned, e7_90rpm) IS a key result.
          Both numbers must be reported in the manuscript.

Inputs:   results/step05/{condition}/{cam}/synced_pose.csv
          config/pipeline_config.yaml

Outputs:  results/step06/{condition}/{cam}/aligned_pose.csv
          results/step06/{condition}/summary.json

Schema (aligned_pose.csv):
          t_s           float  — common grid time (from step05, unchanged)
          x_w_mm        float  — aligned lateral displacement in MILLIMETRES
          y_w_mm        float  — aligned vertical displacement in MILLIMETRES
          z_w_mm        float  — aligned depth displacement in MILLIMETRES
          qx,qy,qz,qw  float  — quaternion (unchanged from step05)
          x_w_mean_m    float  — per-camera mean subtracted (stored for traceability)
          y_w_mean_m    float  — per-camera mean subtracted
          z_w_mean_m    float  — per-camera mean subtracted

          NOTE: x/y/z are converted to MILLIMETRES here. All downstream steps
          (07, 08, 09, 10) work in millimetres. This is the unit conversion point.

Key metric (summary.json):
          raw_z_disagreement_mm     — |mean(z_cam1) - mean(z_cam2)| etc. (from step05)
          aligned_z_disagreement_mm — std(z_cam_i_aligned - z_cam_j_aligned)
          improvement_factor        — raw / aligned

Limits:
          Full-run mean removal absorbs any static aerostatic deflection.
          This is acceptable because: (1) science is dynamic response, not static
          offset; (2) LDV also has arbitrary DC offset; (3) LDV comparison is
          condition-level RMS/peak, both of which survive mean removal unchanged.
          Per the manuscript: 'Displacements are reported relative to the
          condition-mean position, consistent with dynamic response characterization.'

          Step 06 outputs per-camera aligned traces only.
          Step 07 is responsible for averaging and differencing across cameras.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Step 06 — Baseline-Aligned Fusion")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Condition name — e.g. e7_90rpm")
    group.add_argument("--all", action="store_true",
                       help="Process all conditions found in results/step05/")
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


def process_condition(condition: str, config: dict) -> None:
    results_dir = Path(config["paths"]["results_dir"])
    cam_names   = list(config["cameras"].keys())

    step05_root = results_dir / "step05" / condition
    step06_root = results_dir / "step06" / condition

    print(f"\n=== BASELINE ALIGNMENT: {condition} ===\n")

    # ── Load step05 synced poses ──────────────────────────────────────────────
    cam_data = {}
    for cam in cam_names:
        csv_path = step05_root / cam / "synced_pose.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Step05 output missing for {condition}/{cam}. Run step05 first."
            )
        cam_data[cam] = pd.read_csv(csv_path)

    # ── Compute per-camera full-run means (in metres) ─────────────────────────
    means = {}
    for cam in cam_names:
        df = cam_data[cam]
        means[cam] = {
            "x": float(df["x_w"].mean()),
            "y": float(df["y_w"].mean()),
            "z": float(df["z_w"].mean()),
        }

    # ── Print raw Z disagreement (DC offset, carried from step05) ─────────────
    print("  Per-camera full-run means (metres):")
    for cam in cam_names:
        print(f"    {cam}: x={means[cam]['x']:+.6f}  "
              f"y={means[cam]['y']:+.6f}  "
              f"z={means[cam]['z']:+.6f}")

    raw_z_pairs = {}
    cam_list = cam_names
    for i in range(len(cam_list)):
        for j in range(i + 1, len(cam_list)):
            ca, cb = cam_list[i], cam_list[j]
            key = f"{ca}_{cb}"
            raw_z_pairs[key] = abs(means[ca]["z"] - means[cb]["z"]) * 1000.0

    print(f"\n  Raw Z disagreement (DC offset between cameras):")
    for pair, val in raw_z_pairs.items():
        print(f"    {pair}: {val:.1f} mm")

    # ── Apply full-run mean removal and convert to millimetres ────────────────
    aligned = {}
    for cam in cam_names:
        df = cam_data[cam]
        mx, my, mz = means[cam]["x"], means[cam]["y"], means[cam]["z"]

        aligned[cam] = pd.DataFrame({
            "t_s":       df["t_s"].values,
            # Convert to mm: subtract mean (in m), then * 1000
            "x_w_mm":   (df["x_w"].values - mx) * 1000.0,
            "y_w_mm":   (df["y_w"].values - my) * 1000.0,
            "z_w_mm":   (df["z_w"].values - mz) * 1000.0,
            # Quaternions unchanged
            "qx":        df["qx"].values,
            "qy":        df["qy"].values,
            "qz":        df["qz"].values,
            "qw":        df["qw"].values,
            # Store subtracted means for traceability
            "x_w_mean_m": mx,
            "y_w_mean_m": my,
            "z_w_mean_m": mz,
        })

    # ── Compute aligned Z disagreement (residual std of z_diff) ───────────────
    aligned_z_pairs = {}
    for i in range(len(cam_list)):
        for j in range(i + 1, len(cam_list)):
            ca, cb = cam_list[i], cam_list[j]
            key = f"{ca}_{cb}"
            z_diff = aligned[ca]["z_w_mm"].values - aligned[cb]["z_w_mm"].values
            aligned_z_pairs[key] = {
                "std_mm":  round(float(np.std(z_diff)),  4),
                "mean_mm": round(float(np.mean(z_diff)), 4),   # should be ~0
                "max_mm":  round(float(np.max(np.abs(z_diff))), 4),
            }

    print(f"\n  Aligned Z disagreement (residual std after mean removal):")
    for pair, vals in aligned_z_pairs.items():
        raw_val = raw_z_pairs[pair]
        std_val = vals["std_mm"]
        factor  = raw_val / std_val if std_val > 0 else float("inf")
        print(f"    {pair}: std={std_val:.4f} mm  "
              f"mean={vals['mean_mm']:.4f} mm  "
              f"max={vals['max_mm']:.4f} mm  "
              f"| improvement={factor:.1f}x")

    # ── Write per-camera aligned_pose.csv ─────────────────────────────────────
    for cam in cam_names:
        cam06_dir = step06_root / cam
        cam06_dir.mkdir(parents=True, exist_ok=True)

        out_df = aligned[cam].copy()
        # Round to avoid spurious precision
        out_df["t_s"]    = out_df["t_s"].round(9)
        for col in ["x_w_mm", "y_w_mm", "z_w_mm"]:
            out_df[col] = out_df[col].round(6)
        for col in ["qx", "qy", "qz", "qw"]:
            out_df[col] = out_df[col].round(9)
        for col in ["x_w_mean_m", "y_w_mean_m", "z_w_mean_m"]:
            out_df[col] = out_df[col].round(9)

        out_df.to_csv(cam06_dir / "aligned_pose.csv", index=False)

        y_std = float(aligned[cam]["y_w_mm"].std())
        print(f"\n  {cam}: y_w_mm std={y_std:.4f} mm  "
              f"(sanity: should match step05 y_w std * 1000)")

    # ── Summary JSON ──────────────────────────────────────────────────────────
    summary = {
        "condition": condition,
        "n_frames":  int(len(aligned[cam_names[0]])),
        "alignment": "full_run_mean_removal",
        "units_out": "millimetres",
        "per_camera_means_m": {
            cam: {k: round(v, 9) for k, v in means[cam].items()}
            for cam in cam_names
        },
        "raw_z_disagreement_mm": {
            k: round(v, 2) for k, v in raw_z_pairs.items()
        },
        "aligned_z_disagreement_mm": aligned_z_pairs,
        "improvement_factor": {
            pair: round(raw_z_pairs[pair] / aligned_z_pairs[pair]["std_mm"], 1)
            if aligned_z_pairs[pair]["std_mm"] > 0 else None
            for pair in raw_z_pairs
        },
        "y_w_std_mm": {
            cam: round(float(aligned[cam]["y_w_mm"].std()), 4)
            for cam in cam_names
        },
    }

    with open(step06_root / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # ── Gate check ────────────────────────────────────────────────────────────
    print(f"\n  Gate check (target: aligned Z std < 15 mm):")
    all_pass = True
    for pair, vals in aligned_z_pairs.items():
        status = "PASS" if vals["std_mm"] < 15.0 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"    {pair}: {vals['std_mm']:.4f} mm — {status}")

    print()
    if all_pass:
        print(f"  All camera pairs within 15 mm gate — PASS")
    else:
        print(f"  One or more pairs exceed 15 mm gate — INVESTIGATE before Step 07")

    print()


def main():
    args   = parse_args()
    config = load_config(args.config)

    if args.all:
        results_dir = Path(config["paths"]["results_dir"])
        step05_root = results_dir / "step05"
        conditions  = sorted([d.name for d in step05_root.iterdir() if d.is_dir()])
        if not conditions:
            raise FileNotFoundError(f"No step05 results found under {step05_root}")
        print(f"Found {len(conditions)} condition(s) — processing all.")
    else:
        conditions = [condition_from_arg(args.bag)]

    for condition in conditions:
        process_condition(condition, config)


if __name__ == "__main__":
    main()