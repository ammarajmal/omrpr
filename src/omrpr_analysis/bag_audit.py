from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import numpy as np
import numpy.typing as npt
from rosbags.interfaces import Connection
from rosbags.rosbag1 import Reader

type Nanoseconds = int
type AuditValue = str | int | float
type AuditRow = dict[str, AuditValue]


@dataclass(frozen=True)
class TopicAudit:
    """Timing-quality summary for one image topic in one ROS 1 bag."""

    bag: str
    topic: str
    count: int
    duration_s: float
    fps: float
    mean_dt_s: float
    median_dt_s: float
    max_gap_s: float
    gaps_over_25ms: int
    first_s: float
    last_s: float
    non_monotonic_intervals: int
    duplicate_timestamps: int
    status: str
    reasons: str


def classify(fps: float, max_gap_s: float) -> tuple[str, list[str]]:
    """Classify topic timing quality using the OMRPR timing gates."""

    reasons: list[str] = []

    if fps < 55.0:
        reasons.append("fps below 55 Hz")

    if max_gap_s > 0.5:
        reasons.append("max gap over 0.5 s")

    if reasons:
        return "FAIL", reasons

    status = "PASS"

    if not 59.0 <= fps <= 61.0:
        status = "WARN"
        reasons.append("fps outside 59-61 Hz")

    if max_gap_s > 0.1:
        status = "WARN"
        reasons.append("max gap over 0.1 s")

    return status, reasons


def _image_connections(reader: Reader) -> list[Connection]:
    """Return image connections relevant to the OMRPR camera bags."""

    return [connection for connection in reader.connections if "image_raw" in connection.topic]


def _audit_short_topic(
    path: Path,
    topic: str,
    stamps: npt.NDArray[np.int64],
    global_start_ns: Nanoseconds,
) -> TopicAudit:
    """Create a failed audit result for a topic with fewer than two frames."""

    first_s = float((int(stamps[0]) - global_start_ns) / 1e9) if stamps.size == 1 else 0.0

    return TopicAudit(
        bag=str(path),
        topic=topic,
        count=int(stamps.size),
        duration_s=0.0,
        fps=0.0,
        mean_dt_s=0.0,
        median_dt_s=0.0,
        max_gap_s=0.0,
        gaps_over_25ms=0,
        first_s=first_s,
        last_s=first_s,
        non_monotonic_intervals=0,
        duplicate_timestamps=0,
        status="FAIL",
        reasons="fewer than two frames",
    )


def _audit_topic(
    path: Path,
    topic: str,
    values: list[Nanoseconds],
    global_start_ns: Nanoseconds,
) -> TopicAudit:
    """Calculate timing statistics for one topic."""

    stamps: npt.NDArray[np.int64] = np.asarray(values, dtype=np.int64)

    if stamps.size < 2:
        return _audit_short_topic(
            path=path,
            topic=topic,
            stamps=stamps,
            global_start_ns=global_start_ns,
        )

    time_s: npt.NDArray[np.float64] = (stamps.astype(np.float64) - float(global_start_ns)) / 1e9

    gaps_s: npt.NDArray[np.float64] = np.diff(time_s)

    duration_s = float(time_s[-1] - time_s[0])

    fps = float((time_s.size - 1) / duration_s) if duration_s > 0.0 else 0.0

    mean_dt_s = float(np.mean(gaps_s))
    median_dt_s = float(np.median(gaps_s))
    max_gap_s = float(np.max(gaps_s))

    gaps_over_25ms = int(np.count_nonzero(gaps_s > 0.025))
    non_monotonic_intervals = int(np.count_nonzero(gaps_s < 0.0))
    duplicate_timestamps = int(np.count_nonzero(gaps_s == 0.0))

    status, reasons = classify(fps, max_gap_s)

    if non_monotonic_intervals > 0:
        status = "FAIL"
        reasons.append(f"{non_monotonic_intervals} non-monotonic timestamp intervals")

    if duplicate_timestamps > 0:
        if status == "PASS":
            status = "WARN"

        reasons.append(f"{duplicate_timestamps} duplicate timestamp intervals")

    return TopicAudit(
        bag=str(path),
        topic=topic,
        count=int(time_s.size),
        duration_s=duration_s,
        fps=fps,
        mean_dt_s=mean_dt_s,
        median_dt_s=median_dt_s,
        max_gap_s=max_gap_s,
        gaps_over_25ms=gaps_over_25ms,
        first_s=float(time_s[0]),
        last_s=float(time_s[-1]),
        non_monotonic_intervals=non_monotonic_intervals,
        duplicate_timestamps=duplicate_timestamps,
        status=status,
        reasons="; ".join(reasons),
    )


def audit_bag(path: Path) -> list[TopicAudit]:
    """Audit all image topics in one ROS 1 bag."""

    timestamps: dict[str, list[Nanoseconds]] = {}
    global_start_ns: Nanoseconds | None = None

    with Reader(path) as reader:
        image_connections = _image_connections(reader)

        for connection in image_connections:
            timestamps.setdefault(connection.topic, [])

        for connection, timestamp_ns, _ in reader.messages(connections=image_connections):
            if global_start_ns is None:
                global_start_ns = timestamp_ns
            else:
                global_start_ns = min(global_start_ns, timestamp_ns)

            timestamps[connection.topic].append(timestamp_ns)

    if global_start_ns is None:
        return []

    results: list[TopicAudit] = []

    for topic, values in sorted(timestamps.items()):
        results.append(
            _audit_topic(
                path=path,
                topic=topic,
                values=values,
                global_start_ns=global_start_ns,
            )
        )

    return results


def audit_tree(root: Path, output: Path) -> Path:
    """Audit every ROS 1 bag below a directory and write a CSV report."""

    if not root.exists():
        raise FileNotFoundError(f"Bag root does not exist: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"Bag root is not a directory: {root}")

    bag_paths = sorted(root.rglob("*.bag"))
    rows: list[AuditRow] = []

    for bag_path in bag_paths:
        for audit in audit_bag(bag_path):
            row: AuditRow = asdict(audit)
            rows.append(row)

    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [field.name for field in fields(TopicAudit)]

    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)

    return output
