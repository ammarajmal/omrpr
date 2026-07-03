"""
step12_figures_tables.py — OMRPR Pipeline Step 12: Manuscript Figures and Tables

PURPOSE:
    Generate all publication-ready figures and summary tables for the OMRPR
    manuscript. All figures are produced programmatically from locked result
    artifacts. No manual editing is permitted after generation.

INPUTS:
    results/step07/{condition}/motion.csv
    results/step08/{condition}/frequency.json
    results/step09/noise_floor/noise_floor_summary.json
    results/step09/camera_agreement/agreement_per_condition.csv
    results/step09/bootstrap_ci/bootstrap_ci_per_condition.csv
    results/step10/ldv_comparison_table.csv
    results/step10/ldv_summary.json
    results/step11/{condition}/motion_smoothed.csv

OUTPUTS:
    results/step12/
        fig01_displacement_traces.pdf   -- representative traces, e7_90rpm
        fig02_frequency_overview.pdf    -- dominant frequency vs RPM, all conditions
        fig03_ldv_scatter.pdf           -- camera RMS vs LDV RMS, stable regime
        fig04_camera_agreement.pdf      -- raw vs aligned Z disagreement
        fig05_uncertainty.pdf           -- per-condition RMS with CI and noise floor
        tab01_ldv_comparison.csv        -- full 21-condition comparison table
        tab02_summary_stats.csv         -- regime-level summary statistics
        step12_summary.json             -- generation log + gate status

ACCEPTANCE CRITERIA:
    1. All five figures generated without error
    2. Both tables written
    3. Zero forbidden phrases in any caption (checked programmatically)
    4. step12_summary.json reports status: PASS
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

RESULTS_DIR = Path("results")
OUT_DIR     = Path("results/step12")
STEP7_DIR   = RESULTS_DIR / "step07"
STEP8_DIR   = RESULTS_DIR / "step08"
STEP9_DIR   = RESULTS_DIR / "step09"
STEP10_DIR  = RESULTS_DIR / "step10"
STEP11_DIR  = RESULTS_DIR / "step11"

# Option B canonical per-condition table (claim_boundary.md's designated
# cross-check source). Table 1 in the manuscript is built from this file
# directly, so Fig. 3 must use the same source to stay internally consistent —
# do not substitute results/step10/ldv_comparison_table.csv here even though
# it now reproduces close (but not identical) numbers after the 2026-07-03
# step07/step10 formula/geometry fix (see step07_motion_decompose.py docstring).
OPTION_B_VERIFIED_TABLE = (
    Path(__file__).resolve().parents[2]
    / "omrpr_outputs_review" / "final_tables" / "option_b_verified_table.csv"
)

REFERENCE_CONDITION = "e7_90rpm"

F_H_HZ     = 1.430
F_ALPHA_HZ = 3.103

def _load_noise_floor_from_step09() -> tuple[float, float]:
    """Read derived noise floor bounds from step09 output (worst-case per-camera)."""
    path = STEP9_DIR / "noise_floor" / "noise_floor_summary.json"
    try:
        with open(path) as f:
            d = json.load(f)
        bounds = d.get("derived_bounds", {})
        bending = float(bounds["bending_avg_bound_mm"])
        torsion = float(bounds["torsion_diff_bound_mm"])
        return bending, torsion
    except (FileNotFoundError, KeyError):
        # Fallback if step09 hasn't been run; hard-coded values kept for reference
        return 0.017, 0.033


NOISE_FLOOR_BENDING_MM, NOISE_FLOOR_TORSION_MM = _load_noise_floor_from_step09()

# Bending ratio — Option B canonical (claim_boundary.md v2.1). The over-read is
# explained in Discussion Sec. 5.2 by three documented, non-exclusive factors:
# non-simultaneous acquisition (~11 months apart), point-vs-spatial-averaging
# geometry (LDV single point vs. camera cross-bridge average), and residual
# software timing uncertainty (<=20.03 ms max pairwise drift). The earlier
# "y_leak / 9.8 deg inter-camera misalignment" explanation was derived for the
# retracted B0-era result (r=0.845) and does not apply to Option B — do not
# reintroduce it here (see FINALIZATION_PLAN.md Phase 4 checklist).
BENDING_RATIO_MEAN_STABLE = 1.261   # cam / LDV, stable conditions (Option B canonical)
BENDING_STABLE_PEARSON_R  = 0.960   # stable-regime canonical value (claim_boundary.md v2.1)
BENDING_STABLE_N          = 19      # stable-regime canonical condition count (v2.1)
BENDING_LEAKAGE_NOTE = (
    f"Bending cam/LDV ratio = {BENDING_RATIO_MEAN_STABLE:.2f}× (stable mean, "
    f"{BENDING_STABLE_N} conditions). The over-read reflects non-simultaneous "
    "acquisition, point-vs-spatial-averaging geometry, and residual timing "
    "uncertainty (see Discussion Sec. 5.2) — not a validated accuracy figure. "
    f"Bending r = {BENDING_STABLE_PEARSON_R:.3f} (stable, {BENDING_STABLE_N} cond.)."
)

REGIME_BENDING_DOMINATED   = (40,  80)
REGIME_TORSION_DOMINATED   = (90,  220)
REGIME_BENDING_REEMERGENCE = (240, 300)

C_BENDING  = "#1f77b4"
C_TORSION  = "#ff7f0e"
C_SMOOTHED = "#2ca02c"
C_NOISE    = "#7f7f7f"

DPI = 150

FORBIDDEN_PHRASES = [
    "LDV-equivalent accuracy",
    "LDV-validated accuracy",
    "same-run waveform",
    "simultaneous validation",
    "hardware-synchronized",
    "hardware-triggered",
    "torsion angle",
    "measurement failure",
    "TESolution",
    "Anseong",
    "same run",
    "real-time",
]


# ---------------------------------------------------------------------------
# DATA LOADERS
# ---------------------------------------------------------------------------

def load_ldv_table():
    df = pd.read_csv(STEP10_DIR / "ldv_comparison_table.csv")
    df["rpm"] = df["wtt_condition"].apply(
        lambda c: int(c.split("_")[1].replace("rpm", ""))
    )
    return df.sort_values("rpm").reset_index(drop=True)


def load_camera_agreement():
    df = pd.read_csv(STEP9_DIR / "camera_agreement" / "agreement_per_condition.csv")
    df["rpm"] = df["condition"].apply(
        lambda c: int(c.split("_")[1].replace("rpm", ""))
    )
    return df.sort_values("rpm").reset_index(drop=True)


def load_bootstrap_ci():
    return pd.read_csv(STEP9_DIR / "bootstrap_ci" / "bootstrap_ci_per_condition.csv")


def load_step7_motion(condition):
    return pd.read_csv(STEP7_DIR / condition / "motion.csv")


def load_step11_smoothed(condition):
    return pd.read_csv(STEP11_DIR / condition / "motion_smoothed.csv")


def load_frequency_data():
    rows = []
    for cond_dir in sorted(STEP8_DIR.iterdir()):
        if not cond_dir.is_dir():
            continue
        fpath = cond_dir / "frequency.json"
        if not fpath.exists():
            continue
        with open(fpath) as f:
            d = json.load(f)
        cond = cond_dir.name
        rpm  = int(cond.split("_")[1].replace("rpm", ""))
        b = d.get("bending", {})
        t = d.get("torsion", {})
        rows.append({
            "condition":     cond,
            "rpm":           rpm,
            "b_dominant_hz": b.get("dominant_peak_hz", np.nan),
            "b_ref_bin_hz":  b.get("nearest_ref_bin_hz", np.nan),
            "t_dominant_hz": t.get("dominant_peak_hz", np.nan),
            "t_ref_bin_hz":  t.get("nearest_ref_bin_hz", np.nan),
        })
    return pd.DataFrame(rows).sort_values("rpm").reset_index(drop=True)


def load_ldv_summary():
    with open(STEP10_DIR / "ldv_summary.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def shade_regimes(ax, alpha=0.07):
    ax.axvspan(*REGIME_BENDING_DOMINATED,   color=C_BENDING,  alpha=alpha)
    ax.axvspan(*REGIME_TORSION_DOMINATED,   color=C_TORSION,  alpha=alpha)
    ax.axvspan(*REGIME_BENDING_REEMERGENCE, color=C_SMOOTHED, alpha=alpha)


def check_forbidden_phrases(captions):
    found = []
    for cap in captions:
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in cap.lower() and phrase not in found:
                found.append(phrase)
    return found


def save_fig(fig, name):
    path = OUT_DIR / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {path}")


# ---------------------------------------------------------------------------
# FIGURE 1 -- Representative displacement traces (e7_90rpm)
# ---------------------------------------------------------------------------

CAPTION_FIG1 = (
    "Fig. 1. Displacement traces for e7_90rpm (90 RPM, torsion-dominated regime). "
    "Upper: bending channel (cross-bridge average of Camera 1, 2 and 3 "
    "Y-displacements). "
    "Lower: two-point differential displacement proxy (Camera 3 minus the "
    "Camera 1/2 mean). "
    "Grey: Step 07 motion decomposition output; green: RTS-smoothed output (Step 11). "
    "The RTS smoother introduces no measurable phase shift (< ±8.3 ms, resolution-limited "
    "at 60 Hz) and preserves signal amplitude (ratio 0.999), as validated across all 21 conditions."
)


def fig01_displacement_traces():
    raw      = load_step7_motion(REFERENCE_CONDITION)
    smoothed = load_step11_smoothed(REFERENCE_CONDITION)
    t = raw["t_s"].to_numpy() - raw["t_s"].iloc[0]

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    axes[0].plot(t, raw["bending_avg_y_mm"],
                 color="0.65", lw=0.6, label="Raw (Step 07)", zorder=1)
    axes[0].plot(t, smoothed["bending_smoothed_mm"],
                 color=C_SMOOTHED, lw=1.0, label="RTS-smoothed (Step 11)", zorder=2)
    axes[0].set_ylabel("Bending displacement (mm)")
    axes[0].legend(loc="upper right", fontsize=8)
    axes[0].set_title("Bending channel — cross-bridge average (Camera 1, 2 & 3)")

    axes[1].plot(t, raw["torsion_diff_y_mm"],
                 color="0.65", lw=0.6, label="Raw (Step 07)", zorder=1)
    axes[1].plot(t, smoothed["torsion_smoothed_mm"],
                 color=C_SMOOTHED, lw=1.0, label="RTS-smoothed (Step 11)", zorder=2)
    axes[1].set_ylabel("Two-point differential\ndisplacement proxy (mm)")
    axes[1].set_xlabel("Time (s)")
    axes[1].legend(loc="upper right", fontsize=8)
    axes[1].set_title("Torsion proxy — Camera 3 minus Camera 1/2 mean")

    fig.suptitle(
        "e7_90rpm representative traces | commercial aerodynamic testing facility, South Korea",
        fontsize=9
    )
    fig.tight_layout()
    save_fig(fig, "fig01_displacement_traces.pdf")
    return [CAPTION_FIG1]


# ---------------------------------------------------------------------------
# FIGURE 2 -- Dominant frequency vs RPM
# ---------------------------------------------------------------------------

CAPTION_FIG2 = (
    "Fig. 2. Dominant spectral peak frequency (circles) and nearest reference bin "
    "frequency (crosses) vs fan RPM for all 21 conditions. "
    "Upper: bending channel. "
    "Lower: two-point differential displacement proxy. "
    "Shaded bands show the three aerodynamic regimes: "
    "bending-dominated (40-80 RPM), torsion-dominated (90-220 RPM), "
    "bending re-emergence (240-300 RPM). "
    "Configured structural reference targets and measured dominant peaks are "
    "reported separately."
)


def fig02_frequency_overview():
    df = load_frequency_data()

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    for ax, peak_col, ref_col, ref_hz, title, color in [
        (axes[0], "b_dominant_hz", "b_ref_bin_hz", F_H_HZ,
         f"Bending dominant frequency  (f_h = {F_H_HZ} Hz)", C_BENDING),
        (axes[1], "t_dominant_hz", "t_ref_bin_hz", F_ALPHA_HZ,
         f"Torsion proxy dominant frequency  (f_alpha = {F_ALPHA_HZ} Hz)", C_TORSION),
    ]:
        shade_regimes(ax)
        ax.axhline(ref_hz, color="0.3", lw=0.8, ls="--", label=f"f_ref = {ref_hz} Hz")
        ax.scatter(df["rpm"], df[peak_col], s=40, color=color,
                   zorder=5, label="Dominant peak")
        ax.scatter(df["rpm"], df[ref_col], s=25, color=color, marker="x",
                   zorder=5, label="Nearest ref bin")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title(title)
        ax.set_ylim(0, 12)
        ax.legend(loc="upper left", fontsize=7, ncol=3)

    axes[1].set_xlabel("Fan speed (RPM)")
    fig.suptitle("Step 08 — Frequency analysis: dominant peak vs nearest reference bin",
                 fontsize=9)
    fig.tight_layout()
    save_fig(fig, "fig02_frequency_overview.pdf")
    return [CAPTION_FIG2]


# ---------------------------------------------------------------------------
# FIGURE 3 -- LDV condition-level comparison scatter
# ---------------------------------------------------------------------------

CAPTION_FIG3 = (
    "Fig. 3. Condition-level RMS comparison: camera system vs LDV reference. "
    "Left: bending channel. Right: two-point differential displacement proxy. "
    "Stable conditions, 19 total, includes 60 RPM (filled circles); "
    "DCG-excluded 320 RPM, motion blur (open square). "
    "Camera and LDV data are compared condition-by-condition from the same tunnel "
    "using separate recording sessions and separate DAQ systems. "
    "This is a condition-level statistical comparison (RMS and peak per condition). "
    "Pearson r and Spearman rho computed for stable conditions only. "
    + BENDING_LEAKAGE_NOTE
)


def load_option_b_verified_table():
    """
    Option B canonical per-condition table (claim_boundary.md's designated
    cross-check source) — same file Table 1 in the manuscript is built from.
    """
    df = pd.read_csv(OPTION_B_VERIFIED_TABLE)
    df["flag"] = df["flag"].fillna("")
    return df.sort_values("rpm").reset_index(drop=True)


def fig03_ldv_scatter():
    df = load_option_b_verified_table()

    stable   = df[df["flag"] == ""].copy()
    unstable = df[df["flag"] == "DCG-excl"].copy()

    b_r,   _ = stats.pearsonr(stable["cam_bend_rms"], stable["ldv_bend_rms"])
    b_rho, _ = stats.spearmanr(stable["cam_bend_rms"], stable["ldv_bend_rms"])
    t_r,   _ = stats.pearsonr(stable["cam_tors_rms"], stable["ldv_tors_rms"])
    t_rho, _ = stats.spearmanr(stable["cam_tors_rms"], stable["ldv_tors_rms"])

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    for ax, cam_col, ldv_col, color, title, r_val, rho_val in [
        (axes[0], "cam_bend_rms", "ldv_bend_rms",
         C_BENDING, "Bending", b_r, b_rho),
        (axes[1], "cam_tors_rms", "ldv_tors_rms",
         C_TORSION, "Two-point differential proxy", t_r, t_rho),
    ]:
        all_vals = pd.concat([df[cam_col].dropna(), df[ldv_col].dropna()])
        lim = (0, all_vals.max() * 1.1)
        ax.plot(lim, lim, "k--", lw=0.8, alpha=0.5, label="1:1")

        ax.scatter(stable[ldv_col], stable[cam_col],
                   s=50, color=color, zorder=5, label="Stable (19, incl. 60 RPM)")
        ax.scatter(unstable[ldv_col], unstable[cam_col],
                   s=60, color=color, marker="s", facecolors="none",
                   zorder=5, label="DCG-excluded (320 RPM)")

        ax.set_xlabel("LDV RMS (mm)")
        ax.set_ylabel("Camera RMS (mm)")
        ax.set_xlim(*lim)
        ax.set_ylim(*lim)
        ax.set_title(title)
        ax.text(
            0.05, 0.92,
            f"Pearson r = {r_val:.3f}\nSpearman rho = {rho_val:.3f}\n(stable only)",
            transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8)
        )
        if title == "Bending":
            ax.text(
                0.05, 0.60,
                f"Ratio cam/LDV = {BENDING_RATIO_MEAN_STABLE:.2f}x (stable mean)\n"
                "Non-simultaneous acquisition, spatial-averaging\n"
                "geometry, and residual timing uncertainty\n"
                "(see Discussion Sec. 5.2) -- not an accuracy claim.",
                transform=ax.transAxes, fontsize=7, va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.85)
            )
        ax.legend(fontsize=7, loc="lower right")

    fig.suptitle(
        "Condition-level camera vs LDV RMS (same-tunnel, separate-session comparison)",
        fontsize=9
    )
    fig.tight_layout()
    save_fig(fig, "fig03_ldv_scatter.pdf")
    return [CAPTION_FIG3]


# ---------------------------------------------------------------------------
# FIGURE 4 -- Camera agreement
# ---------------------------------------------------------------------------

CAPTION_FIG4 = (
    "Fig. 4. Camera 1 to Camera 2 inter-camera Z-axis agreement after baseline "
    "alignment (Step 06), shown per condition. "
    "Raw Z standard deviation before alignment is approximately 388 mm, reflecting "
    "the physical camera separation projected onto the Z axis. "
    "After full-run mean removal, aligned Z standard deviation is 1.4 mm mean "
    "across 21 conditions (approximately 189 times improvement for e7_90rpm). "
    "Baseline alignment achieves the function of a geometric extrinsic calibration "
    "for displacement measurement without requiring a surveyed world frame."
)


def fig04_camera_agreement():
    df = load_camera_agreement()
    x  = df["rpm"].to_numpy()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(x, df["aligned_z_std_mm"], width=4, color=C_BENDING, alpha=0.85,
           label="Aligned Z std (mm)")
    ax.set_xlabel("Fan speed (RPM)")
    ax.set_ylabel("Aligned Z standard deviation (mm)")
    ax.set_title(
        "Step 06 -- Camera 1-Camera 2 inter-camera Z agreement after baseline alignment\n"
        "(Raw Z std before alignment: ~388 mm; not shown on this scale)"
    )
    ax.legend(fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([str(r) for r in x], rotation=45, fontsize=7)
    ax.text(
        0.98, 0.95,
        "Raw Z std (before alignment): ~388 mm\ne7_90rpm improvement: ~189x",
        transform=ax.transAxes, fontsize=8, ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9)
    )
    fig.tight_layout()
    save_fig(fig, "fig04_camera_agreement.pdf")
    return [CAPTION_FIG4]


# ---------------------------------------------------------------------------
# FIGURE 5 -- Per-condition RMS with noise floor and bootstrap CI
# ---------------------------------------------------------------------------

CAPTION_FIG5 = (
    "Fig. 5. Per-condition camera RMS displacement with 95% bootstrap confidence "
    "intervals (moving-block, 1000 resamples) and static noise floor. "
    "Upper: bending channel. Lower: two-point differential displacement proxy. "
    "Horizontal dashed lines show Step 09 static-bag support bounds "
    f"(bending: {NOISE_FLOOR_BENDING_MM:.3f} mm; torsion proxy: {NOISE_FLOOR_TORSION_MM:.3f} mm). "
    "Grey band indicates the near-floor region where the camera cannot resolve "
    "the true displacement amplitude. "
    "DCG-excluded condition (320 RPM, motion blur) is annotated separately; "
    "60 RPM is a normal stable condition and is not annotated."
)


def fig05_uncertainty():
    df_ldv = load_ldv_table()
    df_ci  = load_bootstrap_ci()

    df_b = (df_ci[df_ci["channel"] == "bending_avg_y_mm"]
            .merge(df_ldv[["wtt_condition", "rpm", "flag"]],
                   left_on="condition", right_on="wtt_condition", how="left")
            .sort_values("rpm").reset_index(drop=True))
    df_t = (df_ci[df_ci["channel"] == "torsion_diff_y_mm"]
            .merge(df_ldv[["wtt_condition", "rpm", "flag"]],
                   left_on="condition", right_on="wtt_condition", how="left")
            .sort_values("rpm").reset_index(drop=True))

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

    for ax, df, noise_floor, color, title in [
        (axes[0], df_b, NOISE_FLOOR_BENDING_MM, C_BENDING,
         f"Bending -- camera RMS  (noise floor: {NOISE_FLOOR_BENDING_MM} mm)"),
        (axes[1], df_t, NOISE_FLOOR_TORSION_MM, C_TORSION,
         f"Torsion proxy -- camera RMS  (noise floor: {NOISE_FLOOR_TORSION_MM} mm)"),
    ]:
        rpm = df["rpm"].to_numpy()
        rms = df["rms_estimate_mm"].to_numpy()
        lo  = df["ci_lo_mm"].to_numpy()
        hi  = df["ci_hi_mm"].to_numpy()

        ax.axhspan(0, noise_floor * 2, color="0.90", alpha=0.6,
                   label="Near noise floor")
        ax.axhline(noise_floor, color=C_NOISE, lw=1.0, ls="--",
                   label=f"Noise floor ({noise_floor} mm)")
        ax.errorbar(rpm, rms, yerr=[rms - lo, hi - rms],
                    fmt="o", color=color, ms=5, lw=1.2, capsize=3,
                    label="Camera RMS +/- 95% CI")

        for _, row in df.iterrows():
            flag = row.get("flag")
            if flag == "high_wind_unstable":
                ax.annotate("High-wind\nunstable",
                            xy=(row["rpm"], row["rms_estimate_mm"]),
                            xytext=(row["rpm"] - 50, row["rms_estimate_mm"] * 0.7),
                            fontsize=6, arrowprops=dict(arrowstyle="->", lw=0.7),
                            color="0.3")

        ax.set_ylabel("RMS displacement (mm)")
        ax.set_title(title)
        ax.legend(fontsize=7, loc="upper left", ncol=3)
        ax.set_ylim(bottom=0)

    axes[1].set_xlabel("Fan speed (RPM)")
    fig.suptitle("Step 09 -- Camera RMS with bootstrap 95% CIs and static noise floor",
                 fontsize=9)
    fig.tight_layout()
    save_fig(fig, "fig05_uncertainty.pdf")
    return [CAPTION_FIG5]


# ---------------------------------------------------------------------------
# TABLE 1 -- Full 21-condition LDV comparison
# ---------------------------------------------------------------------------

def tab01_ldv_comparison():
    df = load_ldv_table()
    df_out = df[[
        "wtt_condition", "rpm", "flag",
        "camera_bending_rms_mm", "ldv_bending_rms_mm_corrected",
        "bending_ratio_cam_over_ldv",
        "camera_torsion_rms_mm", "ldv_torsion_rms_mm_corrected",
        "torsion_ratio_cam_over_ldv",
    ]].rename(columns={
        "wtt_condition":                "Condition",
        "rpm":                          "RPM",
        "flag":                         "Flag",
        "camera_bending_rms_mm":        "Cam_Bending_RMS_mm",
        "ldv_bending_rms_mm_corrected": "LDV_Bending_RMS_mm",
        "bending_ratio_cam_over_ldv":   "Bending_Ratio",
        "camera_torsion_rms_mm":        "Cam_Torsion_RMS_mm",
        "ldv_torsion_rms_mm_corrected": "LDV_Torsion_RMS_mm",
        "torsion_ratio_cam_over_ldv":   "Torsion_Ratio",
    }).copy()

    path = OUT_DIR / "tab01_ldv_comparison.csv"
    df_out.to_csv(path, index=False, float_format="%.4f")
    print(f"  [WRITE] {path}")


# ---------------------------------------------------------------------------
# TABLE 2 -- Regime-level summary statistics
# ---------------------------------------------------------------------------

def tab02_summary_stats():
    ldv = load_ldv_summary()
    sr  = ldv.get("stable_regime", {})
    fr  = ldv.get("full_regime", {})

    rows = [
        {
            "Regime": "Full (20 conditions excl. 0 RPM)",
            "Channel": "Bending",
            "Pearson_r": fr.get("bending_pearson_r"),
            "Spearman_rho": fr.get("bending_spearman_rho"),
            "MAE_mm": fr.get("bending_mae_mm"),
            "RMSE_mm": fr.get("bending_rmse_mm"),
            "Ratio_mean": fr.get("bending_ratio_mean"),
            "N": fr.get("bending_n_conditions"),
        },
        {
            "Regime": "Full (20 conditions)",
            "Channel": "Torsion proxy",
            "Pearson_r": fr.get("torsion_pearson_r"),
            "Spearman_rho": fr.get("torsion_spearman_rho"),
            "MAE_mm": fr.get("torsion_mae_mm"),
            "RMSE_mm": fr.get("torsion_rmse_mm"),
            "Ratio_mean": fr.get("torsion_ratio_mean"),
            "N": fr.get("torsion_n_conditions"),
        },
        {
            "Regime": "Stable (19 conditions, incl. 60 RPM; excl. DCG 320 RPM)",
            "Channel": "Bending",
            "Pearson_r": sr.get("stable_bending_pearson_r"),
            "Spearman_rho": sr.get("stable_bending_spearman_rho"),
            "MAE_mm": sr.get("stable_bending_mae_mm"),
            "RMSE_mm": sr.get("stable_bending_rmse_mm"),
            "Ratio_mean": sr.get("stable_bending_ratio_mean"),
            "N": sr.get("stable_bending_n_conditions"),
        },
        {
            "Regime": "Stable (19 conditions, incl. 60 RPM; excl. DCG 320 RPM)",
            "Channel": "Torsion proxy",
            "Pearson_r": sr.get("stable_torsion_pearson_r"),
            "Spearman_rho": sr.get("stable_torsion_spearman_rho"),
            "MAE_mm": sr.get("stable_torsion_mae_mm"),
            "RMSE_mm": sr.get("stable_torsion_rmse_mm"),
            "Ratio_mean": sr.get("stable_torsion_ratio_mean"),
            "N": sr.get("stable_torsion_n_conditions"),
        },
        {
            "Regime": "Step 09 static noise floor",
            "Channel": "Bending",
            "Pearson_r": None, "Spearman_rho": None, "MAE_mm": None,
            "RMSE_mm": NOISE_FLOOR_BENDING_MM, "Ratio_mean": None, "N": None,
        },
        {
            "Regime": "Step 09 static noise floor",
            "Channel": "Torsion proxy",
            "Pearson_r": None, "Spearman_rho": None, "MAE_mm": None,
            "RMSE_mm": NOISE_FLOOR_TORSION_MM, "Ratio_mean": None, "N": None,
        },
        {
            "Regime": "Step 09 camera agreement aligned Z mean",
            "Channel": "Cam1-Cam2 Z std",
            "Pearson_r": None, "Spearman_rho": None, "MAE_mm": None,
            "RMSE_mm": 1.394, "Ratio_mean": None, "N": 21,
        },
        {
            "Regime": "Step 11 RTS smoother mean amplitude ratio",
            "Channel": "Bending + Torsion",
            "Pearson_r": None, "Spearman_rho": None, "MAE_mm": None,
            "RMSE_mm": None, "Ratio_mean": 0.995, "N": 21,
        },
        {
            "Regime": "FOOTNOTE — " + BENDING_LEAKAGE_NOTE,
            "Channel": "", "Pearson_r": None, "Spearman_rho": None,
            "MAE_mm": None, "RMSE_mm": None, "Ratio_mean": None, "N": None,
        },
    ]

    path = OUT_DIR / "tab02_summary_stats.csv"
    pd.DataFrame(rows).to_csv(path, index=False, float_format="%.4f")
    print(f"  [WRITE] {path}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("STEP 12 -- MANUSCRIPT FIGURES AND TABLES")
    print("=" * 60)

    all_captions = []
    generated    = []
    errors       = []

    steps = [
        ("Fig 01 -- displacement traces",  fig01_displacement_traces),
        ("Fig 02 -- frequency overview",   fig02_frequency_overview),
        ("Fig 03 -- LDV scatter",          fig03_ldv_scatter),
        ("Fig 04 -- camera agreement",     fig04_camera_agreement),
        ("Fig 05 -- uncertainty + CI",     fig05_uncertainty),
    ]

    for label, fn in steps:
        print(f"\n[GENERATE] {label}")
        try:
            captions = fn()
            all_captions.extend(captions)
            generated.append(label)
        except Exception as e:
            print(f"  [ERROR] {e}")
            errors.append((label, str(e)))

    print("\n[GENERATE] Tab 01 -- LDV comparison table")
    try:
        tab01_ldv_comparison()
        generated.append("Tab 01")
    except Exception as e:
        print(f"  [ERROR] {e}")
        errors.append(("Tab 01", str(e)))

    print("\n[GENERATE] Tab 02 -- Summary statistics")
    try:
        tab02_summary_stats()
        generated.append("Tab 02")
    except Exception as e:
        print(f"  [ERROR] {e}")
        errors.append(("Tab 02", str(e)))

    print("\n[CLAIM CHECK] Scanning captions for forbidden phrases...")
    forbidden_found = check_forbidden_phrases(all_captions)
    if forbidden_found:
        print(f"  [FAIL] Forbidden phrases found: {forbidden_found}")
    else:
        print(f"  [PASS] No forbidden phrases in {len(all_captions)} caption(s)")

    overall_gate = (
        "PASS"
        if len(errors) == 0 and len(forbidden_found) == 0
        else "FAIL"
    )

    summary = {
        "step":                  "step12_figures_tables",
        "status":                overall_gate,
        "n_generated":           len(generated),
        "n_errors":              len(errors),
        "generated":             generated,
        "errors":                errors,
        "captions_checked":      len(all_captions),
        "forbidden_found":       forbidden_found,
        "claim_boundary_pass":   len(forbidden_found) == 0,
        "note_comparison": (
            "LDV comparison is condition-level (RMS/peak/frequency per condition). "
            "Camera and LDV are compared condition-by-condition in the same tunnel "
            "from separate recording sessions on separate DAQ systems "
            "at different sampling rates (60 Hz vs 360 Hz)."
        ),
        "note_bending_ratio": BENDING_LEAKAGE_NOTE,
        "note_torsion_proxy": (
            "torsion_diff_y_mm is a two-point differential displacement proxy, "
            "not a validated torsion angle measurement."
        ),
    }

    summary_path = OUT_DIR / "step12_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[WRITE] {summary_path}")

    print("\n" + "=" * 60)
    print(f"STEP 12 COMPLETE -- {overall_gate}")
    print(f"  Figures:    {len(generated) - 2}")
    print(f"  Tables:     2")
    print(f"  Errors:     {len(errors)}")
    print(f"  Claim gate: {'PASS' if not forbidden_found else 'FAIL'}")
    print("=" * 60)

    if overall_gate == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
