"""
Step 08 — Frequency Analysis
==============================
Purpose:  Compute PSD and dominant frequency for bending and torsion proxy
          channels across all conditions. Reports dominant peak and nearest
          structural reference bin as SEPARATE fields — never conflated.

Inputs:   results/step07/{condition}/motion.csv
          config/pipeline_config.yaml

Outputs:  results/step08/{condition}/frequency.json   (per-condition, full PSD arrays)
          results/step08/frequency_summary.csv         (aggregated, one row per condition per channel)

FFT methodology (Methods section text — copy to manuscript):
    "The lower bound of the spectral search range was set to 0.5 Hz to exclude
    quasi-static drift artifacts while remaining well below the configured
    structural reference frequencies. The upper bound of 10 Hz was chosen to
    cover the relevant bending and torsion harmonics while remaining below the
    camera Nyquist regime. A Hann window was applied to the full-length signal
    prior to FFT to reduce spectral leakage."

PSD normalization:
    One-sided PSD, physical units mm²/Hz:
        PSD = 2 * |FFT(signal * window)|² / (fs * sum(window²))
    Factor of 2 accounts for one-sided spectrum.
    Normalization by fs * sum(w²) gives true power spectral density.

SNR formula:
    SNR_dB = 10 * log10(PSD_peak / median(PSD_in_search_band))
    noise_floor = median(PSD) within search band — robust, no distributional assumption.
    low_snr = True if SNR_dB < low_snr_threshold_db (default 3.0 dB).

Reference bin computation:
    Computed DYNAMICALLY from actual N of each condition's motion.csv.
    freqs = np.fft.rfftfreq(N, d=1/fs)
    ref_bin = argmin(|freqs - f_ref|)
    nearest_ref_bin_hz = freqs[ref_bin]   ← actual bin frequency, not target
    This is what the manuscript table cites.

Critical distinction (never violate):
    dominant_peak_hz   = what the DATA says (argmax of PSD in search band)
    nearest_ref_bin_hz = what the STRUCTURAL MODEL predicts (closest FFT bin to f_h or f_alpha)
    These are always separate fields. A reviewer seeing them merged will assume
    agreement by construction.

Limits:
    Near-floor conditions (0–50 RPM) expected to show low_snr=True.
    e0_0rpm has no wind — broadband noise only, no structural excitation.
    e20_320rpm — always report separately; high-wind unstable motion.
    e4_60rpm (VIV) — always investigate separately.
    Full PSD arrays stored in frequency.json for Step 12 figure generation.
    Step 12 must NOT recompute FFTs — load arrays from here.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def parse_args():
    parser = argparse.ArgumentParser(description="Step 08 — Frequency Analysis")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Condition name — e.g. e7_90rpm")
    group.add_argument("--all", action="store_true",
                       help="Process all conditions found in results/step07/")
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


def compute_psd(signal: np.ndarray, fs: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute one-sided PSD of signal using Hann window.
    Returns (freqs_hz, psd_mm2_per_hz).
    Units: mm²/Hz (signal must be in mm).
    """
    N      = len(signal)
    window = np.hanning(N)
    X      = np.fft.rfft(signal * window)
    # One-sided PSD normalised by fs * sum(w²)
    psd    = 2.0 * np.abs(X) ** 2 / (fs * np.sum(window ** 2))
    freqs  = np.fft.rfftfreq(N, d=1.0 / fs)
    # DC bin (index 0) should not be doubled — correct it
    psd[0] /= 2.0
    return freqs, psd


