import csv
import json
from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np
import pytest

from omrpr_analysis import background_compensation as bc


def _shift(image: np.ndarray, dx: float, dy: float) -> np.ndarray:
    matrix = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float32)
    return cv2.warpAffine(
        image, matrix, (image.shape[1], image.shape[0]), borderMode=cv2.BORDER_REFLECT
    )


def _textured_frame(seed: int, shape: tuple[int, int] = (200, 300)) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (rng.random(shape) * 255).astype(np.uint8)


def test_estimate_pairwise_transform_recovers_known_translation() -> None:
    base = _textured_frame(0)
    shifted = _shift(base, 3.0, -2.0)
    mask = bc.marker_exclusion_mask(base.shape, [(50, 50), (70, 50), (70, 70), (50, 70)])

    transform = bc.estimate_pairwise_transform(base, shifted, mask)

    assert transform.status == ""
    assert transform.matrix is not None
    assert transform.matrix[0, 2] == pytest.approx(3.0, abs=0.2)
    assert transform.matrix[1, 2] == pytest.approx(-2.0, abs=0.2)


def test_estimate_pairwise_transform_reports_non_convergence_on_uncorrelated_frames() -> None:
    frame_a = _textured_frame(1)
    frame_b = _textured_frame(2)

    transform = bc.estimate_pairwise_transform(frame_a, frame_b, mask=None)

    assert transform.status == "ecc_non_convergence"
    assert transform.matrix is None


def test_accumulate_stream_transforms_invalidates_every_frame_after_a_failure() -> None:
    good = bc.PairwiseTransform(
        status="", correlation_coefficient=0.99, matrix=bc.IDENTITY_2X3.copy()
    )
    failed = bc.PairwiseTransform(
        status="ecc_non_convergence", correlation_coefficient=float("nan"), matrix=None
    )

    frames = bc.accumulate_stream_transforms([good, failed, good])

    assert frames[0].status == ""
    assert frames[1].status == ""
    assert frames[2].status == "no_transform_upstream"
    assert frames[2].matrix is None
    assert frames[3].status == "no_transform_upstream"
    assert frames[3].matrix is None


def test_apply_cumulative_transform_to_row_compensates_and_blanks_on_failure() -> None:
    matrix = np.array([[1.0, 0.0, -5.0], [0.0, 1.0, 2.0]], dtype=np.float64)
    ok = bc.CumulativeFrame(status="", correlation_coefficient=0.9, matrix=matrix)
    failed = bc.CumulativeFrame(
        status="no_transform_upstream", correlation_coefficient=float("nan"), matrix=None
    )
    row = {"centroid_x": "100.0", "centroid_y": "50.0", "corner0_x": "", "corner0_y": ""}

    ok_row = bc.apply_cumulative_transform_to_row(row, ok)
    failed_row = bc.apply_cumulative_transform_to_row(row, failed)

    assert ok_row["compensation_status"] == ""
    assert float(ok_row["compensated_centroid_x"]) == pytest.approx(95.0)
    assert float(ok_row["compensated_centroid_y"]) == pytest.approx(52.0)
    assert ok_row["compensated_corner0_x"] == ""
    assert failed_row["compensation_status"] == "no_transform_upstream"
    assert failed_row["compensated_centroid_x"] == ""


TRACK_COLUMNS = (
    "condition",
    "camera",
    "topic",
    "frame_idx",
    "centroid_x",
    "centroid_y",
    "corner0_x",
    "corner0_y",
    "corner1_x",
    "corner1_y",
    "corner2_x",
    "corner2_y",
    "corner3_x",
    "corner3_y",
    "corners_finite_and_in_image",
)


