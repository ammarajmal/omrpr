"""Import official AprilTag image-plane tracks without promoting pose calibration."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

SOURCE_COLUMNS = (
    "condition",
    "camera",
    "expected_tag_id",
    "frame_idx",
    "timestamp_s",
    "detected",
    "valid_for_gate",
    "tag_id",
    "decision_margin",
    "hamming",
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
    "image_width_px",
    "image_height_px",
    "raw_num_detections",
    "raw_ids_seen",
)

TRACK_COLUMNS = (
    "observation_id",
    "dataset_id",
    "source_relative_path",
    "topic",
    "physical_marker_group",
    *SOURCE_COLUMNS,
    "rejection_reason",
)


@dataclass(frozen=True)
class ImportSummary:
    total_frames: int
    valid_frames: int
    invalid_frames: int
    sha256: str
    source_expected_tag_id_mismatches: int
    conditions: int
    cameras: tuple[str, ...]
    physical_marker_groups: tuple[str, ...]
    rows_by_marker_group: Mapping[str, int]


def rejection_reason(row: Mapping[str, str], governed_expected_id: int) -> str:
    """Return a deterministic reason for every rejected observation."""

    if row["detected"].strip().lower() != "true":
        return "not_detected"
    if row["tag_id"].strip() and int(row["tag_id"]) != governed_expected_id:
        return "unexpected_tag_id"
    if row["hamming"].strip() and int(row["hamming"]) != 0:
        return "nonzero_hamming"
    if row["corners_finite_and_in_image"].strip().lower() != "true":
        return "corners_invalid_or_out_of_image"
    if row["valid_for_gate"].strip().lower() != "true":
        return "detector_gate_rejected"
    return ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def import_official_tracks(
    source: Path,
    destination: Path,
    expected_tag_ids: Mapping[str, int],
    physical_marker_groups: Mapping[str, str],
    observation_ids: Mapping[tuple[str, str], str] | None = None,
    dataset_identities: Mapping[str, tuple[str, str]] | None = None,
) -> ImportSummary:
    """Copy all official detector rows into a canonical, pixel-only track artifact.

    Misses and gate-invalid frames remain in the output.  This is deliberately an
    import, not a detector or PnP stage: downstream consumers must use
    ``valid_for_gate`` and may not infer metric pose from this data.
    """

    with source.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or ())
        missing = set(SOURCE_COLUMNS) - fields
        if missing:
            raise ValueError(f"official track input missing columns: {sorted(missing)}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        total = valid = 0
        mismatches = 0
        conditions: set[str] = set()
        cameras: set[str] = set()
        marker_counts: Counter[str] = Counter()
        seen_frame_keys: set[tuple[str, str, int]] = set()
        last_frame_by_stream: dict[tuple[str, str], int] = {}
        with destination.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=TRACK_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in reader:
                camera = row["camera"]
                if camera not in expected_tag_ids:
                    raise ValueError(f"unrecognized camera in official track input: {camera}")
                if camera not in physical_marker_groups:
                    raise ValueError(f"no physical marker group declared for camera: {camera}")
                governed_expected_id = int(expected_tag_ids[camera])
                marker_group = physical_marker_groups[camera]
                condition = row["condition"]
                observation_key = (condition, camera)
                frame_idx = int(row["frame_idx"])
                frame_key = (condition, camera, frame_idx)
                if frame_key in seen_frame_keys:
                    raise ValueError(f"duplicate frame identity: {frame_key}")
                previous_frame = last_frame_by_stream.get(observation_key)
                if previous_frame is not None and frame_idx <= previous_frame:
                    raise ValueError(
                        f"non-increasing frame order for {condition}/{camera}: "
                        f"{previous_frame} then {frame_idx}"
                    )
                seen_frame_keys.add(frame_key)
                last_frame_by_stream[observation_key] = frame_idx
                if observation_ids is not None and observation_key not in observation_ids:
                    raise ValueError(f"no observation identity for {condition}/{camera}")
                if dataset_identities is not None and condition not in dataset_identities:
                    raise ValueError(f"no dataset identity for condition: {condition}")
                source_expected_id = int(row["expected_tag_id"])
                if source_expected_id != governed_expected_id:
                    mismatches += 1

                raw_ids_seen = row["raw_ids_seen"].strip()
                if raw_ids_seen:
                    raw_ids = {int(piece) for piece in raw_ids_seen.split(";") if piece.strip()}
                    if raw_ids and raw_ids != {governed_expected_id}:
                        raise ValueError(
                            f"{camera} detector IDs {sorted(raw_ids)} disagree with governed "
                            f"mapping {governed_expected_id}"
                        )

                output_row = {field: row[field] for field in SOURCE_COLUMNS}
                dataset_id, source_relative_path = (
                    dataset_identities[condition] if dataset_identities is not None else ("", "")
                )
                output_row["observation_id"] = (
                    observation_ids[observation_key] if observation_ids is not None else ""
                )
                output_row["dataset_id"] = dataset_id
                output_row["source_relative_path"] = source_relative_path
                output_row["topic"] = f"/sony_{camera}/image_raw/compressed"
                output_row["physical_marker_group"] = marker_group
                output_row["expected_tag_id"] = str(governed_expected_id)
                output_row["rejection_reason"] = rejection_reason(row, governed_expected_id)
                writer.writerow(output_row)
                total += 1
                valid += row["valid_for_gate"].strip().lower() == "true"
                conditions.add(condition)
                cameras.add(camera)
                marker_counts[marker_group] += 1

    return ImportSummary(
        total_frames=total,
        valid_frames=valid,
        invalid_frames=total - valid,
        sha256=sha256_file(source),
        source_expected_tag_id_mismatches=mismatches,
        conditions=len(conditions),
        cameras=tuple(sorted(cameras)),
        physical_marker_groups=tuple(sorted(marker_counts)),
        rows_by_marker_group=dict(sorted(marker_counts.items())),
    )


def write_import_metadata(
    path: Path,
    *,
    source: Path,
    output: Path,
    summary: ImportSummary,
) -> None:
    record = {
        "artifact": "official_apriltag_image_plane_tracks",
        "units": "pixel",
        "metric_pose_status": "not_generated",
        "source_expected_tag_id_mismatches": summary.source_expected_tag_id_mismatches,
        "source_path": str(source),
        "source_sha256": summary.sha256,
        "output_path": str(output),
        "output_sha256": sha256_file(output),
        "total_frames": summary.total_frames,
        "valid_frames": summary.valid_frames,
        "invalid_frames_retained": summary.invalid_frames,
        "conditions": summary.conditions,
        "cameras": list(summary.cameras),
        "physical_marker_groups": list(summary.physical_marker_groups),
        "rows_by_marker_group": dict(summary.rows_by_marker_group),
        "rejection_reason_policy": "one deterministic primary reason; blank when valid",
        "integrity_checks": {
            "frame_identity_unique": True,
            "frame_order_strictly_increasing_within_stream": True,
        },
    }
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
