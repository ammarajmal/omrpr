from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import asdict, dataclass, fields
from itertools import pairwise
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw
from rosbags.highlevel import AnyReader

SUPPORTED_RAW_ENCODINGS = {
    "mono8",
    "8uc1",
    "rgb8",
    "bgr8",
    "rgba8",
    "bgra8",
    "mono16",
    "16uc1",
}


@dataclass(frozen=True)
class FrameMetric:
    bag: str
    topic: str
    msgtype: str
    frame_index: int
    timestamp_ns: int
    width: int
    height: int
    encoding: str
    decode_ok: bool
    decode_error: str
    mean_brightness: float
    contrast_std: float
    laplacian_variance: float
    dark_clip_fraction: float
    bright_clip_fraction: float
    perceptual_hash: str
    sample_path: str


def _data_bytes(data: Any) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, memoryview):
        return data.tobytes()
    return np.asarray(data, dtype=np.uint8).tobytes()


def decode_compressed(message: Any) -> tuple[np.ndarray, str]:
    payload = np.frombuffer(_data_bytes(message.data), dtype=np.uint8)
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("OpenCV could not decode compressed payload")
    return image, str(getattr(message, "format", "compressed"))


def decode_raw(message: Any) -> tuple[np.ndarray, str]:
    encoding = str(message.encoding).lower()
    if encoding not in SUPPORTED_RAW_ENCODINGS:
        raise ValueError(f"unsupported raw encoding: {encoding}")

    height = int(message.height)
    width = int(message.width)
    step = int(message.step)
    if height <= 0 or width <= 0 or step <= 0:
        raise ValueError(f"invalid dimensions/step: {width}x{height}, step={step}")

    raw = _data_bytes(message.data)
    expected = height * step
    if len(raw) < expected:
        raise ValueError(f"short image buffer: {len(raw)} < {expected}")

    rows = np.frombuffer(raw[:expected], dtype=np.uint8).reshape(height, step)
    if encoding in {"mono8", "8uc1"}:
        return cv2.cvtColor(rows[:, :width], cv2.COLOR_GRAY2BGR), encoding
    if encoding in {"mono16", "16uc1"}:
        pixels = rows[:, : width * 2].copy().view(np.uint16).reshape(height, width)
        scaled = cv2.convertScaleAbs(pixels, alpha=255.0 / max(1, int(pixels.max())))
        return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR), encoding

    channels = 4 if "a8" in encoding else 3
    pixels = rows[:, : width * channels].reshape(height, width, channels)
    conversions = {
        "rgb8": cv2.COLOR_RGB2BGR,
        "rgba8": cv2.COLOR_RGBA2BGR,
        "bgra8": cv2.COLOR_BGRA2BGR,
    }
    if encoding == "bgr8":
        return pixels.copy(), encoding
    return cv2.cvtColor(pixels, conversions[encoding]), encoding


def decode_message(message: Any, msgtype: str) -> tuple[np.ndarray, str]:
    if msgtype.endswith("/CompressedImage"):
        return decode_compressed(message)
    if msgtype.endswith("/Image"):
        return decode_raw(message)
    raise ValueError(f"unsupported ROS message type: {msgtype}")


def deterministic_indices(count: int, samples: int) -> set[int]:
    if count <= 0:
        return set()
    size = min(count, max(1, samples))
    return {int(value) for value in np.linspace(0, count - 1, num=size)}


def perceptual_hash(gray: np.ndarray) -> str:
    small = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA)
    bits = small >= float(small.mean())
    value = 0
    for bit in bits.flat:
        value = (value << 1) | int(bit)
    return f"{value:016x}"


