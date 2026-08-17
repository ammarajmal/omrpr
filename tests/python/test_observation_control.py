import csv
from pathlib import Path

import pytest

from omrpr_analysis.observation_control import (
    DetectionMetrics,
    StaticPrecisionMetrics,
    classify_detection,
    classify_static_precision,
    load_control,
    validate_conditions,
)

CONTROL_PATH = Path("configs/observation-control.yaml")


def test_frozen_control_and_condition_manifest() -> None:
    control = load_control(CONTROL_PATH)
    rows = validate_conditions(Path("configs/conditions.csv"), control)
    assert len(rows) == 21
    assert control["campaigns"]["camera"]["cross_instrument_alignment"] == "condition_only"
    assert control["campaigns"]["ldv"]["concurrency_with_camera"] is False
    assert {
        camera: observation["expected_tag_id"]
        for camera, observation in control["camera_observations"].items()
    } == {"cam1": 0, "cam2": 0, "cam3": 0}


@pytest.mark.parametrize(
    ("rate", "misses", "expected"),
    [
        (1.0, 0, "pass"),
        (0.94, 2, "warning"),
        (0.99, 4, "warning"),
        (0.79, 0, "fail"),
        (1.0, 7, "fail"),
    ],
)
def test_detection_classification(rate: float, misses: int, expected: str) -> None:
    control = load_control(CONTROL_PATH)
    status, _ = classify_detection(
        DetectionMetrics(rate, misses), control, condition_id="e7_90rpm", camera="cam1"
    )
    assert status == expected


def test_320rpm_forces_cam3_diagnostic_and_rejects_composite_inputs() -> None:
    control = load_control(CONTROL_PATH)
    good = DetectionMetrics(1.0, 0)
    assert classify_detection(good, control, condition_id="e20_320rpm", camera="cam1")[0] == "fail"
    assert classify_detection(good, control, condition_id="e20_320rpm", camera="cam2")[0] == "fail"
    assert (
        classify_detection(good, control, condition_id="e20_320rpm", camera="cam3")[0] == "warning"
    )


def test_static_precision_thresholds_are_locked() -> None:
    control = load_control(CONTROL_PATH)
    gates = control["static_precision_gates"]
    assert gates["admissible_bending_rms_mm"] == 0.14
    assert gates["admissible_torsion_rms_mm"] == 0.28
    assert gates["review_bending_rms_mm"] == 0.22
    assert gates["review_torsion_rms_mm"] == 0.33


@pytest.mark.parametrize(
    ("bending", "torsion", "expected"),
    [
        (0.11, 0.18, "admissible"),
        (0.18, 0.25, "review"),
        (0.25, 0.35, "reject"),
    ],
)
def test_static_precision_classification(bending: float, torsion: float, expected: str) -> None:
    control = load_control(CONTROL_PATH)
    status, _ = classify_static_precision(
        StaticPrecisionMetrics(bending, torsion),
        control,
    )
    assert status == expected


def test_generated_observation_manifest_has_one_row_per_camera_condition() -> None:
    with Path("configs/observation-manifest.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 63
    assert len({row["observation_id"] for row in rows}) == 63
    high_wind = [row for row in rows if row["condition_id"] == "e20_320rpm"]
    assert {row["instrument"]: row["planned_admissibility"] for row in high_wind} == {
        "cam1": "fail",
        "cam2": "fail",
        "cam3": "warning",
    }


def test_dataset_identity_manifest_freezes_all_primary_wtt_conditions() -> None:
    with Path("configs/dataset-identity-manifest.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 21
    assert len({row["condition_id"] for row in rows}) == 21
    assert all(len(row["sha256"]) == 64 for row in rows)
    assert all(row["identity_status"] == "frozen_sha256" for row in rows)
