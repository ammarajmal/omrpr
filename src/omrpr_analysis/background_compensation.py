"""Estimate and apply stationary-background camera-motion compensation.

No fixed reference marker exists in any governed WTT frame (every source row's
``raw_ids_seen`` is the single governed tag or empty), so camera motion is
estimated directly from each frame's static background via ECC image
registration, with the marker's own region excluded from the alignment.
"""

from __future__ import annotations

import csv
import json
import math
import multiprocessing
import statistics
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import numpy.typing as npt
from rosbags.highlevel import AnyReader

from .official_tracks import sha256_file

ECC_CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6)
ECC_MOTION_TYPE = cv2.MOTION_AFFINE
MARKER_MASK_DILATION_PX = 20

IDENTITY_2X3: npt.NDArray[np.float64] = np.array(
    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64
)

CORNER_FIELDS = (
    ("corner0_x", "corner0_y"),
    ("corner1_x", "corner1_y"),
    ("corner2_x", "corner2_y"),
    ("corner3_x", "corner3_y"),
)

COMPENSATED_FIELDS = (
    "compensated_centroid_x",
    "compensated_centroid_y",
    "compensated_corner0_x",
    "compensated_corner0_y",
    "compensated_corner1_x",
    "compensated_corner1_y",
    "compensated_corner2_x",
    "compensated_corner2_y",
    "compensated_corner3_x",
    "compensated_corner3_y",
    "compensation_status",
    "ecc_correlation_coefficient",
)

RAW_POINT_FIELDS = (
    ("centroid_x", "centroid_y", "compensated_centroid_x", "compensated_centroid_y"),
    ("corner0_x", "corner0_y", "compensated_corner0_x", "compensated_corner0_y"),
    ("corner1_x", "corner1_y", "compensated_corner1_x", "compensated_corner1_y"),
    ("corner2_x", "corner2_y", "compensated_corner2_x", "compensated_corner2_y"),
    ("corner3_x", "corner3_y", "compensated_corner3_x", "compensated_corner3_y"),
)


@dataclass(frozen=True)
class PairwiseTransform:
    """Camera-motion transform estimated between two consecutive frames."""

    status: str
    correlation_coefficient: float
    matrix: npt.NDArray[np.float64] | None
    """2x3 affine mapping frame[i-1] pixel coordinates onto frame[i]."""


@dataclass(frozen=True)
class CumulativeFrame:
    """The frame-0-referenced cumulative background transform for one frame."""

    status: str
    correlation_coefficient: float
    matrix: npt.NDArray[np.float64] | None
    """2x3 affine mapping this frame's pixel coordinates back onto frame 0."""


@dataclass(frozen=True)
class CompensationSummary:
    total_frames: int
    compensated_frames: int
    uncompensated_frames: int
    streams: int
    source_sha256: str
    mean_correlation_coefficient: float
    stream_convergence: Mapping[str, float]


def marker_exclusion_mask(
    shape: tuple[int, int],
    corners: Sequence[tuple[float, float]] | None,
    dilation_px: int = MARKER_MASK_DILATION_PX,
) -> npt.NDArray[np.uint8] | None:
    """Return an ECC input mask (255 usable) excluding the marker's dilated bounding box."""

    if not corners:
        return None
    height, width = shape
    xs = [x for x, _ in corners]
    ys = [y for _, y in corners]
    x0 = max(0, int(min(xs)) - dilation_px)
    y0 = max(0, int(min(ys)) - dilation_px)
    x1 = min(width, int(max(xs)) + dilation_px + 1)
    y1 = min(height, int(max(ys)) + dilation_px + 1)
    if x1 <= x0 or y1 <= y0:
        return None
    mask = np.full((height, width), 255, dtype=np.uint8)
    mask[y0:y1, x0:x1] = 0
    return mask


def estimate_pairwise_transform(
    previous_gray: npt.NDArray[np.uint8],
    current_gray: npt.NDArray[np.uint8],
    mask: npt.NDArray[np.uint8] | None,
) -> PairwiseTransform:
    """Estimate the affine background motion between two consecutive frames via ECC."""

    warp = IDENTITY_2X3.astype(np.float32).copy()
    try:
        correlation_coefficient, result_warp = cv2.findTransformECC(
            previous_gray.astype(np.float32),
            current_gray.astype(np.float32),
            warp,
            ECC_MOTION_TYPE,
            ECC_CRITERIA,
            mask,
        )
        warp = np.asarray(result_warp)
    except cv2.error:
        return PairwiseTransform(
            status="ecc_non_convergence", correlation_coefficient=float("nan"), matrix=None
        )
    return PairwiseTransform(
        status="",
        correlation_coefficient=float(correlation_coefficient),
        matrix=warp.astype(np.float64),
    )


