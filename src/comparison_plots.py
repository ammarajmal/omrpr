"""
comparison_plots.py — Camera vs LDV comparison plots for Results & Discussion.

Generates four publication figures:
    results/comparison_plots/
        fig_freq_comparison.png   -- dominant freq vs RPM, camera + LDV superimposed
        fig_rms_comparison.png    -- RMS amplitude per condition, camera vs LDV paired
        fig_fft_overlay.png       -- FFT spectra overlay for three representative conditions
        fig_timeseries_overlay.png -- time-domain overlay for one representative condition

Data sources:
    Camera freq:   results/step08/frequency_summary.csv
    Camera RMS:    results/step10/ldv_comparison_table.csv
    Camera traces: results/step07/{condition}/motion.csv
    LDV raw:       data/LDV/TESolution/laser_displacement/등류/영각00/D01..D20
    LDV manifest:  data/LDV/manifest.json
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from scipy import signal as sp_signal

# ── paths ─────────────────────────────────────────────────────────────────────
RESULTS_DIR  = Path("results")
OUT_DIR      = Path("results/comparison_plots")
LDV_DIR      = Path(
    "/media/ammar/phd/omrpr/data/LDV/TESolution"
    "/laser_displacement/등류/영각00"
)
MANIFEST     = Path("/media/ammar/phd/omrpr/data/LDV/manifest.json")

# ── constants (confirmed from structural_params.md and pipeline_config.yaml) ──
FS_CAM    = 60.0    # Hz — camera
FS_LDV    = 360.0   # Hz — LDV
PVOLT     = 2.7     # cm/V
DP        = 1.538   # torsion scaling (dside=130 mm, db=200 mm)
FN_B      = 1.4323  # Hz — bending natural frequency
FN_T      = 3.0827  # Hz — torsion natural frequency

# Aerodynamic regime RPM boundaries (from step12 constants)
REGIME_BENDING    = (40,  80)
REGIME_TORSION    = (90,  220)
REGIME_REEMERGE   = (240, 300)

# Colours
C_CAM       = "#1f77b4"   # blue  — camera
C_LDV       = "#d62728"   # red   — LDV
C_REG_B     = "#aec7e8"   # light blue  — bending VIV regime shade
C_REG_T     = "#ffbb78"   # light orange — torsional VIV regime shade
C_REG_R     = "#98df8a"   # light green — re-emergence regime shade
C_FN        = "#7f7f7f"   # grey  — natural frequency lines

DPI = 150

# ── LDV geometry ──────────────────────────────────────────────────────────────

def load_ldv_bias():
    raw = np.loadtxt(str(LDV_DIR / "D00"), usecols=(0, 1))
    return np.mean(raw, axis=0)


def load_ldv_timeseries(d_path: Path, bias: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (bending_mm, torsion_mm) time series for one D-file."""
    raw = np.loadtxt(str(d_path), usecols=(0, 1))
    cal = (raw - bias) * PVOLT          # cm
    bending_mm = ((cal[:, 0] + cal[:, 1]) / 2.0) * 10.0
    torsion_mm = ((cal[:, 1] - cal[:, 0]) * DP)  * 10.0
    return bending_mm, torsion_mm


def dominant_freq(sig: np.ndarray, fs: float,
                  f_lo: float = 0.5, f_hi: float = 10.0) -> float:
    """Dominant FFT peak between f_lo and f_hi Hz."""
    N     = len(sig)
    win   = np.hanning(N)
    S     = np.abs(np.fft.rfft(sig * win))
    freqs = np.fft.rfftfreq(N, d=1.0/fs)
    mask  = (freqs >= f_lo) & (freqs <= f_hi)
    return float(freqs[mask][np.argmax(S[mask])])


def compute_psd(sig: np.ndarray, fs: float):
    """Welch PSD, returns (freqs, psd)."""
    f, p = sp_signal.welch(sig, fs=fs, nperseg=min(len(sig), int(fs * 5)),
                           window="hann", scaling="density")
    return f, p


# ── manifest ──────────────────────────────────────────────────────────────────

