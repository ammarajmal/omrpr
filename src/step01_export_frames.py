"""
Step 01 — Frame Export
======================
Purpose:  Extract PNG frames and timestamps from a ROS 1 bag file.
Inputs:   Path to a .bag file (--bag argument) or --all flag for all WTT bags.
          config/pipeline_config.yaml
Outputs:  results/step01/{condition}/{cam}/frame_XXXXXX.png
          results/step01/{condition}/{cam}/timestamps.csv
          results/step01/{condition}/{cam}/meta.json
          results/step01/{condition}/{cam}/decode_failures.txt  (only if failures occur)
Accepts:  Frame count matches audit, timestamps monotonically increasing,
          no gaps > 0.1 s, all PNGs non-zero size.
Limits:   Assumes compressed image topics (sensor_msgs/CompressedImage).
          Requires rosbags >= 0.11.0 (new typestore API).
"""

import argparse
import csv
import json
from pathlib import Path
import numpy as np
import cv2
import yaml
from collections import defaultdict
from rosbags.rosbag1 import Reader
from rosbags.typesys import Stores, get_typestore


# Typestore is created once at module level (not inside the loop)
TYPESTORE = get_typestore(Stores.ROS1_NOETIC)


def parse_args():
    parser = argparse.ArgumentParser(description="Step 01 — Frame Export")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bag", help="Path to a single .bag file")
    group.add_argument("--all", action="store_true",
                       help="Process all bags found in paths.wtt_dir")
    parser.add_argument("--config", default="config/pipeline_config.yaml")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_condition_name(bag_path: Path) -> str:
    """
    Extract condition name from bag path.
    e.g. data/WTT/e7_90rpm/e7_90rpm_run1.bag  →  'e7_90rpm'
    The condition is the parent folder name, NOT the bag file stem,
    because future runs (run2, run3) will live in the same folder.
    """
    return bag_path.parent.name


def decode_image(image_bytes: bytes) -> np.ndarray | None:
    """
    Decode compressed JPEG/PNG bytes to a BGR numpy array.
    Returns None if decoding fails.
    """
    buf = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return img  # cv2.imdecode already returns None on failure


