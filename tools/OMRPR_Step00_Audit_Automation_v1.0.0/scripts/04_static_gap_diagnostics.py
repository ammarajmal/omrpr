#!/usr/bin/env python3
from __future__ import annotations

import os
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
from rosbags.highlevel import AnyReader


def camera_from_path(path: Path) -> str:
    for part in path.parts:
        if part in {"cam1", "cam2", "cam3"}:
            return part
    return "unknown"


def main() -> None:
    root = (
        Path(os.environ["OMRPR_PROJECT_ROOT"]) / "data/raw/source/camera/rosbag/static"
    ).resolve()
    reports = Path(os.environ["OMRPR_RUN_DIR"]) / "reports"
    threshold = float(os.environ.get("OMRPR_GAP_THRESHOLD_S", "0.025"))

    print("\n[4/6] Static gap and contiguous-segment diagnostics")
    gap_rows: list[dict[str, object]] = []
    segment_rows: list[dict[str, object]] = []

    for bag in sorted(root.rglob("*.bag")):
        with AnyReader([bag]) as reader:
            connections = [
                connection
                for connection in reader.connections
                if connection.topic.endswith("/image_raw")
            ]
            for connection in connections:
                timestamps = np.fromiter(
                    (timestamp for _, timestamp, _ in reader.messages(connections=[connection])),
                    dtype=np.int64,
                )
                if timestamps.size < 2:
                    segment_rows.append(
                        {
                            "bag": str(bag),
                            "camera": camera_from_path(bag),
                            "topic": connection.topic,
                            "messages": int(timestamps.size),
                            "duration_s": 0.0,
                            "gaps_over_threshold": 0,
                            "segment_count": int(timestamps.size > 0),
                            "longest_segment_frames": int(timestamps.size),
                            "longest_segment_duration_s": 0.0,
                        }
                    )
                    continue

                relative = (timestamps - timestamps[0]).astype(np.float64) / 1e9
                deltas = np.diff(relative)
                gap_indices = np.flatnonzero(deltas > threshold)
                boundaries = np.concatenate(([0], gap_indices + 1, [timestamps.size]))
                segment_lengths = np.diff(boundaries)
                segment_durations = np.array(
                    [
                        relative[end - 1] - relative[start] if end > start else 0.0
                        for start, end in pairwise(boundaries)
                    ]
                )

                for rank, index in enumerate(
                    gap_indices[np.argsort(deltas[gap_indices])[::-1]], start=1
                ):
                    gap_rows.append(
                        {
                            "bag": str(bag),
                            "camera": camera_from_path(bag),
                            "topic": connection.topic,
                            "gap_rank_largest_first": rank,
                            "before_frame_index": int(index),
                            "after_frame_index": int(index + 1),
                            "before_time_s": float(relative[index]),
                            "after_time_s": float(relative[index + 1]),
                            "gap_s": float(deltas[index]),
                            "is_internal": bool(index > 0 and index + 1 < timestamps.size - 1),
                        }
                    )

                segment_rows.append(
                    {
                        "bag": str(bag),
                        "camera": camera_from_path(bag),
                        "topic": connection.topic,
                        "messages": int(timestamps.size),
                        "duration_s": float(relative[-1]),
                        "gaps_over_threshold": int(gap_indices.size),
                        "segment_count": int(len(boundaries) - 1),
                        "longest_segment_frames": int(segment_lengths.max()),
                        "longest_segment_duration_s": float(segment_durations.max()),
                    }
                )

    gap_columns = [
        "bag",
        "camera",
        "topic",
        "gap_rank_largest_first",
        "before_frame_index",
        "after_frame_index",
        "before_time_s",
        "after_time_s",
        "gap_s",
        "is_internal",
    ]
    gaps = pd.DataFrame(gap_rows, columns=gap_columns)
    segments = pd.DataFrame(segment_rows)
    gaps.to_csv(reports / "static_gap_details.csv", index=False)
    segments.to_csv(reports / "static_segment_summary.csv", index=False)
    print(f"Static image streams: {len(segments)}")
    print(f"Gaps over {threshold:.6f} s: {len(gaps)}")


if __name__ == "__main__":
    main()
