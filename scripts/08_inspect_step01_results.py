#!/usr/bin/env python3
"""Inspect a completed Step 01 run without assuming obsolete column names."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd


def newest_run(project_root: Path) -> Path:
    runs_root = project_root / "outputs" / "image-audit-runs"
    candidates = [path for path in runs_root.iterdir() if path.is_dir() and path.name != "latest"]
    if not candidates:
        raise SystemExit(f"ERROR: No Step 01 runs found under {runs_root}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve()
    run_dir = args.run_dir.expanduser().resolve() if args.run_dir else newest_run(project_root)
    reports = run_dir / "reports"
    summary_path = reports / "stream_summary.csv"
    if not summary_path.is_file():
        raise SystemExit(f"ERROR: Missing completed-run file: {summary_path}")

    frame = pd.read_csv(summary_path)
    status_column = next(
        (name for name in ("status", "automated_status") if name in frame.columns),
        None,
    )
    if status_column is None:
        raise SystemExit("ERROR: stream_summary.csv has neither 'status' nor 'automated_status'.")

    print(f"Run directory: {run_dir}")
    print(f"Streams: {len(frame)}")
    print("\nAutomated status counts:")
    print(frame[status_column].value_counts(dropna=False).to_string())

    review = frame.loc[frame[status_column].eq("REVIEW")].copy()
    print("\nReasons for REVIEW:")
    if "reasons" in review.columns:
        print(review["reasons"].value_counts(dropna=False).to_string())
    else:
        print("No reasons column present.")

    output = reports / "streams_requiring_review.csv"
    review.to_csv(output, index=False)
    print(f"\nSaved {len(review)} REVIEW streams to:\n{output}")

    manual_path = reports / "manual_review.csv"
    if manual_path.is_file():
        manual = pd.read_csv(manual_path)
        candidate_columns = [
            name
            for name in manual.columns
            if any(token in name.lower() for token in ("decision", "status", "review"))
        ]
        print(f"\nManual-review rows: {len(manual)}")
        for name in candidate_columns:
            counts = Counter(
                "<BLANK>" if pd.isna(value) or str(value).strip() == "" else str(value)
                for value in manual[name]
            )
            print(f"\nManual values [{name}]:")
            for value, count in counts.most_common():
                print(f"{value}: {count}")


if __name__ == "__main__":
    main()
