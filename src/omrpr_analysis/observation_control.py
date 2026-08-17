"""Validation and deterministic decisions for the frozen observation controls."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class DetectionMetrics:
    detection_rate: float
    max_consecutive_misses: int


@dataclass(frozen=True)
class StaticPrecisionMetrics:
    bending_rms_mm: float
    torsion_rms_mm: float


def load_control(path: Path) -> dict[str, Any]:
    record = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("observation control must be a mapping")
    validate_control(record)
    return record


def validate_control(control: dict[str, Any]) -> None:
    if control.get("schema_version") != 1:
        raise ValueError("unsupported observation-control schema")

    observations = control["camera_observations"]
    # The two physical markers have the same decoded ID (0); camera identity
    # distinguishes the two observation locations.
    expected = {"cam1": 0, "cam2": 0, "cam3": 0}
    actual = {camera: values["expected_tag_id"] for camera, values in observations.items()}
    if actual != expected:
        raise ValueError(f"camera/tag mapping changed: {actual}")

    primary = control["primary_observable"]
    if primary["units"] != "pixel" or primary["absolute_metric_claim_permitted"] is not False:
        raise ValueError("image-plane displacement must remain the primary observable")

    gates = control["detection_gates"]
    pass_rate = float(gates["pass_min_detection_rate"])
    warning_rate = float(gates["warning_min_detection_rate"])
    pass_misses = int(gates["pass_max_consecutive_misses"])
    warning_misses = int(gates["warning_max_consecutive_misses"])
    if not 0.0 <= warning_rate < pass_rate <= 1.0:
        raise ValueError("detection-rate thresholds are not ordered")
    if not 0 <= pass_misses < warning_misses:
        raise ValueError("consecutive-miss thresholds are not ordered")

    static_gates = control["static_precision_gates"]
    admissible_bending = float(static_gates["admissible_bending_rms_mm"])
    admissible_torsion = float(static_gates["admissible_torsion_rms_mm"])
    review_bending = float(static_gates["review_bending_rms_mm"])
    review_torsion = float(static_gates["review_torsion_rms_mm"])
    if not 0.0 < admissible_bending < review_bending:
        raise ValueError("bending static-precision thresholds are not ordered")
    if not 0.0 < admissible_torsion < review_torsion:
        raise ValueError("torsion static-precision thresholds are not ordered")

    high_wind = control["special_conditions"]["e20_320rpm"]
    if high_wind["cam1"] != "fail" or high_wind["cam2"] != "fail":
        raise ValueError("320 RPM cam1/cam2 must remain failed")
    if high_wind["cam3"] != "warning":
        raise ValueError("320 RPM cam3 must remain diagnostic-only")
    if high_wind["prohibited_output"] != "multi_camera_composite":
        raise ValueError("320 RPM composite prohibition is missing")


def classify_detection(
    metrics: DetectionMetrics,
    control: dict[str, Any],
    *,
    condition_id: str,
    camera: str,
) -> tuple[str, tuple[str, ...]]:
    special = control["special_conditions"].get(condition_id)
    if special and camera in special:
        forced = str(special[camera])
        return forced, (f"forced_{condition_id}_{camera}",)

    gates = control["detection_gates"]
    reasons: list[str] = []
    if metrics.detection_rate < float(gates["warning_min_detection_rate"]):
        reasons.append("detection_rate_below_warning_minimum")
    if metrics.max_consecutive_misses > int(gates["warning_max_consecutive_misses"]):
        reasons.append("consecutive_misses_above_warning_maximum")
    if reasons:
        return "fail", tuple(reasons)

    if metrics.detection_rate < float(gates["pass_min_detection_rate"]):
        reasons.append("detection_rate_below_pass_minimum")
    if metrics.max_consecutive_misses > int(gates["pass_max_consecutive_misses"]):
        reasons.append("consecutive_misses_above_pass_maximum")
    if reasons:
        return "warning", tuple(reasons)
    return "pass", ()


def classify_static_precision(
    metrics: StaticPrecisionMetrics, control: dict[str, Any]
) -> tuple[str, tuple[str, ...]]:
    gates = control["static_precision_gates"]
    reasons: list[str] = []

    admissible_bending = float(gates["admissible_bending_rms_mm"])
    admissible_torsion = float(gates["admissible_torsion_rms_mm"])
    review_bending = float(gates["review_bending_rms_mm"])
    review_torsion = float(gates["review_torsion_rms_mm"])

    if metrics.bending_rms_mm > review_bending:
        reasons.append("bending_rms_above_review_threshold")
    if metrics.torsion_rms_mm > review_torsion:
        reasons.append("torsion_rms_above_review_threshold")
    if reasons:
        return "reject", tuple(reasons)

    if metrics.bending_rms_mm > admissible_bending:
        reasons.append("bending_rms_above_admissible_threshold")
    if metrics.torsion_rms_mm > admissible_torsion:
        reasons.append("torsion_rms_above_admissible_threshold")
    if reasons:
        return "review", tuple(reasons)
    return "admissible", ()


def validate_conditions(path: Path, control: dict[str, Any]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 21:
        raise ValueError(f"expected 21 conditions, found {len(rows)}")
    if len({row["condition_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate condition IDs")
    if rows[-1]["condition_id"] != "e20_320rpm":
        raise ValueError("320 RPM condition identity changed")
    if rows[-1]["analysis_role"] != "high_wind_separate":
        raise ValueError("320 RPM must remain separate")
    if control["special_conditions"]["e4_60rpm"]["stable_summary"] is not False:
        raise ValueError("60 RPM must remain outside stable summaries")
    return rows