def _to_homogeneous(matrix_2x3: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    homogeneous = np.eye(3, dtype=np.float64)
    homogeneous[:2, :] = matrix_2x3
    return homogeneous


def compose_affine(
    outer: npt.NDArray[np.float64], inner: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """Return the affine transform equivalent to applying `inner` then `outer`."""

    return (_to_homogeneous(outer) @ _to_homogeneous(inner))[:2, :]


def invert_affine(matrix_2x3: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return np.linalg.inv(_to_homogeneous(matrix_2x3))[:2, :]


def apply_affine(matrix_2x3: npt.NDArray[np.float64], x: float, y: float) -> tuple[float, float]:
    point = matrix_2x3 @ np.array([x, y, 1.0], dtype=np.float64)
    return float(point[0]), float(point[1])


def accumulate_stream_transforms(
    pairwise: Sequence[PairwiseTransform],
) -> list[CumulativeFrame]:
    """Compose per-frame-pair transforms into frame-0-referenced cumulative transforms.

    `pairwise[i]` is the transform from frame i to frame i+1. The returned list has
    one entry per frame, starting with frame 0's identity. A single non-convergent
    link invalidates every later frame in the stream: no transform is ever
    fabricated or carried forward across a failed link.
    """

    frames = [
        CumulativeFrame(status="", correlation_coefficient=float("nan"), matrix=IDENTITY_2X3.copy())
    ]
    broken = False
    for transition in pairwise:
        if broken or transition.status or transition.matrix is None:
            broken = True
            frames.append(
                CumulativeFrame(
                    status="no_transform_upstream",
                    correlation_coefficient=float("nan"),
                    matrix=None,
                )
            )
            continue
        previous = frames[-1]
        assert previous.matrix is not None
        cumulative = compose_affine(previous.matrix, invert_affine(transition.matrix))
        frames.append(
            CumulativeFrame(
                status="",
                correlation_coefficient=transition.correlation_coefficient,
                matrix=cumulative,
            )
        )
    return frames


def stream_corners(row: Mapping[str, str]) -> tuple[tuple[float, float], ...] | None:
    """Extract this row's marker corners for masking, or None if not usable."""

    if row.get("corners_finite_and_in_image", "").strip().lower() != "true":
        return None
    try:
        return tuple(
            (float(row[x_field]), float(row[y_field])) for x_field, y_field in CORNER_FIELDS
        )
    except (KeyError, ValueError):
        return None


def compute_stream_pairwise_transforms(
    grays: Sequence[npt.NDArray[np.uint8]],
    rows: Sequence[Mapping[str, str]],
) -> list[PairwiseTransform]:
    """One transform per consecutive frame pair; `grays[i]`/`rows[i]` align by frame_idx."""

    transforms: list[PairwiseTransform] = []
    for i in range(1, len(grays)):
        mask = marker_exclusion_mask(
            (grays[i].shape[0], grays[i].shape[1]), stream_corners(rows[i - 1])
        )
        transforms.append(estimate_pairwise_transform(grays[i - 1], grays[i], mask))
    return transforms


def iter_stream_pairwise_transforms(
    frames: Iterator[npt.NDArray[np.uint8]],
    rows: Sequence[Mapping[str, str]],
) -> Iterator[PairwiseTransform]:
    """Like `compute_stream_pairwise_transforms`, but consumes `frames` lazily.

    Only ever holds two decoded frames in memory at once, instead of the whole
    stream — needed because a full stream of full-resolution frames is several
    GB, which is untenable once streams run in parallel worker processes.
    """

    previous = next(frames, None)
    if previous is None:
        if rows:
            raise ValueError(f"expected {len(rows)} frames, got 0")
        return
    for i in range(1, len(rows)):
        current = next(frames, None)
        if current is None:
            raise ValueError(f"expected {len(rows)} frames, got {i}")
        mask = marker_exclusion_mask(
            (current.shape[0], current.shape[1]), stream_corners(rows[i - 1])
        )
        yield estimate_pairwise_transform(previous, current, mask)
        previous = current
    if next(frames, None) is not None:
        raise ValueError(f"expected {len(rows)} frames, got more")


def apply_cumulative_transform_to_row(
    row: Mapping[str, str], cumulative: CumulativeFrame
) -> dict[str, str]:
    """Return `row` extended with compensated coordinates, or blank fields on failure."""

    updated = dict(row)
    updated["compensation_status"] = cumulative.status
    correlation = cumulative.correlation_coefficient
    updated["ecc_correlation_coefficient"] = "" if math.isnan(correlation) else str(correlation)
    for raw_x_field, raw_y_field, comp_x_field, comp_y_field in RAW_POINT_FIELDS:
        raw_x = row.get(raw_x_field, "").strip()
        raw_y = row.get(raw_y_field, "").strip()
        if cumulative.status or cumulative.matrix is None or not raw_x or not raw_y:
            updated[comp_x_field] = ""
            updated[comp_y_field] = ""
            continue
        compensated_x, compensated_y = apply_affine(cumulative.matrix, float(raw_x), float(raw_y))
        updated[comp_x_field] = str(compensated_x)
        updated[comp_y_field] = str(compensated_y)
    return updated


def iter_bag_grayscale_frames(bag_path: Path, topic: str) -> Iterator[npt.NDArray[np.uint8]]:
    """Yield grayscale frames for one topic, in bag message order."""

    with AnyReader([bag_path]) as reader:
        connections = [connection for connection in reader.connections if connection.topic == topic]
        for connection, _timestamp_ns, raw in reader.messages(connections=connections):
            message = reader.deserialize(raw, connection.msgtype)
            payload = np.frombuffer(bytes(message.data), dtype=np.uint8)  # type: ignore[attr-defined]
            image = cv2.imdecode(payload, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"could not decode frame from {bag_path} topic {topic}")
            yield image.astype(np.uint8)


def legacy_cached_frame_paths(
    cache_root: Path, condition: str, camera: str, frame_count: int
) -> list[Path] | None:
    """Return this stream's pre-extracted step01 PNG paths if all `frame_count` exist.

    Reuses the legacy pipeline's raw JPEG-to-pixel decode (results/step01) as a
    decode cache. This is a plain frame export with no detections or intrinsics
    involved, so it falls outside the rebuild's no-legacy-artifacts constraint.
    """

    cam_dir = cache_root / condition / camera
    paths = [cam_dir / f"frame_{i:06d}.png" for i in range(frame_count)]
    if paths and all(path.is_file() for path in paths):
        return paths
    return None


def iter_cached_grayscale_frames(paths: Sequence[Path]) -> Iterator[npt.NDArray[np.uint8]]:
    """Yield grayscale frames decoded from pre-extracted PNGs, in path order."""

    for path in paths:
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"could not decode cached frame: {path}")
        yield image.astype(np.uint8)


@dataclass(frozen=True)
class _StreamTask:
    condition: str
    camera: str
    rows: list[dict[str, str]]
    bag_path: Path
    topic: str
    frame_cache_root: Path | None


@dataclass(frozen=True)
class _StreamResult:
    condition: str
    camera: str
    output_rows: list[dict[str, str]]
    converged: int
    correlation_values: list[float]


def _stream_frames(task: _StreamTask) -> Iterator[npt.NDArray[np.uint8]]:
    cached_paths = (
        legacy_cached_frame_paths(
            task.frame_cache_root, task.condition, task.camera, len(task.rows)
        )
        if task.frame_cache_root is not None
        else None
    )
    if cached_paths is not None:
        return iter_cached_grayscale_frames(cached_paths)
    return iter_bag_grayscale_frames(task.bag_path, task.topic)


def _process_stream(task: _StreamTask) -> _StreamResult:
    """Worker entry point: safe to run in a separate process (holds ~2 frames, not the stream)."""

    try:
        pairwise = list(iter_stream_pairwise_transforms(_stream_frames(task), task.rows))
    except ValueError as exc:
        raise ValueError(f"{task.condition}/{task.camera}: {exc}") from exc
    cumulative_frames = accumulate_stream_transforms(pairwise)

    output_rows: list[dict[str, str]] = []
    converged = 0
    correlation_values: list[float] = []
    for row, cumulative in zip(task.rows, cumulative_frames, strict=True):
        output_rows.append(apply_cumulative_transform_to_row(row, cumulative))
        if not cumulative.status:
            converged += 1
            if not math.isnan(cumulative.correlation_coefficient):
                correlation_values.append(cumulative.correlation_coefficient)
    return _StreamResult(task.condition, task.camera, output_rows, converged, correlation_values)


def _init_worker() -> None:
    # ECC has no CUDA path in this OpenCV build; each worker's own internal
    # thread pool would otherwise oversubscribe the machine alongside the
    # process pool, so pin every worker to a single thread.
    cv2.setNumThreads(1)


def compensate_tracks(
    source: Path,
    destination: Path,
    bag_paths: Mapping[str, Path],
    frame_cache_root: Path | None = None,
    max_workers: int = 1,
) -> CompensationSummary:
    """Add stationary-background-compensated pixel columns to every S04.02 track row.

    Raw columns are carried through unchanged; a stream whose ECC alignment fails
    partway through is marked ``no_transform_upstream`` from that frame onward
    rather than interpolated or backfilled.
    """

    with source.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fieldnames = list(reader.fieldnames or ())
        rows = list(reader)

    missing_columns = {"condition", "camera", "topic", "frame_idx"} - set(fieldnames)
    if missing_columns:
        raise ValueError(f"track input missing columns: {sorted(missing_columns)}")

    output_fields = fieldnames + list(COMPENSATED_FIELDS)

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["condition"], row["camera"]), []).append(row)

    destination.parent.mkdir(parents=True, exist_ok=True)

    tasks: list[_StreamTask] = []
    for (condition, camera), stream_rows in sorted(grouped.items()):
        stream_rows.sort(key=lambda r: int(r["frame_idx"]))
        frame_indices = [int(r["frame_idx"]) for r in stream_rows]
        if frame_indices != list(range(len(frame_indices))):
            raise ValueError(
                f"non-contiguous frame_idx sequence for {condition}/{camera}: "
                "compensation requires every frame from the source bag"
            )
        bag_path = bag_paths.get(condition)
        if bag_path is None:
            raise ValueError(f"no bag path declared for condition: {condition}")
        topic = stream_rows[0]["topic"]
        tasks.append(_StreamTask(condition, camera, stream_rows, bag_path, topic, frame_cache_root))

    if max_workers > 1:
        with multiprocessing.Pool(max_workers, initializer=_init_worker) as pool:
            results = pool.map(_process_stream, tasks)
    else:
        results = [_process_stream(task) for task in tasks]

    total = compensated_count = 0
    correlation_values: list[float] = []
    stream_convergence: dict[str, float] = {}

    with destination.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=output_fields, lineterminator="\n")
        writer.writeheader()
        for result in results:
            for row in result.output_rows:
                writer.writerow(row)
                total += 1
            compensated_count += result.converged
            correlation_values.extend(result.correlation_values)
            stream_convergence[f"{result.condition}|{result.camera}"] = result.converged / len(
                result.output_rows
            )

    return CompensationSummary(
        total_frames=total,
        compensated_frames=compensated_count,
        uncompensated_frames=total - compensated_count,
        streams=len(grouped),
        source_sha256=sha256_file(source),
        mean_correlation_coefficient=(
            statistics.fmean(correlation_values) if correlation_values else float("nan")
        ),
        stream_convergence=dict(sorted(stream_convergence.items())),
    )


def write_compensation_metadata(
    path: Path,
    *,
    source: Path,
    output: Path,
    summary: CompensationSummary,
) -> None:
    record = {
        "artifact": "stationary_background_compensated_tracks",
        "units": "pixel",
        "metric_pose_status": "not_generated",
        "compensation_method": "cv2.findTransformECC, MOTION_AFFINE, marker region excluded",
        "source_path": str(source),
        "source_sha256": summary.source_sha256,
        "output_path": str(output),
        "output_sha256": sha256_file(output),
        "total_frames": summary.total_frames,
        "compensated_frames": summary.compensated_frames,
        "uncompensated_frames_retained": summary.uncompensated_frames,
        "streams": summary.streams,
        "mean_correlation_coefficient": summary.mean_correlation_coefficient,
        "stream_convergence_fraction": dict(summary.stream_convergence),
        "compensation_status_policy": (
            "no_transform_upstream once a stream's ECC alignment fails; no interpolation"
        ),
    }
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
