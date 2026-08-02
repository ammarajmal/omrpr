from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

from omrpr_analysis.paths import ProjectPaths

# Confirmed real VIV lock-in resonance (not measurement noise), 2026-08-03: a
# data-driven local-jump z-score flagged e4_60rpm/e5_70rpm/e6_80rpm as sharp outliers
# against a smooth RPM trend; reading Displacement Measurement System_V2.pdf pages
# 10/14/18 (D10=70rpm) showed a clean, sustained, high-amplitude sinusoidal
# oscillation independently agreed on by the laser AND all three of the vendor's own
# cameras - a textbook VIV lock-in signature, not noise (contrast: page 21, D31=240rpm,
# not flagged, shows a much smaller irregular non-periodic buffeting response).
# LEGACY_ANALYSIS_REPORT.md section 13 already documented the 60rpm point in
# isolation; this extends it to the full resonance neighborhood with independent
# multi-instrument confirmation. Excluded here ONLY from the calibration-trend/
# correlation fit (a real resonance legitimately distorts that), never implying the
# data itself is unreliable - report it as a genuine finding, per
# SUBMISSION_READINESS_CHECKLIST.md's "60 RPM VIV behavior explained" requirement.
VIV_RESONANCE_RPMS = (60.0, 70.0, 80.0)
HIGH_WIND_RPM = 320.0  # section 17 claim-boundary rule: always reported separately.
EXCLUDED_RPMS = (*VIV_RESONANCE_RPMS, HIGH_WIND_RPM)


@dataclass(frozen=True)
class LaserRow:
    rpm: float
    bending_rms_mm: float
    torsion_rms_mm: float


@dataclass(frozen=True)
class CameraRow:
    camera: str
    rpm: float
    bending_rms_mm: float


@dataclass(frozen=True)
class FusedRow:
    rpm: float
    bending_rms_mm: float
    torsion_rms_mm: float


def load_fused(path: Path) -> dict[float, FusedRow]:
    rows: dict[float, FusedRow] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rpm = float(row["rpm"])
            rows[rpm] = FusedRow(
                rpm=rpm,
                bending_rms_mm=float(row["bending_rms_mm"]),
                torsion_rms_mm=float(row["torsion_rms_mm"]),
            )
    return rows


def load_laser(path: Path) -> dict[float, LaserRow]:
    rows: dict[float, LaserRow] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rpm = float(row["rpm"])
            rows[rpm] = LaserRow(
                rpm=rpm,
                bending_rms_mm=float(row["bending_rms_mm"]),
                torsion_rms_mm=float(row["torsion_rms_mm"]),
            )
    return rows


def load_camera(path: Path) -> dict[str, dict[float, CameraRow]]:
    rows: dict[str, dict[float, CameraRow]] = {"cam1": {}, "cam2": {}, "cam3": {}}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rpm = float(row["rpm"])
            cam = row["camera"]
            rows[cam][rpm] = CameraRow(
                camera=cam, rpm=rpm, bending_rms_mm=float(row["bending_rms_mm"])
            )
    return rows


def pearson(x: npt.NDArray[np.float64], y: npt.NDArray[np.float64]) -> float:
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x: npt.NDArray[np.float64], y: npt.NDArray[np.float64]) -> float:
    return pearson(
        np.argsort(np.argsort(x)).astype(np.float64), np.argsort(np.argsort(y)).astype(np.float64)
    )


