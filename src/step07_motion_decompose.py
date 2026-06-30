"""
Step 07 — Motion Decomposition
================================
Purpose:  Decompose aligned per-camera displacements into two physically
          meaningful channels:

          bending_avg_y_mm  = mean(cam1_y, cam2_y)
              — Average vertical displacement of Marker A across both cameras.
                Represents bridge bending (vertical oscillation).
                cam1 vs cam2 correlation r=0.999 confirms sign consistency.

          torsion_diff_y_mm = cam3_y - bending_avg_y_mm
              — Differential vertical displacement between Marker B (cam3)
                and Marker A (cam1/cam2 average).
                Two-point differential displacement proxy for torsion.
                Treated as unsigned proxy — sign not physically calibrated.
                Physical validation: dominant frequency should separate from the
                bending reference target used in Step 08 and cluster near the
                torsion-reference band in torsion-dominated conditions.

Key decisions (locked):
          - Full-run mean removal was done in Step 06. No second mean removal here.
            bending_avg_y_mm is zero-mean by construction (average of two zero-mean signals).
            torsion_diff_y_mm is zero-mean by construction (difference of two zero-mean signals).
          - Torsion is a proxy, not a calibrated torsion angle. Never call it a torsion angle.
          - No sign flip applied to either channel. Sign consistency confirmed by r=0.999
            for cam1 vs cam2 y_w_mm.

Inputs:   results/step06/{condition}/{cam}/aligned_pose.csv  (cam1, cam2, cam3)
          config/pipeline_config.yaml

Outputs:  results/step07/{condition}/motion.csv
          results/step07/{condition}/summary.json

Schema (motion.csv):
          t_s                float  — common grid time (from step06, unchanged)
          bending_avg_y_mm   float  — (cam1_y + cam2_y) / 2
          torsion_diff_y_mm  float  — cam3_y - bending_avg_y_mm

Schema (summary.json):
          bending_rms_mm       — RMS of bending_avg_y_mm
          bending_std_mm       — std of bending_avg_y_mm (== RMS since zero-mean)
          bending_peak_mm      — max absolute value
          torsion_rms_mm       — RMS of torsion_diff_y_mm
          torsion_std_mm       — std of torsion_diff_y_mm
          torsion_peak_mm      — max absolute value
          cam1_cam2_y_corr     — Pearson r between cam1 and cam2 y_w_mm (internal check)
          n_frames             — number of time steps

Limits:
          Step 07 does NOT perform frequency analysis — that is Step 08.
          Step 07 does NOT perform uncertainty quantification — that is Step 09.
          Step 07 does NOT compare to LDV — that is Step 10.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Step 07 — Motion Decomposition")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Condition name — e.g. e7_90rpm")
    group.add_argument("--all", action="store_true",
                       help="Process all conditions found in results/step06/")
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
    step06_root = results_dir / "step06" / condition
    step07_root = results_dir / "step07" / condition
    step07_root.mkdir(parents=True, exist_ok=True)

    print(f"\n=== MOTION DECOMPOSITION: {condition} ===\n")

    # ── Load per-camera aligned poses ─────────────────────────────────────────
    def load_cam(cam: str) -> pd.DataFrame:
        p = step06_root / cam / "aligned_pose.csv"
        if not p.exists():
            raise FileNotFoundError(
                f"Step06 output missing for {condition}/{cam}. Run step06 first."
            )
        return pd.read_csv(p)

    df1 = load_cam("cam1")
    df2 = load_cam("cam2")
    df3 = load_cam("cam3")

    # ── Verify time grids are identical ──────────────────────────────────────
    if not (np.allclose(df1.t_s.values, df2.t_s.values, atol=1e-9) and
            np.allclose(df1.t_s.values, df3.t_s.values, atol=1e-9)):
        raise RuntimeError(
            f"t_s mismatch across cameras for {condition}. "
            f"Check step05/step06 outputs."
        )

    n_frames = len(df1)

    # ── Internal consistency check: cam1 vs cam2 correlation ─────────────────
    y1 = df1["y_w_mm"].values
    y2 = df2["y_w_mm"].values
    y3 = df3["y_w_mm"].values

    cam12_corr = float(np.corrcoef(y1, y2)[0, 1])
    print(f"  cam1 vs cam2 y_w_mm Pearson r = {cam12_corr:.6f}")
    if cam12_corr < 0.95:
        print(f"  [WARN] cam1-cam2 correlation below 0.95 — check sign consistency")
    elif cam12_corr < 0.0:
        print(f"  [CRITICAL] cam1-cam2 correlation is NEGATIVE — sign flip detected. "
              f"Negate one camera's y_w_mm before averaging.")

    # ── Decompose ─────────────────────────────────────────────────────────────
    bending_avg_y_mm  = (y1 + y2) / 2.0
    torsion_diff_y_mm = y3 - bending_avg_y_mm

    # Verify zero-mean (should be by construction — assert as safety check)
    bending_mean  = float(np.mean(bending_avg_y_mm))
    torsion_mean  = float(np.mean(torsion_diff_y_mm))
    if abs(bending_mean) > 0.01:
        print(f"  [WARN] bending_avg_y_mm mean = {bending_mean:.6f} mm "
              f"(expected ~0 — check step06 alignment)")
    if abs(torsion_mean) > 0.01:
        print(f"  [WARN] torsion_diff_y_mm mean = {torsion_mean:.6f} mm "
              f"(expected ~0 — check step06 alignment)")

    # ── Write motion.csv ──────────────────────────────────────────────────────
    motion_df = pd.DataFrame({
        "t_s":               np.round(df1["t_s"].values, 9),
        "bending_avg_y_mm":  np.round(bending_avg_y_mm, 6),
        "torsion_diff_y_mm": np.round(torsion_diff_y_mm, 6),
    })
    motion_df.to_csv(step07_root / "motion.csv", index=False)

    # ── Compute summary statistics ────────────────────────────────────────────
    # For zero-mean signals: RMS == std. Compute both for completeness.
    b_rms  = float(np.sqrt(np.mean(bending_avg_y_mm  ** 2)))
    b_std  = float(np.std(bending_avg_y_mm))
    b_peak = float(np.max(np.abs(bending_avg_y_mm)))

    t_rms  = float(np.sqrt(np.mean(torsion_diff_y_mm ** 2)))
    t_std  = float(np.std(torsion_diff_y_mm))
    t_peak = float(np.max(np.abs(torsion_diff_y_mm)))

    summary = {
        "condition":         condition,
        "n_frames":          n_frames,
        "cam1_cam2_y_corr":  round(cam12_corr, 6),
        "bending_avg_y_mm": {
            "rms_mm":  round(b_rms,  4),
            "std_mm":  round(b_std,  4),
            "peak_mm": round(b_peak, 4),
            "mean_mm": round(bending_mean, 6),
        },
        "torsion_diff_y_mm": {
            "rms_mm":  round(t_rms,  4),
            "std_mm":  round(t_std,  4),
            "peak_mm": round(t_peak, 4),
            "mean_mm": round(torsion_mean, 6),
        },
    }

    with open(step07_root / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # ── Print summary ─────────────────────────────────────────────────────────
    print(f"\n  bending_avg_y_mm:  RMS={b_rms:.4f} mm  "
          f"peak={b_peak:.4f} mm  std={b_std:.4f} mm")
    print(f"  torsion_diff_y_mm: RMS={t_rms:.4f} mm  "
          f"peak={t_peak:.4f} mm  std={t_std:.4f} mm")
    print()


def main():
    args   = parse_args()
    config = load_config(args.config)

    if args.all:
        results_dir = Path(config["paths"]["results_dir"])
        step06_root = results_dir / "step06"
        conditions  = sorted([d.name for d in step06_root.iterdir() if d.is_dir()])
        if not conditions:
            raise FileNotFoundError(f"No step06 results found under {step06_root}")
        print(f"Found {len(conditions)} condition(s) — processing all.")
    else:
        conditions = [condition_from_arg(args.bag)]

    for condition in conditions:
        process_condition(condition, config)


if __name__ == "__main__":
    main()
