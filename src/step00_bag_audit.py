"""
Step 00 — ROS Bag Audit
=======================
Purpose:  Extract and report metadata from a single ROS 1 bag file.
Inputs:   Path to a .bag file (--bag argument)
Outputs:  Terminal summary + results/step00/<bag_name>_audit.json
Accepts:  FPS 59-61 Hz per camera topic, no frame gap > 0.1 s
Limits:   Does not decode image content — metadata only.
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict
import numpy as np
from rosbags.rosbag1 import Reader


def parse_args():
    parser = argparse.ArgumentParser(description="Step 00 — ROS Bag Audit")
    parser.add_argument("--bag", required=True, help="Path to .bag file")
    return parser.parse_args()


def audit_bag(bag_path: Path) -> dict:
    """
    Open a bag file and extract per-topic metadata.
    Returns a dict with topic stats.
    """
    topic_timestamps = defaultdict(list)
    topic_msgtypes = {}

    with Reader(bag_path) as reader:
        # --- FILL THIS IN ---
        # 1. Find bag_start_ns: the minimum timestamp across ALL messages
        # 2. For each message, record its normalized timestamp under its topic
        # 3. Record the msgtype for each topic
        # Hint: iterate with:
        #   for connection, timestamp, rawdata in reader.messages():
        # Remember: t_normalized = (timestamp - bag_start_ns) / 1e9
        pass

    # Build per-topic stats
    stats = {"bag": bag_path.name, "topics": {}}
    for topic, times in topic_timestamps.items():
        times = sorted(times)
        gaps = np.diff(times)
        duration = times[-1] - times[0] if len(times) > 1 else 0
        fps = (len(times) - 1) / duration if duration > 0 else 0
        stats["topics"][topic] = {
            "msgtype": topic_msgtypes[topic],
            "count": len(times),
            "first_s": round(times[0], 4),
            "last_s": round(times[-1], 4),
            "duration_s": round(duration, 4),
            "fps": round(fps, 2),
            "max_gap_s": round(float(np.max(gaps)), 4) if len(gaps) > 0 else 0,
        }

    # Compute skew: max spread of per-topic first timestamps
    first_timestamps = [v["first_s"] for v in stats["topics"].values()]
    stats["timestamp_skew_s"] = round(max(first_timestamps) - min(first_timestamps), 4)
    return stats


def compute_acceptance(stats: dict) -> str:
    """
    Return 'PASS', 'WARN', or 'FAIL' based on FPS and gap criteria.
    Only evaluate image topics (topics containing 'image' or 'compressed').
    """
    # --- FILL THIS IN ---
    # PASS: all image topics FPS in 59-61 Hz AND max_gap_s <= 0.1
    # WARN: FPS 55-59 or 61-65 OR one gap 0.1-0.5
    # FAIL: any image topic FPS < 55 OR any gap > 0.5
    pass


def print_report(stats: dict, acceptance: str):
    """Print a human-readable summary table."""
    print(f"\n=== BAG AUDIT: {stats['bag']} ===\n")
    header = f"{'Topic':<45} {'Count':>6} {'FPS':>6} {'Duration':>10} {'First':>8} {'Last':>8} {'MaxGap':>8}"
    print(header)
    print("-" * len(header))
    for topic, t in stats["topics"].items():
        print(
            f"{topic:<45} {t['count']:>6} {t['fps']:>6.2f} "
            f"{t['duration_s']:>10.2f} {t['first_s']:>8.3f} "
            f"{t['last_s']:>8.3f} {t['max_gap_s']:>8.4f}"
        )
    print(f"\nTimestamp skew across topics: {stats['timestamp_skew_s']:.4f} s")
    print(f"Acceptance: {acceptance}\n")


def save_json(stats: dict, acceptance: str, bag_path: Path):
    """Save audit results as JSON to results/step00/."""
    # --- FILL THIS IN ---
    # Save to: results/step00/<bag_stem>_audit.json
    # Include acceptance in the saved dict
    # Hint: use Path.mkdir(parents=True, exist_ok=True) to create the folder
    pass


def main():
    args = parse_args()
    bag_path = Path(args.bag)
    if not bag_path.exists():
        raise FileNotFoundError(f"Bag file not found: {bag_path}")
    stats = audit_bag(bag_path)
    acceptance = compute_acceptance(stats)
    print_report(stats, acceptance)
    save_json(stats, acceptance, bag_path)


if __name__ == "__main__":
    main()