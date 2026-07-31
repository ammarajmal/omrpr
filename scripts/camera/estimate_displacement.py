from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import apriltag
import cv2
import numpy as np
import numpy.typing as npt
import yaml
from rosbags.highlevel import AnyReader

from omrpr_analysis.paths import ProjectPaths

TAG_SIZE_M = 0.020  # tag36h11, per AGENTS.md / configs/project.yaml
CAMS = ("cam1", "cam2", "cam3")

# Both physical markers on the rig happen to carry the same AprilTag payload (id=0),
# confirmed 2026-07-31 from rig photos: marker "ID-0-1" is seen by cam1 and cam2,
# marker "ID-0-2" (a physically different marker, 20cm away) is seen by cam3 only.
# AprilTag numeric id cannot disambiguate them - camera source is the only reliable
# signal. No camera ever sees both markers at once, so torsion-proxy (their
# differential) is built across camera groups, not within one camera's frames.
MARKER_CAMERAS: dict[str, tuple[str, ...]] = {
    "ID-0-1": ("cam1", "cam2"),
    "ID-0-2": ("cam3",),
}
MARKER_SPACING_CM = 20.0
SYNC_TOLERANCE_NS = 25_000_000  # 25ms, matching the final legacy fuse_detections_wtt.py choice

# apriltag's 'lb-rb-rt-lt' corner order: left-bottom, right-bottom, right-top, left-top.
TAG_OBJECT_POINTS = np.array(
    [
        [-TAG_SIZE_M / 2, -TAG_SIZE_M / 2, 0.0],
        [TAG_SIZE_M / 2, -TAG_SIZE_M / 2, 0.0],
        [TAG_SIZE_M / 2, TAG_SIZE_M / 2, 0.0],
        [-TAG_SIZE_M / 2, TAG_SIZE_M / 2, 0.0],
    ],
    dtype=np.float64,
)

CONDITION_RE = re.compile(r"^e\d+_(\d+)rpm$")


@dataclass(frozen=True)
class ProvisionalIntrinsics:
    k: npt.NDArray[np.float64]
    d: npt.NDArray[np.float64]
    distortion_model: str


def load_provisional_intrinsics(cam: str, root: Path) -> ProvisionalIntrinsics:
    path = root / "outputs/calibration/provisional_camera_info" / f"{cam}.yaml"
    record = yaml.safe_load(path.read_text(encoding="utf-8"))
    profile = record["wtt_experiment"]
    k = np.array(profile["K"], dtype=np.float64).reshape(3, 3)
    d = np.array(profile["D"], dtype=np.float64)
    return ProvisionalIntrinsics(k=k, d=d, distortion_model=profile["distortion_model"])


def solve_tag_pose(
    corners_lb_rb_rt_lt: npt.NDArray[np.float64],
    intrinsics: ProvisionalIntrinsics,
) -> npt.NDArray[np.float64] | None:
    """Undistort with the full rational-polynomial model, then solvePnP. Returns tvec (m)."""

    image_points = corners_lb_rb_rt_lt.reshape(-1, 1, 2).astype(np.float64)
    undistorted = cv2.undistortPoints(image_points, intrinsics.k, intrinsics.d, P=intrinsics.k)

    ok, _rvec, tvec = cv2.solvePnP(
        TAG_OBJECT_POINTS,
        undistorted,
        intrinsics.k,
        None,
        flags=cv2.SOLVEPNP_IPPE_SQUARE,
    )
    if not ok:
        return None
    return tvec.reshape(3)


def condition_rpm(condition_dir: str) -> float | None:
    match = CONDITION_RE.match(condition_dir)
    return float(match.group(1)) if match else None


@dataclass(frozen=True)
class MarkerTrack:
    timestamps_ns: npt.NDArray[np.int64]
    positions: npt.NDArray[np.float64]  # Nx3, camera frame, meters


