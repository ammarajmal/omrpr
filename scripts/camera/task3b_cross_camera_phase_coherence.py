"""Task 3 follow-on: does the *phase relationship* between cameras match
physical expectation, not just the frequency content Task 3 already checked?

Two structural predictions this tests:
- cam1 vs cam2 -- two independent camera views of the SAME physical marker
  (ID-0-1) -- should be near in-phase at the bending frequency (1.4303 Hz).
  They are looking at one physical point, so any real phase offset would be
  a synchronization or sign-convention artifact, not physics.
- marker-A (cam1+cam2, ID-0-1) vs marker-B (cam3, ID-0-2) should be near
  anti-phase at the torsion frequency (3.1036 Hz). estimate_displacement.py
  defines torsion-proxy as marker2 - marker1; that differential is only a
  meaningful torsion signal if the two markers genuinely oscillate out of
  phase at that frequency, not merely at different amplitude.

As corroborating context, this also reports the two "off-diagonal" combinations
(cam1 vs cam2 @ torsion; marker-A vs marker-B @ bending), both expected
in-phase -- bending is the symmetric mode, torsion is the antisymmetric one,
so only the torsion band should show anti-phase behaviour across markers.

Sign-convention note: Task 3's PCA axis had an arbitrary SVD sign (harmless
for a magnitude-only frequency search). Phase comparison cannot tolerate
that, so this script re-derives each camera's per-condition PCA axis with
the same sign-fix estimate_displacement.py already applies to its metric
axis (pca_dominant_axis: flip so the positive-pixel-Y component wins) --
applied here in pixel space, so this stays calibration-free like Task 3.

Method: cameras are matched by timestamp, not frame_idx (LEGACY_ANALYSIS_
REPORT.md sec.18 rec.9 -- frame_idx is a per-camera decode counter, not a
shared sample clock), same 25 ms tolerance as estimate_displacement.py's
fuse_condition/SYNC_TOLERANCE_NS. Magnitude-squared coherence and cross-
spectral phase are read at the single frequency bin nearest each reference
frequency, not the local peak in a window -- phase is only meaningful
exactly at the known modal frequency, and hunting a local peak could latch
onto unrelated nearby noise. Unlike Task 3's frequency search, this uses a
segmented (multi-window-averaged) Welch estimate, not a full-length one --
coherence is only a real statistic across multiple segments (a single
segment forces |Cxy|=1 identically), and averaging denoises the phase too.

Input:  outputs/apriltag-detections/official-v3.4.5/per_frame_tracks.csv
Output: outputs/diagnostics/task3b_cross_camera_phase_coherence.csv
        outputs/reports/task3b_cross_camera_phase_coherence.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd
from scipy.signal import coherence, csd

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKS_CSV = REPO_ROOT / "outputs/apriltag-detections/official-v3.4.5/per_frame_tracks.csv"
OUT_CSV = REPO_ROOT / "outputs/diagnostics/task3b_cross_camera_phase_coherence.csv"
OUT_MD = REPO_ROOT / "outputs/reports/task3b_cross_camera_phase_coherence.md"

F_BENDING_HZ = 1.4303  # must match per_camera_frequency_recovery.py -- owner-supplied 2026-09-02
F_TORSION_HZ = 3.1036
NOMINAL_FS_HZ = 60.0
SYNC_TOLERANCE_S = 0.025  # 25 ms, matches estimate_displacement.py's SYNC_TOLERANCE_NS
MAX_GAP_S = 1.5 / NOMINAL_FS_HZ  # matched-series break threshold for the longest-run search
PHASE_CLASS_TOL_DEG = 45.0  # within this of 0 -> in-phase, of 180 -> anti-phase, else ambiguous
MIN_MATCHED_SAMPLES = 10
COHERENCE_NPERSEG = 128  # df=0.469 Hz, well under the 1.67 Hz bending/torsion band spacing
COHERENCE_MIN_SAMPLES = 4 * COHERENCE_NPERSEG  # require a handful of averaged segments
COHERENCE_NFFT = 4096  # zero-pad only -- true resolution stays nperseg-limited, this just
# avoids picket-fence bin-snap: at nperseg=128 the raw grid (df=0.469 Hz) puts no bin
# within 0.17 Hz of 3.1036 Hz, close enough to matter if phase varies quickly with
# frequency near a resonance; nfft=4096 (df=0.0146 Hz) lets us read arbitrarily close
# to the exact target instead of snapping to whichever raw bin happens to be nearest.


def pca_axis_pixel(centroid_xy: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """Same construction as Task 3's pca_1d, but sign-fixed the way
    estimate_displacement.py's pca_dominant_axis fixes its metric axis: flip
    to the +pixel-Y-leaning direction so sign is a property of the pixel
    coordinate system, not an arbitrary SVD artifact. Frequency content is
    sign-invariant (Task 3 didn't need this); phase comparison is not."""
    centered = centroid_xy - centroid_xy.mean(axis=0)
    _u, _s, vt = np.linalg.svd(centered, full_matrices=False)
    axis = vt[0]
    if axis[1] < 0:
        axis = -axis
    return axis


def camera_series(
    df_condition: pd.DataFrame, camera: str
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]] | None:
    g = df_condition[df_condition["camera"] == camera].sort_values("timestamp_s")
    if g.empty:
        return None
    t_s = g["timestamp_s"].to_numpy()
    xy = g[["centroid_x", "centroid_y"]].to_numpy()
    axis = pca_axis_pixel(xy)
    y = (xy - xy.mean(axis=0)) @ axis
    return t_s, y


