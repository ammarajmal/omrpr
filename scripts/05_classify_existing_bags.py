#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

PATTERN = re.compile(r"(e(?:[0-9]|1[0-9]|20)_[0-9]+rpm)", re.IGNORECASE)


def classify(path: Path) -> tuple[str, str]:
    lower = str(path).lower()
    match = PATTERN.search(path.name)
    condition = match.group(1).lower() if match else "unmapped"
    if "5sec" in lower or "5_sec" in lower:
        return "wtt-5sec", condition
    if "static" in lower:
        for cam in ("cam1", "cam2", "cam3"):
            if cam in lower:
                return f"static/{cam}", condition
        return "static/unmapped-camera", condition
    if match:
        return "wtt-main", condition
    return "unclassified", condition


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--output", type=Path, default=Path("bag-classification.csv"))
    args = ap.parse_args()
    rows = []
    for bag in sorted(args.source.rglob("*.bag")):
        category, condition = classify(bag)
        rows.append((str(bag), bag.stat().st_size, category, condition, "review"))
    with args.output.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["source", "size_bytes", "category", "condition_id", "review_status"])
        wr.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
