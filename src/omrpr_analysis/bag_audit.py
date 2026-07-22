from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from rosbags.rosbag1 import Reader


@dataclass(frozen=True)
class TopicAudit:
    bag: str
    topic: str
    count: int
    duration_s: float
    fps: float
    max_gap_s: float
    gaps_over_25ms: int
    first_s: float
    status: str
    reasons: str


def classify(fps: float, max_gap: float) -> tuple[str, list[str]]:
    reasons = []
    if fps < 55.0 or max_gap > 0.5:
        return "FAIL", ["hard timing gate"]
    status = "PASS"
    if not 59.0 <= fps <= 61.0:
        status = "WARN"
        reasons.append("fps outside 59-61 Hz")
    if max_gap > 0.1:
        status = "WARN"
        reasons.append("max gap over 0.1 s")
    return status, reasons


def audit_bag(path: Path) -> list[TopicAudit]:
    with Reader(path) as reader:
        image_connections = [c for c in reader.connections if "image_raw" in c.topic]
        timestamps = {c.topic: [] for c in image_connections}
        global_start: int | None = None
        for connection, timestamp, _ in reader.messages(connections=image_connections):
            global_start = timestamp if global_start is None else min(global_start, timestamp)
            timestamps[connection.topic].append(timestamp)
    if global_start is None:
        return []
    results = []
    for topic, values in timestamps.items():
        stamps = np.asarray(values, dtype=np.int64)
        if len(stamps) < 2:
            results.append(
                TopicAudit(
                    str(path),
                    topic,
                    len(stamps),
                    0.0,
                    0.0,
                    0.0,
                    0,
                    0.0,
                    "FAIL",
                    "fewer than two frames",
                )
            )
            continue
        t = (stamps - global_start) / 1e9
        gaps = np.diff(t)
        duration = float(t[-1] - t[0])
        fps = float((len(t) - 1) / duration) if duration > 0 else 0.0
        max_gap = float(gaps.max())
        status, reasons = classify(fps, max_gap)
        results.append(
            TopicAudit(
                str(path),
                topic,
                len(t),
                duration,
                fps,
                max_gap,
                int(np.sum(gaps > 0.025)),
                float(t[0]),
                status,
                "; ".join(reasons),
            )
        )
    return results


def audit_tree(root: Path, output: Path) -> Path:
    rows = []
    for bag in sorted(root.rglob("*.bag")):
        rows.extend(asdict(item) for item in audit_bag(bag))
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [f.name for f in TopicAudit.__dataclass_fields__.values()]
    with output.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)
    return output