def nearest_match(
    ref_ts: npt.NDArray[np.float64],
    src_ts: npt.NDArray[np.float64],
    src_vals: npt.NDArray[np.float64],
    tol_s: float = SYNC_TOLERANCE_S,
) -> tuple[npt.NDArray[np.bool_], npt.NDArray[np.float64]]:
    """Port of estimate_displacement.py's nearest_match, in seconds instead of ns."""
    if src_ts.size == 0:
        return np.zeros(ref_ts.size, dtype=bool), np.zeros(ref_ts.size)
    idx = np.searchsorted(src_ts, ref_ts)
    idx = np.clip(idx, 1, src_ts.size - 1)
    left = idx - 1
    use_left = np.abs(ref_ts - src_ts[left]) <= np.abs(ref_ts - src_ts[idx])
    nearest_idx = np.where(use_left, left, idx)
    delta = np.abs(ref_ts - src_ts[nearest_idx])
    matched = delta <= tol_s
    return matched, src_vals[nearest_idx]


def marker_a_series(
    df_condition: pd.DataFrame,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]] | None:
    """Marker A (ID-0-1) is seen redundantly by cam1 and cam2: nearest-match
    cam2 onto cam1's timestamps and average, mirroring estimate_displacement.py's
    marker_group_series -- in pixel space, so this stays calibration-free."""
    s1 = camera_series(df_condition, "cam1")
    s2 = camera_series(df_condition, "cam2")
    if s1 is None or s2 is None:
        return None
    t1, y1 = s1
    t2, y2 = s2
    matched, y2m = nearest_match(t1, t2, y2)
    if matched.sum() < MIN_MATCHED_SAMPLES:
        return None
    return t1[matched], (y1[matched] + y2m[matched]) / 2.0


def longest_continuous_run(ts: npt.NDArray[np.float64], max_gap_s: float) -> tuple[int, int]:
    """Longest run of consecutive samples with no time gap larger than
    max_gap_s. Time-based analogue of Task 3's frame_idx-based
    longest_continuous_run, needed here because cross-camera timestamp
    matching can drop samples a single camera's own frame_idx wouldn't
    flag as gapped."""
    if ts.size == 0:
        return -1, -1
    gaps = np.diff(ts)
    breaks = np.where(gaps > max_gap_s)[0]
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [ts.size - 1]))
    lengths = ends - starts + 1
    best = int(np.argmax(lengths))
    return int(starts[best]), int(ends[best])


