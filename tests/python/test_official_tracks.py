import csv
import json
from pathlib import Path

import pytest

from omrpr_analysis.official_tracks import (
    SOURCE_COLUMNS,
    import_official_tracks,
    write_import_metadata,
)


def write_fixture(path: Path, *, cam3_tag: int = 0, cam3_raw_ids: str = "0") -> None:
    rows = []
    for camera, tag, valid, raw_ids in (
        ("cam1", 0, "True", "0"),
        ("cam3", cam3_tag, "False", cam3_raw_ids),
    ):
        row = {column: "" for column in SOURCE_COLUMNS}
        row.update(
            {
                "condition": "e0_0rpm",
                "camera": camera,
                "expected_tag_id": str(tag),
                "frame_idx": "0",
                "timestamp_s": "0.0",
                "detected": "True",
                "valid_for_gate": valid,
                "corners_finite_and_in_image": "True",
                "raw_ids_seen": raw_ids,
            }
        )
        rows.append(row)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SOURCE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def test_import_preserves_invalid_rows_and_records_pixel_only_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    output = tmp_path / "tracks.csv"
    metadata = tmp_path / "metadata.json"
    write_fixture(source)

    summary = import_official_tracks(
        source,
        output,
        {"cam1": 0, "cam3": 0},
        {"cam1": "center_marker", "cam3": "side_marker"},
    )
    write_import_metadata(metadata, source=source, output=output, summary=summary)

    assert summary.total_frames == 2
    assert summary.valid_frames == 1
    assert summary.source_expected_tag_id_mismatches == 0
    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2
    assert {row["expected_tag_id"] for row in rows} == {"0"}
    assert {row["physical_marker_group"] for row in rows} == {
        "center_marker",
        "side_marker",
    }
    assert rows[0]["rejection_reason"] == ""
    assert rows[1]["rejection_reason"] == "detector_gate_rejected"
    assert rows[0]["topic"] == "/sony_cam1/image_raw/compressed"
    record = json.loads(metadata.read_text(encoding="utf-8"))
    assert record["units"] == "pixel"
    assert record["metric_pose_status"] == "not_generated"
    assert record["invalid_frames_retained"] == 1
    assert record["source_expected_tag_id_mismatches"] == 0
    assert record["physical_marker_groups"] == ["center_marker", "side_marker"]
    assert record["rows_by_marker_group"] == {"center_marker": 1, "side_marker": 1}


def test_import_canonicalizes_stale_source_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    write_fixture(source, cam3_tag=1, cam3_raw_ids="0")

    summary = import_official_tracks(
        source,
        tmp_path / "tracks.csv",
        {"cam1": 0, "cam3": 0},
        {"cam1": "center_marker", "cam3": "side_marker"},
    )
    assert summary.source_expected_tag_id_mismatches == 1


def test_import_rejects_detector_ids_that_disagree_with_governed_mapping(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    write_fixture(source, cam3_tag=1, cam3_raw_ids="1")

    with pytest.raises(ValueError, match="detector IDs"):
        import_official_tracks(
            source,
            tmp_path / "tracks.csv",
            {"cam1": 0, "cam3": 0},
            {"cam1": "center_marker", "cam3": "side_marker"},
        )
