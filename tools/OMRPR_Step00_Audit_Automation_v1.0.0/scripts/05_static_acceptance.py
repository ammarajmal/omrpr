#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


def decision(row: pd.Series) -> str:
    fps = float(row["fps"])
    max_gap = float(row["max_gap_s"])
    nonmono = int(row["non_monotonic_intervals"])
    duplicates = int(row["duplicate_timestamps"])

    if nonmono > 0 or duplicates > 0:
        return "REJECT_TIMESTAMP_INTEGRITY"
    if max_gap > 0.5:
        return "REVIEW_LONG_GAP"
    if 25.0 <= fps <= 40.0 and max_gap <= 0.1:
        return "ACCEPT_LOWER_RATE_PENDING_IMAGE_CHECK"
    if 59.0 <= fps <= 61.0 and max_gap <= 0.1:
        return "ACCEPT_AS_RECORDED"
    if max_gap <= 0.5:
        return "ACCEPT_AFTER_SEGMENT_SELECTION"
    return "MANUAL_REVIEW"


def main() -> None:
    reports = Path(os.environ["OMRPR_RUN_DIR"]) / "reports"
    audit = pd.read_csv(reports / "topic_audit.csv")
    segments = pd.read_csv(reports / "static_segment_summary.csv")
    static = audit[audit["bag"].astype(str).str.contains("/static/", regex=False)].copy()

    static["filename"] = static["bag"].map(lambda value: Path(value).name)
    static["camera"] = static["bag"].str.extract(r"/static/(cam[123])/")
    static["acceptance_decision"] = static.apply(decision, axis=1)

    segment_fields = [
        "bag",
        "topic",
        "gaps_over_threshold",
        "segment_count",
        "longest_segment_frames",
        "longest_segment_duration_s",
    ]
    review = static.merge(segments[segment_fields], on=["bag", "topic"], how="left")
    columns = [
        "camera",
        "filename",
        "topic",
        "count",
        "duration_s",
        "fps",
        "mean_dt_s",
        "median_dt_s",
        "max_gap_s",
        "gaps_over_25ms",
        "gaps_over_threshold",
        "segment_count",
        "longest_segment_frames",
        "longest_segment_duration_s",
        "non_monotonic_intervals",
        "duplicate_timestamps",
        "status",
        "reasons",
        "acceptance_decision",
        "bag",
    ]
    review = review[columns].sort_values(["camera", "filename", "topic"])
    output = reports / "static_bag_acceptance_review_v2.csv"
    review.to_csv(output, index=False)

    print("\n[5/6] Static acceptance review")
    print(review["acceptance_decision"].value_counts().to_string())
    print(f"Written: {output}")


if __name__ == "__main__":
    main()
