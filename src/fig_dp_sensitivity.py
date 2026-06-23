"""
fig_dp_sensitivity.py — dp geometry parameter sensitivity analysis (Step 10 supplement)

PURPOSE:
    Sweeps dp (= db/dside) over the physically plausible range [1.40, 1.65] to show that
    torsion correlation conclusions are robust to uncertainty in the LDV geometry parameter.

    dp = db / dside = 20.0 cm / 13.0 cm = 1.538 (nominal, confirmed from facility document).
    If dside is uncertain by ±0.5 cm, dp ranges from 1.481 to 1.600.
    Range [1.40, 1.65] is generous (±0.9 cm on dside).

    KEY RESULT: Pearson r is scale-invariant (dp multiplies all LDV torsion values by a
    constant → r unchanged). The ratio camera/LDV scales as dp_nominal/dp_test.
    Both conclusions hold across the entire plausible range.

INPUTS:
    results/step10/ldv_comparison_table.csv

OUTPUTS:
    results/step10/dp_sensitivity.json
    results/step10/fig_dp_sensitivity.png
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

DP_NOMINAL = 20.0 / 13.0  # 1.538...
DP_RANGE   = np.arange(1.40, 1.66, 0.05)
STABLE_EXCLUDE = {"e4_60rpm", "e20_320rpm"}

RESULTS_DIR = Path("results/step10")
TABLE_PATH  = RESULTS_DIR / "ldv_comparison_table.csv"


def run_sensitivity():
    df = pd.read_csv(TABLE_PATH)

    # Stable regime (exclude VIV outlier and high-wind unstable)
    stable = df[~df["wtt_condition"].isin(STABLE_EXCLUDE)].copy()

    cam_torsion = stable["camera_torsion_rms_mm"].values
    ldv_torsion_nominal = stable["ldv_torsion_rms_mm_corrected"].values

    rows = []
    for dp in DP_RANGE:
        # Scale LDV torsion by dp/dp_nominal (linear in dp)
        ldv_torsion_scaled = ldv_torsion_nominal * (dp / DP_NOMINAL)

        r, p = stats.pearsonr(cam_torsion, ldv_torsion_scaled)
        ratio_mean = float(np.mean(cam_torsion / ldv_torsion_scaled))

        rows.append({
            "dp": round(float(dp), 3),
            "dside_cm": round(20.0 / dp, 3),
            "torsion_pearson_r": round(r, 6),
            "torsion_pearson_p": round(p, 8),
            "torsion_ratio_cam_over_ldv": round(ratio_mean, 4),
        })

    return rows


def make_figure(rows, out_path):
    dp_vals = [r["dp"] for r in rows]
    r_vals  = [r["torsion_pearson_r"] for r in rows]
    ratio_vals = [r["torsion_ratio_cam_over_ldv"] for r in rows]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Left: Pearson r vs dp
    ax = axes[0]
    ax.plot(dp_vals, r_vals, "o-", color="#2196F3", linewidth=2, markersize=7)
    ax.axvline(DP_NOMINAL, color="gray", linestyle="--", linewidth=1.2, label=f"Nominal dp={DP_NOMINAL:.3f}")
    ax.axhline(0.90, color="red", linestyle=":", linewidth=1.2, label="Gate r = 0.90")
    ax.set_xlabel("dp  (= db / dside)")
    ax.set_ylabel("Torsion Pearson r (stable regime)")
    ax.set_title("Torsion Pearson r vs dp")
    ax.set_ylim(0.80, 1.05)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.text(0.05, 0.07,
            "r is scale-invariant — dp does not affect r",
            transform=ax.transAxes, fontsize=9, color="#555")

    # Right: ratio vs dp
    ax = axes[1]
    ax.plot(dp_vals, ratio_vals, "s-", color="#FF5722", linewidth=2, markersize=7)
    ax.axvline(DP_NOMINAL, color="gray", linestyle="--", linewidth=1.2, label=f"Nominal dp={DP_NOMINAL:.3f}")
    ax.axhline(1.0, color="black", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("dp  (= db / dside)")
    ax.set_ylabel("Camera / LDV torsion RMS ratio")
    ax.set_title("Torsion ratio vs dp")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle("dp Geometry Sensitivity Analysis — Torsion (stable regime, excl. 60/320 RPM)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[WRITE] {out_path}")


def main():
    rows = run_sensitivity()

    # Print table
    print(f"\n{'dp':>6s}  {'dside_cm':>9s}  {'Torsion r':>10s}  {'Ratio':>7s}")
    print("─" * 42)
    for r in rows:
        marker = " ← nominal" if abs(r["dp"] - DP_NOMINAL) < 0.005 else ""
        print(f"{r['dp']:>6.3f}  {r['dside_cm']:>9.3f}  {r['torsion_pearson_r']:>10.6f}  {r['torsion_ratio_cam_over_ldv']:>7.4f}{marker}")

    print(f"\n[RESULT] r is identical across all dp values: {rows[0]['torsion_pearson_r']:.6f}")
    print(f"[RESULT] Ratio range: {min(r['torsion_ratio_cam_over_ldv'] for r in rows):.4f}"
          f" – {max(r['torsion_ratio_cam_over_ldv'] for r in rows):.4f}")
    print(f"[RESULT] All r values exceed gate (0.90): {all(r['torsion_pearson_r'] > 0.90 for r in rows)}")

    out_json = RESULTS_DIR / "dp_sensitivity.json"
    with open(out_json, "w") as f:
        json.dump({
            "dp_nominal": round(DP_NOMINAL, 6),
            "dp_range": [round(float(d), 3) for d in DP_RANGE],
            "note": (
                "Pearson r is scale-invariant — dp multiplies all LDV torsion values by a "
                "constant, leaving r unchanged. Ratio scales as dp_nominal/dp_test. "
                "All values exceed the gate threshold of 0.90."
            ),
            "results": rows,
        }, f, indent=2)
    print(f"[WRITE] {out_json}")

    make_figure(rows, RESULTS_DIR / "fig_dp_sensitivity.png")


if __name__ == "__main__":
    main()