def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)


# ── Figure 1: dominant frequency vs RPM ───────────────────────────────────────

def fig_freq_comparison():
    freq_csv = pd.read_csv(RESULTS_DIR / "step08" / "frequency_summary.csv")
    manifest = load_manifest()
    bias     = load_ldv_bias()

    cam_rows = {
        row["condition"]: row
        for _, row in freq_csv.iterrows()
    }

    rpms, cam_bend_f, cam_tors_f = [], [], []
    ldv_bend_f, ldv_tors_f       = [], []
    flags                         = []

    for entry in manifest["conditions"]:
        cond  = entry["wtt_condition"]
        rpm   = entry["rpm"]
        dflag = entry.get("note", "")

        d_path = LDV_DIR / entry["ldv_file"].replace(".csv", "")
        if not d_path.exists():
            d_path = LDV_DIR / entry["ldv_file"]
        if not d_path.exists():
            continue

        b_mm, t_mm = load_ldv_timeseries(d_path, bias)

        ldv_bf = dominant_freq(b_mm - np.mean(b_mm), FS_LDV)
        ldv_tf = dominant_freq(t_mm - np.mean(t_mm), FS_LDV)

        bend_key  = f"{cond},bending"
        tors_key  = f"{cond},torsion_proxy"
        cam_b_row = freq_csv[(freq_csv["condition"] == cond) & (freq_csv["channel"] == "bending")]
        cam_t_row = freq_csv[(freq_csv["condition"] == cond) & (freq_csv["channel"] == "torsion_proxy")]

        if cam_b_row.empty or cam_t_row.empty:
            continue

        rpms.append(rpm)
        cam_bend_f.append(float(cam_b_row["dominant_peak_hz"].values[0]))
        cam_tors_f.append(float(cam_t_row["dominant_peak_hz"].values[0]))
        ldv_bend_f.append(ldv_bf)
        ldv_tors_f.append(ldv_tf)
        flags.append(dflag)

    rpms       = np.array(rpms)
    cam_bend_f = np.array(cam_bend_f)
    cam_tors_f = np.array(cam_tors_f)
    ldv_bend_f = np.array(ldv_bend_f)
    ldv_tors_f = np.array(ldv_tors_f)
    excl       = np.array(["high_wind" in f for f in flags])
    viv        = np.array(["VIV" in f for f in flags])
    stable     = ~excl & ~viv

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    for ax, cam_f, ldv_f, ch_label in [
        (axes[0], cam_bend_f, ldv_bend_f, "Bending"),
        (axes[1], cam_tors_f, ldv_tors_f, "Torsion proxy"),
    ]:
        _shade_regimes(ax, rpms)

        # stable conditions
        ax.plot(rpms[stable], cam_f[stable], "o-",  color=C_CAM, lw=1.5, ms=6,
                label="Camera", zorder=5)
        ax.plot(rpms[stable], ldv_f[stable], "s--", color=C_LDV, lw=1.5, ms=6,
                label="LDV", zorder=5)

        # VIV outlier (e4_60rpm)
        if viv.any():
            ax.plot(rpms[viv], cam_f[viv], "o", color=C_CAM, ms=8,
                    markeredgecolor="k", markeredgewidth=0.8, zorder=6)
            ax.plot(rpms[viv], ldv_f[viv], "s", color=C_LDV, ms=8,
                    markeredgecolor="k", markeredgewidth=0.8, zorder=6)

        # e20 excluded
        if excl.any():
            ax.plot(rpms[excl], cam_f[excl], "x", color=C_CAM, ms=9, mew=2,
                    zorder=6, label="e20 (DCG-excl.)")
            ax.plot(rpms[excl], ldv_f[excl], "x", color=C_LDV, ms=9, mew=2,
                    zorder=6)

        # natural frequency reference lines
        fn_ref = FN_B if ch_label == "Bending" else FN_T
        ax.axhline(fn_ref, color=C_FN, ls=":", lw=1.2,
                   label=f"$f_n$ = {fn_ref:.4f} Hz")

        ax.set_ylabel("Dominant freq. (Hz)", fontsize=10)
        ax.set_title(f"{ch_label} channel", fontsize=10)
        ax.legend(fontsize=8, loc="upper left")
        ax.set_ylim(0, 12)
        ax.grid(axis="y", alpha=0.3)

    axes[1].set_xlabel("Fan speed (RPM)", fontsize=10)
    axes[1].set_xticks(rpms)
    axes[1].set_xticklabels([str(r) for r in rpms], rotation=45, fontsize=7)

    _add_regime_legend(fig)
    fig.suptitle(
        "Dominant frequency vs fan speed — camera (60 Hz) vs LDV (360 Hz)\n"
        f"Simultaneous same-tunnel recording  |  $f_{{n,b}}$={FN_B} Hz, $f_{{n,t}}$={FN_T} Hz",
        fontsize=10
    )
    fig.tight_layout()
    path = OUT_DIR / "fig_freq_comparison.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {path}")


