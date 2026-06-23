"""
fig_ldv_rms_trend.py — LDV vs Camera RMS/Peak/Mean trend overlay.

Directly analogous to the facility's four-panel figure (Bending/Torsion × RPM/U),
with camera superimposed on LDV — the key validation figure for publication.

Outputs (results/comparison_plots/):
    fig_rms_4panel.pdf   — 4-panel RMS: Bending/Torsion × RPM/wind-speed
    fig_mrp_6panel.pdf   — 6-panel Mean/RMS/Peak vs RPM  (facility format)

e20 treatment:
    Bending: cam3-only 2.194 mm shown as open triangle; cam1/cam2 excluded (DCG criterion)
    Torsion: no camera point (cam1/cam2 DCG-excluded); LDV shown as open square
    LDV e20: shown in both channels with open marker and footnote annotation

e4_60rpm: VIV outlier — shown as diamond marker, included in figure, labelled.

Data sources:
    results/step10/ldv_comparison_table.csv   — RMS + mean, both instruments
    results/step07/{cond}/motion.csv          — camera time series for peak
    results/step06/e20_320rpm/cam3/aligned_pose.csv — cam3-only e20 bending
    data/LDV/.../D01..D20                     — LDV raw (for peak computation)
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# ── paths ─────────────────────────────────────────────────────────────────────
RESULTS_DIR = Path("results")
OUT_DIR     = Path("results/comparison_plots")
LDV_DIR     = Path(
    "/media/ammar/phd/omrpr/data/LDV/TESolution"
    "/laser_displacement/등류/영각00"
)
MANIFEST = Path("/media/ammar/phd/omrpr/data/LDV/manifest.json")

# ── confirmed geometry (step10, do not change) ────────────────────────────────
PVOLT  = 2.7      # cm/V
DP     = 20.0 / 13.0   # 1.538... (db=200mm, dside=130mm)
FS_LDV = 360.0    # Hz

# ── structural parameters (from free_vib_analysis, Tunnel B 2025) ─────────────
FN_B = 1.4323   # Hz — bending
FN_T = 3.0827   # Hz — torsion
B    = 0.40     # m  — chord

# ── wind speed table (from Excel '계산풍속(풍동)', structural_params.md) ─────────
# source: laser_displacement/등류/영각00/영상계측_laser_등류_영각00.xlsx
WIND_SPEED_MS = {
    "e0_0rpm":   0.000,
    "e1_20rpm":  0.000,
    "e2_40rpm":  0.516,
    "e3_50rpm":  0.699,
    "e4_60rpm":  0.882,
    "e5_70rpm":  1.066,
    "e6_80rpm":  1.249,
    "e7_90rpm":  1.432,
    "e8_100rpm": 1.616,
    "e9_110rpm": 1.799,
    "e10_120rpm":1.982,
    "e11_140rpm":2.349,
    "e12_160rpm":2.715,
    "e13_180rpm":3.082,
    "e14_200rpm":3.449,
    "e15_220rpm":3.815,
    "e16_240rpm":4.182,
    "e17_260rpm":4.548,
    "e18_280rpm":4.915,
    "e19_300rpm":5.282,
    "e20_320rpm":5.648,
}

# ── aerodynamic regime boundaries ─────────────────────────────────────────────
# RPM
REG_BEND_RPM  = (40,  80)
REG_TORS_RPM  = (90,  220)
REG_REEM_RPM  = (240, 300)
# wind speed (m/s) — derived from table above
REG_BEND_U    = (0.516, 1.249)
REG_TORS_U    = (1.432, 3.815)
REG_REEM_U    = (4.182, 5.282)

# ── colours ───────────────────────────────────────────────────────────────────
C_CAM   = "#1f77b4"    # blue   — camera
C_LDV   = "#d62728"    # red    — LDV
C_CAM3  = "#2ca02c"    # green  — cam3-only e20
C_REG_B = "#aec7e8"    # light blue   — bending VIV shade
C_REG_T = "#ffbb78"    # light orange — torsional VIV shade
C_REG_R = "#98df8a"    # light green  — re-emergence shade
C_FN    = "#7f7f7f"    # grey   — fn reference lines

DPI = 200


# ── LDV loading ───────────────────────────────────────────────────────────────

def _load_ldv_bias():
    raw = np.loadtxt(str(LDV_DIR / "D00"), usecols=(0, 1))
    return np.mean(raw, axis=0)


def _process_ldv(d_path: Path, bias: np.ndarray) -> dict:
    """
    Load one D-file, apply calibration, return Mean/RMS/Peak in mm.
    Identical calibration chain to step10 (bug-free version).
    """
    raw  = np.loadtxt(str(d_path), usecols=(0, 1))
    cal  = (raw - bias) * PVOLT           # cm
    b_mm = ((cal[:, 0] + cal[:, 1]) / 2.0) * 10.0
    t_mm = ((cal[:, 1] - cal[:, 0]) * DP)  * 10.0
    return {
        "b_mean": float(np.mean(b_mm)),
        "t_mean": float(np.mean(t_mm)),
        "b_rms":  float(np.std(b_mm)),
        "t_rms":  float(np.std(t_mm)),
        "b_peak": float(np.max(np.abs(b_mm - np.mean(b_mm)))),
        "t_peak": float(np.max(np.abs(t_mm - np.mean(t_mm)))),
    }


# ── camera loading ────────────────────────────────────────────────────────────

def _load_camera_stats(cond: str) -> dict:
    p = RESULTS_DIR / "step07" / cond / "motion.csv"
    df = pd.read_csv(p)
    b  = df["bending_avg_y_mm"].dropna().values
    t  = df["torsion_diff_y_mm"].dropna().values
    return {
        "b_mean": float(np.mean(b)),
        "t_mean": float(np.mean(t)),
        "b_rms":  float(np.std(b)),
        "t_rms":  float(np.std(t)),
        "b_peak": float(np.max(np.abs(b - np.mean(b)))),
        "t_peak": float(np.max(np.abs(t - np.mean(t)))),
    }


# ── build combined dataframe ───────────────────────────────────────────────────

def build_dataframe() -> pd.DataFrame:
    """
    Merge LDV comparison table (RMS already computed) with camera peak/mean
    and LDV peak values. Returns one row per WTT condition (excluding e0_0rpm).
    """
    tbl  = pd.read_csv(RESULTS_DIR / "step10" / "ldv_comparison_table.csv")
    bias = _load_ldv_bias()

    with open(MANIFEST) as f:
        manifest = json.load(f)
    d_map = {
        c["wtt_condition"]: c["ldv_file"].replace(".csv", "")
        for c in manifest["conditions"]
    }

    rows = []
    for _, row in tbl.iterrows():
        cond = row["wtt_condition"]
        rpm  = int(row["rpm"])
        flag = str(row.get("flag", ""))

        # skip zero-wind (no LDV reference)
        if rpm == 0:
            continue

        # LDV stats (peak from raw D-file)
        d_label = d_map.get(cond)
        d_path  = LDV_DIR / d_label if d_label else None
        if d_path is None or not d_path.exists():
            continue

        ldv = _process_ldv(d_path, bias)

        # Camera stats
        try:
            cam = _load_camera_stats(cond)
        except FileNotFoundError:
            continue

        rows.append({
            "cond":    cond,
            "rpm":     rpm,
            "U_ms":    WIND_SPEED_MS.get(cond, float("nan")),
            "flag":    flag,
            # RMS (from ldv_comparison_table, already validated)
            "cam_b_rms": row["camera_bending_rms_mm"],
            "cam_t_rms": row["camera_torsion_rms_mm"],
            "ldv_b_rms": row["ldv_bending_rms_mm_corrected"],
            "ldv_t_rms": row["ldv_torsion_rms_mm_corrected"],
            # Mean
            "cam_b_mean": cam["b_mean"],
            "cam_t_mean": cam["t_mean"],
            "ldv_b_mean": row["ldv_bending_mean_mm_corrected"],
            "ldv_t_mean": row["ldv_torsion_mean_mm_corrected"],
            # Peak (from full time series)
            "cam_b_peak": cam["b_peak"],
            "cam_t_peak": cam["t_peak"],
            "ldv_b_peak": ldv["b_peak"],
            "ldv_t_peak": ldv["t_peak"],
        })

    df = pd.DataFrame(rows).sort_values("rpm").reset_index(drop=True)

    # cam3-only e20 bending (cam1/cam2 DCG-excluded — bending is contaminated)
    cam3_path = (
        RESULTS_DIR / "step06" / "e20_320rpm" / "cam3" / "aligned_pose.csv"
    )
    cam3_y = pd.read_csv(cam3_path)["y_w_mm"].values
    cam3_b_rms  = float(np.std(cam3_y))
    cam3_b_peak = float(np.max(np.abs(cam3_y - np.mean(cam3_y))))

    return df, cam3_b_rms, cam3_b_peak


# ── regime shading helpers ─────────────────────────────────────────────────────

def _shade(ax, x_lo, x_hi, color, alpha=0.20):
    ax.axvspan(x_lo, x_hi, color=color, alpha=alpha, zorder=0)


def _shade_rpm(ax):
    _shade(ax, *REG_BEND_RPM, C_REG_B)
    _shade(ax, *REG_TORS_RPM, C_REG_T)
    _shade(ax, *REG_REEM_RPM, C_REG_R)


def _shade_U(ax):
    _shade(ax, *REG_BEND_U, C_REG_B)
    _shade(ax, *REG_TORS_U, C_REG_T)
    _shade(ax, *REG_REEM_U, C_REG_R)


def _regime_patches():
    return [
        mpatches.Patch(color=C_REG_B, alpha=0.5, label="Bending VIV (40–80 RPM)"),
        mpatches.Patch(color=C_REG_T, alpha=0.5, label="Torsional VIV (90–220 RPM)"),
        mpatches.Patch(color=C_REG_R, alpha=0.5, label="Bending re-emergence (240–300 RPM)"),
    ]


# ── marker helpers ────────────────────────────────────────────────────────────

def _split(df, col_val="high_wind_unstable"):
    excl  = df["flag"].str.contains("high_wind", na=False)
    viv   = df["flag"].str.contains("VIV",       na=False)
    stable = ~excl & ~viv
    return stable, viv, excl


def _plot_trend(ax, x_all, cam_all, ldv_all, stable, viv, excl,
                cam3_x=None, cam3_val=None, label_cam=True, label_ldv=True,
                is_bending=True):
    """
    Plot camera and LDV as connected lines (stable) with special markers for
    VIV and excluded (e20) conditions. For bending: e20 camera replaced by
    cam3-only point; for torsion: no camera e20 point.
    """
    kw_stable = dict(lw=1.6, ms=5, zorder=5)

    # stable line
    ax.plot(x_all[stable], cam_all[stable], "o-", color=C_CAM,
            label=("Camera" if label_cam else None), **kw_stable)
    ax.plot(x_all[stable], ldv_all[stable], "s--", color=C_LDV,
            label=("LDV" if label_ldv else None), **kw_stable)

    # VIV outlier (e4_60rpm)
    if viv.any():
        ax.plot(x_all[viv], cam_all[viv], "D", color=C_CAM, ms=7,
                markeredgecolor="k", markeredgewidth=0.8, zorder=6,
                label="Camera (VIV)" if label_cam else None)
        ax.plot(x_all[viv], ldv_all[viv], "D", color=C_LDV, ms=7,
                markeredgecolor="k", markeredgewidth=0.8, zorder=6,
                label="LDV (VIV)" if label_ldv else None)

    # e20: LDV shown as open square; camera bending = cam3 only; torsion = no camera
    if excl.any():
        ax.plot(x_all[excl], ldv_all[excl], "s", color=C_LDV, ms=8,
                markerfacecolor="none", markeredgewidth=1.5, zorder=6)
        if is_bending and cam3_x is not None and cam3_val is not None:
            ax.plot(cam3_x, cam3_val, "^", color=C_CAM3, ms=8,
                    markeredgecolor="k", markeredgewidth=0.8, zorder=7,
                    label="Camera cam3 only (320 RPM, DCG excl.)")
        # if torsion: do nothing — no camera e20 torsion point


# ── Figure 1: 4-panel RMS (Bending/Torsion × RPM/U) ─────────────────────────

def fig_rms_4panel(df: pd.DataFrame, cam3_b_rms: float):
    stable, viv, excl = _split(df)

    x_rpm = df["rpm"].values
    x_U   = df["U_ms"].values

    e20_rpm = df.loc[excl, "rpm"].values[0]  if excl.any() else None
    e20_U   = df.loc[excl, "U_ms"].values[0] if excl.any() else None

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.subplots_adjust(hspace=0.38, wspace=0.32)

    panels = [
        # (ax,       x_arr,  cam_col,    ldv_col,    x_label,          shade_fn,   is_bend, cam3_x,    cam3_val)
        (axes[0, 0], x_rpm, "cam_b_rms", "ldv_b_rms", "Fan speed (RPM)",    _shade_rpm, True,  e20_rpm, cam3_b_rms),
        (axes[0, 1], x_rpm, "cam_t_rms", "ldv_t_rms", "Fan speed (RPM)",    _shade_rpm, False, None,    None),
        (axes[1, 0], x_U,   "cam_b_rms", "ldv_b_rms", "Wind speed U (m/s)", _shade_U,   True,  e20_U,   cam3_b_rms),
        (axes[1, 1], x_U,   "cam_t_rms", "ldv_t_rms", "Wind speed U (m/s)", _shade_U,   False, None,    None),
    ]
    titles = ["(a) Bending RMS", "(b) Torsion RMS",
              "(c) Bending RMS", "(d) Torsion RMS"]

    for idx, (ax, x, cam_col, ldv_col, xlabel, shade_fn, is_bend, c3x, c3v) in enumerate(panels):
        shade_fn(ax)
        cam_vals = df[cam_col].values
        ldv_vals = df[ldv_col].values

        # replace e20 camera bending with nan so the stable line doesn't connect to it
        if is_bend:
            cam_vals = cam_vals.copy()
            cam_vals[excl] = np.nan

        _plot_trend(ax, x, cam_vals, ldv_vals, stable, viv, excl,
                    cam3_x=c3x, cam3_val=c3v,
                    label_cam=(idx == 0), label_ldv=(idx == 0),
                    is_bending=is_bend)

        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel("RMS displacement (mm)", fontsize=9)
        ax.set_title(titles[idx], fontsize=10, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        ax.set_ylim(bottom=0)
        ax.tick_params(labelsize=8)

    # shared legend
    handles, labels = axes[0, 0].get_legend_handles_labels()
    # add regime patches
    handles += _regime_patches()
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.04), frameon=True)

    fig.suptitle(
        "Condition-level RMS: Camera vs LDV  —  same-tunnel separate-session comparison\n"
        r"Camera 60 Hz  |  LDV 360 Hz  |  $f_{n,b}$=" + f"{FN_B} Hz, "
        r"$f_{n,t}$=" + f"{FN_T} Hz  |  "
        "e20 320 RPM: LDV valid (open), cam1/cam2 DCG-excluded, cam3-only shown (▲)",
        fontsize=9
    )

    out = OUT_DIR / "fig_rms_4panel.pdf"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {out}")


# ── Figure 2: 6-panel Mean / RMS / Peak vs RPM ───────────────────────────────

def fig_mrp_6panel(df: pd.DataFrame, cam3_b_rms: float, cam3_b_peak: float):
    stable, viv, excl = _split(df)
    x_rpm  = df["rpm"].values
    e20_rpm = df.loc[excl, "rpm"].values[0] if excl.any() else None

    # 2 rows (bending, torsion) × 3 cols (Mean, RMS, Peak)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.subplots_adjust(hspace=0.42, wspace=0.35)

    metrics = [
        # (col_idx, cam_col,     ldv_col,     ylabel,              c3_val,      is_bend_c3)
        (0, "cam_b_mean", "ldv_b_mean", "Mean displacement (mm)",  None,          False),
        (1, "cam_b_rms",  "ldv_b_rms",  "RMS displacement (mm)",   cam3_b_rms,   True),
        (2, "cam_b_peak", "ldv_b_peak", "Peak displacement (mm)",  cam3_b_peak,  True),
    ]
    tors_metrics = [
        (0, "cam_t_mean", "ldv_t_mean", "Mean displacement (mm)",  None,  False),
        (1, "cam_t_rms",  "ldv_t_rms",  "RMS displacement (mm)",   None,  False),
        (2, "cam_t_peak", "ldv_t_peak", "Peak displacement (mm)",  None,  False),
    ]
    row_labels   = ["Bending", "Torsion"]
    col_letters  = list("abc")

    for row_idx, (met_list, row_label) in enumerate(
        [(metrics, "Bending"), (tors_metrics, "Torsion")]
    ):
        is_bend = (row_label == "Bending")
        for col_idx, cam_col, ldv_col, ylabel, c3v, use_c3 in met_list:
            ax = axes[row_idx, col_idx]
            _shade_rpm(ax)

            cam_vals = df[cam_col].values.copy()
            ldv_vals = df[ldv_col].values

            # suppress contaminated e20 camera bending
            if is_bend:
                cam_vals[excl] = np.nan

            c3x   = e20_rpm if (use_c3 and c3v is not None) else None
            c3val = c3v if use_c3 else None

            _plot_trend(ax, x_rpm, cam_vals, ldv_vals, stable, viv, excl,
                        cam3_x=c3x, cam3_val=c3val,
                        label_cam=(row_idx == 0 and col_idx == 0),
                        label_ldv=(row_idx == 0 and col_idx == 0),
                        is_bending=is_bend)

            title_letter = "abcdef"[row_idx * 3 + col_idx]
            metric_name  = ["Mean", "RMS", "Peak"][col_idx]
            ax.set_title(f"({title_letter}) {row_label} {metric_name}", fontsize=10,
                         fontweight="bold")
            ax.set_xlabel("Fan speed (RPM)", fontsize=9)
            ax.set_ylabel(ylabel, fontsize=9)
            ax.grid(axis="y", alpha=0.3)
            ax.set_ylim(bottom=0)
            ax.tick_params(labelsize=8)

    # shared legend
    handles, labels = axes[0, 0].get_legend_handles_labels()
    handles += _regime_patches()
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=8,
               bbox_to_anchor=(0.5, -0.04), frameon=True)

    fig.suptitle(
        "Mean / RMS / Peak displacement: Camera vs LDV  —  same-tunnel separate-session comparison\n"
        "Camera 60 Hz  |  LDV 360 Hz  |  "
        "Peak = max|x − x̄|  |  e20 cam1/cam2 DCG-excluded; cam3-only shown (▲, bending only)",
        fontsize=9
    )

    out = OUT_DIR / "fig_mrp_6panel.pdf"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {out}")


# ── Figure 3: RMS scatter plot camera vs LDV (one point per condition) ────────

def fig_rms_scatter(df: pd.DataFrame):
    """
    Direct scatter: camera RMS vs LDV RMS, separately for bending and torsion.
    Includes 1:1 reference line and best-fit line with Pearson r annotation.
    e20 excluded from both channels.
    """
    from scipy import stats as sp_stats

    stable, viv, excl = _split(df)
    use_mask = stable | viv  # exclude e20 from scatter (contaminated bending, no camera torsion)

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    for ax, cam_col, ldv_col, title in [
        (axes[0], "cam_b_rms", "ldv_b_rms", "Bending RMS"),
        (axes[1], "cam_t_rms", "ldv_t_rms", "Torsion RMS"),
    ]:
        sub = df[use_mask].copy()
        cam_v = sub[cam_col].values
        ldv_v = sub[ldv_col].values
        viv_m = viv[use_mask].values

        # stable
        ax.scatter(ldv_v[~viv_m], cam_v[~viv_m], color=C_CAM, s=40, zorder=5,
                   label="Stable conditions")
        # VIV
        if viv_m.any():
            ax.scatter(ldv_v[viv_m], cam_v[viv_m], color=C_CAM, s=60,
                       marker="D", edgecolors="k", linewidths=0.8, zorder=6,
                       label="VIV (60 RPM)")

        # 1:1 line
        lim = max(ldv_v.max(), cam_v.max()) * 1.05
        ax.plot([0, lim], [0, lim], "k--", lw=1.0, alpha=0.5, label="1:1")

        # Pearson r
        r, p = sp_stats.pearsonr(ldv_v, cam_v)
        slope, intercept, *_ = sp_stats.linregress(ldv_v, cam_v)
        x_fit = np.array([0, lim])
        ax.plot(x_fit, slope * x_fit + intercept, color=C_CAM, lw=1.2, ls="-",
                alpha=0.6, label=f"Fit (r={r:.3f})")

        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_xlabel("LDV RMS (mm)", fontsize=10)
        ax.set_ylabel("Camera RMS (mm)", fontsize=10)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_aspect("equal")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
        ax.annotate(f"r = {r:.3f}\np = {p:.3e}",
                    xy=(0.05, 0.85), xycoords="axes fraction", fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))

    fig.suptitle(
        "Camera RMS vs LDV RMS — condition-level comparison (e1–e19, excl. e20 DCG)\n"
        "Simultaneous same-tunnel recording  |  Bending: cam1+cam2 avg  |  "
        "Torsion: cam1−cam2 diff × dp",
        fontsize=9
    )
    fig.tight_layout()
    out = OUT_DIR / "fig_rms_scatter.pdf"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  [WRITE] {out}")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("fig_ldv_rms_trend.py — LDV vs Camera trend figures")
    print("=" * 60)

    print("\n[DATA] Loading LDV and camera stats...")
    df, cam3_b_rms, cam3_b_peak = build_dataframe()
    print(f"       {len(df)} conditions loaded (excl. e0_0rpm)")
    print(f"       cam3 e20 bending RMS  = {cam3_b_rms:.3f} mm")
    print(f"       cam3 e20 bending peak = {cam3_b_peak:.3f} mm")

    steps = [
        ("Fig 1 — 4-panel RMS (Bending/Torsion × RPM/U)",
         lambda: fig_rms_4panel(df, cam3_b_rms)),
        ("Fig 2 — 6-panel Mean/RMS/Peak vs RPM",
         lambda: fig_mrp_6panel(df, cam3_b_rms, cam3_b_peak)),
        ("Fig 3 — RMS scatter camera vs LDV",
         lambda: fig_rms_scatter(df)),
    ]

    for label, fn in steps:
        print(f"\n[GENERATE] {label}")
        try:
            fn()
        except Exception as e:
            import traceback
            print(f"  [ERROR] {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("DONE — outputs in results/comparison_plots/")
    print("=" * 60)


if __name__ == "__main__":
    main()