def track_marker(bag: Path, cam: str, intrinsics: ProvisionalIntrinsics) -> MarkerTrack:
    """Per-frame position of the single best (highest decision-margin) detection.

    One physical marker per camera view in this rig - if a frame ever shows more than
    one detection (misdetection artifact), keep only the highest-margin one rather than
    conflating two different apriltag ids as if they were meaningfully different
    markers (that produced two spurious rows in the previous version of this script).
    """

    detector = apriltag.apriltag("tag36h11")
    timestamps: list[int] = []
    positions: list[npt.NDArray[np.float64]] = []

    with AnyReader([bag]) as reader:
        connections = [
            c for c in reader.connections if c.topic == f"/sony_{cam}/image_raw/compressed"
        ]
        for connection, timestamp_ns, raw in reader.messages(connections=connections):
            msg = reader.deserialize(raw, connection.msgtype)
            data = np.frombuffer(bytes(msg.data), dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            detections = detector.detect(image)
            if not detections:
                continue
            best = max(detections, key=lambda d: d["margin"])
            tvec = solve_tag_pose(np.asarray(best["lb-rb-rt-lt"]), intrinsics)
            if tvec is None:
                continue
            timestamps.append(timestamp_ns)
            positions.append(tvec)

    return MarkerTrack(
        timestamps_ns=np.array(timestamps, dtype=np.int64),
        positions=np.array(positions, dtype=np.float64) if positions else np.zeros((0, 3)),
    )


def y_deviation_mm(track: MarkerTrack) -> npt.NDArray[np.float64]:
    """Vertical (camera-Y) displacement from the full-run mean, in mm."""

    y = track.positions[:, 1]
    return (y - y.mean()) * 1000.0


def nearest_match(
    ref_ts: npt.NDArray[np.int64],
    src_ts: npt.NDArray[np.int64],
    src_vals: npt.NDArray[np.float64],
    tolerance_ns: int = SYNC_TOLERANCE_NS,
) -> tuple[npt.NDArray[np.bool_], npt.NDArray[np.float64]]:
    """For each ref timestamp, nearest-neighbor match against src. Matches by timestamp,
    not positional truncation (LEGACY_ANALYSIS_REPORT.md section 18 rec. 9)."""

    if src_ts.size == 0:
        return np.zeros(ref_ts.size, dtype=bool), np.zeros(ref_ts.size)

    idx = np.searchsorted(src_ts, ref_ts)
    idx = np.clip(idx, 1, src_ts.size - 1)
    left = idx - 1
    use_left = np.abs(ref_ts - src_ts[left]) <= np.abs(ref_ts - src_ts[idx])
    nearest_idx = np.where(use_left, left, idx)
    delta = np.abs(ref_ts - src_ts[nearest_idx])
    matched = delta <= tolerance_ns
    return matched, src_vals[nearest_idx]


@dataclass(frozen=True)
class PerCameraStats:
    camera: str
    condition: str
    rpm: float
    n_frames: int
    bending_mean_mm: float
    bending_rms_mm: float
    bending_peak_mm: float


def per_camera_stats(
    camera: str, condition: str, rpm: float, track: MarkerTrack
) -> PerCameraStats | None:
    if track.positions.shape[0] == 0:
        return None
    dev = y_deviation_mm(track)
    mean = float(dev.mean())
    return PerCameraStats(
        camera=camera,
        condition=condition,
        rpm=rpm,
        n_frames=int(track.positions.shape[0]),
        bending_mean_mm=mean,
        bending_rms_mm=float(dev.std()),
        bending_peak_mm=float(np.max(np.abs(dev - mean))),
    )


@dataclass(frozen=True)
class FusedConditionStats:
    condition: str
    rpm: float
    n_matched: int
    bending_mean_mm: float
    bending_rms_mm: float
    bending_peak_mm: float
    torsion_mean_mm: float
    torsion_rms_mm: float
    torsion_peak_mm: float


def marker_group_series(
    tracks: list[MarkerTrack],
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.float64]] | None:
    """Combine one or more cameras viewing the same physical marker.

    Single camera: that camera's own (timestamps, y-deviation-mm) series.
    Multiple cameras (redundant views of one marker): nearest-match every other
    camera's series onto the first camera's timestamps and average, dropping samples
    that don't have a match within tolerance in every camera.
    """

    tracks = [t for t in tracks if t.positions.shape[0] > 0]
    if not tracks:
        return None

    ref_ts = tracks[0].timestamps_ns
    ref_dev = y_deviation_mm(tracks[0])
    if len(tracks) == 1:
        return ref_ts, ref_dev

    matched_mask = np.ones(ref_ts.size, dtype=bool)
    accum = ref_dev.copy()
    for other in tracks[1:]:
        other_dev = y_deviation_mm(other)
        matched, vals = nearest_match(ref_ts, other.timestamps_ns, other_dev)
        matched_mask &= matched
        accum = accum + vals

    combined = accum[matched_mask] / len(tracks)
    return ref_ts[matched_mask], combined