def main() -> None:
    paths = ProjectPaths.discover()
    laser = load_laser(paths.interim / "condition-matched/laser_tunnel_a_2024.csv")
    camera = load_camera(paths.interim / "condition-matched/camera_tunnel_a_2024.csv")
    fused_path = paths.interim / "condition-matched/camera_fused_tunnel_a_2024.csv"
    fused = load_fused(fused_path) if fused_path.exists() else {}

    report_lines: list[str] = []
    report_lines.append("# Camera vs Laser (Tunnel A) condition-level discrepancy - PROVISIONAL")
    report_lines.append("")
    report_lines.append(
        "Per-camera bending (below) is projected onto each camera's own PCA-derived "
        "dominant-oscillation axis (Phase 6, replacing the earlier raw image-Y axis) - "
        "that axis landed ~90deg from image-Y for all three cameras (essentially each "
        "camera's own depth/Z direction), plausibly a symptom of the still-provisional "
        "intrinsics' bad focal length inflating apparent-depth noise in solvePnP, so "
        "absolute magnitude and sign still aren't directly comparable to the laser's "
        "physically-calibrated mm; only trend shape (correlation across the RPM sweep) "
        "is meaningfully interpretable there. The fused bending/torsion-proxy section "
        "combines the two physical markers on the rig (ID-0-1, seen by cam1+cam2; "
        "ID-0-2, seen by cam3 only, 20cm away - both markers happen to carry the same "
        "AprilTag payload id, confirmed from rig photos 2026-07-31, camera source is "
        "what disambiguates them) the same way BRID2D1_choi.m combines its two laser "
        "channels: bending=avg, torsion=diff. Still provisional: no real multi-camera "
        "extrinsics establish that cam1/cam2/cam3's individually-derived PCA axes all "
        "point the same physical direction in a shared world frame (a legacy "
        "extrinsics file was cross-checked for cam3 vs cam1 only, secondary evidence, "
        "not authoritative - see plan file)."
    )
    report_lines.append("")

    for cam in ("cam1", "cam2", "cam3"):
        joined = [
            (rpm, camera[cam][rpm].bending_rms_mm, laser[rpm].bending_rms_mm)
            for rpm in sorted(camera[cam])
            if rpm in laser
        ]
        stable = [row for row in joined if row[0] not in EXCLUDED_RPMS]
        excluded = [row for row in joined if row[0] in EXCLUDED_RPMS]

        report_lines.append(f"## {cam}")
        report_lines.append("")
        report_lines.append(
            f"n conditions joined: {len(joined)} (stable regime n={len(stable)}, "
            f"excluded: {[r[0] for r in excluded]}). e20_320rpm has no laser "
            "counterpart at all (Windspeed.xlsx's highest usable step is 310rpm/D38) "
            "so it never enters the join - this is a data-availability gap, not a "
            "deliberate exclusion, though the effect (320rpm absent from any "
            "stable-regime comparison) matches the claim-boundary rule anyway."
        )

        if len(stable) >= 3:
            cam_vals = np.array([r[1] for r in stable])
            laser_vals = np.array([r[2] for r in stable])
            report_lines.append(
                f"- Pearson r (bending RMS, stable regime): {pearson(cam_vals, laser_vals):.3f}"
            )
            report_lines.append(
                f"- Spearman rho (bending RMS, stable regime): {spearman(cam_vals, laser_vals):.3f}"
            )

        report_lines.append("")
        report_lines.append("| rpm | camera bending RMS (raw axis, mm) | laser bending RMS (mm) |")
        report_lines.append("|---|---|---|")
        for rpm, cam_val, laser_val in joined:
            flag = " (excluded)" if rpm in EXCLUDED_RPMS else ""
            report_lines.append(f"| {rpm:.0f}{flag} | {cam_val:.4f} | {laser_val:.4f} |")
        report_lines.append("")

    if fused:
        joined = [
            (
                rpm,
                fused[rpm].bending_rms_mm,
                fused[rpm].torsion_rms_mm,
                laser[rpm].bending_rms_mm,
                laser[rpm].torsion_rms_mm,
            )
            for rpm in sorted(fused)
            if rpm in laser
        ]
        stable = [row for row in joined if row[0] not in EXCLUDED_RPMS]
        excluded = [row for row in joined if row[0] in EXCLUDED_RPMS]

        report_lines.append("## Fused (two-marker) bending and torsion-proxy")
        report_lines.append("")
        report_lines.append(
            f"n conditions joined: {len(joined)} (stable regime n={len(stable)}, "
            f"excluded: {[r[0] for r in excluded]})"
        )

        if len(stable) >= 3:
            cam_bend = np.array([r[1] for r in stable])
            laser_bend = np.array([r[3] for r in stable])
            cam_tors = np.array([r[2] for r in stable])
            laser_tors = np.array([r[4] for r in stable])
            bend_pearson = pearson(cam_bend, laser_bend)
            bend_spearman = spearman(cam_bend, laser_bend)
            torsion_pearson = pearson(cam_tors, laser_tors)
            torsion_spearman = spearman(cam_tors, laser_tors)
            report_lines.append(
                f"- Bending Pearson r / Spearman rho: {bend_pearson:.3f} / {bend_spearman:.3f}"
            )
            report_lines.append(
                f"- Torsion-proxy Pearson r / Spearman rho: "
                f"{torsion_pearson:.3f} / {torsion_spearman:.3f}"
            )

        report_lines.append("")
        report_lines.append(
            "| rpm | camera bending RMS (mm) | laser bending RMS (mm) | "
            "camera torsion RMS (mm) | laser torsion RMS (mm) |"
        )
        report_lines.append("|---|---|---|---|---|")
        for rpm, cb, ct, lb, lt in joined:
            flag = " (excluded)" if rpm in EXCLUDED_RPMS else ""
            report_lines.append(f"| {rpm:.0f}{flag} | {cb:.4f} | {lb:.4f} | {ct:.4f} | {lt:.4f} |")
        report_lines.append("")
    else:
        report_lines.append("## Fused (two-marker) bending and torsion-proxy")
        report_lines.append("")
        report_lines.append(f"Not yet available - {fused_path} does not exist.")
        report_lines.append("")

    report_lines.append("## Excluded conditions are confirmed real resonance events, not noise")
    report_lines.append("")
    report_lines.append(
        "Verified 2026-08-03 by reading Displacement Measurement System_V2.pdf pages "
        "10/14/18 (D10=70rpm, inside the excluded zone): the laser AND all three of "
        "the vendor's own independent cameras show a clean, sustained, high-amplitude "
        "sinusoidal oscillation for the full 30s record - a textbook VIV lock-in "
        "signature. Contrast page 21 (D31=240rpm, not excluded): much smaller, "
        "irregular, non-periodic buffeting response. e4_60rpm/e5_70rpm/e6_80rpm are "
        "excluded from the correlation/trend numbers above ONLY because a real "
        "resonance legitimately distorts a calibration-quality trend fit - this is not "
        "a claim that the data there is noisy or unreliable. It is the opposite: "
        "report it as a genuine physical finding (VIV lock-in near the vertical-"
        "bending natural frequency), per SUBMISSION_READINESS_CHECKLIST.md's '60 RPM "
        "VIV behavior explained' requirement, not as data to discard."
    )
    report_lines.append("")
    report_lines.append("## Next step (in progress)")
    report_lines.append("")
    report_lines.append(
        "Joint intrinsics refinement (AprilTag reprojection error + laser-agreement "
        "error) was scoped in the plan and, as of 2026-08-02, handed to a Codex "
        "background task (task-msbxiznq-y4uxu8) rather than implemented directly here. "
        "The marker-spacing blocker is resolved (20cm, confirmed 2026-07-31). A fully "
        "defensible camera-to-rig axis alignment still isn't established - Phase 6's "
        "PCA axis is a real, data-derived improvement (fused bending Pearson "
        "0.368->0.579, fused torsion Spearman 0.812->0.868) but landed suspiciously "
        "close to each camera's own depth axis, and the Codex task's exclusion set "
        "was only briefed as rpm=60 - it needs reconciling against the wider "
        "e4/e5/e6 resonance-neighborhood finding above once it completes. Correlation "
        "numbers in this report are the honest current evidence base for whether the "
        "provisional CameraInfo intrinsics need correction at all."
    )

    out_path = paths.root / "outputs/reports/step02b_laser_corrected_intrinsics_discrepancy.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"-> {out_path}")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
