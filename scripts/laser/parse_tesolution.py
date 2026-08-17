from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pandas as pd

from omrpr_analysis.paths import ProjectPaths

# BRID2D1_choi.m calibration constants (raw/laser/csv/tunnel-a-2024/2D_WTT/BRID2D1_choi.m)
PVOLT = np.array([2.7, 2.7])
DSIDE_CM = 10.0
DB_CM = 20.0
DP = (
    DB_CM / DSIDE_CM
)  # 2.0, confirmed as the Tunnel A geometry in LEGACY_ANALYSIS_REPORT.md section 2

# Confirmed directly from the source PDF (raw/experiment-logs/tesolution-2024-tunnel-a/
# Displacement Measurement System_V2.pdf, page 9, "3. Deck WTT - Data comparison (laser
# & camera)"): both the bending and torsional charts' y-axis is explicitly labeled
# "Displacement (cm)" - the WTT laser channel's native scale is centimeters, not
# millimeters (2026-07-31, user-flagged and PDF-verified). This also matches
# LEGACY_ANALYSIS_REPORT.md section 15's documented history of this same codebase
# family mislabeling centimeter LDV output as millimeters elsewhere (fixed there with a
# "_mm_corrected" column), and fqB.m (free_vibration, same sensor family, PDF-confirmed
# "Amplitude(mm)" axis, cal=27) uses a calibration constant exactly 10x BRID2D1_choi.m's
# pvolt=2.7 for the same physical quantity. Applying x10 lands high-wind torsion RMS at
# ~16mm, matching LEGACY_ANALYSIS_REPORT.md section 15's independently documented
# ~17.08mm LDV high-wind torsion-proxy RMS, and the PDF's own WTT chart scale (bending
# RMS ~0.1-0.5cm, torsion peak ~2cm at the wind-velocity spike). Three independent
# confirmations - treat CM_TO_MM as required, not optional.
CM_TO_MM = 10.0


@dataclass(frozen=True)
class ConditionStats:
    dn: int
    rpm: float
    bending_mean_mm: float
    bending_rms_mm: float
    bending_peak_mm: float
    torsion_mean_mm: float
    torsion_rms_mm: float
    torsion_peak_mm: float


