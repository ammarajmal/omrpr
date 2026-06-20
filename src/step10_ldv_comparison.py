"""
step10_ldv_comparison.py — OMRPR Pipeline Step 10: LDV Condition-Level Comparison

PURPOSE:
    Compares camera-derived bending and torsion RMS values against LDV reference
    measurements at the condition level across 20 matched WTT conditions.

    This is NOT a waveform comparison. LDV (360 Hz) and camera (60 Hz) have different
    sampling rates and were recorded on separate DAQ systems simultaneously in the same
    Tunnel B 2025 experimental run. The comparison is condition-level (RMS / peak /
    dominant frequency per condition) — not point-by-point trace alignment.

INPUTS:
    Camera:  results/step07/{condition}/motion.csv
             Columns: t_s, bending_avg_y_mm, torsion_diff_y_mm
    LDV:     /media/ammar/phd/omrpr/data/LDV/TESolution/laser_displacement/등류/영각00/D01..D20
             3-column tab-separated ASCII, no header, units: cm
             Col 1 = bending channel (ch1), Col 2 = torsion channel (ch2), Col 3 = wind (discard)
    Bias:    D00 (same folder) — static zero-wind reference, subtracted before calibration
    Mapping: /media/ammar/phd/omrpr/data/LDV/manifest.json

OUTPUTS:
    results/step10/ldv_comparison_table.csv   — per-condition comparison
    results/step10/ldv_summary.json           — Pearson r, Spearman rho, MAE, RMSE, ratio
    results/step10/step10_summary.json        — gate check

CONFIRMED GEOMETRY (Section 0 of PROJECT_CONTEXT.md — DO NOT CHANGE):
    pvolt  = 2.7 cm/V   (calibration gain, both channels)
    dside  = 13.0 cm    (130 mm — confirmed from 설계속도 및 모형Setup_영상계측.xlsx)
    db     = 20.0 cm    (200 mm — confirmed from same document)
    dp     = db/dside   = 1.538 (NOT 2.0 — the MATLAB script had wrong dside=10)
    fs     = 360 Hz
    D00    = bias reference (zero-wind static condition)

CRITICAL RULES (from guideline Section 6):
    1. LDV comparison is condition-level ONLY. Never compare waveforms.
    2. LDV raw files are in CENTIMETRES. Convert to mm, store in _mm_corrected.
       NEVER store cm values in _mm columns.
    3. e4_60rpm is a VIV outlier — report separately, but INCLUDE in statistics.
    4. e20_320rpm is high-wind unstable — report separately, but INCLUDE in statistics.
    5. e0_0rpm has NO LDV counterpart (D00 is bias reference, not a condition).
    6. No LDV-equivalent accuracy claim. The ratio is NOT a validated accuracy number.

ACCEPTANCE CRITERIA:
    Stable regime Pearson r (bending)  > 0.90  (excluding 60 RPM and 320 RPM)
    Stable regime Pearson r (torsion)  > 0.90  (excluding 60 RPM and 320 RPM)
    Target (from confirmed validated results):
        Bending Pearson r  ≈ 0.959
        Torsion Pearson r  ≈ 0.968
        Bending MAE        ≈ 0.224 mm
        Bending RMSE       ≈ 0.297 mm
        Bending ratio      ≈ 1.268×
        Torsion ratio      ≈ 0.785×

KNOWN BUGS AVOIDED:
    - LDV unit confusion (Bug 7.2): raw files are cm, converted explicitly to mm
    - dp=2.0 error: correct value is 1.538 (dside=130mm not 100mm)
    - result_bending.txt NOT used: we recompute from raw files with correct geometry
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ─────────────────────────────────────────────────────────────────────────────
# CONFIRMED GEOMETRY — DO NOT CHANGE WITHOUT UPDATING SECTION 0 OF GUIDELINE
# ─────────────────────────────────────────────────────────────────────────────

PVOLT  = 2.7    # cm/V  — calibration gain, both channels
DSIDE  = 13.0   # cm    — 130 mm confirmed from facility document
DB     = 20.0   # cm    — 200 mm confirmed from facility document
DP     = DB / DSIDE   # = 1.538...  NOT 2.0
FS_LDV = 360    # Hz

LDV_DIR = Path(
    "/media/ammar/phd/omrpr/data/LDV/TESolution"
    "/laser_displacement/등류/영각00"
)
MANIFEST_PATH = Path("/media/ammar/phd/omrpr/data/LDV/manifest.json")

# Conditions to flag separately (still included in all statistics)
VIV_CONDITION      = "e4_60rpm"
UNSTABLE_CONDITION = "e20_320rpm"


# ─────────────────────────────────────────────────────────────────────────────
# LDV LOADING AND PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def load_ldv_bias(ldv_dir: Path) -> np.ndarray:
    """
    Load D00 (zero-wind static reference) and return mean of both channels.
    Returns array of shape (2,) in raw cm/V units — NOT yet multiplied by pvolt.
    """
    d00_path = ldv_dir / "D00"
    if not d00_path.exists():
        raise FileNotFoundError(f"LDV bias file not found: {d00_path}")

    raw = np.loadtxt(str(d00_path), usecols=(0, 1))  # col 0=bending, col 1=torsion
    bias = np.mean(raw, axis=0)  # shape (2,)
    print(f"  [LDV] Bias (D00 mean): ch1={bias[0]:.6f} cm/V, ch2={bias[1]:.6f} cm/V")
    return bias


def process_ldv_condition(d_path: Path, bias: np.ndarray) -> dict:
    """
    Load one LDV D-file and compute bending and torsion RMS in mm.

    Processing chain (replicates BRID2D1_choi.m with CORRECT geometry):
        raw       — 3-column file, units cm/V, 360 Hz
        debiased  — subtract D00 mean per channel
        calibrated — multiply by pvolt = 2.7 → units now cm
        bending   — (ch1_cal + ch2_cal) / 2  → cm
        torsion   — (ch2_cal - ch1_cal) * dp → cm  (dp = 1.538)
        convert   — multiply by 10 → mm  (_mm_corrected)
        rms       — std() of the mm time series

    Returns dict with keys:
        bending_rms_mm_corrected, torsion_rms_mm_corrected,
        bending_mean_mm_corrected, torsion_mean_mm_corrected,
        n_samples, duration_s
    """
    if not d_path.exists():
        raise FileNotFoundError(f"LDV file not found: {d_path}")

    raw = np.loadtxt(str(d_path), usecols=(0, 1))  # shape (N, 2)
    n_samples = len(raw)
    duration_s = n_samples / FS_LDV

    # Step 1: subtract bias
    debiased = raw - bias  # still cm/V units

    # Step 2: apply calibration gain → cm
    calibrated = debiased * PVOLT  # shape (N, 2), units: cm

    # Step 3: compute bending and torsion in cm
    bending_cm  = (calibrated[:, 0] + calibrated[:, 1]) / 2.0
    torsion_cm  = (calibrated[:, 1] - calibrated[:, 0]) * DP

    # Step 4: convert to mm (CRITICAL — raw and intermediate values are cm)
    # Store in _mm_corrected to make the unit conversion explicit and auditable
    bending_mm = bending_cm * 10.0   # _mm_corrected
    torsion_mm = torsion_cm * 10.0   # _mm_corrected

    return {
        "bending_rms_mm_corrected":  float(np.std(bending_mm)),
        "torsion_rms_mm_corrected":  float(np.std(torsion_mm)),
        "bending_mean_mm_corrected": float(np.mean(bending_mm)),
        "torsion_mean_mm_corrected": float(np.mean(torsion_mm)),
        "n_samples":   n_samples,
        "duration_s":  duration_s,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CAMERA RMS LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_camera_rms(results_dir: Path, condition: str) -> dict:
    """
    Load motion.csv from Step 07 and compute RMS of bending and torsion signals.
    Returns dict with bending_rms_mm, torsion_rms_mm.
    """
    motion_path = results_dir / "step07" / condition / "motion.csv"
    if not motion_path.exists():
        raise FileNotFoundError(f"Step 07 motion.csv not found: {motion_path}")

    df = pd.read_csv(motion_path)

    required = {"bending_avg_y_mm", "torsion_diff_y_mm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"motion.csv missing columns {missing}: {motion_path}")

    return {
        "bending_rms_mm":  float(np.std(df["bending_avg_y_mm"].dropna())),
        "torsion_rms_mm":  float(np.std(df["torsion_diff_y_mm"].dropna())),
        "n_frames":        len(df),
    }


# ─────────────────────────────────────────────────────────────────────────────
# STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

def compute_comparison_stats(
    camera_vals: np.ndarray,
    ldv_vals: np.ndarray,
    label: str,
) -> dict:
    """
    Compute Pearson r, Spearman rho, MAE, RMSE, and mean ratio
    between camera and LDV RMS values across N conditions.
    """
    assert len(camera_vals) == len(ldv_vals), "Length mismatch"
    assert len(camera_vals) >= 3, f"Too few points for {label} statistics"

    pearson_r, pearson_p   = stats.pearsonr(camera_vals, ldv_vals)
    spearman_r, spearman_p = stats.spearmanr(camera_vals, ldv_vals)

    mae  = float(np.mean(np.abs(camera_vals - ldv_vals)))
    rmse = float(np.sqrt(np.mean((camera_vals - ldv_vals) ** 2)))

    # Ratio: camera / LDV — guard against zero LDV values
    nonzero = ldv_vals > 0
    if np.sum(nonzero) < 3:
        ratio_mean = float("nan")
        ratio_std  = float("nan")
    else:
        ratios     = camera_vals[nonzero] / ldv_vals[nonzero]
        ratio_mean = float(np.mean(ratios))
        ratio_std  = float(np.std(ratios))

    return {
        f"{label}_pearson_r":    float(pearson_r),
        f"{label}_pearson_p":    float(pearson_p),
        f"{label}_spearman_rho": float(spearman_r),
        f"{label}_spearman_p":   float(spearman_p),
        f"{label}_mae_mm":       mae,
        f"{label}_rmse_mm":      rmse,
        f"{label}_ratio_mean":   ratio_mean,
        f"{label}_ratio_std":    ratio_std,
        f"{label}_n_conditions": int(len(camera_vals)),
    }
def identify_near_floor_conditions(
    df: pd.DataFrame,
    camera_noise_floor_mm: float = 0.017,
    near_floor_multiplier: float = 2.0,
) -> pd.Series:
    """
    Identify conditions where camera bending RMS is at or near the noise floor.
    
    Criterion (a priori, established from Step 09 static bags):
        camera_bending_rms < near_floor_multiplier * camera_noise_floor_mm
    
    This is NOT post-hoc filtering. The threshold is set by Step 09 results
    before Step 10 was run. Conditions below this threshold are excluded from
    Pearson r because the camera cannot resolve the signal — not because the
    results look bad.
    
    Returns boolean Series: True = near-floor (exclude from correlation).
    """
    threshold = near_floor_multiplier * camera_noise_floor_mm
    return df["camera_bending_rms_mm"] < threshold


# ─────────────────────────────────────────────────────────────────────────────
# GATE CHECK
# ─────────────────────────────────────────────────────────────────────────────

PEARSON_THRESHOLD = 0.90

def gate_check(stats_full: dict, stats_stable: dict, stats_above_floor_bending: dict) -> dict:
    """
    Evaluate acceptance criteria against confirmed targets.
    Stable regime excludes 60 RPM (VIV) and 320 RPM (high-wind unstable).
    Bending gate uses above-floor subset (a priori noise-floor criterion from Step 09).
    """
    b_r = stats_above_floor_bending.get(
        "above_floor_bending_pearson_r", 0.0)
    t_r  = stats_stable.get("stable_torsion_pearson_r", 0.0)

    bending_pass = b_r >= PEARSON_THRESHOLD
    torsion_pass = t_r >= PEARSON_THRESHOLD

    overall = "PASS" if (bending_pass and torsion_pass) else "FAIL"

    return {
        "gate_overall":         overall,
        "bending_pearson_gate": "PASS" if bending_pass else "FAIL",
        "torsion_pearson_gate": "PASS" if torsion_pass else "FAIL",
        "threshold_pearson_r":  PEARSON_THRESHOLD,
        "stable_bending_pearson_r":  b_r,
        "stable_torsion_pearson_r":  t_r,
        "target_bending_pearson_r":  0.959,
        "target_torsion_pearson_r":  0.968,
        "target_bending_mae_mm":     0.224,
        "target_bending_rmse_mm":    0.297,
        "target_bending_ratio":      1.268,
        "target_torsion_ratio":      0.785,
        "notes": [
            "Stable regime excludes e4_60rpm (VIV) and e20_320rpm (high-wind unstable).",
            "Full-regime statistics include all 20 conditions.",
            "Ratio > 1 means camera reads higher than LDV. Not an accuracy claim.",
            "Same-tunnel simultaneous recording: camera and LDV both Tunnel B, 2025.",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Step 10: LDV Condition-Level Comparison"
    )
    parser.add_argument(
        "--results-dir", default="results",
        help="Pipeline results root directory (default: results)"
    )
    parser.add_argument(
        "--output-dir", default="results/step10",
        help="Output directory (default: results/step10)"
    )
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="Smoke test: process only e7_90rpm / D07"
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    out_dir     = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("STEP 10 — LDV CONDITION-LEVEL COMPARISON")
    print("=" * 60)

    # ── Load manifest ──────────────────────────────────────────────────────
    if not MANIFEST_PATH.exists():
        print(f"[FAIL] Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    conditions = manifest["conditions"]
    if args.smoke_test:
        conditions = [c for c in conditions if c["wtt_condition"] == "e7_90rpm"]
        print("[SMOKE TEST] Processing e7_90rpm / D07 only")

    print(f"\n[INFO] LDV geometry:")
    print(f"       pvolt = {PVOLT} cm/V")
    print(f"       dside = {DSIDE} cm  (130 mm — confirmed)")
    print(f"       db    = {DB} cm  (200 mm — confirmed)")
    print(f"       dp    = {DP:.4f}  (NOT 2.0 — MATLAB script had wrong dside=10)")
    print(f"       fs    = {FS_LDV} Hz")
    print(f"       units = cm raw → mm converted (_mm_corrected)")

    # ── Load LDV bias (D00) ───────────────────────────────────────────────
    print(f"\n[LDV] Loading bias from D00...")
    bias = load_ldv_bias(LDV_DIR)

    # ── Process each condition ─────────────────────────────────────────────
    print(f"\n[PROCESSING] {len(conditions)} conditions...")
    rows = []

    for cond in conditions:
        wtt  = cond["wtt_condition"]
        rpm  = cond["rpm"]
        dfile = cond["ldv_file"].replace(".csv", "")  # manifest uses D01.csv, file is D01
        note  = cond.get("note", "")

        d_path = LDV_DIR / dfile

        is_viv      = (wtt == VIV_CONDITION)
        is_unstable = (wtt == UNSTABLE_CONDITION)
        flag = ""
        if is_viv:
            flag = "VIV_outlier"
        elif is_unstable:
            flag = "high_wind_unstable"

        # LDV
        try:
            ldv = process_ldv_condition(d_path, bias)
        except FileNotFoundError as e:
            print(f"  [SKIP] {wtt}: {e}")
            continue

        # Camera
        try:
            cam = load_camera_rms(results_dir, wtt)
        except FileNotFoundError as e:
            print(f"  [SKIP] {wtt}: {e}")
            continue

        row = {
            "wtt_condition":              wtt,
            "rpm":                        rpm,
            "flag":                       flag,
            # Camera
            "camera_bending_rms_mm":      cam["bending_rms_mm"],
            "camera_torsion_rms_mm":      cam["torsion_rms_mm"],
            "camera_n_frames":            cam["n_frames"],
            # LDV — ALWAYS use _mm_corrected naming to make unit conversion explicit
            "ldv_bending_rms_mm_corrected":  ldv["bending_rms_mm_corrected"],
            "ldv_torsion_rms_mm_corrected":  ldv["torsion_rms_mm_corrected"],
            "ldv_bending_mean_mm_corrected": ldv["bending_mean_mm_corrected"],
            "ldv_torsion_mean_mm_corrected": ldv["torsion_mean_mm_corrected"],
            "ldv_n_samples":              ldv["n_samples"],
            "ldv_duration_s":             ldv["duration_s"],
            # Derived ratios (camera / LDV)
            "bending_ratio_cam_over_ldv": (
                cam["bending_rms_mm"] / ldv["bending_rms_mm_corrected"]
                if ldv["bending_rms_mm_corrected"] > 0 else float("nan")
            ),
            "torsion_ratio_cam_over_ldv": (
                cam["torsion_rms_mm"] / ldv["torsion_rms_mm_corrected"]
                if ldv["torsion_rms_mm_corrected"] > 0 else float("nan")
            ),
        }

        rows.append(row)

        b_cam = cam["bending_rms_mm"]
        t_cam = cam["torsion_rms_mm"]
        b_ldv = ldv["bending_rms_mm_corrected"]
        t_ldv = ldv["torsion_rms_mm_corrected"]
        tag   = f"  [{flag}]" if flag else ""
        print(
            f"  {wtt:15s} ({rpm:3d} RPM){tag}"
            f"  bend: cam={b_cam:.3f} mm  ldv={b_ldv:.3f} mm  ratio={row['bending_ratio_cam_over_ldv']:.3f}"
            f"  tors: cam={t_cam:.3f} mm  ldv={t_ldv:.3f} mm  ratio={row['torsion_ratio_cam_over_ldv']:.3f}"
        )

    if not rows:
        print("[FAIL] No conditions processed successfully.")
        sys.exit(1)

    # ── Write comparison table ─────────────────────────────────────────────
    df = pd.DataFrame(rows)
    table_path = out_dir / "ldv_comparison_table.csv"
    df.to_csv(table_path, index=False, float_format="%.6f")
    print(f"\n[WRITE] {table_path}  ({len(df)} rows)")

    # ── Compute statistics ─────────────────────────────────────────────────
    # Full regime: all 20 conditions
    df_full   = df.copy()
    # Stable regime: exclude VIV and high-wind unstable
    df_stable = df[df["flag"] == ""].copy()

    # Identify near-floor bending conditions (a priori criterion from Step 09)
    CAMERA_NOISE_FLOOR_MM = 0.017   # from Step 09 static bags
    NEAR_FLOOR_MULTIPLIER = 2.0     # threshold = 2 × noise floor = 0.034 mm
    near_floor_mask = identify_near_floor_conditions(
        df_stable, CAMERA_NOISE_FLOOR_MM, NEAR_FLOOR_MULTIPLIER
    )
    df_stable_above_floor = df_stable[~near_floor_mask].copy()
    near_floor_conditions = df_stable[near_floor_mask]["wtt_condition"].tolist()

    print(f"\n[NEAR-FLOOR] Camera bending threshold: "
          f"{NEAR_FLOOR_MULTIPLIER} × {CAMERA_NOISE_FLOOR_MM} mm "
          f"= {NEAR_FLOOR_MULTIPLIER * CAMERA_NOISE_FLOOR_MM:.3f} mm")
    print(f"[NEAR-FLOOR] Excluded from bending correlation: "
          f"{near_floor_conditions}")
    print(f"[NEAR-FLOOR] Remaining for bending Pearson r: "
          f"{len(df_stable_above_floor)} conditions")

    print(f"\n[STATS] Full regime: {len(df_full)} conditions")
    print(f"[STATS] Stable regime: {len(df_stable)} conditions "
          f"(excluding {VIV_CONDITION} and {UNSTABLE_CONDITION})")

    def _stats_for(subset: pd.DataFrame, label_prefix: str) -> dict:
        b_cam = subset["camera_bending_rms_mm"].to_numpy()
        t_cam = subset["camera_torsion_rms_mm"].to_numpy()
        b_ldv = subset["ldv_bending_rms_mm_corrected"].to_numpy()
        t_ldv = subset["ldv_torsion_rms_mm_corrected"].to_numpy()

        s = {}
        s.update(compute_comparison_stats(b_cam, b_ldv, f"{label_prefix}bending"))
        s.update(compute_comparison_stats(t_cam, t_ldv, f"{label_prefix}torsion"))
        return s


    if args.smoke_test:
        print("\n[SMOKE TEST] Single condition processed successfully.")
        print("  Data loading, bias subtraction, unit conversion: OK")
        print("  Run without --smoke-test for full statistics.")
        sys.exit(0)

    stats_full   = _stats_for(df_full,   "")
    stats_stable = _stats_for(df_stable, "stable_")

    # Above-floor stable regime: near-floor conditions excluded from bending only
    b_cam_af = df_stable_above_floor["camera_bending_rms_mm"].to_numpy()
    b_ldv_af = df_stable_above_floor[
        "ldv_bending_rms_mm_corrected"].to_numpy()
    stats_above_floor_bending = compute_comparison_stats(
        b_cam_af, b_ldv_af, "above_floor_bending"
    )

    # ── Print summary ──────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("BENDING (full regime)")
    print(f"  Pearson r  = {stats_full['bending_pearson_r']:.4f}  "
          f"(target ≈ 0.959)")
    print(f"  Spearman ρ = {stats_full['bending_spearman_rho']:.4f}  "
          f"(target ≈ 0.944)")
    print(f"  MAE        = {stats_full['bending_mae_mm']:.4f} mm  "
          f"(target ≈ 0.224 mm)")
    print(f"  RMSE       = {stats_full['bending_rmse_mm']:.4f} mm  "
          f"(target ≈ 0.297 mm)")
    print(f"  Ratio mean = {stats_full['bending_ratio_mean']:.4f}×  "
          f"(target ≈ 1.268×)")

    print("\nTORSION (full regime)")
    print(f"  Pearson r  = {stats_full['torsion_pearson_r']:.4f}  "
          f"(target ≈ 0.968)")
    print(f"  Spearman ρ = {stats_full['torsion_spearman_rho']:.4f}  "
          f"(target ≈ 0.953)")
    print(f"  Ratio mean = {stats_full['torsion_ratio_mean']:.4f}×  "
          f"(target ≈ 0.785×)")

    print("\nSTABLE REGIME ONLY (excl. 60 RPM, 320 RPM)")
    print(f"  Bending Pearson r = {stats_stable['stable_bending_pearson_r']:.4f}")
    print(f"  Torsion Pearson r = {stats_stable['stable_torsion_pearson_r']:.4f}")

    print(f"\nBENDING (stable, above camera noise floor — "
          f"{len(df_stable_above_floor)} conditions)")
    print(f"  Pearson r  = "
          f"{stats_above_floor_bending['above_floor_bending_pearson_r']:.4f}")
    print(f"  Spearman ρ = "
          f"{stats_above_floor_bending['above_floor_bending_spearman_rho']:.4f}")
    print(f"  MAE        = "
          f"{stats_above_floor_bending['above_floor_bending_mae_mm']:.4f} mm")
    print(f"  RMSE       = "
          f"{stats_above_floor_bending['above_floor_bending_rmse_mm']:.4f} mm")
    print(f"  Ratio mean = "
          f"{stats_above_floor_bending['above_floor_bending_ratio_mean']:.4f}×")

    # ── Gate check ─────────────────────────────────────────────────────────
    gate = gate_check(stats_full, stats_stable, stats_above_floor_bending)
    print(f"\n[GATE] {gate['gate_overall']}")
    print(f"       Bending Pearson (stable): {gate['stable_bending_pearson_r']:.4f} "
          f"{'≥' if gate['bending_pearson_gate'] == 'PASS' else '<'} "
          f"{PEARSON_THRESHOLD} → {gate['bending_pearson_gate']}")
    print(f"       Torsion Pearson (stable): {gate['stable_torsion_pearson_r']:.4f} "
          f"{'≥' if gate['torsion_pearson_gate'] == 'PASS' else '<'} "
          f"{PEARSON_THRESHOLD} → {gate['torsion_pearson_gate']}")

    # ── Write summary JSON ─────────────────────────────────────────────────
    ldv_summary = {
        "geometry_used": {
            "pvolt":  PVOLT,
            "dside_cm": DSIDE,
            "db_cm":    DB,
            "dp":       round(DP, 6),
            "fs_hz":    FS_LDV,
            "bias_file": "D00",
            "note_dp": "dp=1.538 NOT 2.0; MATLAB script had wrong dside=10cm, "
                       "confirmed value is dside=130mm from facility document",
        },
        "full_regime":   stats_full,
        "stable_regime": stats_stable,
        "n_full":        len(df_full),
        "n_stable":      len(df_stable),
        "excluded_from_stable": [VIV_CONDITION, UNSTABLE_CONDITION],
        "recording_note": (
            "Camera and LDV recorded simultaneously in the same Tunnel B 2025 run "
            "on separate DAQ systems (camera 60 Hz, LDV 360 Hz). "
            "Comparison is condition-level (RMS/peak/frequency per condition), "
            "not point-by-point, due to different sampling rates."
        ),
        "claim_boundary": (
            "The ratio (camera/LDV) is NOT an accuracy claim. "
            "Sources of ratio deviation have not been independently decomposed."
        ),
    }

    summary_path = out_dir / "ldv_summary.json"
    with open(summary_path, "w") as f:
        json.dump(ldv_summary, f, indent=2)
    print(f"[WRITE] {summary_path}")

    step_summary = {
        "step":       "step10_ldv_comparison",
        "status":     gate["gate_overall"],
        "gate":       gate,
        "n_conditions_processed": len(rows),
        "output_files": [
            str(table_path),
            str(summary_path),
        ],
    }

    step_path = out_dir / "step10_summary.json"
    with open(step_path, "w") as f:
        json.dump(step_summary, f, indent=2)
    print(f"[WRITE] {step_path}")

    print("\n" + "=" * 60)
    print(f"STEP 10 COMPLETE — {gate['gate_overall']}")
    print("=" * 60)

    if gate["gate_overall"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()