"""
comparison_plots_v2.py — LDV vs Camera Publication Comparison Figures

Generates five publication-ready figures for Results & Discussion:

    Fig A — LDV vs Camera: Mean / RMS / Peak vs RPM (4-panel, matching facility format)
    Fig B — LDV vs Camera: Mean / RMS / Peak vs Wind Speed (4-panel)
    Fig C — FFT/PSD overlay in physical units mm²/Hz (3 representative conditions)
    Fig D — FFT/PSD overlay normalised to unit peak (spectral shape comparison)
    Fig E — Regime-annotated scatter: Camera RMS vs LDV RMS (bending + torsion)

All figures use confirmed geometry:
    pvolt = 2.7 cm/V, dside = 130 mm, db = 200 mm, dp = 1.538, fs_LDV = 360 Hz
    fn_b = 1.4323 Hz, fn_t = 3.0827 Hz, B = 0.40 m

Save to:  results/comparison_plots_v2/
Run from: /media/ammar/phd/omrpr/

Usage:
    python src/comparison_plots_v2.py

Requirements:
    numpy, scipy, pandas, matplotlib (standard omrpr conda environment)
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from scipy import signal as sp_signal

# ─── Paths ───────────────────────────────────────────────────────────────────
RESULTS_DIR = Path("results")
LDV_DIR     = Path("data/LDV/TESolution/laser_displacement/등류/영각00")
MANIFEST    = Path("data/LDV/manifest.json")
OUT_DIR     = Path("results/comparison_plots_v2")

# ─── Confirmed constants ─────────────────────────────────────────────────────
PVOLT   = 2.7        # cm/V
DSIDE   = 13.0       # cm  (130 mm)
DB      = 20.0       # cm  (200 mm)
DP      = DB / DSIDE  # 1.538...
FS_LDV  = 360.0      # Hz
FS_CAM  = 60.0       # Hz
FN_B    = 1.4323     # Hz
FN_T    = 3.0827     # Hz

# e20 (320 RPM) DCG-excluded from main analysis; shown separately
DCG_EXCLUDED = "e20_320rpm"
VIV_COND     = "e4_60rpm"

# ─── Aerodynamic regime RPM boundaries ───────────────────────────────────────
REGIME_BENDING   = (40,  80)
REGIME_TORSION   = (90,  220)
REGIME_REEMERGE  = (240, 300)

# ─── Colour scheme (colourblind-safe) ────────────────────────────────────────
C_CAM    = "#1f77b4"   # blue   — camera
C_LDV    = "#d62728"   # red    — LDV
C_PEAK   = "#ff7f0e"   # orange — peak values
C_MEAN   = "#2ca02c"   # green  — mean values

C_REG_B  = "#aec7e8"   # bending VIV regime
C_REG_T  = "#ffbb78"   # torsional VIV regime
C_REG_R  = "#98df8a"   # bending re-emergence

DPI = 180

# ─── Publication RC params ───────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "DejaVu Sans",
    "font.size":         10,
    "axes.titlesize":    10,
    "axes.titleweight":  "bold",
    "axes.labelsize":    10,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "legend.fontsize":   8.5,
    "figure.dpi":        DPI,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "grid.linestyle":    "--",
})


# ═════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═════════════════════════════════════════════════════════════════════════════

def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def load_ldv_bias():
    raw = np.loadtxt(str(LDV_DIR / "D00"), usecols=(0, 1))
    return np.mean(raw, axis=0)


def load_ldv_timeseries(d_path: Path, bias: np.ndarray):
    """Return (bending_mm, torsion_mm) full time series in mm."""
    raw  = np.loadtxt(str(d_path), usecols=(0, 1))
    cal  = (raw - bias) * PVOLT             # cm
    b_mm = ((cal[:, 0] + cal[:, 1]) / 2.0) * 10.0
    t_mm = ((cal[:, 1] - cal[:, 0]) * DP)  * 10.0
    return b_mm, t_mm


def ldv_stats(b_mm: np.ndarray, t_mm: np.ndarray):
    """Return (b_mean, b_rms, b_peak, t_mean, t_rms, t_peak) all in mm."""
    b_dem = b_mm - np.mean(b_mm)
    t_dem = t_mm - np.mean(t_mm)
    return (
        float(np.mean(b_mm)),
        float(np.std(b_mm)),          # std ≡ rms after mean removal
        float(np.max(np.abs(b_dem))), # peak of oscillatory component (mean-removed)
        float(np.mean(t_mm)),
        float(np.std(t_mm)),
        float(np.max(np.abs(t_dem))),
    )


def load_camera_timeseries(condition: str):
    """Return (bending_mm, torsion_mm, t_s) arrays from step07 motion.csv."""
    path = RESULTS_DIR / "step07" / condition / "motion.csv"
    if not path.exists():
        return None, None, None
    df = pd.read_csv(path)
    b  = df["bending_avg_y_mm"].values - np.mean(df["bending_avg_y_mm"].values)
    t  = df["torsion_diff_y_mm"].values - np.mean(df["torsion_diff_y_mm"].values)
    ts = df["t_s"].values
    return b, t, ts


def camera_stats(b_mm, t_mm):
    """Return (b_mean, b_rms, b_peak, t_mean, t_rms, t_peak)."""
    return (
        0.0,                            # mean is zero by step06 construction
        float(np.std(b_mm)),
        float(np.max(np.abs(b_mm))),
        0.0,
        float(np.std(t_mm)),
        float(np.max(np.abs(t_mm))),
    )


def compute_psd(sig, fs):
    """One-sided Welch PSD in mm²/Hz."""
    nperseg = min(len(sig), int(fs * 5))
    f, p = sp_signal.welch(sig, fs=fs, nperseg=nperseg,
                            window="hann", scaling="density")
    return f, p


def build_full_dataset():
    """
    Build master DataFrame with LDV and camera stats per condition.
    Returns df with columns: condition, rpm, windspeed,
                             ldv_b_mean/rms/peak, ldv_t_mean/rms/peak,
                             cam_b_mean/rms/peak, cam_t_mean/rms/peak,
                             flag
    """
    manifest = load_manifest()
    bias     = load_ldv_bias()
    rows     = []

    for entry in manifest["conditions"]:
        cond  = entry["wtt_condition"]
        rpm   = entry["rpm"]
        ws    = entry.get("windspeed_ms", 0.0)
        dfile = entry["ldv_file"].replace(".csv", "")

        # Wind speed from manifest or Excel mapping
        ws_map = {
            20: 0.000, 40: 0.516, 50: 0.699, 60: 0.882,
            70: 1.066, 80: 1.249, 90: 1.432, 100: 1.616,
            110: 1.799, 120: 1.982, 140: 2.349, 160: 2.715,
            180: 3.082, 200: 3.449, 220: 3.815, 240: 4.182,
            260: 4.548, 280: 4.915, 300: 5.282, 320: 5.648,
        }
        windspeed = ws_map.get(rpm, ws)

        d_path = LDV_DIR / dfile
        if not d_path.exists():
            print(f"  [SKIP LDV] {dfile} not found")
            continue

        b_ldv, t_ldv = load_ldv_timeseries(d_path, bias)
        lm, lr, lp, ltm, ltr, ltp = ldv_stats(b_ldv, t_ldv)

        b_cam, t_cam, _ = load_camera_timeseries(cond)
        if b_cam is None:
            print(f"  [SKIP CAM] {cond} motion.csv not found")
            cm, cr, cp, ctm, ctr, ctp = (np.nan,)*6
        else:
            cm, cr, cp, ctm, ctr, ctp = camera_stats(b_cam, t_cam)

        flag = ""
        if cond == DCG_EXCLUDED:
            flag = "DCG_excluded"
        elif cond == VIV_COND:
            flag = "VIV"

        rows.append({
            "condition": cond, "rpm": rpm, "windspeed": windspeed, "flag": flag,
            "ldv_b_mean": lm,  "ldv_b_rms": lr,  "ldv_b_peak": lp,
            "ldv_t_mean": ltm, "ldv_t_rms": ltr, "ldv_t_peak": ltp,
            "cam_b_mean": cm,  "cam_b_rms": cr,  "cam_b_peak": cp,
            "cam_t_mean": ctm, "cam_t_rms": ctr, "cam_t_peak": ctp,
        })

    df = pd.DataFrame(rows).sort_values("rpm").reset_index(drop=True)
    print(f"[DATA] Loaded {len(df)} conditions")
    return df


# ═════════════════════════════════════════════════════════════════════════════
# REGIME SHADING HELPER
# ═════════════════════════════════════════════════════════════════════════════

def shade_regimes_rpm(ax, alpha=0.18):
    ax.axvspan(*REGIME_BENDING,  color=C_REG_B, alpha=alpha, zorder=0)
    ax.axvspan(*REGIME_TORSION,  color=C_REG_T, alpha=alpha, zorder=0)
    ax.axvspan(*REGIME_REEMERGE, color=C_REG_R, alpha=alpha, zorder=0)


def shade_regimes_ws(ax, alpha=0.18):
    """Shade by wind speed equivalent of RPM regime boundaries."""
    # Bending VIV: 40–80 RPM → 0.516–1.249 m/s
    # Torsional VIV: 90–220 RPM → 1.432–3.815 m/s
    # Bending re-emergence: 240–300 RPM → 4.182–5.282 m/s
    ax.axvspan(0.516, 1.249, color=C_REG_B, alpha=alpha, zorder=0)
    ax.axvspan(1.432, 3.815, color=C_REG_T, alpha=alpha, zorder=0)
    ax.axvspan(4.182, 5.282, color=C_REG_R, alpha=alpha, zorder=0)


def regime_legend_patches():
    return [
        mpatches.Patch(color=C_REG_B, alpha=0.5, label="Bending VIV (40–80 RPM)"),
        mpatches.Patch(color=C_REG_T, alpha=0.5, label="Torsional VIV (90–220 RPM)"),
        mpatches.Patch(color=C_REG_R, alpha=0.5, label="Bending re-emergence (240–300 RPM)"),
    ]


# ═════════════════════════════════════════════════════════════════════════════
# FIGURE A — Mean / RMS / Peak vs RPM  (matching facility format)
# ═════════════════════════════════════════════════════════════════════════════

def fig_A_rpm(df: pd.DataFrame):
    """
    4-panel figure: Bending(RPM) | Torsion(RPM) top row
                   Bending(RPM zoom no e20) | Torsion(RPM zoom no e20) bottom row
    Each panel: LDV Mean, RMS, Peak + Camera RMS
    Matches the facility's own Excel figure format.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        "Camera vs LDV: Mean / RMS / Peak Displacement vs Fan Speed\n"
        f"LDV @ 360 Hz  |  Camera @ 60 Hz  |  Simultaneous same-tunnel recording",
        fontsize=11, fontweight="bold"
    )

    # Separate stable (all), and no-DCG for zoomed bottom row
    df_all    = df.copy()
    df_stable = df[df["flag"] != "DCG_excluded"].copy()

    for row_idx, (data, row_label) in enumerate([
        (df_all,    "All conditions (incl. e20 DCG-excluded)"),
        (df_stable, "Stable + VIV conditions (e20 DCG-excluded)"),
    ]):
        for col_idx, (channel, ch_label, b_or_t) in enumerate([
            ("Bending",       "Bending displacement (mm)",       "b"),
            ("Torsion proxy", "Two-point differential proxy (mm)", "t"),
        ]):
            ax = axes[row_idx, col_idx]
            shade_regimes_rpm(ax)

            x = data["rpm"].values

            ldv_mean = data[f"ldv_{b_or_t}_mean"].abs().values  # |mean|
            ldv_rms  = data[f"ldv_{b_or_t}_rms"].values
            ldv_peak = data[f"ldv_{b_or_t}_peak"].values
            cam_rms  = data[f"cam_{b_or_t}_rms"].values

            # LDV traces
            ax.plot(x, ldv_mean, "k-o",  ms=5, lw=1.2, label="LDV |Mean|",
                    zorder=4, alpha=0.8)
            ax.plot(x, ldv_rms,  "r-s",  ms=5, lw=1.5, label="LDV RMS",
                    zorder=5)
            ax.plot(x, ldv_peak, "r--^", ms=5, lw=1.2, label="LDV Peak",
                    zorder=4, alpha=0.7)

            # Camera RMS
            valid_cam = ~np.isnan(cam_rms)
            ax.plot(x[valid_cam], cam_rms[valid_cam], "b-o",
                    ms=6, lw=2.0, label="Camera RMS", zorder=6)

            # Mark DCG-excluded and VIV with special markers
            for _, r in data.iterrows():
                if r["flag"] == "DCG_excluded":
                    ax.axvline(r["rpm"], color="gray", ls=":", lw=1.0, alpha=0.7)
                    ax.text(r["rpm"], ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 1,
                            "DCG\nexcl.", ha="center", va="top", fontsize=6,
                            color="gray")
                elif r["flag"] == "VIV":
                    ax.axvline(r["rpm"], color="purple", ls=":", lw=1.0, alpha=0.5)

            ax.set_xlabel("Fan speed (RPM)")
            ax.set_ylabel(ch_label)
            ax.set_title(f"{channel} — {row_label}", fontsize=9)
            if col_idx == 0 and row_idx == 0:
                ax.legend(loc="upper left", fontsize=8, ncol=2)

    # Add regime legend at bottom
    patches = regime_legend_patches()
    fig.legend(handles=patches, loc="lower center", ncol=3,
               fontsize=8.5, bbox_to_anchor=(0.5, -0.01), frameon=True)

    fig.tight_layout(rect=[0, 0.03, 1, 1])
    path = OUT_DIR / "figA_mean_rms_peak_vs_rpm.pdf"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {path}")
    # Also save PNG for quick review
    path_png = OUT_DIR / "figA_mean_rms_peak_vs_rpm.png"
    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 9))
    # Re-draw for PNG (simpler approach: just save the same data)
    return path