# ── Figure 2: RMS per condition (paired bars) ──────────────────────────────────

def fig_rms_comparison():
    df = pd.read_csv(RESULTS_DIR / "step10" / "ldv_comparison_table.csv")
    df = df[df["rpm"] > 0].copy()  # drop e0_0rpm (no LDV)

    rpms     = df["rpm"].values
    n        = len(rpms)
    x        = np.arange(n)
    width    = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, cam_col, ldv_col, title in [
        (axes[0], "camera_bending_rms_mm", "ldv_bending_rms_mm_corrected", "Bending"),
        (axes[1], "camera_torsion_rms_mm", "ldv_torsion_rms_mm_corrected", "Torsion proxy"),
    ]:
        cam_rms = df[cam_col].values
        ldv_rms = df[ldv_col].values

        bar_cam = ax.bar(x - width/2, cam_rms, width, color=C_CAM, alpha=0.85,
                         label="Camera", zorder=3)
        bar_ldv = ax.bar(x + width/2, ldv_rms, width, color=C_LDV, alpha=0.85,
                         label="LDV", zorder=3)

        # regime background
        for i, rpm in enumerate(rpms):
            if REGIME_BENDING[0] <= rpm <= REGIME_BENDING[1]:
                ax.axvspan(i - 0.5, i + 0.5, color=C_REG_B, alpha=0.25, zorder=0)
            elif REGIME_TORSION[0] <= rpm <= REGIME_TORSION[1]:
                ax.axvspan(i - 0.5, i + 0.5, color=C_REG_T, alpha=0.25, zorder=0)
            elif REGIME_REEMERGE[0] <= rpm <= REGIME_REEMERGE[1]:
                ax.axvspan(i - 0.5, i + 0.5, color=C_REG_R, alpha=0.25, zorder=0)

        # mark special conditions
        for i, (rpm, flag) in enumerate(zip(rpms, df["flag"].fillna(""))):
            if "VIV" in str(flag):
                ax.annotate("VIV", (i, max(cam_rms[i], ldv_rms[i])),
                            ha="center", va="bottom", fontsize=6, color="purple")
            elif "unstable" in str(flag):
                ax.annotate("DCG\nexcl.", (i, max(cam_rms[i], ldv_rms[i])),
                            ha="center", va="bottom", fontsize=6, color="gray")

        ax.set_xticks(x)
        ax.set_xticklabels([str(r) for r in rpms], rotation=45, fontsize=7)
        ax.set_xlabel("Fan speed (RPM)", fontsize=10)
        ax.set_ylabel("RMS displacement (mm)", fontsize=10)
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(axis="y", alpha=0.3)

    _add_regime_legend(fig)
    fig.suptitle(
        "Condition-level RMS comparison — camera vs LDV\n"
        "Simultaneous same-tunnel recording  |  Regime shading: blue=bending VIV, "
        "orange=torsional VIV, green=bending re-emergence",
        fontsize=9
    )
    fig.tight_layout()
    path = OUT_DIR / "fig_rms_comparison.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {path}")