def _write_track_fixture(path: Path) -> None:
    rows = [
        {
            "condition": "e0_0rpm",
            "camera": "cam1",
            "topic": "/sony_cam1/image_raw/compressed",
            "frame_idx": str(i),
            "centroid_x": "150.0",
            "centroid_y": "100.0",
            "corner0_x": "140.0",
            "corner0_y": "90.0",
            "corner1_x": "160.0",
            "corner1_y": "90.0",
            "corner2_x": "160.0",
            "corner2_y": "110.0",
            "corner3_x": "140.0",
            "corner3_y": "110.0",
            "corners_finite_and_in_image": "True",
        }
        for i in range(3)
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRACK_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def test_compensate_tracks_writes_compensated_columns_and_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "per_frame_tracks.csv"
    destination = tmp_path / "compensated_tracks.csv"
    metadata_path = tmp_path / "compensation_metadata.json"
    _write_track_fixture(source)

    base = _textured_frame(3)
    frames = [base, _shift(base, 1.0, 0.5), _shift(base, 2.0, 1.0)]

    def fake_iter_bag_grayscale_frames(bag_path: Path, topic: str) -> Iterator[np.ndarray]:
        assert bag_path == Path("fake.bag")
        assert topic == "/sony_cam1/image_raw/compressed"
        yield from frames

    monkeypatch.setattr(bc, "iter_bag_grayscale_frames", fake_iter_bag_grayscale_frames)

    summary = bc.compensate_tracks(source, destination, {"e0_0rpm": Path("fake.bag")})
    bc.write_compensation_metadata(
        metadata_path, source=source, output=destination, summary=summary
    )

    assert summary.total_frames == 3
    assert summary.compensated_frames == 3
    assert summary.streams == 1

    with destination.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert rows[0]["centroid_x"] == "150.0"
    assert float(rows[0]["compensated_centroid_x"]) == pytest.approx(150.0, abs=1e-6)
    # cumulative transform maps frame i's coordinates back onto frame 0, so a
    # raw centroid held fixed while the background drifts by (2.0, 1.0) comes
    # back compensated by roughly minus that drift.
    assert float(rows[2]["compensated_centroid_x"]) == pytest.approx(148.0, abs=0.3)
    assert all(row["compensation_status"] == "" for row in rows)

    record = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert record["units"] == "pixel"
    assert record["metric_pose_status"] == "not_generated"
    assert record["total_frames"] == 3
    assert record["stream_convergence_fraction"] == {"e0_0rpm|cam1": 1.0}


def test_legacy_cached_frame_paths_requires_every_frame_present(tmp_path: Path) -> None:
    cam_dir = tmp_path / "e0_0rpm" / "cam1"
    cam_dir.mkdir(parents=True)
    (cam_dir / "frame_000000.png").write_bytes(b"x")
    (cam_dir / "frame_000001.png").write_bytes(b"x")

    assert bc.legacy_cached_frame_paths(tmp_path, "e0_0rpm", "cam1", 2) is not None
    assert bc.legacy_cached_frame_paths(tmp_path, "e0_0rpm", "cam1", 3) is None
    assert bc.legacy_cached_frame_paths(tmp_path, "missing_condition", "cam1", 1) is None


def test_compensate_tracks_prefers_frame_cache_over_bag_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "per_frame_tracks.csv"
    destination = tmp_path / "compensated_tracks.csv"
    _write_track_fixture(source)

    base = _textured_frame(3)
    frames = [base, _shift(base, 1.0, 0.5), _shift(base, 2.0, 1.0)]
    cache_root = tmp_path / "step01"
    cam_dir = cache_root / "e0_0rpm" / "cam1"
    cam_dir.mkdir(parents=True)
    for i, frame in enumerate(frames):
        cv2.imwrite(str(cam_dir / f"frame_{i:06d}.png"), frame)

    def fail_if_bag_decoded(bag_path: Path, topic: str) -> Iterator[np.ndarray]:
        raise AssertionError("bag decode should not run when the frame cache is complete")
        yield  # pragma: no cover

    monkeypatch.setattr(bc, "iter_bag_grayscale_frames", fail_if_bag_decoded)

    summary = bc.compensate_tracks(
        source, destination, {"e0_0rpm": Path("fake.bag")}, frame_cache_root=cache_root
    )

    assert summary.total_frames == 3
    assert summary.compensated_frames == 3


def test_compensate_tracks_rejects_non_contiguous_frame_indices(tmp_path: Path) -> None:
    source = tmp_path / "per_frame_tracks.csv"
    rows = [{column: "" for column in TRACK_COLUMNS} for _ in range(2)]
    rows[0].update({"condition": "e0_0rpm", "camera": "cam1", "topic": "t", "frame_idx": "0"})
    rows[1].update({"condition": "e0_0rpm", "camera": "cam1", "topic": "t", "frame_idx": "2"})
    with source.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRACK_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="non-contiguous"):
        bc.compensate_tracks(source, tmp_path / "out.csv", {"e0_0rpm": Path("fake.bag")})
