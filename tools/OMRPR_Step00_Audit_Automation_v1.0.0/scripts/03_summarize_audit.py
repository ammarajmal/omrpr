#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

REQUIRED = {
    "bag",
    "topic",
    "status",
    "reasons",
    "fps",
    "max_gap_s",
    "duplicate_timestamps",
    "non_monotonic_intervals",
}


def dataset_group(bag: str) -> str:
    if "/wtt-main/" in bag:
        return "wtt-main"
    if "/wtt-5sec/" in bag:
        return "wtt-5sec"
    if "/static/cam1/" in bag:
        return "static-cam1"
    if "/static/cam2/" in bag:
        return "static-cam2"
    if "/static/cam3/" in bag:
        return "static-cam3"
    return "unknown"


def main() -> None:
    run_dir = Path(os.environ["OMRPR_RUN_DIR"])
    reports = run_dir / "reports"
    source = reports / "topic_audit.csv"
    expected_bags = int(os.environ["OMRPR_EXPECTED_BAGS"])

    print("\n[3/6] Dataset and coverage summary")
    df = pd.read_csv(source)
    missing = REQUIRED.difference(df.columns)
    if missing:
        raise SystemExit(f"Audit CSV lacks columns: {sorted(missing)}")

    df["dataset_group"] = df["bag"].astype(str).map(dataset_group)
    if (df["dataset_group"] == "unknown").any():
        unknown = sorted(df.loc[df["dataset_group"] == "unknown", "bag"].unique())
        raise SystemExit(f"Unknown dataset paths in audit: {unknown}")

    summary = (
        df.groupby(["dataset_group", "status"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["PASS", "WARN", "FAIL"], fill_value=0)
    )
    summary["TOTAL_TOPIC_ROWS"] = summary[["PASS", "WARN", "FAIL"]].sum(axis=1)
    summary = summary.join(df.groupby("dataset_group")["bag"].nunique().rename("UNIQUE_BAGS"))
    summary = summary.reset_index()
    summary.to_csv(reports / "dataset_summary.csv", index=False)

    coverage = (
        df.groupby(["dataset_group", "bag"], as_index=False)
        .agg(
            TOPIC_ROWS=("topic", "size"),
            PASS=("status", lambda values: int((values == "PASS").sum())),
            WARN=("status", lambda values: int((values == "WARN").sum())),
            FAIL=("status", lambda values: int((values == "FAIL").sum())),
        )
        .sort_values(["dataset_group", "bag"])
    )
    coverage.to_csv(reports / "bag_coverage.csv", index=False)

    non_pass = df.loc[df["status"] != "PASS"].copy()
    non_pass.to_csv(reports / "non_pass_records.csv", index=False)

    unique_bags = int(df["bag"].nunique())
    if unique_bags != expected_bags:
        raise SystemExit(
            f"Coverage failure: audited {unique_bags} unique bags; expected {expected_bags}"
        )

    wtt_nonpass = non_pass[non_pass["dataset_group"].isin(["wtt-main", "wtt-5sec"])]
    print(summary.to_string(index=False))
    print(f"Unique bags audited: {unique_bags}")
    print(f"WTT non-PASS rows: {len(wtt_nonpass)}")


if __name__ == "__main__":
    main()
