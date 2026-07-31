from types import SimpleNamespace

import cv2
import numpy as np

from omrpr_analysis.image_audit import (
    decode_compressed,
    decode_raw,
    deterministic_indices,
    perceptual_hash,
)


def test_deterministic_indices_include_boundaries() -> None:
    assert deterministic_indices(100, 5) == {0, 24, 49, 74, 99}
    assert deterministic_indices(2, 12) == {0, 1}


def test_decode_bgr8_with_row_padding() -> None:
    pixels = np.arange(18, dtype=np.uint8).reshape(2, 9)
    padded = np.pad(pixels, ((0, 0), (0, 3)))
    message = SimpleNamespace(encoding="bgr8", height=2, width=3, step=12, data=padded.ravel())
    decoded, encoding = decode_raw(message)
    assert encoding == "bgr8"
    assert decoded.shape == (2, 3, 3)
    np.testing.assert_array_equal(decoded.reshape(2, 9), pixels)


def test_decode_compressed_jpeg() -> None:
    source = np.full((20, 30, 3), 127, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", source)
    assert ok
    decoded, _ = decode_compressed(SimpleNamespace(data=encoded, format="jpeg"))
    assert decoded.shape == source.shape


def test_perceptual_hash_is_stable() -> None:
    gray = np.arange(64, dtype=np.uint8).reshape(8, 8)
    assert perceptual_hash(gray) == perceptual_hash(gray.copy())