def export_bag(bag_path: Path, config: dict) -> tuple[dict, str]:
    """
    Main extraction loop for one bag file.
    Returns a summary dict keyed by camera name.
    """
    condition = get_condition_name(bag_path)
    results_dir = Path(config["paths"]["results_dir"])
    cam_config = config["cameras"]

    # Build reverse map: topic → cam_name
    topic_to_cam = {v["topic"]: k for k, v in cam_config.items()}

    # Create output directories
    for cam_name in cam_config:
        out_dir = results_dir / "step01" / condition / cam_name
        out_dir.mkdir(parents=True, exist_ok=True)

    # Pass 1: collect all relevant timestamps to find bag_start_ns
    # We open the bag once to find the global start time so that all
    # normalised timestamps are relative to the earliest message in the bag.
    # This cannot be done in a single pass because we need bag_start_ns
    # before we can normalise any individual timestamp.
    all_timestamps = []
    with Reader(bag_path) as reader:
        for connection, timestamp, _ in reader.messages():
            if connection.topic in topic_to_cam:
                all_timestamps.append(timestamp)

    if not all_timestamps:
        raise RuntimeError(f"No matching topics found in {bag_path}. "
                           f"Check camera topics in pipeline_config.yaml.")

    bag_start_ns = min(all_timestamps)

    # Pass 2: decode and save frames
    frame_counters  = defaultdict(int)   # cam_name → next frame index
    cam_timestamps  = defaultdict(list)  # cam_name → [timestamp_s, ...]
    decode_failures = defaultdict(list)  # cam_name → [frame_idx, ...]

    with Reader(bag_path) as reader:
        for connection, timestamp, rawdata in reader.messages():
            if connection.topic not in topic_to_cam:
                continue

            cam_name  = topic_to_cam[connection.topic]
            frame_idx = frame_counters[cam_name]
            t_s       = (timestamp - bag_start_ns) / 1e9

            msg         = TYPESTORE.deserialize_ros1(rawdata, connection.msgtype)
            image_bytes = bytes(msg.data)

            img = decode_image(image_bytes)
            if img is None:
                print(f"  [WARN] decode failed: {cam_name} frame {frame_idx:06d} "
                      f"@ t={t_s:.4f}s — skipping")
                decode_failures[cam_name].append(frame_idx)
                frame_counters[cam_name] += 1
                continue

            out_path = (results_dir / "step01" / condition / cam_name
                        / f"frame_{frame_idx:06d}.png")
            cv2.imwrite(str(out_path), img)

            cam_timestamps[cam_name].append(t_s)
            frame_counters[cam_name] += 1

    # Write per-camera outputs
    for cam_name, cam_cfg in cam_config.items():
        cam_dir = results_dir / "step01" / condition / cam_name

        # timestamps.csv — columns: frame_idx, timestamp_s
        ts_path = cam_dir / "timestamps.csv"
        with open(ts_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["frame_idx", "timestamp_s"])
            for idx, t_s in enumerate(cam_timestamps[cam_name]):
                writer.writerow([idx, f"{t_s:.9f}"])

        # meta.json — traceability record for the paper
        meta = {
            "cam":         cam_name,
            "topic":       cam_cfg["topic"],
            "condition":   condition,
            "bag":         str(bag_path),
            "frame_count": len(cam_timestamps[cam_name]),
        }
        with open(cam_dir / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)

        # decode_failures.txt — only written if there were failures
        failures = decode_failures.get(cam_name, [])
        if failures:
            with open(cam_dir / "decode_failures.txt", "w") as f:
                f.write("\n".join(str(i) for i in failures) + "\n")

    # Build summary
    summary = {}
    for cam_name in cam_config:
        ts_list = cam_timestamps[cam_name]
        ts_arr  = np.array(ts_list, dtype=np.float64)
        gaps    = np.diff(ts_arr)
        n_fail  = len(decode_failures.get(cam_name, []))

        summary[cam_name] = {
            "frame_count":     len(ts_list),
            "max_gap_s":       round(float(np.max(gaps)), 4) if len(gaps) > 0 else 0.0,
            "monotonic":       bool(np.all(gaps > 0)),
            "decode_failures": n_fail,
        }

    return summary, condition


def print_summary(summary: dict, condition: str):
    print(f"\n=== FRAME EXPORT: {condition} ===\n")
    all_ok = True
    for cam, s in summary.items():
        gap_ok   = s["max_gap_s"] <= 0.1
        status   = "OK" if (s["monotonic"] and gap_ok and s["decode_failures"] == 0) else "WARN"
        if status == "WARN":
            all_ok = False
        fail_str = f" | decode_failures={s['decode_failures']}" if s["decode_failures"] > 0 else ""
        print(f"  {cam}: {s['frame_count']:5d} frames | "
              f"max_gap={s['max_gap_s']:.4f}s | "
              f"monotonic={s['monotonic']} | {status}{fail_str}")

    print()
    if all_ok:
        print("  ✓ All cameras PASS")
    else:
        print("  ✗ One or more cameras have warnings — check decode_failures.txt")


def main():
    args   = parse_args()
    config = load_config(args.config)

    if args.all:
        wtt_dir   = Path(config["paths"]["wtt_dir"])
        bag_paths = sorted(wtt_dir.glob("**/*.bag"))
        if not bag_paths:
            raise FileNotFoundError(f"No .bag files found under {wtt_dir}")
        print(f"Found {len(bag_paths)} bag(s) — processing all.\n")
    else:
        bag_paths = [Path(args.bag)]

    for bag_path in bag_paths:
        if not bag_path.exists():
            raise FileNotFoundError(f"Bag not found: {bag_path}")
        summary, condition = export_bag(bag_path, config)
        print_summary(summary, condition)


if __name__ == "__main__":
    main()