def analyse_channel(
    signal: np.ndarray,
    fs: float,
    f_ref: float,
    search_min: float,
    search_max: float,
    snr_threshold_db: float,
    channel_name: str,
) -> dict:
    """
    Run full frequency analysis for one channel (bending or torsion).
    Returns a dict with all scalar metrics + full PSD arrays.
    """
    freqs, psd = compute_psd(signal, fs)
    N = len(signal)

    # ── Search band mask ──────────────────────────────────────────────────────
    band_mask = (freqs >= search_min) & (freqs <= search_max)
    if not np.any(band_mask):
        raise RuntimeError(
            f"No FFT bins found in search band [{search_min}, {search_max}] Hz. "
            f"Check fs and signal length."
        )

    freqs_band = freqs[band_mask]
    psd_band   = psd[band_mask]

    # ── Dominant peak — what the DATA says ───────────────────────────────────
    peak_idx_in_band  = int(np.argmax(psd_band))
    dominant_peak_hz  = float(freqs_band[peak_idx_in_band])
    peak_power        = float(psd_band[peak_idx_in_band])

    # ── Noise floor and SNR ───────────────────────────────────────────────────
    noise_floor_power = float(np.median(psd_band))
    if noise_floor_power > 0:
        snr_db = float(10.0 * np.log10(peak_power / noise_floor_power))
    else:
        snr_db = float("inf")
    low_snr = snr_db < snr_threshold_db

    # ── Nearest reference bin — what the STRUCTURAL MODEL predicts ───────────
    # Computed dynamically from actual N — never hardcoded
    ref_bin_idx       = int(np.argmin(np.abs(freqs - f_ref)))
    nearest_ref_bin_hz = float(freqs[ref_bin_idx])
    ref_bin_power     = float(psd[ref_bin_idx])

    # ── Frequency resolution ──────────────────────────────────────────────────
    bin_spacing_hz = float(fs / N)

    return {
        "channel":            channel_name,
        "n_frames":           N,
        "bin_spacing_hz":     round(bin_spacing_hz, 6),
        "f_ref_target_hz":    f_ref,                          # structural model target
        "nearest_ref_bin_hz": round(nearest_ref_bin_hz, 6),  # actual FFT bin — cite this
        "dominant_peak_hz":   round(dominant_peak_hz, 6),    # what data says
        "peak_power":         round(peak_power, 8),
        "noise_floor_power":  round(noise_floor_power, 8),
        "snr_db":             round(snr_db, 4),
        "low_snr":            bool(low_snr),
        "search_min_hz":      search_min,
        "search_max_hz":      search_max,
        # Full arrays for Step 12 figure generation — do NOT recompute in Step 12
        "freqs_hz":           [round(f, 6) for f in freqs.tolist()],
        "psd_mm2_per_hz":     [round(p, 10) for p in psd.tolist()],
    }