def frame_metric(
    *,
    bag: Path,
    topic: str,
    msgtype: str,
    frame_index: int,
    timestamp_ns: int,
    image: np.ndarray,
    encoding: str,
    sample_path: Path,
) -> FrameMetric:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return FrameMetric(
        bag=str(bag),
        topic=topic,
        msgtype=msgtype,
        frame_index=frame_index,
        timestamp_ns=timestamp_ns,
        width=int(image.shape[1]),
        height=int(image.shape[0]),
        encoding=encoding,
        decode_ok=True,
        decode_error="",
        mean_brightness=float(gray.mean()),
        contrast_std=float(gray.std()),
        laplacian_variance=float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        dark_clip_fraction=float(np.mean(gray <= 5)),
        bright_clip_fraction=float(np.mean(gray >= 250)),
        perceptual_hash=perceptual_hash(gray),
        sample_path=str(sample_path),
    )


def failed_metric(
    bag: Path,
    topic: str,
    msgtype: str,
    frame_index: int,
    timestamp_ns: int,
    error: Exception,
) -> FrameMetric:
    return FrameMetric(
        bag=str(bag),
        topic=topic,
        msgtype=msgtype,
        frame_index=frame_index,
        timestamp_ns=timestamp_ns,
        width=0,
        height=0,
        encoding="",
        decode_ok=False,
        decode_error=f"{type(error).__name__}: {error}",
        mean_brightness=math.nan,
        contrast_std=math.nan,
        laplacian_variance=math.nan,
        dark_clip_fraction=math.nan,
        bright_clip_fraction=math.nan,
        perceptual_hash="",
        sample_path="",
    )


def safe_stream_name(bag: Path, root: Path, topic: str, msgtype: str) -> str:
    relative = str(bag.relative_to(root))
    digest = hashlib.sha256(f"{relative}|{topic}|{msgtype}".encode()).hexdigest()[:12]
    camera = next((part for part in topic.split("/") if part.startswith("sony_cam")), "camera")
    kind = "compressed" if msgtype.endswith("/CompressedImage") else "raw"
    return f"{bag.stem}__{camera}__{kind}__{digest}"


def write_contact_sheet(images: list[tuple[np.ndarray, str]], destination: Path) -> None:
    if not images:
        return
    thumb_w, thumb_h, label_h = 320, 180, 28
    columns = min(4, len(images))
    rows = math.ceil(len(images) / columns)
    canvas = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(canvas)
    for position, (bgr, label) in enumerate(images):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        thumb = Image.fromarray(rgb)
        thumb.thumbnail((thumb_w, thumb_h))
        x = (position % columns) * thumb_w
        y = (position // columns) * (thumb_h + label_h)
        canvas.paste(thumb, (x, y))
        draw.text((x + 4, y + thumb_h + 5), label[:48], fill="black")
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, quality=90)


def audit_tree(root: Path, output: Path, samples_per_stream: int = 12) -> list[FrameMetric]:
    bags = sorted(root.rglob("*.bag"))
    if not bags:
        raise FileNotFoundError(f"no .bag files found below {root}")

    samples_dir = output / "samples"
    sheets_dir = output / "contact_sheets"
    rows: list[FrameMetric] = []

    for bag in bags:
        with AnyReader([bag]) as reader:
            connections = [
                connection
                for connection in reader.connections
                if "image_raw" in connection.topic
                and connection.msgtype.endswith(("/Image", "/CompressedImage"))
            ]
            for connection in connections:
                selected = deterministic_indices(int(connection.msgcount), samples_per_stream)
                stream = safe_stream_name(bag, root, connection.topic, connection.msgtype)
                sheet_images: list[tuple[np.ndarray, str]] = []
                frame_index = 0
                for current, timestamp_ns, rawdata in reader.messages(connections=[connection]):
                    if frame_index not in selected:
                        frame_index += 1
                        continue
                    try:
                        message = reader.deserialize(rawdata, current.msgtype)
                        image, encoding = decode_message(message, current.msgtype)
                        sample_path = samples_dir / stream / f"frame_{frame_index:06d}.jpg"
                        sample_path.parent.mkdir(parents=True, exist_ok=True)
                        if not cv2.imwrite(str(sample_path), image):
                            raise OSError(f"failed to write sample {sample_path}")
                        rows.append(
                            frame_metric(
                                bag=bag,
                                topic=current.topic,
                                msgtype=current.msgtype,
                                frame_index=frame_index,
                                timestamp_ns=timestamp_ns,
                                image=image,
                                encoding=encoding,
                                sample_path=sample_path,
                            )
                        )
                        sheet_images.append((image, f"frame {frame_index}"))
                    except Exception as error:
                        rows.append(
                            failed_metric(
                                bag,
                                current.topic,
                                current.msgtype,
                                frame_index,
                                timestamp_ns,
                                error,
                            )
                        )
                    frame_index += 1
                write_contact_sheet(sheet_images, sheets_dir / f"{stream}.jpg")

    write_metrics(rows, output / "frame_metrics.csv")
    write_stream_summary(rows, output / "stream_summary.csv")
    write_manual_review(rows, output / "manual_review.csv")
    return rows