# ═════════════════════════════════════════════════════════════════════════════
# FIGURE A (PNG version, combined) — the one we actually produce
# ═════════════════════════════════════════════════════════════════════════════

def fig_A_full(df: pd.DataFrame, x_col: str, x_label: str,
               shade_fn, fname_stem: str, x_label_viv: str = None):
    """
    Generic 4-panel LDV vs Camera Mean/RMS/Peak figure.
    x_col: 'rpm' or 'windspeed'
    """
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32)

    panels = [
        (0, 0, "b", "Bending", "Bending displacement (mm)"),
        (0, 1, "t", "Torsion proxy", "Two-point differential proxy (mm)"),
    ]

    df_all    = df.copy()
    df_stable = df[df["flag"] != "DCG_excluded"].copy()
    datasets  = [(df_all, "All 20 conditions"), (df_stable, "e20 DCG-excluded")]

    for row_idx, (data, row_title) in enumerate(datasets):
        for col_idx, b_or_t, ch_label, y_label in [
            (0, "b", "Bending",       "Bending displacement (mm)"),
            (1, "t", "Torsion proxy", "Two-point differential proxy (mm)"),
        ]:
            ax = fig.add_subplot(gs[row_idx, col_idx])
            shade_fn(ax)

            x = data[x_col].values
            ldv_rms  = data[f"ldv_{b_or_t}_rms"].values
            ldv_peak = data[f"ldv_{b_or_t}_peak"].values
            ldv_mean = data[f"ldv_{b_or_t}_mean"].abs().values
            cam_rms  = data[f"cam_{b_or_t}_rms"].values
            cam_peak = data[f"cam_{b_or_t}_peak"].values

            # LDV
            ax.plot(x, ldv_mean, "k-o",  ms=4.5, lw=1.1, label="LDV |Mean|",
                    alpha=0.75, zorder=3)
            ax.plot(x, ldv_rms,  "-s",   ms=5.5, lw=1.8, color=C_LDV,
                    label="LDV RMS", zorder=5)
            ax.plot(x, ldv_peak, "--^",  ms=4.5, lw=1.1, color=C_LDV,
                    label="LDV Peak", alpha=0.65, zorder=3)

            # Camera — exclude ALL DCG-contaminated camera metrics from continuous line
            # (both RMS and Peak are corrupted by the interpolation artifact for e20)
            dcg_mask = data["flag"].values == "DCG_excluded"
            valid     = ~np.isnan(cam_rms)
            valid_cam = valid & ~dcg_mask   # exclude contaminated point from line

            ax.plot(x[valid_cam], cam_rms[valid_cam],  "-o", ms=6, lw=2.2,
                    color=C_CAM, label="Camera RMS", zorder=6)
            ax.plot(x[valid_cam], cam_peak[valid_cam], "--v", ms=4, lw=1.0,
                    color=C_CAM, label="Camera Peak", alpha=0.6, zorder=3)
            # Mark contaminated camera point as isolated × markers
            if np.any(dcg_mask & valid):
                xv_dcg = x[dcg_mask & valid]
                ax.scatter(xv_dcg, cam_rms[dcg_mask & valid],
                           marker="x", s=55, color=C_CAM, lw=1.8,
                           zorder=5, alpha=0.55, label="Camera (DCG artifact)")
                ax.scatter(xv_dcg, cam_peak[dcg_mask & valid],
                           marker="x", s=55, color=C_CAM, lw=1.8,
                           zorder=5, alpha=0.55)

            # Annotation for VIV condition
            for _, r in data.iterrows():
                xv = r[x_col]
                if r["flag"] == "VIV":
                    ax.annotate("VIV\n(60 RPM)",
                                xy=(xv, r[f"ldv_{b_or_t}_rms"]),
                                xytext=(xv + (0.2 if x_col == "windspeed" else 8),
                                        r[f"ldv_{b_or_t}_rms"] * 0.6),
                                fontsize=6.5, color="purple",
                                arrowprops=dict(arrowstyle="->", lw=0.7,
                                                color="purple"))

            ax.set_xlabel(x_label, fontsize=10)
            ax.set_ylabel(y_label, fontsize=10)
            ax.set_title(f"{ch_label} — {row_title}", fontsize=9.5)
            ax.set_ylim(bottom=0)

            if row_idx == 0 and col_idx == 0:
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, labels, fontsize=7.5, loc="upper left",
                          ncol=2, framealpha=0.85)

    # Add DCG exclusion note for top row
    axes_top_right = fig.get_axes()[1]
    axes_top_right.text(0.98, 0.97,
                        "e20 (320 RPM) included\nCamera Peak excluded from line\n(× marker = contaminated artifact)",
                        transform=axes_top_right.transAxes,
                        fontsize=6.5, ha="right", va="top",
                        bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow",
                                  ec="gray", alpha=0.85))

    fig.suptitle(
        f"Camera vs LDV — Mean / RMS / Peak vs {x_label}\n"
        "Simultaneous same-tunnel recording | "
        "Regime shading: blue=Bending VIV, orange=Torsional VIV, green=Bending re-emergence",
        fontsize=11, fontweight="bold"
    )

    # Regime legend
    patches = regime_legend_patches()
    fig.legend(handles=patches, loc="lower center", ncol=3, fontsize=9,
               bbox_to_anchor=(0.5, -0.01), frameon=True)

    fig.tight_layout(rect=[0, 0.035, 1, 1])
    for ext in ["pdf", "png"]:
        path = OUT_DIR / f"{fname_stem}.{ext}"
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        print(f"  [WRITE] {path}")
    plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# FIGURE C+D — FFT / PSD overlay (physical units + normalised)
