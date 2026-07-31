from __future__ import annotations

import argparse
from pathlib import Path

from omrpr_analysis.image_audit import audit_tree


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded OMRPR ROS image audit")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples-per-stream", type=int, default=12)
    args = parser.parse_args()
    rows = audit_tree(args.root.resolve(), args.output.resolve(), args.samples_per_stream)
    failures = sum(not row.decode_ok for row in rows)
    print(f"Sampled frames: {len(rows)}")
    print(f"Decode failures: {failures}")
    print(f"Output: {args.output.resolve()}")
    if failures:
        raise SystemExit(5)


if __name__ == "__main__":
    main()