def write_metrics(rows: list[FrameMetric], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[field.name for field in fields(FrameMetric)])
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def _hamming(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def write_stream_summary(rows: list[FrameMetric], path: Path) -> None:
    groups: dict[tuple[str, str, str], list[FrameMetric]] = {}
    for row in rows:
        groups.setdefault((row.bag, row.topic, row.msgtype), []).append(row)
    fieldnames = [
        "bag",
        "topic",
        "msgtype",
        "samples_requested_or_available",
        "decode_failures",
        "widths",
        "heights",
        "encodings",
        "brightness_mean",
        "contrast_mean",
        "sharpness_mean",
        "near_duplicate_pairs",
        "status",
        "reasons",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for key, items in sorted(groups.items()):
            good = [item for item in items if item.decode_ok]
            reasons: list[str] = []
            failures = len(items) - len(good)
            if failures:
                reasons.append(f"{failures} decode failure(s)")
            widths = sorted({item.width for item in good})
            heights = sorted({item.height for item in good})
            encodings = sorted({item.encoding for item in good})
            if len(widths) > 1 or len(heights) > 1:
                reasons.append("inconsistent resolution")
            if len(encodings) > 1:
                reasons.append("inconsistent encoding")
            hashes = [item.perceptual_hash for item in good]
            near_duplicates = sum(_hamming(left, right) <= 2 for left, right in pairwise(hashes))
            if near_duplicates >= max(2, len(hashes) // 2):
                reasons.append("many sampled frames are near-duplicates")
            writer.writerow(
                {
                    "bag": key[0],
                    "topic": key[1],
                    "msgtype": key[2],
                    "samples_requested_or_available": len(items),
                    "decode_failures": failures,
                    "widths": ";".join(map(str, widths)),
                    "heights": ";".join(map(str, heights)),
                    "encodings": ";".join(encodings),
                    "brightness_mean": np.mean([item.mean_brightness for item in good])
                    if good
                    else math.nan,
                    "contrast_mean": np.mean([item.contrast_std for item in good])
                    if good
                    else math.nan,
                    "sharpness_mean": np.mean([item.laplacian_variance for item in good])
                    if good
                    else math.nan,
                    "near_duplicate_pairs": near_duplicates,
                    "status": "REVIEW" if reasons else "PASS",
                    "reasons": "; ".join(reasons),
                }
            )


def write_manual_review(rows: list[FrameMetric], path: Path) -> None:
    keys = sorted({(row.bag, row.topic, row.msgtype) for row in rows})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "bag",
                "topic",
                "msgtype",
                "reviewer",
                "reviewed_at",
                "image_content_ok",
                "tag_visible",
                "motion_blur_ok",
                "acceptance",
                "notes",
            ]
        )
        for bag, topic, msgtype in keys:
            writer.writerow([bag, topic, msgtype, "", "", "", "", "", "PENDING", ""])
