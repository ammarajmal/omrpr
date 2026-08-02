from __future__ import annotations

import argparse
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

# Secondary cross-check only (2026-07-31 decision) - never used to correct any
# position/displacement number, only to sanity-check the PCA axes against each other.
# Source: /mnt/data/DEV/shm-displacement-project-backup/scripts/dynamic_test/
# multi_cam_extrinsics.yaml, rotation block of cam3_to_cam1 (translation dropped, only
# the rotation is relevant for comparing axis directions). LEGACY_ANALYSIS_REPORT.md
# section 8 called this file "internally sane by contrast" with the (badly broken)
# legacy intrinsics, but it's still an unreviewed legacy artifact - treat accordingly.
LEGACY_CAM3_TO_CAM1_ROTATION = np.array(
    [
        [0.9948346721509006, 0.006609106664801174, 0.10129311326789793],
        [-0.004720277941999101, 0.9998106990901134, -0.018875512207325095],
        [-0.10139868866292207, 0.01829988235021971, 0.9946775458626821],
    ]
)


@dataclass(frozen=True)
class ProvisionalIntrinsics:
    k: npt.NDArray[np.float64]
    d: npt.NDArray[np.float64]
    distortion_model: str


def load_intrinsics(cam: str, intrinsics_dir: Path) -> ProvisionalIntrinsics:
    path = intrinsics_dir / f"{cam}.yaml"
    record = yaml.safe_load(path.read_text(encoding="utf-8"))
    profile = record.get("wtt_experiment", record)
    k = np.array(profile["K"], dtype=np.float64).reshape(3, 3)
    d = np.array(profile["D"], dtype=np.float64)
    return ProvisionalIntrinsics(k=k, d=d, distortion_model=profile["distortion_model"])


def load_provisional_intrinsics(cam: str, root: Path) -> ProvisionalIntrinsics:
    return load_intrinsics(cam, root / "outputs/calibration/provisional_camera_info")


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


def track_from_corner_cache(
    cache_path: Path, cam: str, condition: str, intrinsics: ProvisionalIntrinsics
) -> MarkerTrack:
    """Re-solve cached official-AprilTag detections under alternate intrinsics."""

    with np.load(cache_path) as cache:
        timestamps = cache[f"{cam}__{condition}__timestamps_ns"]
        corners = cache[f"{cam}__{condition}__corners"]
    kept_ts: list[int] = []
    positions: list[npt.NDArray[np.float64]] = []
    for timestamp_ns, frame_corners in zip(timestamps, corners, strict=True):
        tvec = solve_tag_pose(frame_corners, intrinsics)
        if tvec is not None:
            kept_ts.append(int(timestamp_ns))
            positions.append(tvec)
    return MarkerTrack(
        timestamps_ns=np.asarray(kept_ts, dtype=np.int64),
        positions=np.asarray(positions, dtype=np.float64) if positions else np.zeros((0, 3)),
    )