def phase_coherence_at(
    t_x: npt.NDArray[np.float64],
    y_x: npt.NDArray[np.float64],
    t_y: npt.NDArray[np.float64],
    y_y: npt.NDArray[np.float64],
    target_hz: float,
) -> dict | None:
    """Nearest-match y onto x's timestamps, restrict to the longest gap-free
    run of the matched pair, and read magnitude-squared coherence and
    cross-spectral phase at the single frequency bin nearest target_hz."""
    matched, y_aligned = nearest_match(t_x, t_y, y_y)
    if matched.sum() < MIN_MATCHED_SAMPLES:
        return None
    t_c, x_c, y_c = t_x[matched], y_x[matched], y_aligned[matched]

    start, end = longest_continuous_run(t_c, MAX_GAP_S)
    n = end - start + 1
    if n < MIN_MATCHED_SAMPLES:
        return None
    x_r, y_r = x_c[start : end + 1], y_c[start : end + 1]

    # Unlike Task 3's peak search, this cannot reuse a full-length, non-segmented
    # Welch: with nperseg == len(signal) there is exactly one segment, and
    # magnitude-squared coherence collapses to |Sxy|^2/(Sxx*Syy) == 1.0 at every
    # bin by construction -- a mathematical identity, not evidence of anything.
    # Coherence is only a meaningful statistic when averaged over multiple
    # segments, and averaging the cross-spectrum over segments also denoises the
    # phase estimate itself, which a single-segment FFT bin would not. This
    # trades resolution for statistical validity -- acceptable here since the
    # target frequency is known exactly, unlike Task 3's peak-finding problem.
    if n < COHERENCE_MIN_SAMPLES:
        return None
    nperseg = COHERENCE_NPERSEG
    noverlap = nperseg // 2
    freqs, cxy = coherence(
        x_r, y_r, fs=NOMINAL_FS_HZ, nperseg=nperseg, noverlap=noverlap, nfft=COHERENCE_NFFT
    )
    _, pxy = csd(
        x_r, y_r, fs=NOMINAL_FS_HZ, nperseg=nperseg, noverlap=noverlap, nfft=COHERENCE_NFFT
    )
    idx = int(np.argmin(np.abs(freqs - target_hz)))

    n_segments = int((n - nperseg) // noverlap + 1)
    return {
        "n_common_samples": int(matched.sum()),
        "n_continuous_run": n,
        "n_segments": n_segments,
        "freq_bin_hz": round(float(freqs[idx]), 4),
        "coherence": round(float(cxy[idx]), 4),
        "phase_deg": round(float(np.degrees(np.angle(pxy[idx]))), 2),
    }


def classify_phase(phase_deg: float, tol_deg: float = PHASE_CLASS_TOL_DEG) -> str:
    wrapped = ((phase_deg + 180.0) % 360.0) - 180.0  # into (-180, 180]
    dist_to_0 = abs(wrapped)
    dist_to_180 = 180.0 - dist_to_0
    if dist_to_0 <= tol_deg:
        return "in-phase"
    if dist_to_180 <= tol_deg:
        return "anti-phase"
    return "ambiguous"


def main() -> None:
    df = pd.read_csv(
        TRACKS_CSV,
        usecols=["condition", "camera", "timestamp_s", "detected", "centroid_x", "centroid_y"],
    )
    df = df[df["detected"]].copy()

    rows: list[dict] = []
    for condition in sorted(df["condition"].unique()):
        rpm = float(condition.split("_")[-1].replace("rpm", ""))
        cd = df[df["condition"] == condition]

        s1 = camera_series(cd, "cam1")
        s2 = camera_series(cd, "cam2")
        s3 = camera_series(cd, "cam3")
        ma = marker_a_series(cd)

        pairs: list[tuple[str, str, tuple, tuple, float, str]] = []
        if s1 is not None and s2 is not None:
            pairs.append(("cam1_vs_cam2", "bending", s1, s2, F_BENDING_HZ, "in-phase"))
            pairs.append(("cam1_vs_cam2", "torsion", s1, s2, F_TORSION_HZ, "in-phase"))
        if ma is not None and s3 is not None:
            pairs.append(("markerA_vs_markerB", "bending", ma, s3, F_BENDING_HZ, "in-phase"))
            pairs.append(("markerA_vs_markerB", "torsion", ma, s3, F_TORSION_HZ, "anti-phase"))

        for pair_name, band, (t_x, y_x), (t_y, y_y), target_hz, expected in pairs:
            result = phase_coherence_at(t_x, y_x, t_y, y_y, target_hz)
            row = {
                "condition": condition,
                "rpm": rpm,
                "pair": pair_name,
                "band": band,
                "target_hz": target_hz,
                "expected_phase": expected,
            }
            if result is None:
                row["observed_phase"] = "insufficient_data"
                row["matches_expected"] = False
            else:
                row.update(result)
                row["observed_phase"] = classify_phase(result["phase_deg"])
                row["matches_expected"] = row["observed_phase"] == expected
            rows.append(row)

    out = pd.DataFrame(rows).sort_values(["rpm", "pair", "band"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(out)} rows)")
    print(out.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
