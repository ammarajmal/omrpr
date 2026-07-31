from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from rosbags.highlevel import AnyReader

from omrpr_analysis.paths import ProjectPaths

RATIONALE = (
    "CameraInfo values are republished from a static camera_info_manager-style YAML, "
    "not derived fresh for this dataset. LEGACY_ANALYSIS_REPORT.md section 1 documents "
    "this exact intrinsics source as physically implausible (cross-camera disagreement, "
    "focal length far outside a plausible range for the lens). AGENTS.md forbids "
    "importing legacy camera intrinsics; Step 02 remains blocked pending physical "
    "calibration-target images. The wtt_experiment and static_test profiles below are "
    "two distinct legacy calibration artifacts (confirmed by an exact numeric match to "
    "LEGACY_ANALYSIS_REPORT.md section 1's 'camera_info.yaml' and 'sony_camN_recalib.yaml' "
    "columns respectively) - do not assume one represents the other. An empirical check "
    "against a real AprilTag detection in a wtt-main e0_0rpm frame (2026-07-31, distance "
    "~1.5m) found the wtt_experiment profile's implied focal length within 7-16% of what "
    "the image shows (ratios 0.84x-1.07x across cam1/cam2/cam3) - closer than the general "
    "'physically implausible' finding in the legacy report suggested, but still a "
    "provisional prior only, to be corrected via the laser-displacement discrepancy loop "
    "(docs/DATA_PLACEMENT.md tunnel-a-2024) before any downstream number is treated as "
    "final."
)


@dataclass(frozen=True)
class CameraInfoSample:
    bag: str
    frame_id: str
    width: int
    height: int
    distortion_model: str
    k: list[float]
    d: list[float]
    r: list[float]
    p: list[float]


def read_camera_info(bag: Path, topic: str) -> CameraInfoSample | None:
    with AnyReader([bag]) as reader:
        connections = [c for c in reader.connections if c.topic == topic]
        if not connections:
            return None
        for connection, _, raw in reader.messages(connections=connections):
            msg = reader.deserialize(raw, connection.msgtype)
            return CameraInfoSample(
                bag=str(bag),
                frame_id=msg.header.frame_id,
                width=int(msg.width),
                height=int(msg.height),
                distortion_model=msg.distortion_model,
                k=[float(v) for v in msg.K],
                d=[float(v) for v in msg.D],
                r=[float(v) for v in msg.R],
                p=[float(v) for v in msg.P],
            )
    return None


def collect_samples(bags: list[Path], cam: str) -> list[CameraInfoSample]:
    topic = f"/sony_{cam}/camera_info"
    samples: list[CameraInfoSample] = []
    for bag in bags:
        sample = read_camera_info(bag, topic)
        if sample is not None:
            samples.append(sample)
    return samples


def assert_static(samples: list[CameraInfoSample], cam: str, profile: str) -> None:
    if not samples:
        raise RuntimeError(f"No camera_info samples found for {cam}/{profile}")
    first = samples[0]
    for other in samples[1:]:
        if (
            other.k != first.k
            or other.d != first.d
            or other.distortion_model != first.distortion_model
        ):
            raise RuntimeError(
                f"{cam}/{profile}: camera_info differs across bags "
                f"({first.bag} vs {other.bag}) - provisional-prior assumption of a "
                "static per-camera-per-profile value is violated"
            )


def build_profile(samples: list[CameraInfoSample]) -> dict:
    reference = samples[0]
    return {
        "frame_id": reference.frame_id,
        "width": reference.width,
        "height": reference.height,
        "distortion_model": reference.distortion_model,
        "K": reference.k,
        "D": reference.d,
        "R": reference.r,
        "P": reference.p,
        "fx": reference.k[0],
        "fy": reference.k[4],
        "cx": reference.k[2],
        "cy": reference.k[5],
        "verified_static_across_bags": [Path(s.bag).name for s in samples],
    }


def main() -> None:
    paths = ProjectPaths.discover()
    rosbag_root = paths.raw / "camera/rosbag"
    out_dir = paths.root / "outputs/calibration/provisional_camera_info"
    out_dir.mkdir(parents=True, exist_ok=True)

    profile_bags = {
        "cam1": {
            "wtt_experiment": [
                rosbag_root / "wtt-main/e0_0rpm/e0_0rpm_run1.bag",
                rosbag_root / "wtt-main/e20_320rpm/e20_320rpm_run1.bag",
                rosbag_root / "wtt-5sec/e0_0rpm/e0_0rpm_run1.bag",
            ],
            "static_test": [
                rosbag_root / "static/cam1/static_cam1_test1.bag",
                rosbag_root / "static/cam1/static_cam1_test2.bag",
            ],
        },
        "cam2": {
            "wtt_experiment": [
                rosbag_root / "wtt-main/e0_0rpm/e0_0rpm_run1.bag",
                rosbag_root / "wtt-main/e20_320rpm/e20_320rpm_run1.bag",
                rosbag_root / "wtt-5sec/e0_0rpm/e0_0rpm_run1.bag",
            ],
            "static_test": [
                rosbag_root / "static/cam2/static_cam2_test1.bag",
                rosbag_root / "static/cam2/static_cam2_test2.bag",
            ],
        },
        "cam3": {
            "wtt_experiment": [
                rosbag_root / "wtt-main/e0_0rpm/e0_0rpm_run1.bag",
                rosbag_root / "wtt-main/e20_320rpm/e20_320rpm_run1.bag",
                rosbag_root / "wtt-5sec/e0_0rpm/e0_0rpm_run1.bag",
            ],
            "static_test": [
                rosbag_root / "static/cam3/static_cam3_test1.bag",
                rosbag_root / "static/cam3/static_cam3_test2.bag",
            ],
        },
    }

    for cam, profiles in profile_bags.items():
        record: dict = {"status": "PROVISIONAL_UNVERIFIED", "camera": cam, "rationale": RATIONALE}
        for profile, bags in profiles.items():
            existing = [b for b in bags if b.exists()]
            samples = collect_samples(existing, cam)
            assert_static(samples, cam, profile)
            record[profile] = build_profile(samples)

        out_path = out_dir / f"{cam}.yaml"
        out_path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        wtt = record["wtt_experiment"]
        static = record["static_test"]
        print(
            f"{cam}: wtt fx={wtt['fx']:.1f} fy={wtt['fy']:.1f} ({wtt['distortion_model']}) | "
            f"static fx={static['fx']:.1f} fy={static['fy']:.1f} ({static['distortion_model']}) "
            f"-> {out_path}"
        )


if __name__ == "__main__":
    main()