# ── Figure 3: FFT / PSD overlay ────────────────────────────────────────────────

def fig_fft_overlay():
    """
    3 representative conditions (one per regime) × 2 channels = 6 subplots.
    Shows how camera and LDV spectra agree on dominant peak.
    """
    REP_CONDITIONS = [
        ("e5_70rpm",  "D05", "Bending VIV (70 RPM, U*_b=2.16)"),
        ("e7_90rpm",  "D07", "Torsional VIV (90 RPM, U*_b=2.91)"),
        ("e17_260rpm","D17", "Bending re-emergence (260 RPM, U*_b=9.23)"),
    ]

    bias = load_ldv_bias()
    fig, axes = plt.subplots(3, 2, figsize=(12, 9))

    for row_idx, (cond, d_label, regime_label) in enumerate(REP_CONDITIONS):
        # --- LDV ---
        d_path = LDV_DIR / d_label
        b_ldv, t_ldv = load_ldv_timeseries(d_path, bias)

        # --- Camera ---
        motion_csv = RESULTS_DIR / "step07" / cond / "motion.csv"
        df_cam = pd.read_csv(motion_csv)
        b_cam = df_cam["bending_avg_y_mm"].values - np.mean(df_cam["bending_avg_y_mm"].values)
        t_cam = df_cam["torsion_diff_y_mm"].values - np.mean(df_cam["torsion_diff_y_mm"].values)

        for col_idx, (sig_cam, sig_ldv, ch_label) in enumerate([
            (b_cam, b_ldv - np.mean(b_ldv), "Bending"),
            (t_cam, t_ldv - np.mean(t_ldv), "Torsion proxy"),
        ]):
            ax = axes[row_idx, col_idx]

            # PSD
            f_cam, p_cam = compute_psd(sig_cam, FS_CAM)
            f_ldv, p_ldv = compute_psd(sig_ldv, FS_LDV)

            # normalise to peak = 1 for visual comparison
            pk_cam = p_cam.max() if p_cam.max() > 0 else 1.0
            pk_ldv = p_ldv.max() if p_ldv.max() > 0 else 1.0

            ax.semilogy(f_cam, p_cam / pk_cam, color=C_CAM, lw=1.2, label="Camera")
            ax.semilogy(f_ldv, p_ldv / pk_ldv, color=C_LDV, lw=1.0, ls="--",
                        alpha=0.85, label="LDV")

            ax.axvline(FN_B, color=C_FN, ls=":", lw=1.0, label=f"$f_{{n,b}}$={FN_B} Hz")
            ax.axvline(FN_T, color="olive", ls=":", lw=1.0, label=f"$f_{{n,t}}$={FN_T} Hz")

            ax.set_xlim(0, 10)
            ax.set_ylim(1e-6, 2)
            ax.set_xlabel("Frequency (Hz)", fontsize=8)
            ax.set_ylabel("Norm. PSD", fontsize=8)
            ax.set_title(f"{regime_label}  |  {ch_label}", fontsize=8)
            ax.legend(fontsize=7, loc="upper right")
            ax.grid(alpha=0.2)

    fig.suptitle(
        "Power spectral density — camera vs LDV, three aerodynamic regimes\n"
        "Spectra normalised to unit peak. Camera 60 Hz, LDV 360 Hz.",
        fontsize=10
    )
    fig.tight_layout()
    path = OUT_DIR / "fig_fft_overlay.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {path}")


# ── Figure 4: time-series overlay ─────────────────────────────────────────────