# ═════════════════════════════════════════════════════════════════════════════

def fig_fft_physical_and_normalised(df: pd.DataFrame):
    """
    3 representative conditions (one per regime) × 2 channels × 2 versions.
    Physical: mm²/Hz on log scale — shows BOTH frequency AND amplitude agreement.
    Normalised: unit-peak — shows spectral shape and dominant frequency agreement.
    """
    bias = load_ldv_bias()

    # Representative conditions: one per regime
    # Bending VIV: e5_70rpm, Torsional VIV: e7_90rpm, Bending re-emergence: e17_260rpm
    REP = [
        ("e5_70rpm",   "D05", "Bending VIV\n70 RPM,  U*_b=1.86"),
        ("e7_90rpm",   "D07", "Torsional VIV\n90 RPM,  U*_b=2.50"),
        ("e17_260rpm", "D17", "Bending re-emergence\n260 RPM,  U*_b=7.94"),
    ]

    for version in ["physical", "normalised"]:
        fig, axes = plt.subplots(3, 2, figsize=(13, 12))
        fig.suptitle(
            ("Power Spectral Density — Camera vs LDV, Three Aerodynamic Regimes\n"
             "Physical units (mm²/Hz)" if version == "physical"
             else "Power Spectral Density — Camera vs LDV, Three Aerodynamic Regimes\n"
                  "Normalised to unit peak (spectral shape comparison)") + "\n"
            f"Camera @ {FS_CAM:.0f} Hz   |   LDV @ {FS_LDV:.0f} Hz   |   "
            f"$f_{{n,b}}$={FN_B} Hz,  $f_{{n,t}}$={FN_T} Hz",
            fontsize=11, fontweight="bold"
        )

        for row_idx, (cond, d_label, regime_label) in enumerate(REP):
            # LDV
            d_path = LDV_DIR / d_label
            b_ldv, t_ldv = load_ldv_timeseries(d_path, bias)
            b_ldv -= np.mean(b_ldv)
            t_ldv -= np.mean(t_ldv)

            # Camera
            b_cam, t_cam, _ = load_camera_timeseries(cond)
            if b_cam is None:
                print(f"  [SKIP] {cond} camera data not found")
                continue
            b_cam -= np.mean(b_cam)
            t_cam -= np.mean(t_cam)

            for col_idx, (sig_cam, sig_ldv, ch_label) in enumerate([
                (b_cam, b_ldv, "Bending"),
                (t_cam, t_ldv, "Torsion proxy"),
            ]):
                ax = axes[row_idx, col_idx]

                f_cam, p_cam = compute_psd(sig_cam, FS_CAM)
                f_ldv, p_ldv = compute_psd(sig_ldv, FS_LDV)

                if version == "normalised":
                    pk_c = max(p_cam.max(), 1e-12)
                    pk_l = max(p_ldv.max(), 1e-12)
                    p_cam = p_cam / pk_c
                    p_ldv = p_ldv / pk_l
                    y_label = "Normalised PSD"
                else:
                    y_label = "PSD (mm²/Hz)"

                ax.semilogy(f_cam, p_cam, lw=1.4, color=C_CAM,
                            label=f"Camera ({FS_CAM:.0f} Hz)", zorder=5)
                ax.semilogy(f_ldv, p_ldv, lw=1.0, color=C_LDV, ls="--",
                            alpha=0.85, label=f"LDV ({FS_LDV:.0f} Hz)", zorder=4)

                # Natural frequency reference lines
                ax.axvline(FN_B, color="0.4", ls=":", lw=1.2,
                           label=f"$f_{{n,b}}$={FN_B} Hz")
                ax.axvline(FN_T, color="0.6", ls="-.", lw=1.0,
                           label=f"$f_{{n,t}}$={FN_T} Hz")

                ax.set_xlim(0, 10)
                if version == "normalised":
                    ax.set_ylim(1e-5, 2)
                ax.set_xlabel("Frequency (Hz)", fontsize=9.5)
                ax.set_ylabel(y_label, fontsize=9.5)
                ax.set_title(f"{regime_label}  |  {ch_label}", fontsize=9)
                ax.grid(True, which="both", alpha=0.2)

                if row_idx == 0 and col_idx == 0:
                    ax.legend(fontsize=8, loc="upper right")

                # Annotate dominant camera peak
                f_search = (f_cam >= 0.5) & (f_cam <= 10)
                if np.any(f_search):
                    pk_f = float(f_cam[f_search][np.argmax(p_cam[f_search])])
                    pk_v = float(p_cam[f_search].max())
                    ax.annotate(f"{pk_f:.2f} Hz",
                                xy=(pk_f, pk_v),
                                xytext=(pk_f + 0.5, pk_v * (3 if version == "physical" else 3)),
                                fontsize=7.5, color=C_CAM,
                                arrowprops=dict(arrowstyle="->", lw=0.7, color=C_CAM))

        fig.tight_layout(rect=[0, 0, 1, 0.97])
        suffix = "physical_units" if version == "physical" else "normalised"
        for ext in ["pdf", "png"]:
            path = OUT_DIR / f"figC_fft_overlay_{suffix}.{ext}"
            fig.savefig(path, dpi=DPI, bbox_inches="tight")
            print(f"  [WRITE] {path}")
        plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# FIGURE E — Regime-annotated RMS scatter (Camera vs LDV)