def convert_displacements(
    data: npt.NDArray[np.float64], bias: npt.NDArray[np.float64]
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Convert raw two-channel LDV samples to bending and torsion-proxy mm."""

    calibrated = (data - bias) * PVOLT
    bending_mm = (calibrated[:, 0] + calibrated[:, 1]) / 2 * CM_TO_MM
    torsion_mm = (calibrated[:, 1] - calibrated[:, 0]) * DP * CM_TO_MM
    return bending_mm, torsion_mm


def compute_condition_timeseries(
    data: npt.NDArray[np.float64], bias: npt.NDArray[np.float64]
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Return the full bending and torsion-proxy displacement series in mm."""

    return convert_displacements(data, bias)


def load_rpm_lookup(windspeed_xlsx: Path) -> dict[int, float]:
    """Dn -> RPM, from the '실험rpm' column. D0 (bias) has no row and is excluded.

    Mapping verified two ways: (1) the xlsx's own 'file' column reads D01..D40,
    a direct textual match to disk files D1..D38 with no reason to assume a shift;
    (2) an independent wind-speed-proxy channel (column 3 of every raw Dn file,
    unused by BRID2D1_choi.m but present) is smoothly monotonic in disk index n and
    correlates with the xlsx's own calculated wind speed at every candidate offset
    (-1/0/+1) too similarly to be decisive on its own (Pearson r 0.96-0.97 for all
    three; ratio coefficient-of-variation 0.51-0.62, offset 0 in the middle) - not a
    strong independent confirmation, but nothing contradicts the direct reading either.
    Direct (no offset) is used as the physically simplest interpretation given D0 is
    excluded from the table as the bias run. Re-verify with a proper wind-speed
    regression if this mapping becomes load-bearing for a manuscript claim.
    """

    raw = pd.read_excel(windspeed_xlsx)
    raw.columns = ["file", "rpm", "u_meas", "u_calc", "note", "_a", "_b", "_c", "_d"]
    raw = raw[raw["file"].astype(str).str.match(r"^D\d+$", na=False)].copy()
    raw["n"] = raw["file"].str.extract(r"D0?(\d+)")[0].astype(int)
    raw["rpm"] = pd.to_numeric(raw["rpm"], errors="coerce")
    return {int(row.n): float(row.rpm) for row in raw.itertuples() if not pd.isna(row.rpm)}


def load_dn(path: Path) -> npt.NDArray[np.float64]:
    return np.loadtxt(path)[:, :2]


def compute_condition(
    dn: int, rpm: float, data: npt.NDArray[np.float64], bias: npt.NDArray[np.float64]
) -> ConditionStats:
    bending, torsion = convert_displacements(data, bias)

    bending_mean = float(bending.mean())
    torsion_mean = float(torsion.mean())

    return ConditionStats(
        dn=dn,
        rpm=rpm,
        bending_mean_mm=bending_mean,
        bending_rms_mm=float(bending.std()),
        bending_peak_mm=float(np.max(np.abs(bending - bending_mean))),
        torsion_mean_mm=torsion_mean,
        torsion_rms_mm=float(torsion.std()),
        torsion_peak_mm=float(np.max(np.abs(torsion - torsion_mean))),
    )


def parse_all(dataset_root: Path) -> list[ConditionStats]:
    lookup = load_rpm_lookup(dataset_root / "Windspeed.xlsx")
    bias = load_dn(dataset_root / "D0").mean(axis=0)

    files = sorted(
        (p for p in dataset_root.iterdir() if re.fullmatch(r"D\d+", p.name)),
        key=lambda p: int(p.name[1:]),
    )

    results: list[ConditionStats] = []
    for path in files:
        n = int(path.name[1:])
        if n == 0:
            continue
        if n not in lookup:
            continue
        data = load_dn(path)
        results.append(compute_condition(n, lookup[n], data, bias))
    return results


def write_csv(rows: list[ConditionStats], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(ConditionStats.__dataclass_fields__)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_condition_timeseries(
    dn: int,
    bending_mm: npt.NDArray[np.float64],
    torsion_mm: npt.NDArray[np.float64],
    out_dir: Path,
) -> Path:
    """Write one condition's displacement series indexed by raw sample number."""

    if bending_mm.shape != torsion_mm.shape:
        raise ValueError("bending_mm and torsion_mm must have the same shape")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"D{dn}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_index", "bending_mm", "torsion_mm"])
        writer.writerows(zip(range(len(bending_mm)), bending_mm, torsion_mm, strict=True))
    return out_path


def write_all_timeseries(dataset_root: Path, out_dir: Path) -> int:
    """Convert and write every condition represented in the RPM lookup."""

    lookup = load_rpm_lookup(dataset_root / "Windspeed.xlsx")
    bias = load_dn(dataset_root / "D0").mean(axis=0)
    written = 0
    for dn in sorted(lookup):
        path = dataset_root / f"D{dn}"
        if not path.exists():
            continue
        bending_mm, torsion_mm = compute_condition_timeseries(load_dn(path), bias)
        write_condition_timeseries(dn, bending_mm, torsion_mm, out_dir)
        written += 1
    return written


def main() -> None:
    paths = ProjectPaths.discover()
    dataset_root = paths.raw / "laser/csv/tunnel-a-2024/2D_WTT"
    out_path = paths.interim / "condition-matched/laser_tunnel_a_2024.csv"
    timeseries_dir = paths.interim / "condition-matched/laser_tunnel_a_2024_timeseries"

    rows = parse_all(dataset_root)
    write_csv(rows, out_path)
    timeseries_count = write_all_timeseries(dataset_root, timeseries_dir)

    print(f"{len(rows)} conditions parsed -> {out_path}")
    print(f"{timeseries_count} condition time series -> {timeseries_dir}")
    for row in rows:
        print(
            f"D{row.dn} rpm={row.rpm:.0f} bending_rms={row.bending_rms_mm:.3f}mm "
            f"torsion_rms={row.torsion_rms_mm:.3f}mm"
        )


if __name__ == "__main__":
    main()