def fuse_condition(
    condition: str, rpm: float, cam_tracks: dict[str, MarkerTrack]
) -> FusedConditionStats | None:
    """Bending = avg(marker1, marker2), torsion = marker2 - marker1, mirroring
    BRID2D1_choi.m's own (ch1+ch2)/2 and (ch2-ch1) construction. Reported as a raw
    differential in mm over the documented 20cm marker baseline, not rescaled to any
    reference radius - unlike the laser's dp=db/dside factor, which is specific to the
    laser sensors' own dside=10cm/db=20cm geometry and isn't transferable here."""

    marker_series: dict[str, tuple[npt.NDArray[np.int64], npt.NDArray[np.float64]]] = {}
    for marker, cams in MARKER_CAMERAS.items():
        series = marker_group_series([cam_tracks[c] for c in cams])
        if series is None:
            return None
        marker_series[marker] = series

    (m1_ts, m1_dev) = marker_series["ID-0-1"]
    (m2_ts, m2_dev) = marker_series["ID-0-2"]
    matched, m2_aligned = nearest_match(m1_ts, m2_ts, m2_dev)
    if matched.sum() < 10:
        return None

    m1_aligned = m1_dev[matched]
    m2_aligned = m2_aligned[matched]

    bending = (m1_aligned + m2_aligned) / 2
    torsion = m2_aligned - m1_aligned
    bending_mean = float(bending.mean())
    torsion_mean = float(torsion.mean())

    return FusedConditionStats(
        condition=condition,
        rpm=rpm,
        n_matched=int(matched.sum()),
        bending_mean_mm=bending_mean,
        bending_rms_mm=float(bending.std()),
        bending_peak_mm=float(np.max(np.abs(bending - bending_mean))),
        torsion_mean_mm=torsion_mean,
        torsion_rms_mm=float(torsion.std()),
        torsion_peak_mm=float(np.max(np.abs(torsion - torsion_mean))),
    )


def find_condition_bags(rosbag_root: Path, dataset: str) -> list[tuple[str, float, Path]]:
    out: list[tuple[str, float, Path]] = []
    dataset_root = rosbag_root / dataset
    if not dataset_root.exists():
        return out
    for condition_dir in sorted(dataset_root.iterdir()):
        rpm = condition_rpm(condition_dir.name)
        if rpm is None:
            continue
        bags = sorted(condition_dir.glob("*_run1.bag"))
        if bags:
            out.append((condition_dir.name, rpm, bags[0]))
    return out


def write_csv(rows: list, out_path: Path) -> None:
    if not rows:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].__dataclass_fields__)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def main() -> None:
    paths = ProjectPaths.discover()
    rosbag_root = paths.raw / "camera/rosbag"

    intrinsics = {cam: load_provisional_intrinsics(cam, paths.root) for cam in CAMS}
    conditions = find_condition_bags(rosbag_root, "wtt-main")

    per_camera_rows: list[PerCameraStats] = []
    fused_rows: list[FusedConditionStats] = []

    for condition_name, rpm, bag in conditions:
        tracks: dict[str, MarkerTrack] = {}
        for cam in CAMS:
            track = track_marker(bag, cam, intrinsics[cam])
            tracks[cam] = track
            stats = per_camera_stats(cam, condition_name, rpm, track)
            if stats is None:
                print(f"{cam} {condition_name}: no marker detected")
                continue
            per_camera_rows.append(stats)
            print(
                f"{cam} {condition_name} rpm={rpm:.0f} n={stats.n_frames} "
                f"bending_rms={stats.bending_rms_mm:.4f}mm"
            )

        fused = fuse_condition(condition_name, rpm, tracks)
        if fused is None:
            print(f"FUSED {condition_name}: not enough matched samples across marker groups")
            continue
        fused_rows.append(fused)
        print(
            f"FUSED {condition_name} rpm={rpm:.0f} n={fused.n_matched} "
            f"bending_rms={fused.bending_rms_mm:.4f}mm "
            f"torsion_rms={fused.torsion_rms_mm:.4f}mm (20cm baseline)"
        )

    write_csv(per_camera_rows, paths.interim / "condition-matched/camera_tunnel_a_2024.csv")
    write_csv(fused_rows, paths.interim / "condition-matched/camera_fused_tunnel_a_2024.csv")
    print(f"{len(per_camera_rows)} per-camera rows, {len(fused_rows)} fused rows")


if __name__ == "__main__":
    main()