# ═════════════════════════════════════════════════════════════════════════════

def fig_E_scatter(df: pd.DataFrame):
    """
    Camera RMS vs LDV RMS scatter, colour-coded by aerodynamic regime.
    Stronger version of the existing fig03_ldv_scatter — shows WHY the
    bending ratio is regime-dependent.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    def regime_color(rpm, flag):
        if flag == "DCG_excluded": return "gray"
        if flag == "VIV":          return "purple"
        if REGIME_BENDING[0]  <= rpm <= REGIME_BENDING[1]:  return C_REG_B
        if REGIME_TORSION[0]  <= rpm <= REGIME_TORSION[1]:  return C_REG_T
        if REGIME_REEMERGE[0] <= rpm <= REGIME_REEMERGE[1]: return C_REG_R
        return "0.6"

    def regime_label(rpm, flag):
        if flag == "DCG_excluded": return "DCG-excluded (e20)"
        if flag == "VIV":          return "VIV outlier (e4)"
        if REGIME_BENDING[0]  <= rpm <= REGIME_BENDING[1]:  return "Bending VIV"
        if REGIME_TORSION[0]  <= rpm <= REGIME_TORSION[1]:  return "Torsional VIV"
        if REGIME_REEMERGE[0] <= rpm <= REGIME_REEMERGE[1]: return "Bending re-emergence"
        return "Near-floor"

    for ax, b_or_t, ch_label, r_val in [
        (axes[0], "b", "Bending",        0.845),
        (axes[1], "t", "Torsion proxy",  0.940),
    ]:
        ldv_col = f"ldv_{b_or_t}_rms"
        cam_col = f"cam_{b_or_t}_rms"

        # 1:1 reference line
        all_vals = pd.concat([df[ldv_col], df[cam_col].dropna()])
        lim = (0, all_vals.max() * 1.12)
        ax.plot(lim, lim, "k--", lw=0.9, alpha=0.4, label="1:1 line")

        # Plot per-point with regime colour
        legend_labels_added = set()
        for _, row in df.iterrows():
            xv = row[ldv_col]
            yv = row[cam_col]
            if np.isnan(yv):
                continue
            c  = regime_color(row["rpm"], row["flag"])
            lbl = regime_label(row["rpm"], row["flag"])

            marker = "x" if row["flag"] == "DCG_excluded" else \
                     "^" if row["flag"] == "VIV" else "o"
            ms = 10 if row["flag"] in ("DCG_excluded", "VIV") else 7
            lw = 2  if row["flag"] == "DCG_excluded" else 1

            if lbl not in legend_labels_added:
                ax.scatter(xv, yv, s=ms**2, color=c, marker=marker, lw=lw,
                           facecolors="none" if row["flag"] else c,
                           label=lbl, zorder=5, edgecolors=c)
                legend_labels_added.add(lbl)
            else:
                ax.scatter(xv, yv, s=ms**2, color=c, marker=marker, lw=lw,
                           facecolors="none" if row["flag"] else c,
                           zorder=5, edgecolors=c)

            # RPM labels on hover points of interest
            if row["rpm"] in (60, 70, 90, 160, 200, 260, 300, 320):
                ax.annotate(f"{row['rpm']}",
                            xy=(xv, yv), xytext=(xv + lim[1]*0.01, yv),
                            fontsize=6.5, color=c,
                            va="center")

        # Pearson r text box
        # Compute from stable only
        stable_mask = (df["flag"] == "")
        x_st = df.loc[stable_mask, ldv_col].values
        y_st = df.loc[stable_mask, cam_col].values
        valid = ~np.isnan(y_st)
        if np.sum(valid) >= 3:
            from scipy.stats import pearsonr, spearmanr
            r_p, _ = pearsonr(x_st[valid], y_st[valid])
            r_s, _ = spearmanr(x_st[valid], y_st[valid])
            ax.text(0.05, 0.92,
                    f"Stable regime only:\nPearson r = {r_p:.3f}\nSpearman ρ = {r_s:.3f}",
                    transform=ax.transAxes, fontsize=8.5, va="top",
                    bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray",
                              alpha=0.9))

        ax.set_xlabel("LDV RMS (mm)", fontsize=10.5)
        ax.set_ylabel("Camera RMS (mm)", fontsize=10.5)
        ax.set_xlim(*lim); ax.set_ylim(*lim)
        ax.set_title(ch_label, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, loc="lower right",
                  framealpha=0.85, ncol=1)

        # Add bending leakage annotation to bending panel
        if b_or_t == "b":
            ax.text(0.60, 0.20,
                    "Bending ratio elevation in torsional VIV\nregime (90–220 RPM) due to\n"
                    "cross-axis leakage:  y_leak ≈ α·sin(9.8°)",
                    transform=ax.transAxes, fontsize=7.5,
                    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow",
                              ec="orange", alpha=0.9))

    fig.suptitle(
        "Condition-Level RMS: Camera vs LDV — Colour-Coded by Aerodynamic Regime\n"
        "Simultaneous recording | Commercial aerodynamic testing facility, South Korea",
        fontsize=11, fontweight="bold"
    )
    fig.tight_layout()
    for ext in ["pdf", "png"]:
        path = OUT_DIR / f"figE_scatter_by_regime.{ext}"
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        print(f"  [WRITE] {path}")
    plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# FIGURE F — Time-series dual-panel for two conditions
# ═════════════════════════════════════════════════════════════════════════════

def fig_F_timeseries(df: pd.DataFrame):
    """
    Side-by-side time-domain overlay for two conditions:
    Left: e5_70rpm (Bending VIV)   Right: e7_90rpm (Torsional VIV)
    Camera (60 Hz) and LDV (360 Hz) traces, mean-removed, first 15 s.
    """
    bias = load_ldv_bias()
    PAIRS = [
        ("e5_70rpm",  "D05", "Bending VIV (70 RPM, U*_b=1.86)"),
        ("e7_90rpm",  "D07", "Torsional VIV (90 RPM, U*_b=2.50)"),
    ]
    T_SHOW = 15.0   # seconds

    fig = plt.figure(figsize=(16, 10))
    gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.30)

    for col_idx, (cond, d_label, title) in enumerate(PAIRS):
        b_ldv_full, t_ldv_full = load_ldv_timeseries(LDV_DIR / d_label, bias)
        t_ldv = np.arange(len(b_ldv_full)) / FS_LDV
        m_ldv = t_ldv <= T_SHOW
        b_ldv = (b_ldv_full - np.mean(b_ldv_full))[m_ldv]
        t_ldv = t_ldv[m_ldv]
        t_ldv_t = (np.arange(len(t_ldv_full)) / FS_LDV)
        m_ldv_t = t_ldv_t <= T_SHOW
        t_ldv_mm = (t_ldv_full - np.mean(t_ldv_full))[m_ldv_t]

        b_cam_full, t_cam_full, ts_cam = load_camera_timeseries(cond)
        if b_cam_full is None:
            print(f"  [SKIP timeseries] {cond}")
            continue
        ts_cam = ts_cam - ts_cam[0]
        m_cam = ts_cam <= T_SHOW
        b_cam = b_cam_full[m_cam]
        t_cam = t_cam_full[m_cam]
        ts_cam = ts_cam[m_cam]

        for row_idx, (cam_sig, ldv_sig, t_cam_ax, t_ldv_ax, ch) in enumerate([
            (b_cam, b_ldv, ts_cam, t_ldv, "Bending"),
            (t_cam, t_ldv_mm, ts_cam, t_ldv_t[m_ldv_t], "Torsion proxy"),
        ]):
            ax = fig.add_subplot(gs[row_idx, col_idx])
            ax.plot(t_ldv_ax, ldv_sig, color=C_LDV, lw=0.7, alpha=0.80,
                    label=f"LDV ({FS_LDV:.0f} Hz)", zorder=3)
            ax.plot(t_cam_ax, cam_sig, color=C_CAM, lw=1.2, alpha=0.90,
                    label=f"Camera ({FS_CAM:.0f} Hz)", zorder=4)
            ax.axhline(0, color="k", lw=0.4, alpha=0.3)
            ax.set_xlabel("Time (s)", fontsize=10)
            ax.set_ylabel(f"{ch} displacement (mm)", fontsize=10)
            ax.set_title(f"{title}  |  {ch}", fontsize=9.5)
            if row_idx == 0 and col_idx == 0:
                ax.legend(fontsize=8.5, loc="upper right")

    fig.suptitle(
        "Time-Domain Overlay — Camera vs LDV\n"
        "Both instruments recorded simultaneously on separate DAQ systems. Traces mean-removed.",
        fontsize=11, fontweight="bold"
    )
    for ext in ["pdf", "png"]:
        path = OUT_DIR / f"figF_timeseries_two_conditions.{ext}"
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        print(f"  [WRITE] {path}")
    plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 65)
    print("COMPARISON PLOTS v2 — Camera vs LDV Publication Figures")
    print("=" * 65)

    print("\n[1/6] Loading data...")
    df = build_full_dataset()

    print(f"\n[INFO] Conditions loaded: {len(df)}")
    print(f"[INFO] DCG excluded: {df[df['flag']=='DCG_excluded']['condition'].tolist()}")
    print(f"[INFO] VIV flagged:  {df[df['flag']=='VIV']['condition'].tolist()}")

    print("\n[2/6] Fig A — Mean/RMS/Peak vs RPM...")
    fig_A_full(df,
               x_col="rpm",
               x_label="Fan speed (RPM)",
               shade_fn=shade_regimes_rpm,
               fname_stem="figA_mean_rms_peak_vs_rpm")

    print("\n[3/6] Fig B — Mean/RMS/Peak vs Wind Speed...")
    fig_A_full(df,
               x_col="windspeed",
               x_label="Mean wind speed (m/s)",
               shade_fn=shade_regimes_ws,
               fname_stem="figB_mean_rms_peak_vs_windspeed")

    print("\n[4/6] Fig C/D — FFT/PSD overlay (physical + normalised)...")
    fig_fft_physical_and_normalised(df)

    print("\n[5/6] Fig E — Regime-annotated scatter...")
    fig_E_scatter(df)

    print("\n[6/6] Fig F — Time-series overlay (2 conditions)...")
    fig_F_timeseries(df)

    print("\n" + "=" * 65)
    print("DONE — all outputs in:", OUT_DIR.resolve())
    print("=" * 65)

    # Print manifest of outputs
    outputs = sorted(OUT_DIR.glob("*.png")) + sorted(OUT_DIR.glob("*.pdf"))
    print(f"\nGenerated {len(outputs)} files:")
    for p in sorted(OUT_DIR.iterdir()):
        size_kb = p.stat().st_size // 1024
        print(f"  {p.name:55s}  {size_kb:4d} KB")


if __name__ == "__main__":
    main()