def track_marker(bag: Path, cam: str, intrinsics: ProvisionalIntrinsics) -> MarkerTrack:
    """Per-frame position of the single best (highest decision-margin) detection.

    One physical marker per camera view in this rig - if a frame ever shows more than
    one detection (misdetection artifact), keep only the highest-margin one rather than
    conflating two different apriltag ids as if they were meaningfully different
    markers (that produced two spurious rows in an earlier version of this script).
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


def pca_dominant_axis(track: MarkerTrack) -> npt.NDArray[np.float64]:
    """First principal component of the mean-centered 3D trajectory - the camera's own
    real dominant oscillation direction, replacing the arbitrary raw image-Y axis."""

    centered = track.positions - track.positions.mean(axis=0)
    _u, _s, vt = np.linalg.svd(centered, full_matrices=False)
    axis = vt[0]
    if axis[1] < 0:  # arbitrary sign convention: prefer the +image-Y-leaning direction
        axis = -axis
    return axis


def axis_deviation_mm(track: MarkerTrack, axis: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """Displacement from the full-run mean, projected onto a fixed axis, in mm."""

    centered = track.positions - track.positions.mean(axis=0)
    return (centered @ axis) * 1000.0


def amplitude_3d_rms(track: MarkerTrack) -> float:
    """Axis-agnostic amplitude metric (RMS of 3D deviation norm) used only to pick
    which condition best constrains a camera's PCA axis - not a reported statistic."""

    if track.positions.shape[0] < 10:
        return 0.0
    centered = track.positions - track.positions.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum(centered**2, axis=1))))


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
    camera: str, condition: str, rpm: float, track: MarkerTrack, axis: npt.NDArray[np.float64]
) -> PerCameraStats | None:
    if track.positions.shape[0] == 0:
        return None
    dev = axis_deviation_mm(track, axis)
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
    axes: list[npt.NDArray[np.float64]],
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.float64]] | None:
    """Combine one or more cameras viewing the same physical marker, each projected onto
    its own PCA axis first.

    Single camera: that camera's own (timestamps, axis-deviation-mm) series.
    Multiple cameras (redundant views of one marker): nearest-match every other
    camera's series onto the first camera's timestamps and average, dropping samples
    that don't have a match within tolerance in every camera.
    """

    paired = [(t, a) for t, a in zip(tracks, axes, strict=True) if t.positions.shape[0] > 0]
    if not paired:
        return None

    ref_track, ref_axis = paired[0]
    ref_ts = ref_track.timestamps_ns
    ref_dev = axis_deviation_mm(ref_track, ref_axis)
    if len(paired) == 1:
        return ref_ts, ref_dev

    matched_mask = np.ones(ref_ts.size, dtype=bool)
    accum = ref_dev.copy()
    for other_track, other_axis in paired[1:]:
        other_dev = axis_deviation_mm(other_track, other_axis)
        matched, vals = nearest_match(ref_ts, other_track.timestamps_ns, other_dev)
        matched_mask &= matched
        accum = accum + vals

    combined = accum[matched_mask] / len(paired)
    return ref_ts[matched_mask], combined


def fuse_condition(
    condition: str,
    rpm: float,
    cam_tracks: dict[str, MarkerTrack],
    cam_axes: dict[str, npt.NDArray[np.float64]],
) -> FusedConditionStats | None:
    """Bending = avg(marker1, marker2), torsion = marker2 - marker1, mirroring
    BRID2D1_choi.m's own (ch1+ch2)/2 and (ch2-ch1) construction. Reported as a raw
    differential in mm over the documented 20cm marker baseline, not rescaled to any
    reference radius - unlike the laser's dp=db/dside factor, which is specific to the
    laser sensors' own dside=10cm/db=20cm geometry and isn't transferable here."""

    marker_series: dict[str, tuple[npt.NDArray[np.int64], npt.NDArray[np.float64]]] = {}
    for marker, cams in MARKER_CAMERAS.items():
        series = marker_group_series([cam_tracks[c] for c in cams], [cam_axes[c] for c in cams])
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


