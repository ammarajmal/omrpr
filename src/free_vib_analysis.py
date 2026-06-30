"""
Free-vibration analysis of bridge model (Tunnel B, 2025 campaign).
Translates fqB.m / fqT.m MATLAB logic to Python.

Outputs:
  - fn_b, zeta_b (bending natural frequency and damping ratio)
  - fn_t, zeta_t (torsion natural frequency and damping ratio)
  - Reduced-velocity regime table for all 21 camera conditions (e0–e20)
  - Figure: results/free_vib_analysis.png
"""

import numpy as np
import scipy.signal as sig
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path("/media/ammar/phd/omrpr/data/LDV/TESolution/laser_displacement/자유진동")
RESULTS_DIR = Path("/media/ammar/phd/omrpr/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants (from MATLAB scripts and tunnel Excel)
# ---------------------------------------------------------------------------
FS = 360.0          # sampling rate (Hz)
CAL = 27.0          # voltage-to-mm calibration (mm/V), same for both channels
B = 0.40            # chord length (m) — from model setup sheet (교폭=0.4m), NOT Lee 2016 PDF (0.344 m)

# Band-pass filter parameters (from fqB.m / fqT.m)
BENDING = dict(
    file="Bd1",
    f_centre=1.4299,    # Hz — filter centre (fqB.m line 26)
    band=0.01,          # Hz half-bandwidth
    win_start=10961,    # 0-indexed (MATLAB 10962): post-transient window for log-decrement
    win_end=22962,      # 0-indexed exclusive (MATLAB 22962)
    channel=0,          # Python 0-indexed (MATLAB idc=1)
    use_matlab_window=True,   # MATLAB window correctly avoids initial transient
)
TORSION = dict(
    file="Td1",
    f_centre=3.1098,
    band=0.01,
    win_start=2871,     # MATLAB window only used for FFT — it precedes the actual pluck
    win_end=8872,
    channel=1,          # Python 0-indexed (MATLAB idc=2)
    use_matlab_window=False,  # Use Hilbert-based decay window instead
)

# Wind speed table for e0–e20 (from 영상계측_laser_등류_영각00.xlsx, sheet '등류')
# e0=D00 (static, 0 RPM); e1=D01 (20 RPM, below cal. threshold → 0 m/s); e2–e20=D02–D20
CONDITIONS = [
    # (label,   RPM, U_m/s,  regime)
    ("e0",        0,  0.000,  "Static"),
    ("e1",       20,  0.000,  "Static"),          # below calibration threshold
    ("e2",       40,  0.516,  "Bending VIV"),
    ("e3",       50,  0.699,  "Bending VIV"),
    ("e4",       60,  0.882,  "Bending VIV"),
    ("e5",       70,  1.066,  "Bending VIV"),
    ("e6",       80,  1.249,  "Torsional VIV"),
    ("e7",       90,  1.432,  "Torsional VIV"),
    ("e8",      100,  1.616,  "Torsional VIV"),
    ("e9",      110,  1.799,  "Torsional VIV"),
    ("e10",     120,  1.982,  "Torsional VIV"),
    ("e11",     140,  2.349,  "Torsional VIV"),
    ("e12",     160,  2.715,  "Torsional VIV"),
    ("e13",     180,  3.082,  "Torsional VIV"),
    ("e14",     200,  3.449,  "Torsional VIV"),
    ("e15",     220,  3.815,  "Torsional VIV"),
    ("e16",     240,  4.182,  "Bending re-emergence"),
    ("e17",     260,  4.548,  "Bending re-emergence"),
    ("e18",     280,  4.915,  "Bending re-emergence"),
    ("e19",     300,  5.282,  "Bending re-emergence"),
    ("e20",     320,  5.648,  "Flutter (excluded)"),
]

# ---------------------------------------------------------------------------
# Free-vibration analysis
# ---------------------------------------------------------------------------

def _bandpass_fir(data: np.ndarray, f_centre: float, band: float) -> np.ndarray:
    """Zero-phase FIR bandpass, matching MATLAB fir1(2000, ...) + filtfilt."""
    nyq = FS / 2.0
    fl, fh = f_centre - band, f_centre + band
    b = sig.firwin(2001, [fl / nyq, fh / nyq], pass_zero=False)
    return sig.filtfilt(b, 1.0, data, axis=0)


def _log_decrement_damping(fvdata: np.ndarray, n_peaks: int, period_samples: int):
    """
    Log-decrement damping from successive positive and negative peaks.
    Matches MATLAB polyfit(aa, log(peaks), 1) followed by the sqrt formula.
    ζ = sqrt(a²/(a²+4π²)) where a is the slope of log(peaks) vs peak number.
    """
    pos_peaks, neg_peaks = [], []
    for jj in range(n_peaks):
        segment = fvdata[jj * period_samples:(jj + 1) * period_samples]
        if len(segment) == 0:
            break
        pos_peaks.append(segment.max())
        neg_peaks.append(-segment.min())   # make positive

    pos_peaks = np.array(pos_peaks)
    neg_peaks = np.array(neg_peaks)
    aa = np.arange(1, len(pos_peaks) + 1, dtype=float)

    a_pos = np.polyfit(aa, np.log(pos_peaks), 1)[0]
    a_neg = np.polyfit(aa, np.log(neg_peaks), 1)[0]

    def _zeta(a):
        return np.sqrt(a**2 / (a**2 + 4 * np.pi**2))

    zeta_pos = _zeta(a_pos)
    zeta_neg = _zeta(a_neg)
    return zeta_pos, zeta_neg, (zeta_pos + zeta_neg) / 2.0, pos_peaks, neg_peaks, aa, a_pos, a_neg


def _find_decay_window(filtered_ch: np.ndarray, noise_floor_mm: float = 0.05):
    """
    Locate the free-vibration decay window using the Hilbert envelope.
    Returns (start_idx, end_idx) bracketing the exponential decay region.
    The window begins at the amplitude peak and ends when the envelope
    drops below noise_floor_mm (or signal end, whichever comes first).
    """
    env = np.abs(sig.hilbert(filtered_ch))
    peak_idx = int(np.argmax(env))
    after_peak = np.where(env[peak_idx:] < noise_floor_mm)[0]
    end_idx = (peak_idx + int(after_peak[0])) if len(after_peak) else len(filtered_ch)
    return peak_idx, end_idx


def analyse_free_vib(cfg: dict):
    """Run free-vibration analysis for one mode (bending or torsion)."""
    raw = np.loadtxt(DATA_DIR / cfg["file"])          # shape (72000, 2), units V
    data = raw * CAL                                   # → mm
    data = sig.detrend(data, type="linear", axis=0)   # remove mean + trend

    # Band-pass filter
    filtered = _bandpass_fir(data, cfg["f_centre"], cfg["band"])

    ch = cfg["channel"]
    # FFT always uses MATLAB window (known to contain the response)
    matlab_fv = filtered[cfg["win_start"]:cfg["win_end"], :]
    nfft = 2**20
    freq = np.fft.rfftfreq(nfft, d=1.0 / FS)
    amp = np.abs(np.fft.rfft(matlab_fv[:, ch], n=nfft)) / FS
    fn_fft = freq[np.argmax(amp)]
    period_samples = round(1.0 / (fn_fft * (1.0 / FS)))

    if cfg["use_matlab_window"]:
        # MATLAB window was deliberately chosen post-transient — use it for log-decrement
        fv = matlab_fv
        start_idx, end_idx = cfg["win_start"], cfg["win_end"]
    else:
        # MATLAB window predates the pluck for this mode; use Hilbert-based decay window
        start_idx, end_idx = _find_decay_window(filtered[:, ch], noise_floor_mm=0.05)
        fv = filtered[start_idx:end_idx, :]

    n_peaks_actual = len(fv) // period_samples
    zeta_pos, zeta_neg, zeta_avg, pos_peaks, neg_peaks, aa, a_pos, a_neg = \
        _log_decrement_damping(fv[:, ch], n_peaks_actual, period_samples)

    return dict(
        fn=fn_fft,
        zeta_pos=zeta_pos,
        zeta_neg=zeta_neg,
        zeta_avg=zeta_avg,
        fv=fv,
        ch=ch,
        freq=freq,
        amp=amp,
        pos_peaks=pos_peaks,
        neg_peaks=neg_peaks,
        aa=aa,
        a_pos=a_pos,
        a_neg=a_neg,
        win_start=start_idx,
        win_end=end_idx,
        cfg=cfg,
    )


# ---------------------------------------------------------------------------
# Regime table
# ---------------------------------------------------------------------------

def build_regime_table(fn_b: float, fn_t: float):
    rows = []
    for label, rpm, U, regime in CONDITIONS:
        u_star_b = U / (fn_b * B) if U > 0 else 0.0
        u_star_t = U / (fn_t * B) if U > 0 else 0.0
        rows.append((label, rpm, U, u_star_b, u_star_t, regime))
    return rows


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

def make_figure(b_res, t_res, regime_rows, fn_b, fn_t, zeta_b, zeta_t):
    fig = plt.figure(figsize=(16, 14))
    fig.suptitle(
        f"Free-vibration analysis — Tunnel B 2025\n"
        f"fn_b = {fn_b:.4f} Hz, ζ_b = {zeta_b*100:.3f}%  |  "
        f"fn_t = {fn_t:.4f} Hz, ζ_t = {zeta_t*100:.3f}%",
        fontsize=12, fontweight="bold"
    )
    gs = fig.add_gridspec(4, 2, hspace=0.45, wspace=0.35)

    # ---- Row 0: Free-vib time histories ----
    dt = 1.0 / FS
    for col, res, label, fn_val in [(0, b_res, "Bending", fn_b), (1, t_res, "Torsion", fn_t)]:
        ax = fig.add_subplot(gs[0, col])
        t = np.arange(len(res["fv"])) * dt
        ax.plot(t, res["fv"][:, res["ch"]], lw=0.6)
        ax.set_title(f"{label} free-vibration (filtered, Ch{res['ch']+1})")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude (mm)")
        ax.grid(True, alpha=0.3)

    # ---- Row 1: FFT ----
    for col, res, label in [(0, b_res, "Bending"), (1, t_res, "Torsion")]:
        ax = fig.add_subplot(gs[1, col])
        ax.plot(res["freq"], res["amp"], lw=0.7)
        ax.set_xlim(0, 10)
        ax.set_title(f"{label} FFT — peak at {res['fn']:.4f} Hz")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Amplitude (mm)")
        ax.axvline(res["fn"], color="r", lw=1.2, ls="--", label=f"fn = {res['fn']:.4f} Hz")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # ---- Row 2: Log-decrement ----
    for col, res, label in [(0, b_res, "Bending"), (1, t_res, "Torsion")]:
        ax = fig.add_subplot(gs[2, col])
        aa = res["aa"]
        ax.plot(aa, np.log(res["pos_peaks"]), "go", ms=4, label="Positive peaks")
        ax.plot(aa, np.log(res["neg_peaks"]), "bs", ms=4, label="Negative peaks")
        ax.plot(aa, np.polyval([res["a_pos"], np.log(res["pos_peaks"][0]) - res["a_pos"]], aa),
                "g--", lw=1, alpha=0.7)
        ax.plot(aa, np.polyval([res["a_neg"], np.log(res["neg_peaks"][0]) - res["a_neg"]], aa),
                "b--", lw=1, alpha=0.7)
        zp = res["zeta_pos"] * 100
        zn = res["zeta_neg"] * 100
        za = res["zeta_avg"] * 100
        ax.set_title(f"{label} log-decrement\nζ⁺={zp:.3f}%  ζ⁻={zn:.3f}%  ζ_avg={za:.3f}%")
        ax.set_xlabel("Peak number")
        ax.set_ylabel("ln(peak amplitude)")
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

    # ---- Row 3: Reduced-velocity regime bar chart ----
    ax = fig.add_subplot(gs[3, :])
    labels   = [r[0] for r in regime_rows]
    u_stars  = [r[3] for r in regime_rows]
    regimes  = [r[5] for r in regime_rows]
    regime_colors = {
        "Static":               "#aaaaaa",
        "Bending VIV":          "#2196F3",
        "Torsional VIV":        "#F44336",
        "Bending re-emergence": "#4CAF50",
        "Flutter (excluded)":   "#FF9800",
    }
    colors = [regime_colors[r] for r in regimes]
    bars = ax.bar(labels, u_stars, color=colors, edgecolor="k", linewidth=0.4)
    ax.set_title(f"Reduced velocity U* = U / (fn_b × B),  fn_b = {fn_b:.4f} Hz, B = {B} m")
    ax.set_xlabel("Condition")
    ax.set_ylabel("U* (–)")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.grid(True, axis="y", alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=v, label=k, edgecolor="k")
                       for k, v in regime_colors.items()]
    ax.legend(handles=legend_elements, fontsize=8, loc="upper left")

    # Annotate U* values on bars
    for bar, val in zip(bars, u_stars):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=6)

    out = RESULTS_DIR / "free_vib_analysis.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Analysing bending free vibration (Bd1)...")
    b_res = analyse_free_vib(BENDING)

    print("Analysing torsion free vibration (Td1)...")
    t_res = analyse_free_vib(TORSION)

    fn_b   = b_res["fn"]
    fn_t   = t_res["fn"]
    zeta_b = b_res["zeta_avg"]
    zeta_t = t_res["zeta_avg"]

    # Regime table
    regime_rows = build_regime_table(fn_b, fn_t)

    # Figure
    fig_path = make_figure(b_res, t_res, regime_rows, fn_b, fn_t, zeta_b, zeta_t)

    # Print summary
    print()
    print("=" * 65)
    print("FREE-VIBRATION RESULTS (Tunnel B 2025)")
    print("=" * 65)
    print(f"  Bending:  fn_b = {fn_b:.4f} Hz    ζ_b = {zeta_b*100:.3f}%")
    print(f"            (ζ⁺ = {b_res['zeta_pos']*100:.3f}%  |  ζ⁻ = {b_res['zeta_neg']*100:.3f}%)")
    print(f"  Torsion:  fn_t = {fn_t:.4f} Hz    ζ_t = {zeta_t*100:.3f}%")
    print(f"            (ζ⁺ = {t_res['zeta_pos']*100:.3f}%  |  ζ⁻ = {t_res['zeta_neg']*100:.3f}%)")
    print()
    print(f"  Frequency ratio: fn_t/fn_b = {fn_t/fn_b:.3f}")
    print(f"  PDF (Lee 2016) values:  fn_b=1.95 Hz, fn_t=5.15 Hz  → DIFFERENT MODEL")
    print()

    print("REDUCED VELOCITY REGIME TABLE")
    print("-" * 75)
    print(f"  {'Cond':<6} {'RPM':>5} {'U (m/s)':>9} {'U*_b':>7} {'U*_t':>7}  Regime")
    print("-" * 75)
    for label, rpm, U, u_star_b, u_star_t, regime in regime_rows:
        print(f"  {label:<6} {rpm:>5} {U:>9.3f} {u_star_b:>7.2f} {u_star_t:>7.2f}  {regime}")
    print("-" * 75)
    print(f"  U*_b = U / (fn_b × B) = U / ({fn_b:.4f} × {B}) = U / {fn_b*B:.4f} m/s")
    print(f"  U*_t = U / (fn_t × B) = U / ({fn_t:.4f} × {B}) = U / {fn_t*B:.4f} m/s")
    print()

    # Regime boundaries
    bviv = [(r[0], r[3]) for r in regime_rows if r[5] == "Bending VIV"]
    tviv = [(r[0], r[3]) for r in regime_rows if r[5] == "Torsional VIV"]
    bre  = [(r[0], r[3]) for r in regime_rows if r[5] == "Bending re-emergence"]
    print("REGIME BOUNDARIES (U*_b)")
    print(f"  Bending VIV:          {bviv[0][1]:.2f} – {bviv[-1][1]:.2f}")
    print(f"  Torsional VIV:        {tviv[0][1]:.2f} – {tviv[-1][1]:.2f}")
    print(f"  Bending re-emergence: {bre[0][1]:.2f} – {bre[-1][1]:.2f}")
    print(f"  Flutter (excluded):   {[r[3] for r in regime_rows if 'excluded' in r[5]][0]:.2f}")
    print()
    print(f"  Figure saved: {fig_path}")
    print("=" * 65)


if __name__ == "__main__":
    main()
