#!/usr/bin/env python3
"""Import verified official-AprilTag corner tracks as the Paper 2 primary observable."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from omrpr_analysis.observation_control import load_control
from omrpr_analysis.official_tracks import import_official_tracks, write_import_metadata
from omrpr_analysis.paths import ProjectPaths

DEFAULT_SOURCE = Path(
    "/mnt/space/adev/projects/active/structural-vision-research/"
    "evidence/fresh_quality_scores/per_frame_detections.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs/apriltag-detections/official-v3.4.5")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    paths = ProjectPaths.discover()
    control = load_control(paths.root / "configs/observation-control.yaml")
    expected_ids = {
        camera: int(observation["expected_tag_id"])
        for camera, observation in control["camera_observations"].items()
    }
    marker_groups = {
        camera: str(observation["physical_location"])
        for camera, observation in control["camera_observations"].items()
    }
    with (paths.root / "configs/observation-manifest.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        observation_ids = {
            (row["condition_id"], row["instrument"]): row["observation_id"]
            for row in csv.DictReader(stream)
            if row["campaign"] == "camera-2025-10"
        }
    with (paths.root / "configs/dataset-identity-manifest.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        dataset_identities = {
            row["condition_id"]: (row["dataset_id"], row["relative_source_path"])
            for row in csv.DictReader(stream)
            if row["dataset_id"].startswith("camera-wtt-main-")
        }
    destination = args.output_dir / "per_frame_tracks.csv"
    summary = import_official_tracks(
        args.source,
        destination,
        expected_ids,
        marker_groups,
        observation_ids,
        dataset_identities,
    )
    metadata = destination.with_name("import_metadata.json")
    write_import_metadata(metadata, source=args.source, output=destination, summary=summary)
    print(
        f"imported {summary.total_frames} frames "
        f"({summary.valid_frames} gate-valid; {summary.invalid_frames} retained invalid)"
    )
    print(destination)
    print(metadata)


if __name__ == "__main__":
    main()
