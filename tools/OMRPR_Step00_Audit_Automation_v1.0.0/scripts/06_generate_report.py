#!/usr/bin/env python3
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd


def markdown_table(df: pd.DataFrame) -> str:
    headers = [str(value) for value in df.columns]
    rows = [[str(value) for value in row] for row in df.itertuples(index=False)]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    head = (
        "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(headers)) + " |"
    )
    rule = "| " + " | ".join("-" * width for width in widths) + " |"
    body = [
        "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |"
        for row in rows
    ]
    return "\n".join([head, rule, *body])


def main() -> None:
    run_dir = Path(os.environ["OMRPR_RUN_DIR"])
    reports = run_dir / "reports"
    audit = pd.read_csv(reports / "topic_audit.csv")
    summary = pd.read_csv(reports / "dataset_summary.csv")
    review = pd.read_csv(reports / "static_bag_acceptance_review_v2.csv")
    gaps = pd.read_csv(reports / "static_gap_details.csv")

    unique_bags = int(audit["bag"].nunique())
    pass_count = int((audit["status"] == "PASS").sum())
    warn_count = int((audit["status"] == "WARN").sum())
    fail_count = int((audit["status"] == "FAIL").sum())
    wtt_nonpass = audit[
        audit["bag"].str.contains(r"/wtt-(?:main|5sec)/", regex=True) & (audit["status"] != "PASS")
    ]

    decisions = (
        review["acceptance_decision"]
        .value_counts()
        .rename_axis("decision")
        .reset_index(name="count")
    )
    largest = gaps.sort_values("gap_s", ascending=False).head(10)
    largest_view = (
        largest[["camera", "bag", "topic", "gap_s", "before_time_s", "is_internal"]]
        .assign(bag=lambda frame: frame["bag"].map(lambda value: Path(value).name))
        .round({"gap_s": 6, "before_time_s": 6})
    )

    text = f"""# OMRPR Step 00 Audit Report

- Run ID: `{run_dir.name}`
- Generated: `{datetime.now().astimezone().isoformat(timespec="seconds")}`
- Project: `{os.environ["OMRPR_PROJECT_ROOT"]}`
- Unique bags audited: **{unique_bags}**
- Topic rows: **{len(audit)}**
- PASS/WARN/FAIL: **{pass_count}/{warn_count}/{fail_count}**

## Dataset summary

{markdown_table(summary)}

## Wind-tunnel gate

Wind-tunnel non-PASS topic rows: **{len(wtt_nonpass)}**.

{"All `wtt-main` and `wtt-5sec` audited topics passed the configured structural and timing gates." if wtt_nonpass.empty else "One or more wind-tunnel topics require review; inspect `non_pass_records.csv`."}

## Static engineering review

{markdown_table(decisions)}

These labels are provisional engineering decisions. They do not delete or
scientifically exclude data. Lower-rate recordings must use actual timestamps,
and recordings with gaps should be analyzed using selected contiguous segments.

## Ten largest static gaps

{markdown_table(largest_view) if not largest_view.empty else "No gaps above the configured threshold were found."}

## Gate status

- Step 00A — raw bag inventory and organization: **COMPLETE**
- Step 00B — structural and timing audit: **COMPLETE**
- Step 00C — data acceptance decision: **CONDITIONALLY COMPLETE**
- Step 01 — image decode and sampling audit: **NOT STARTED**

Step 00C remains conditional because static image content has not yet been
visually decoded and checked. The ROS bags were read without modification.

## Files

- `topic_audit.csv`: exact audit snapshot used by this run.
- `dataset_summary.csv`: dataset-level counts.
- `bag_coverage.csv`: one row per audited bag.
- `non_pass_records.csv`: all WARN and FAIL topic rows.
- `static_gap_details.csv`: location of each static gap above the threshold.
- `static_segment_summary.csv`: contiguous-segment statistics.
- `static_bag_acceptance_review_v2.csv`: provisional static review table.
- `output_manifest.sha256`: report integrity hashes.
"""
    output = reports / "STEP00_AUDIT_REPORT.md"
    output.write_text(text, encoding="utf-8")
    print("\n[6/6] Final report")
    print(f"Written: {output}")


if __name__ == "__main__":
    main()