def fig_timeseries_overlay():
    """
    One representative condition (e7_90rpm, torsion-dominated).
    Camera (60 Hz) and LDV (360 Hz) shown on the same 20 s axis.
    Both mean-removed. Not point-by-point aligned — separate DAQ systems and
    separate recording sessions at different rates.
    """
    COND    = "e7_90rpm"
    D_LABEL = "D07"
    T_SHOW  = 20.0  # seconds to show

    bias = load_ldv_bias()
    d_path = LDV_DIR / D_LABEL
    b_ldv, t_ldv = load_ldv_timeseries(d_path, bias)
    b_ldv -= np.mean(b_ldv)
    t_ldv -= np.mean(t_ldv)
    t_ldv_s = np.arange(len(b_ldv)) / FS_LDV

    motion_csv = RESULTS_DIR / "step07" / COND / "motion.csv"
    df_cam = pd.read_csv(motion_csv)
    b_cam = df_cam["bending_avg_y_mm"].values - np.mean(df_cam["bending_avg_y_mm"].values)
    t_cam = df_cam["torsion_diff_y_mm"].values - np.mean(df_cam["torsion_diff_y_mm"].values)
    t_cam_s = df_cam["t_s"].values - df_cam["t_s"].values[0]

    # crop to T_SHOW seconds
    m_cam = t_cam_s <= T_SHOW
    m_ldv = t_ldv_s <= T_SHOW

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    for ax, cam_sig, ldv_sig, ch_label in [
        (axes[0], b_cam[m_cam], b_ldv[m_ldv], "Bending"),
        (axes[1], t_cam[m_cam], t_ldv[m_ldv], "Torsion proxy"),
    ]:
        ax.plot(t_cam_s[m_cam], cam_sig, color=C_CAM, lw=0.8, alpha=0.9,
                label=f"Camera (60 Hz)")
        ax.plot(t_ldv_s[m_ldv], ldv_sig, color=C_LDV, lw=0.6, alpha=0.7,
                label=f"LDV (360 Hz)", ls="--")
        ax.set_ylabel("Displacement (mm)", fontsize=10)
        ax.set_title(ch_label, fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=0.2)
        ax.axhline(0, color="k", lw=0.5, alpha=0.3)

    axes[1].set_xlabel("Time (s)", fontsize=10)
    fig.suptitle(
        f"Time-domain overlay — {COND.replace('_', ' ')} (torsion-dominated regime, U*_b=2.91)\n"
        "Camera and LDV shown for qualitative comparison only; they come from "
        "separate recording sessions on separate DAQ systems. "
        "Traces mean-removed for comparison.",
        fontsize=9
    )
    fig.tight_layout()
    path = OUT_DIR / "fig_timeseries_overlay.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {path}")


# ── helpers ────────────────────────────────────────────────────────────────────

def _shade_regimes(ax, rpms: np.ndarray):
    r_min, r_max = rpms.min(), rpms.max()
    lo_b, hi_b = REGIME_BENDING
    lo_t, hi_t = REGIME_TORSION
    lo_r, hi_r = REGIME_REEMERGE
    ax.axvspan(lo_b, hi_b, color=C_REG_B, alpha=0.25, zorder=0)
    ax.axvspan(lo_t, hi_t, color=C_REG_T, alpha=0.25, zorder=0)
    ax.axvspan(lo_r, hi_r, color=C_REG_R, alpha=0.25, zorder=0)


def _add_regime_legend(fig):
    patches = [
        mpatches.Patch(color=C_REG_B, alpha=0.5, label="Bending VIV (40–80 RPM)"),
        mpatches.Patch(color=C_REG_T, alpha=0.5, label="Torsional VIV (90–220 RPM)"),
        mpatches.Patch(color=C_REG_R, alpha=0.5, label="Bending re-emergence (240–300 RPM)"),
    ]
    fig.legend(handles=patches, loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.02), frameon=True)


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("COMPARISON PLOTS — camera vs LDV")
    print("=" * 60)

    steps = [
        ("Fig 1 — frequency vs RPM",    fig_freq_comparison),
        ("Fig 2 — RMS per condition",   fig_rms_comparison),
        ("Fig 3 — FFT overlay",         fig_fft_overlay),
        ("Fig 4 — time-series overlay", fig_timeseries_overlay),
    ]

    for label, fn in steps:
        print(f"\n[GENERATE] {label}")
        try:
            fn()
        except Exception as e:
            import traceback
            print(f"  [ERROR] {e}")
            traceback.print_exc()

    print("\nDONE — outputs in results/comparison_plots/")


if __name__ == "__main__":
    main()
