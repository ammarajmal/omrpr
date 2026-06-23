"""
comparison_plot_options.py — defensible supplementary/main-text comparison options

Generates a small gallery of figure candidates that avoid overclaiming amplitude
agreement while still surfacing the strongest comparison stories in the data.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


BASE = Path("results")
STEP10 = BASE / "step10" / "ldv_comparison_table.csv"
STEP11 = BASE / "step11"
OUT_DIR = BASE / "comparison_plots_options"

C_BEND = "#1f77b4"
C_TORS = "#d62728"
C_SMOOTH = "#2ca02c"
C_RATIO = "#7f7f7f"
C_REG_B = "#aec7e8"
C_REG_T = "#ffbb78"
C_REG_R = "#98df8a"

REGIME_BENDING = (40, 80)
REGIME_TORSION = (90, 220)
REGIME_REEMERGE = (240, 300)


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
})


def load_data() -> pd.DataFrame:
    df = pd.read_csv(STEP10).sort_values("rpm").reset_index(drop=True)
    b_s, t_s = [], []
    for cond in df["wtt_condition"]:
        diag = json.loads((STEP11 / cond / "smoothing_diagnostics.json").read_text())
        b_s.append(diag["bending_smoothed_rms_mm"])
        t_s.append(diag["torsion_smoothed_rms_mm"])
    df["camera_bending_rms_smoothed_mm"] = b_s
    df["camera_torsion_rms_smoothed_mm"] = t_s
    return df


def shade_regimes(ax):
    ax.axvspan(*REGIME_BENDING, color=C_REG_B, alpha=0.18, zorder=0)
    ax.axvspan(*REGIME_TORSION, color=C_REG_T, alpha=0.18, zorder=0)
    ax.axvspan(*REGIME_REEMERGE, color=C_REG_R, alpha=0.18, zorder=0)


def save(fig, stem):
    for ext in ["pdf", "png"]:
        fig.savefig(OUT_DIR / f"{stem}.{ext}", bbox_inches="tight", dpi=180)
    plt.close(fig)


def option01_ratio_vs_rpm(df: pd.DataFrame):
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for ax, ratio_col, title, color in [
        (axes[0], "bending_ratio_cam_over_ldv", "Bending ratio (camera / LDV)", C_BEND),
        (axes[1], "torsion_ratio_cam_over_ldv", "Torsion-proxy ratio (camera / LDV)", C_TORS),
    ]:
        shade_regimes(ax)
        stable = df["flag"].isna()
        ax.axhline(1.0, color="0.35", lw=1.0, ls="--", label="1.0")
        ax.plot(df.loc[stable, "rpm"], df.loc[stable, ratio_col], "-o", color=color, lw=2)
        flagged = df[~stable]
        if not flagged.empty:
            ax.scatter(flagged["rpm"], flagged[ratio_col], marker="x", s=60, color=color, alpha=0.6)
        ax.set_ylabel("Camera / LDV")
        ax.set_title(title)
        ax.set_ylim(bottom=0)
    axes[1].set_xlabel("Fan speed (RPM)")
    fig.suptitle(
        "Option 1 — Ratio vs RPM\n"
        "Most honest view of amplitude agreement across separate sessions",
        fontweight="bold",
    )
    fig.tight_layout()
    save(fig, "option01_ratio_vs_rpm")


def option02_torsion_regime_rms(df: pd.DataFrame):
    sub = df[(df["flag"].isna()) & (df["rpm"] >= 90) & (df["rpm"] <= 220)].copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(sub["rpm"], sub["ldv_torsion_rms_mm_corrected"], "-s", color=C_TORS, lw=2.2, label="LDV RMS")
    ax.plot(sub["rpm"], sub["camera_torsion_rms_mm"], "-o", color=C_BEND, lw=2.0, label="Camera raw RMS")
    ax.plot(sub["rpm"], sub["camera_torsion_rms_smoothed_mm"], "--D", color=C_SMOOTH, lw=1.5, label="Camera smoothed RMS")
    r = pearsonr(sub["ldv_torsion_rms_mm_corrected"], sub["camera_torsion_rms_mm"])[0]
    rho = spearmanr(sub["ldv_torsion_rms_mm_corrected"], sub["camera_torsion_rms_mm"])[0]
    ax.text(
        0.02, 0.96,
        f"Stable torsional regime only\nn = {len(sub)}, Pearson r = {r:.3f}, Spearman rho = {rho:.3f}\n"
        f"Mean ratio = {sub['torsion_ratio_cam_over_ldv'].mean():.3f}",
        transform=ax.transAxes, va="top",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.9),
    )
    ax.set_xlabel("Fan speed (RPM)")
    ax.set_ylabel("RMS (mm)")
    ax.set_title("Option 2 — Torsion-proxy RMS in 90-220 RPM torsional regime")
    ax.legend()
    fig.tight_layout()
    save(fig, "option02_torsion_regime_rms")


def option03_bending_reemergence_rms(df: pd.DataFrame):
    sub = df[(df["flag"].isna()) & (df["rpm"] >= 240) & (df["rpm"] <= 300)].copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(sub["rpm"], sub["ldv_bending_rms_mm_corrected"], "-s", color=C_TORS, lw=2.2, label="LDV RMS")
    ax.plot(sub["rpm"], sub["camera_bending_rms_mm"], "-o", color=C_BEND, lw=2.0, label="Camera raw RMS")
    ax.plot(sub["rpm"], sub["camera_bending_rms_smoothed_mm"], "--D", color=C_SMOOTH, lw=1.5, label="Camera smoothed RMS")
    r = pearsonr(sub["ldv_bending_rms_mm_corrected"], sub["camera_bending_rms_mm"])[0]
    ax.text(
        0.02, 0.96,
        f"Stable re-emergence only\nn = {len(sub)}, Pearson r = {r:.3f}\n"
        f"Mean ratio = {sub['bending_ratio_cam_over_ldv'].mean():.3f}",
        transform=ax.transAxes, va="top",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.9),
    )
    ax.set_xlabel("Fan speed (RPM)")
    ax.set_ylabel("RMS (mm)")
    ax.set_title("Option 3 — Bending RMS in 240-300 RPM re-emergence regime")
    ax.legend()
    fig.tight_layout()
    save(fig, "option03_bending_reemergence_rms")


def option04_normalized_rms(df: pd.DataFrame):
    stable = df[df["flag"].isna()].copy()
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    configs = [
        (
            axes[0],
            "ldv_bending_rms_mm_corrected",
            "camera_bending_rms_mm",
            "Normalized bending RMS (stable conditions)",
            C_BEND,
        ),
        (
            axes[1],
            "ldv_torsion_rms_mm_corrected",
            "camera_torsion_rms_mm",
            "Normalized torsion-proxy RMS (stable conditions)",
            C_TORS,
        ),
    ]
    for ax, ldv_col, cam_col, title, color in configs:
        shade_regimes(ax)
        ldv = stable[ldv_col] / stable[ldv_col].max()
        cam = stable[cam_col] / stable[cam_col].max()
        ax.plot(stable["rpm"], ldv, "-s", color=C_TORS, lw=2.2, label="LDV normalized")
        ax.plot(stable["rpm"], cam, "-o", color=color, lw=2.0, label="Camera normalized")
        ax.set_ylabel("Normalized RMS")
        ax.set_title(title)
        ax.set_ylim(0, 1.1)
    axes[1].set_xlabel("Fan speed (RPM)")
    axes[0].legend()
    fig.suptitle(
        "Option 4 — Normalized RMS trends\n"
        "Shows shape agreement without asking amplitudes to match 1:1",
        fontweight="bold",
    )
    fig.tight_layout()
    save(fig, "option04_normalized_rms_trends")


def option05_regime_scatter_pair(df: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    subsets = [
        (
            axes[0],
            df[(df["flag"].isna()) & (df["rpm"] >= 90) & (df["rpm"] <= 220)].copy(),
            "ldv_torsion_rms_mm_corrected",
            "camera_torsion_rms_mm",
            "Option 5A — Torsion regime scatter",
            C_TORS,
        ),
        (
            axes[1],
            df[(df["flag"].isna()) & (df["rpm"] >= 240) & (df["rpm"] <= 300)].copy(),
            "ldv_bending_rms_mm_corrected",
            "camera_bending_rms_mm",
            "Option 5B — Re-emergence bending scatter",
            C_BEND,
        ),
    ]
    for ax, sub, xcol, ycol, title, color in subsets:
        lim = max(sub[xcol].max(), sub[ycol].max()) * 1.1
        ax.plot([0, lim], [0, lim], "--", color="0.5", lw=1.0)
        ax.scatter(sub[xcol], sub[ycol], s=70, color=color)
        for _, row in sub.iterrows():
            ax.annotate(str(int(row["rpm"])), (row[xcol], row[ycol]), xytext=(4, 3), textcoords="offset points", fontsize=8)
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_xlabel("LDV RMS (mm)")
        ax.set_ylabel("Camera RMS (mm)")
        ax.set_title(title)
    fig.tight_layout()
    save(fig, "option05_regime_specific_scatter")


def option06_contact_sheet():
    # placeholder title card to make the option set easier to browse in a folder
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis("off")
    text = (
        "Comparison Figure Options\n\n"
        "Option 1: Ratio vs RPM\n"
        "Option 2: Torsion-regime RMS (90-220 RPM)\n"
        "Option 3: Bending re-emergence RMS (240-300 RPM)\n"
        "Option 4: Normalized RMS trends\n"
        "Option 5: Regime-specific scatter pair"
    )
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=14)
    fig.tight_layout()
    save(fig, "option00_index")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    option06_contact_sheet()
    option01_ratio_vs_rpm(df)
    option02_torsion_regime_rms(df)
    option03_bending_reemergence_rms(df)
    option04_normalized_rms(df)
    option05_regime_scatter_pair(df)
    print("Wrote option figures to", OUT_DIR.resolve())


if __name__ == "__main__":
    main()
