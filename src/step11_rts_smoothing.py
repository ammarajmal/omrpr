"""
step11_rts_smoothing.py — OMRPR Pipeline Step 11: RTS/Kalman Smoothing (B1 Stage)

PURPOSE:
    Applies a Rauch-Tung-Striebel (RTS) smoother to the fused displacement
    traces from Step 07. The RTS smoother is non-causal — it uses all N
    observations (forward + backward pass) to improve estimates at every
    timestep. This is only possible offline.

INPUTS:
    results/step07/{condition}/motion.csv
    Columns: t_s, bending_avg_y_mm, torsion_diff_y_mm

OUTPUTS:
    results/step11/{condition}/motion_smoothed.csv
        Columns: t_s, bending_avg_y_mm, torsion_diff_y_mm,
                 bending_smoothed_mm, torsion_smoothed_mm
    results/step11/{condition}/smoothing_diagnostics.json
    results/step11/step11_summary.json

STATE VECTOR:
    x_k = [position, velocity]^T  (applied independently to bending and torsion)
    2-state 1D Kalman — simpler and more numerically stable than the full
    6-state 3D vector for scalar time series smoothing.
    The 6-state formulation in the guideline (Section 5.6) applies when
    smoothing full 3D pose; here we smooth scalar derived channels.

PROCESS MODEL:
    x_{k+1} = F @ x_k + w_k        w_k ~ N(0, Q)
    F = [[1, dt],                   (constant-velocity model)
         [0,  1]]

MEASUREMENT MODEL:
    z_k = H @ x_k + v_k            v_k ~ N(0, R)
    H = [1, 0]                      (observe position only)

TIMING:
    dt = 1/60.0 s (exact — Step 05 constructs uniform 60 Hz grid by design)
    Do NOT use np.diff(t_s) — the grid is uniform by construction.

ACCEPTANCE CRITERIA (from guideline Section 4, Step 11):
    1. Phase shift < 10 ms
    2. Dominant frequency preserved (peak within ±0.1 Hz of unsmoothed)
    3. Amplitude not reduced (smoothed RMS >= 95% of unsmoothed RMS)

CONFIRMED TARGETS (from validated results):
    Phase shift < 10 ms
    Dominant frequency error < 0.1 Hz

CRITICAL NOTE — NON-CAUSAL:
    RTS uses future frames to correct past estimates. This is only valid
    offline. Never claim or imply this smoother could run in real-time.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

FS          = 60.0          # Hz — uniform grid from Step 05
DT          = 1.0 / FS     # seconds — exact, not computed from t_s differences
HANN_WINDOW = True          # always use Hann window for FFT

# Tunable parameters — match pipeline_config.yaml rts_smoother section.
# Validated on all 21 conditions: 21/21 PASS, phase 0.00 ms, amplitude ratio 0.957–1.000.
PROCESS_NOISE_STD     = 10.0   # mm/s — process noise standard deviation
MEASUREMENT_NOISE_STD =  0.05  # mm   — measurement noise standard deviation

# Acceptance thresholds
PHASE_SHIFT_THRESHOLD_MS  = 10.0    # ms
FREQ_TOLERANCE_HZ         = 0.1     # Hz
AMPLITUDE_RATIO_MIN       = 0.95    # smoothed RMS / raw RMS must be >= this


# ─────────────────────────────────────────────────────────────────────────────
# KALMAN FORWARD PASS
# ─────────────────────────────────────────────────────────────────────────────

def kalman_forward(
    measurements: np.ndarray,
    dt: float,
    process_noise_std: float,
    measurement_noise_std: float,
) -> tuple:
    """
    Kalman filter forward pass on a 1D displacement time series.

    State: x = [position, velocity]^T
    Process model: constant velocity (position += velocity * dt)
    Measurement model: observe position only

    Returns:
        x_filt  : (N, 2) filtered state estimates x_{k|k}
        P_filt  : (N, 2, 2) filtered covariance P_{k|k}
        x_pred  : (N, 2) predicted state estimates x_{k|k-1}
        P_pred  : (N, 2, 2) predicted covariance P_{k|k-1}
    """
    N = len(measurements)

    # State transition matrix (constant velocity model)
    F = np.array([[1.0, dt],
                  [0.0, 1.0]])

    # Measurement matrix (observe position only)
    H = np.array([[1.0, 0.0]])

    # Process noise covariance — direct position-noise model.
    # Q[0,0] = (sigma*dt)^2 ≈ (sigma/60)^2 mm^2, comparable to R for sigma~10 mm/s.
    # The kinematic G@G.T formulation gives Q[0,0] = sigma^2*dt^4/4 ≈ 2e-6 mm^2,
    # far below any realistic R, collapsing the Kalman gain to ~0 regardless of sigma.
    Q = np.diag([(process_noise_std * dt)**2, process_noise_std**2])

    # Measurement noise covariance
    R = np.array([[measurement_noise_std**2]])

    # Storage
    x_filt = np.zeros((N, 2))
    P_filt = np.zeros((N, 2, 2))
    x_pred = np.zeros((N, 2))
    P_pred = np.zeros((N, 2, 2))

    # Initial state: mean of first 10 frames to reduce sensitivity to noisy first sample
    init_window = min(10, len(measurements))
    x = np.array([np.mean(measurements[:init_window]), 0.0])
    # Initial covariance: scale to signal amplitude so filter converges quickly
    signal_std_estimate = np.std(measurements)
    P = np.diag([signal_std_estimate**2, (signal_std_estimate * FS)**2])

    for k in range(N):
        # Predict
        x_p = F @ x
        P_p = F @ P @ F.T + Q

        x_pred[k] = x_p
        P_pred[k] = P_p

        # Update
        z   = np.array([measurements[k]])
        y   = z - H @ x_p                      # innovation
        S   = H @ P_p @ H.T + R                # innovation covariance
        K   = P_p @ H.T @ np.linalg.inv(S)     # Kalman gain
        x   = x_p + K @ y
        P   = (np.eye(2) - K @ H) @ P_p

        x_filt[k] = x
        P_filt[k] = P

    return x_filt, P_filt, x_pred, P_pred


# ─────────────────────────────────────────────────────────────────────────────
# RTS BACKWARD PASS
# ─────────────────────────────────────────────────────────────────────────────

def rts_backward(
    x_filt: np.ndarray,
    P_filt: np.ndarray,
    x_pred: np.ndarray,
    P_pred: np.ndarray,
    dt: float,
    process_noise_std: float,
) -> np.ndarray:
    """
    Rauch-Tung-Striebel backward smoothing pass.

    Starts from the final Kalman estimate and propagates backward,
    incorporating future information into past state estimates.
    This is non-causal — requires the complete forward pass first.

    Returns:
        x_smooth : (N, 2) smoothed state estimates x_{k|N}
    """
    N = len(x_filt)

    F = np.array([[1.0, dt],
                  [0.0, 1.0]])

    Q = np.diag([(process_noise_std * dt)**2, process_noise_std**2])

    x_smooth = np.zeros_like(x_filt)
    P_smooth = np.zeros_like(P_filt)

    # Initialize backward pass from final forward estimate
    x_smooth[-1] = x_filt[-1]
    P_smooth[-1] = P_filt[-1]

    for k in range(N - 2, -1, -1):
        # Smoother gain
        P_pred_inv = np.linalg.inv(P_pred[k + 1])
        G_k = P_filt[k] @ F.T @ P_pred_inv

        # Smoothed state and covariance
        x_smooth[k] = (x_filt[k]
                       + G_k @ (x_smooth[k + 1] - x_pred[k + 1]))
        P_smooth[k] = (P_filt[k]
                       + G_k @ (P_smooth[k + 1] - P_pred[k + 1]) @ G_k.T)

    return x_smooth


# ─────────────────────────────────────────────────────────────────────────────
# FULL RTS SMOOTHER
# ─────────────────────────────────────────────────────────────────────────────

def rts_smooth(
    measurements: np.ndarray,
    dt: float = DT,
    process_noise_std: float = PROCESS_NOISE_STD,
    measurement_noise_std: float = MEASUREMENT_NOISE_STD,
) -> np.ndarray:
    """
    Apply RTS smoother to a 1D measurement sequence.
    Returns smoothed position estimates (N,).
    """
    x_filt, P_filt, x_pred, P_pred = kalman_forward(
        measurements, dt, process_noise_std, measurement_noise_std
    )
    x_smooth = rts_backward(
        x_filt, P_filt, x_pred, P_pred, dt, process_noise_std
    )
    return x_smooth[:, 0]   # position component only


# ─────────────────────────────────────────────────────────────────────────────
# DIAGNOSTICS
# ─────────────────────────────────────────────────────────────────────────────

def dominant_frequency(signal_mm: np.ndarray, fs: float = FS) -> float:
    """
    Find dominant frequency using Hann-windowed FFT.
    Returns frequency in Hz of the peak spectral component.
    Excludes DC (0 Hz).
    """
    n = len(signal_mm)
    window = np.hanning(n)
    spectrum = np.abs(np.fft.rfft(signal_mm * window))
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    # Exclude DC
    spectrum[0] = 0.0
    peak_idx = np.argmax(spectrum)
    return float(freqs[peak_idx])


def estimate_phase_shift_ms(
    raw: np.ndarray,
    smoothed: np.ndarray,
    fs: float = FS,
) -> float:
    """
    Estimate phase shift between raw and smoothed signals via cross-correlation.
    Returns phase shift in milliseconds. Positive = smoothed lags raw.

    RTS smoother should have near-zero phase shift because it is non-causal
    (uses future frames). A causal filter always introduces positive lag.
    """
    correlation = np.correlate(raw - np.mean(raw),
                               smoothed - np.mean(smoothed),
                               mode="full")
    lags = np.arange(-(len(raw) - 1), len(raw))
    peak_lag = lags[np.argmax(correlation)]
    phase_shift_ms = (peak_lag / fs) * 1000.0
    return float(phase_shift_ms)


def compute_diagnostics(
    raw: np.ndarray,
    smoothed: np.ndarray,
    channel: str,
    fs: float = FS,
) -> dict:
    """
    Compute all acceptance criteria diagnostics for one channel.
    """
    raw_rms      = float(np.std(raw))
    smoothed_rms = float(np.std(smoothed))
    amplitude_ratio = smoothed_rms / raw_rms if raw_rms > 0 else float("nan")

    raw_freq      = dominant_frequency(raw, fs)
    smoothed_freq = dominant_frequency(smoothed, fs)
    freq_error_hz = abs(smoothed_freq - raw_freq)

    phase_shift_ms = estimate_phase_shift_ms(raw, smoothed, fs)

    phase_pass     = abs(phase_shift_ms) < PHASE_SHIFT_THRESHOLD_MS
    freq_pass      = freq_error_hz < FREQ_TOLERANCE_HZ
    amplitude_pass = amplitude_ratio >= AMPLITUDE_RATIO_MIN

    gate = "PASS" if (phase_pass and freq_pass and amplitude_pass) else "FAIL"

    return {
        f"{channel}_raw_rms_mm":          raw_rms,
        f"{channel}_smoothed_rms_mm":     smoothed_rms,
        f"{channel}_amplitude_ratio":     amplitude_ratio,
        f"{channel}_amplitude_pass":      "PASS" if amplitude_pass else "FAIL",
        f"{channel}_raw_dominant_freq_hz":      raw_freq,
        f"{channel}_smoothed_dominant_freq_hz": smoothed_freq,
        f"{channel}_freq_error_hz":       freq_error_hz,
        f"{channel}_freq_pass":           "PASS" if freq_pass else "FAIL",
        f"{channel}_phase_shift_ms":      phase_shift_ms,
        f"{channel}_phase_pass":          "PASS" if phase_pass else "FAIL",
        f"{channel}_gate":                gate,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROCESS ONE CONDITION
# ─────────────────────────────────────────────────────────────────────────────

def process_condition(
    condition: str,
    results_dir: Path,
    out_dir: Path,
    process_noise_std: float = PROCESS_NOISE_STD,
    measurement_noise_std: float = MEASUREMENT_NOISE_STD,
) -> dict:
    """
    Load Step 07 motion.csv, apply RTS smoother to both channels,
    write smoothed output, return diagnostics.
    """
    motion_path = results_dir / "step07" / condition / "motion.csv"
    if not motion_path.exists():
        raise FileNotFoundError(f"Step 07 motion.csv not found: {motion_path}")

    df = pd.read_csv(motion_path)

    required = {"t_s", "bending_avg_y_mm", "torsion_diff_y_mm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"motion.csv missing columns {missing}")

    bending_raw = df["bending_avg_y_mm"].to_numpy(dtype=float)
    torsion_raw = df["torsion_diff_y_mm"].to_numpy(dtype=float)

    # Handle NaN — interpolate before smoothing
    def fill_nans(arr: np.ndarray) -> np.ndarray:
        mask = np.isnan(arr)
        if mask.any():
            idx = np.arange(len(arr))
            arr = np.interp(idx, idx[~mask], arr[~mask])
        return arr

    bending_raw = fill_nans(bending_raw)
    torsion_raw = fill_nans(torsion_raw)

    # Apply RTS smoother independently to each channel
    bending_smoothed = rts_smooth(
        bending_raw, DT, process_noise_std, measurement_noise_std
    )
    torsion_smoothed = rts_smooth(
        torsion_raw, DT, process_noise_std, measurement_noise_std
    )

    # Compute diagnostics
    diag_b = compute_diagnostics(bending_raw, bending_smoothed, "bending")
    diag_t = compute_diagnostics(torsion_raw, torsion_smoothed, "torsion")
    diagnostics = {**diag_b, **diag_t}

    condition_gate = (
        "PASS"
        if diag_b["bending_gate"] == "PASS"
        and diag_t["torsion_gate"] == "PASS"
        else "FAIL"
    )
    diagnostics["condition_gate"] = condition_gate
    diagnostics["condition"] = condition
    diagnostics["n_frames"] = len(df)
    diagnostics["process_noise_std"] = process_noise_std
    diagnostics["measurement_noise_std"] = measurement_noise_std

    # Write smoothed CSV
    cond_out = out_dir / condition
    cond_out.mkdir(parents=True, exist_ok=True)

    df_out = df[["t_s", "bending_avg_y_mm", "torsion_diff_y_mm"]].copy()
    df_out["bending_smoothed_mm"] = bending_smoothed
    df_out["torsion_smoothed_mm"] = torsion_smoothed

    csv_path = cond_out / "motion_smoothed.csv"
    df_out.to_csv(csv_path, index=False, float_format="%.6f")

    diag_path = cond_out / "smoothing_diagnostics.json"
    with open(diag_path, "w") as f:
        json.dump(diagnostics, f, indent=2)

    return diagnostics


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Step 11: RTS/Kalman Smoothing (B1 Stage)"
    )
    parser.add_argument(
        "--condition", default=None,
        help="Single condition to process (e.g. e7_90rpm). "
             "Omit to process all conditions."
    )
    parser.add_argument(
        "--results-dir", default="results",
        help="Pipeline results root (default: results)"
    )
    parser.add_argument(
        "--output-dir", default="results/step11",
        help="Output directory (default: results/step11)"
    )
    parser.add_argument(
        "--process-noise-std", type=float, default=PROCESS_NOISE_STD,
        help=f"Process noise std dev in mm/s (default: {PROCESS_NOISE_STD})"
    )
    parser.add_argument(
        "--measurement-noise-std", type=float, default=MEASUREMENT_NOISE_STD,
        help=f"Measurement noise std dev in mm (default: {MEASUREMENT_NOISE_STD})"
    )
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="Process only e7_90rpm"
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    out_dir     = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("STEP 11 — RTS/KALMAN SMOOTHING (B1 STAGE)")
    print("=" * 60)
    print(f"\n[CONFIG] dt = 1/60 s (uniform grid — Step 05 by construction)")
    print(f"[CONFIG] process_noise_std    = {args.process_noise_std} mm/s")
    print(f"[CONFIG] measurement_noise_std = {args.measurement_noise_std} mm")
    print(f"[CONFIG] Non-causal RTS — offline only")
    print(f"\n[CRITERIA] Phase shift    < {PHASE_SHIFT_THRESHOLD_MS} ms")
    print(f"[CRITERIA] Freq error     < {FREQ_TOLERANCE_HZ} Hz")
    print(f"[CRITERIA] Amplitude ratio >= {AMPLITUDE_RATIO_MIN}")

    # Discover conditions
    if args.smoke_test:
        conditions = ["e7_90rpm"]
        print("\n[SMOKE TEST] Processing e7_90rpm only")
    elif args.condition:
        conditions = [args.condition]
    else:
        step07_dir = results_dir / "step07"
        if not step07_dir.exists():
            print(f"[FAIL] Step 07 output not found: {step07_dir}")
            sys.exit(1)
        conditions = sorted([
            d.name for d in step07_dir.iterdir()
            if d.is_dir() and (d / "motion.csv").exists()
        ])

    print(f"\n[PROCESSING] {len(conditions)} conditions...")

    all_diagnostics = []
    n_pass = 0
    n_fail = 0

    for condition in conditions:
        try:
            diag = process_condition(
                condition, results_dir, out_dir,
                args.process_noise_std, args.measurement_noise_std,
            )
            gate = diag["condition_gate"]
            b_phase = diag["bending_phase_shift_ms"]
            t_phase = diag["torsion_phase_shift_ms"]
            b_freq  = diag["bending_freq_error_hz"]
            t_freq  = diag["torsion_freq_error_hz"]
            b_amp   = diag["bending_amplitude_ratio"]
            t_amp   = diag["torsion_amplitude_ratio"]

            print(
                f"  {condition:15s} [{gate}]"
                f"  phase: b={b_phase:+.2f}ms t={t_phase:+.2f}ms"
                f"  freq_err: b={b_freq:.3f}Hz t={t_freq:.3f}Hz"
                f"  amp_ratio: b={b_amp:.3f} t={t_amp:.3f}"
            )

            if gate == "PASS":
                n_pass += 1
            else:
                n_fail += 1

            all_diagnostics.append(diag)

        except Exception as e:
            print(f"  {condition:15s} [ERROR] {e}")
            n_fail += 1

    # ── Summary ───────────────────────────────────────────────────────────
    overall_gate = "PASS" if n_fail == 0 else "FAIL"

    if all_diagnostics:
        phase_shifts_b = [d["bending_phase_shift_ms"] for d in all_diagnostics]
        phase_shifts_t = [d["torsion_phase_shift_ms"] for d in all_diagnostics]
        amp_ratios_b   = [d["bending_amplitude_ratio"] for d in all_diagnostics]
        amp_ratios_t   = [d["torsion_amplitude_ratio"] for d in all_diagnostics]

        print(f"\n{'─' * 60}")
        print(f"SUMMARY ({n_pass} PASS / {n_fail} FAIL)")
        print(f"  Bending phase shift:  "
              f"mean={np.mean(phase_shifts_b):+.2f} ms  "
              f"max={np.max(np.abs(phase_shifts_b)):.2f} ms  "
              f"(threshold < {PHASE_SHIFT_THRESHOLD_MS} ms)")
        print(f"  Torsion phase shift:  "
              f"mean={np.mean(phase_shifts_t):+.2f} ms  "
              f"max={np.max(np.abs(phase_shifts_t)):.2f} ms")
        print(f"  Bending amp ratio:    "
              f"mean={np.mean(amp_ratios_b):.3f}  "
              f"min={np.min(amp_ratios_b):.3f}  "
              f"(threshold >= {AMPLITUDE_RATIO_MIN})")
        print(f"  Torsion amp ratio:    "
              f"mean={np.mean(amp_ratios_t):.3f}  "
              f"min={np.min(amp_ratios_t):.3f}")

    step_summary = {
        "step":            "step11_rts_smoothing",
        "status":          overall_gate,
        "n_conditions":    len(conditions),
        "n_pass":          n_pass,
        "n_fail":          n_fail,
        "smoother":        "Rauch-Tung-Striebel (non-causal, offline only)",
        "state_vector":    "[position, velocity] — 1D per channel",
        "process_model":   "constant velocity, dt=1/60 s (uniform grid)",
        "process_noise_std":     args.process_noise_std,
        "measurement_noise_std": args.measurement_noise_std,
        "acceptance_criteria": {
            "phase_shift_threshold_ms":  PHASE_SHIFT_THRESHOLD_MS,
            "freq_tolerance_hz":         FREQ_TOLERANCE_HZ,
            "amplitude_ratio_min":       AMPLITUDE_RATIO_MIN,
        },
        "note_non_causal": (
            "RTS backward pass uses future observations. "
            "Only valid offline. Never claim real-time capability."
        ),
    }

    summary_path = out_dir / "step11_summary.json"
    with open(summary_path, "w") as f:
        json.dump(step_summary, f, indent=2)
    print(f"\n[WRITE] {summary_path}")

    print("\n" + "=" * 60)
    print(f"STEP 11 COMPLETE — {overall_gate}")
    print("=" * 60)

    if overall_gate == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()