def angle_deg(a: npt.NDArray[np.float64], b: npt.NDArray[np.float64]) -> float:
    cos_theta = np.clip(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PROVISIONAL camera displacement and torsion-proxy reconstruction"
    )
    parser.add_argument(
        "--intrinsics-dir",
        type=Path,
        help="Directory containing cam1.yaml..cam3.yaml; defaults to provisional CameraInfo",
    )
    parser.add_argument(
        "--corner-cache",
        type=Path,
        help="Optional official-AprilTag corner cache made by refine_intrinsics_laser.py",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Derived CSV directory; defaults to data/interim/source/condition-matched",
    )
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    rosbag_root = paths.raw / "camera/rosbag"

    intrinsics_dir = args.intrinsics_dir or (
        paths.root / "outputs/calibration/provisional_camera_info"
    )
    intrinsics = {cam: load_intrinsics(cam, intrinsics_dir) for cam in CAMS}
    conditions = find_condition_bags(rosbag_root, "wtt-main")

    # Single detection pass: cache every (camera, condition) track in memory so the PCA
    # axis (which needs to see all of one camera's conditions first, to pick the
    # highest-amplitude one) doesn't require a second sweep over the bags.
    all_tracks: dict[str, dict[str, MarkerTrack]] = {cam: {} for cam in CAMS}
    for condition_name, _rpm, bag in conditions:
        for cam in CAMS:
            track = (
                track_from_corner_cache(args.corner_cache, cam, condition_name, intrinsics[cam])
                if args.corner_cache
                else track_marker(bag, cam, intrinsics[cam])
            )
            all_tracks[cam][condition_name] = track
            print(f"tracked {cam} {condition_name}: n={track.positions.shape[0]}")

    # Per camera: pick its own highest-3D-amplitude condition and derive a PCA axis
    # from it, replacing the arbitrary raw image-Y axis used previously.
    cam_axes: dict[str, npt.NDArray[np.float64]] = {}
    for cam in CAMS:
        best_condition = max(all_tracks[cam], key=lambda c: amplitude_3d_rms(all_tracks[cam][c]))
        axis = pca_dominant_axis(all_tracks[cam][best_condition])
        cam_axes[cam] = axis
        raw_y = np.array([0.0, 1.0, 0.0])
        print(
            f"{cam}: PCA axis from {best_condition} = {axis.round(4).tolist()}, "
            f"{angle_deg(axis, raw_y):.1f} deg from raw image-Y"
        )

    # Legacy extrinsics cross-check (secondary only, see module docstring constant):
    # is cam3's PCA axis, rotated into cam1's frame via the legacy cam3_to_cam1
    # rotation, roughly consistent with cam1's own PCA axis (both looking at the rig's
    # real bending direction, just from different cameras)?
    cam3_axis_in_cam1_frame = LEGACY_CAM3_TO_CAM1_ROTATION @ cam_axes["cam3"]
    cross_check_angle = angle_deg(cam3_axis_in_cam1_frame, cam_axes["cam1"])
    print(
        f"Legacy-extrinsics cross-check (secondary only): cam3's PCA axis rotated into "
        f"cam1's frame is {cross_check_angle:.1f} deg from cam1's own PCA axis"
    )

    per_camera_rows: list[PerCameraStats] = []
    fused_rows: list[FusedConditionStats] = []

    for condition_name, rpm, _bag in conditions:
        tracks = {cam: all_tracks[cam][condition_name] for cam in CAMS}
        for cam in CAMS:
            stats = per_camera_stats(cam, condition_name, rpm, tracks[cam], cam_axes[cam])
            if stats is None:
                print(f"{cam} {condition_name}: no marker detected")
                continue
            per_camera_rows.append(stats)
            print(
                f"{cam} {condition_name} rpm={rpm:.0f} n={stats.n_frames} "
                f"bending_rms={stats.bending_rms_mm:.4f}mm (PCA axis)"
            )

        fused = fuse_condition(condition_name, rpm, tracks, cam_axes)
        if fused is None:
            print(f"FUSED {condition_name}: not enough matched samples across marker groups")
            continue
        fused_rows.append(fused)
        print(
            f"FUSED {condition_name} rpm={rpm:.0f} n={fused.n_matched} "
            f"bending_rms={fused.bending_rms_mm:.4f}mm "
            f"torsion_rms={fused.torsion_rms_mm:.4f}mm (20cm baseline, PCA axis)"
        )

    output_dir = args.output_dir or (paths.interim / "condition-matched")
    write_csv(per_camera_rows, output_dir / "camera_tunnel_a_2024.csv")
    write_csv(fused_rows, output_dir / "camera_fused_tunnel_a_2024.csv")
    print(f"{len(per_camera_rows)} per-camera rows, {len(fused_rows)} fused rows")


if __name__ == "__main__":
    main()