def process_condition(condition: str, config: dict) -> dict:
    """
    Run frequency analysis for one condition. Returns row dict for aggregated CSV.
    """
    results_dir = Path(config["paths"]["results_dir"])
    freq_cfg    = config["frequency"]

    fs              = float(freq_cfg["fs_hz"])
    f_h_hz          = float(freq_cfg["f_h_hz"])
    f_alpha_hz      = float(freq_cfg["f_alpha_hz"])
    search_min      = float(freq_cfg["search_min_hz"])
    search_max      = float(freq_cfg["search_max_hz"])
    snr_threshold   = float(freq_cfg["low_snr_threshold_db"])

    motion_csv = results_dir / "step07" / condition / "motion.csv"
    if not motion_csv.exists():
        raise FileNotFoundError(
            f"Step07 output missing for {condition}. Run step07 first."
        )

    df = pd.read_csv(motion_csv)

    bending_signal  = df["bending_avg_y_mm"].values
    torsion_signal  = df["torsion_diff_y_mm"].values

    # ── Analyse both channels ─────────────────────────────────────────────────
    bending_result = analyse_channel(
        bending_signal, fs, f_h_hz,
        search_min, search_max, snr_threshold, "bending"
    )
    torsion_result = analyse_channel(
        torsion_signal, fs, f_alpha_hz,
        search_min, search_max, snr_threshold, "torsion_proxy"
    )

    # ── Write per-condition frequency.json ────────────────────────────────────
    out_dir = results_dir / "step08" / condition
    out_dir.mkdir(parents=True, exist_ok=True)

    freq_json = {
        "condition": condition,
        "n_frames":  len(df),
        "fs_hz":     fs,
        "bending":   bending_result,
        "torsion":   torsion_result,
    }

    with open(out_dir / "frequency.json", "w") as f:
        json.dump(freq_json, f, indent=2)

    # ── Print per-condition summary ───────────────────────────────────────────
    b  = bending_result
    t  = torsion_result
    b_flag = "LOW_SNR" if b["low_snr"] else "OK"
    t_flag = "LOW_SNR" if t["low_snr"] else "OK"

    print(f"  {condition}:")
    print(f"    bending : peak={b['dominant_peak_hz']:.4f}Hz  "
          f"ref={b['nearest_ref_bin_hz']:.4f}Hz  "
          f"SNR={b['snr_db']:.1f}dB  {b_flag}")
    print(f"    torsion : peak={t['dominant_peak_hz']:.4f}Hz  "
          f"ref={t['nearest_ref_bin_hz']:.4f}Hz  "
          f"SNR={t['snr_db']:.1f}dB  {t_flag}")

    # ── Return rows for aggregated CSV ────────────────────────────────────────
    def make_row(res, channel_label):
        return {
            "condition":          condition,
            "channel":            channel_label,
            "dominant_peak_hz":   res["dominant_peak_hz"],
            "nearest_ref_bin_hz": res["nearest_ref_bin_hz"],
            "f_ref_target_hz":    res["f_ref_target_hz"],
            "snr_db":             res["snr_db"],
            "low_snr":            res["low_snr"],
            "peak_power":         res["peak_power"],
            "noise_floor_power":  res["noise_floor_power"],
            "n_frames":           res["n_frames"],
            "bin_spacing_hz":     res["bin_spacing_hz"],
        }

    return [
        make_row(bending_result, "bending"),
        make_row(torsion_result, "torsion_proxy"),
    ]


def main():
    args   = parse_args()
    config = load_config(args.config)

    if "frequency" not in config:
        raise KeyError(
            "Missing 'frequency' block in pipeline_config.yaml. "
            "Add f_h_hz, f_alpha_hz, search_min_hz, search_max_hz, "
            "low_snr_threshold_db, fs_hz, window_type."
        )

    results_dir = Path(config["paths"]["results_dir"])

    if args.all:
        step07_root = results_dir / "step07"
        conditions  = sorted([d.name for d in step07_root.iterdir() if d.is_dir()])
        if not conditions:
            raise FileNotFoundError(f"No step07 results found under {step07_root}")
        print(f"Found {len(conditions)} condition(s) — processing all.\n")
    else:
        conditions = [condition_from_arg(args.bag)]

    print("=== FREQUENCY ANALYSIS ===\n")

    all_rows = []
    for condition in conditions:
        rows = process_condition(condition, config)
        all_rows.extend(rows)

    # ── Write aggregated frequency_summary.csv ────────────────────────────────
    summary_csv = results_dir / "step08" / "frequency_summary.csv"
    summary_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "condition", "channel",
        "dominant_peak_hz", "nearest_ref_bin_hz", "f_ref_target_hz",
        "snr_db", "low_snr",
        "peak_power", "noise_floor_power",
        "n_frames", "bin_spacing_hz",
    ]

    # If running --bag (single condition), append to existing CSV rather than overwrite
    write_header = not summary_csv.exists() or args.all
    mode = "w" if (args.all or not summary_csv.exists()) else "a"

    with open(summary_csv, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n  Aggregated summary written: {summary_csv}")

    # ── Print low SNR conditions as a final gate check ────────────────────────
    low_snr_rows = [r for r in all_rows if r["low_snr"]]
    if low_snr_rows:
        print(f"\n  Low SNR conditions (SNR < {config['frequency']['low_snr_threshold_db']} dB):")
        for r in low_snr_rows:
            print(f"    {r['condition']} [{r['channel']}]: SNR={r['snr_db']:.1f} dB")
    else:
        print(f"\n  All conditions above SNR threshold.")

    print()


if __name__ == "__main__":
    main()
