#!/usr/bin/env python3
"""Hash the canonical Paper 2 WTT bags without modifying raw data."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/source/camera/rosbag/wtt-main"
TARGET = ROOT / "configs/dataset-identity-manifest.csv"
FIELDS = [
    "dataset_id",
    "condition_id",
    "relative_source_path",
    "size_bytes",
    "sha256",
    "analysis_role",
    "identity_status",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def condition_roles() -> dict[str, str]:
    with (ROOT / "configs/conditions.csv").open(newline="", encoding="utf-8") as stream:
        return {row["condition_id"]: row["analysis_role"] for row in csv.DictReader(stream)}


def main() -> None:
    if not RAW.is_dir():
        raise SystemExit(f"missing canonical WTT root: {RAW}")
    roles = condition_roles()
    bags = sorted(RAW.glob("*/*.bag"))
    if len(bags) != 21:
        raise SystemExit(f"expected 21 canonical WTT bags, found {len(bags)}")

    rows = []
    for index, bag in enumerate(bags, 1):
        condition_id = bag.parent.name
        if condition_id not in roles:
            raise SystemExit(f"unregistered condition directory: {condition_id}")
        print(f"[{index:02d}/{len(bags)}] hashing {condition_id}", flush=True)
        rows.append(
            {
                "dataset_id": f"camera-wtt-main-{condition_id}",
                "condition_id": condition_id,
                "relative_source_path": bag.relative_to(ROOT / "data/raw/source").as_posix(),
                "size_bytes": bag.stat().st_size,
                "sha256": sha256(bag),
                "analysis_role": roles[condition_id],
                "identity_status": "frozen_sha256",
            }
        )

    with TARGET.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} frozen identities to {TARGET}")


if __name__ == "__main__":
    main()
