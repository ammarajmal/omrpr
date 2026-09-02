"""Task 4 (first bounded test): can KLT or RAFT-guided point propagation
bridge the exact official-AprilTag detection gaps Task 3 found (e20_320rpm,
cam1/cam2, ~39% missing frames from motion blur -- see
svr-320rpm-quad-segmentation-failure evidence), without silently drifting
away from the true marker position?

This is the "return-anchor drift gate" the roadmap's quarantined G4 scope
calls for (`ai-context/03_ROADMAP.md`: "AprilTag-anchored bounded KLT,
hidden-frame/synthetic tests, return-anchor drift gates"): AprilTag-anchored
bounded tracking, evaluated only where a real re-detection exists to check
against -- a tracked position is never itself treated as ground truth.

Method, per gap (AprilTag-detected frame `s` -> N missing frames -> AprilTag-
detected frame `e`, both bounds real detections; e20_320rpm cam1/cam2 only,
the only condition/cameras with real gaps per Task 3):

- Baseline: zero-order hold -- predict centroid(e) == centroid(s). Any
  tracker that can't beat this isn't earning its complexity.
- KLT: pyramidal Lucas-Kanade (cv2.calcOpticalFlowPyrLK), seeded at the tag's
  4 corners from frame s, stepped frame-by-frame through s+1..e using the
  real exported PNGs already on disk (external, read-only, from
  `/mnt/phd/fin_phd/omrpr_fin/results/step01` -- the same step01 export Task
  3's detection cache was built from; no new bag processing). Predicted
  centroid = mean of whichever corners are still tracked at e (AprilTag's own
  centroid is confirmed == mean-of-4-corners, verified against
  per_frame_tracks.csv before writing this).
- RAFT+KLT: torchvision's pretrained RAFT (dense optical flow), run on a
  256x256 crop centered on the current point estimate (a "bounded" local
  search, matching the roadmap's own bounded-tracking framing, not a
  full-frame 1920x1080 flow field), stepped frame-by-frame the same way as
  KLT but propagating the single centroid point via the flow vector sampled
  at its own location each step, rather than KLT's 4 independently-tracked
  corners. This specific interpretation of "RAFT+KLT" (RAFT as a drop-in
  correspondence engine in the same iterative point-propagation loop as KLT)
  isn't defined elsewhere in the project docs -- stated explicitly here so
  it can be revisited if a different meaning was intended.
- Drift = pixel distance between each method's predicted centroid at e and
  the real AprilTag centroid detected at e. Reported per gap, not averaged
  away first, since gap length (3-6 frames here) plausibly predicts drift.

Input:  outputs/apriltag-detections/official-v3.4.5/per_frame_tracks.csv
        /mnt/phd/fin_phd/omrpr_fin/results/step01/e20_320rpm/{cam1,cam2}/frame_*.png
Output: outputs/diagnostics/task4_gap_bridging_benchmark.csv
        outputs/reports/task4_gap_bridging_benchmark.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import numpy.typing as npt
import pandas as pd
import torch
from torchvision.models.optical_flow import Raft_Small_Weights, raft_small

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKS_CSV = REPO_ROOT / "outputs/apriltag-detections/official-v3.4.5/per_frame_tracks.csv"
FRAME_ROOT = Path("/mnt/phd/fin_phd/omrpr_fin/results/step01")  # external, read-only raw export
OUT_CSV = REPO_ROOT / "outputs/diagnostics/task4_gap_bridging_benchmark.csv"
OUT_MD = REPO_ROOT / "outputs/reports/task4_gap_bridging_benchmark.md"

CONDITION = "e20_320rpm"  # the only condition with real official-AprilTag gaps (Task 3)
CAMERAS = ("cam1", "cam2")
RAFT_CROP = 512  # local, bounded search window -- not full-frame flow. Must exceed the
# largest per-frame displacement or the true correspondence falls outside the crop and
# gets silently clipped: 256 was tried first and produced 50-140px drift that vanished
# to <2px at 512, confirming it was a crop-boundary artifact, not a real RAFT weakness
# (this specimen moves ~60-90 px/frame at 320 RPM).
CORNER_COLS = [f"corner{i}_{ax}" for i in range(4) for ax in ("x", "y")]


def frame_path(condition: str, camera: str, frame_idx: int) -> Path:
    return FRAME_ROOT / condition / camera / f"frame_{frame_idx:06d}.png"


def load_bgr(condition: str, camera: str, frame_idx: int) -> npt.NDArray[np.uint8]:
    path = frame_path(condition, camera, frame_idx)
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"could not read {path}")
    return img


def find_bounded_gaps(detected: npt.NDArray[np.bool_]) -> list[tuple[int, int]]:
    """Runs of False strictly between two True positions -- (start, end)
    positional indices of the bounding True frames, so start+1..end-1 is the
    missing span. Leading/trailing gaps with no far bound are excluded: there
    is nothing to check drift against."""
    gaps: list[tuple[int, int]] = []
    n = len(detected)
    i = 0
    while i < n:
        if not detected[i]:
            j = i
            while j < n and not detected[j]:
                j += 1
            if i > 0 and j < n:
                gaps.append((i - 1, j))
            i = j
        else:
            i += 1
    return gaps


def klt_corner_track(
    condition: str, camera: str, start_idx: int, end_idx: int, corners0: npt.NDArray[np.float32]
) -> npt.NDArray[np.float64] | None:
    """Pyramidal LK, stepped frame-by-frame across the gap. Corners that lose
    lock partway through are dropped from the mean at the end, not from the
    tracking itself (cv2 requires all points in one call to share status)."""
    lk_params = dict(
        winSize=(21, 21),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
    )
    prev_gray = cv2.cvtColor(load_bgr(condition, camera, start_idx), cv2.COLOR_BGR2GRAY)
    pts = corners0.reshape(-1, 1, 2).astype(np.float32)
    alive = np.ones(len(corners0), dtype=bool)

    for f in range(start_idx + 1, end_idx + 1):
        cur_gray = cv2.cvtColor(load_bgr(condition, camera, f), cv2.COLOR_BGR2GRAY)
        next_pts, status, _err = cv2.calcOpticalFlowPyrLK(
            prev_gray, cur_gray, pts, None, **lk_params
        )
        status = status.reshape(-1).astype(bool)
        alive &= status
        pts = next_pts
        prev_gray = cur_gray
        if not np.any(alive):
            return None

    final = pts.reshape(-1, 2)[alive]
    return final.mean(axis=0)


class RaftPointTracker:
    """Wraps torchvision's pretrained RAFT for the single-point, local-crop
    propagation this script needs -- not a general-purpose flow utility."""

    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu") -> None:
        self.device = device
        weights = Raft_Small_Weights.DEFAULT
        self.transforms = weights.transforms()
        self.model = raft_small(weights=weights, progress=False).to(device).eval()

    @torch.no_grad()
    def flow_at_point(
        self,
        img1_bgr: npt.NDArray[np.uint8],
        img2_bgr: npt.NDArray[np.uint8],
        point_xy: tuple[float, float],
        crop: int = RAFT_CROP,
    ) -> tuple[float, float]:
        h, w = img1_bgr.shape[:2]
        x, y = point_xy
        x0 = int(np.clip(x - crop / 2, 0, w - crop))
        y0 = int(np.clip(y - crop / 2, 0, h - crop))
        c1 = cv2.cvtColor(img1_bgr[y0 : y0 + crop, x0 : x0 + crop], cv2.COLOR_BGR2RGB)
        c2 = cv2.cvtColor(img2_bgr[y0 : y0 + crop, x0 : x0 + crop], cv2.COLOR_BGR2RGB)
        t1 = torch.from_numpy(c1).permute(2, 0, 1).unsqueeze(0)
        t2 = torch.from_numpy(c2).permute(2, 0, 1).unsqueeze(0)
        t1, t2 = self.transforms(t1, t2)
        flows = self.model(t1.to(self.device), t2.to(self.device))
        flow = flows[-1][0].cpu().numpy()  # [2, crop, crop]: channel 0 = dx, 1 = dy

        lx = int(np.clip(round(x - x0), 0, crop - 1))
        ly = int(np.clip(round(y - y0), 0, crop - 1))
        return float(flow[0, ly, lx]), float(flow[1, ly, lx])

    def track(
        self, condition: str, camera: str, start_idx: int, end_idx: int, point0: tuple[float, float]
    ) -> tuple[float, float]:
        x, y = point0
        prev_img = load_bgr(condition, camera, start_idx)
        for f in range(start_idx + 1, end_idx + 1):
            cur_img = load_bgr(condition, camera, f)
            dx, dy = self.flow_at_point(prev_img, cur_img, (x, y))
            x, y = x + dx, y + dy
            prev_img = cur_img
        return x, y


def main() -> None:
    df = pd.read_csv(TRACKS_CSV, low_memory=False)
    raft = RaftPointTracker()
    print(f"RAFT device: {raft.device}")

    rows: list[dict] = []
    for camera in CAMERAS:
        g = df[(df["condition"] == CONDITION) & (df["camera"] == camera)].sort_values("frame_idx")
        g = g.reset_index(drop=True)
        detected = g["detected"].to_numpy()
        gaps = find_bounded_gaps(detected)
        print(f"{camera}: {len(gaps)} bounded gaps")

        for gap_i, (start_pos, end_pos) in enumerate(gaps):
            s_row = g.iloc[start_pos]
            e_row = g.iloc[end_pos]
            start_idx, end_idx = int(s_row["frame_idx"]), int(e_row["frame_idx"])
            gap_len = end_idx - start_idx - 1

            corners0 = s_row[CORNER_COLS].to_numpy(dtype=np.float32).reshape(4, 2)
            centroid0 = np.array([s_row["centroid_x"], s_row["centroid_y"]], dtype=np.float64)
            centroid_true = np.array([e_row["centroid_x"], e_row["centroid_y"]], dtype=np.float64)

            baseline_drift = float(np.linalg.norm(centroid0 - centroid_true))

            klt_pred = klt_corner_track(CONDITION, camera, start_idx, end_idx, corners0)
            klt_drift = (
                float(np.linalg.norm(klt_pred - centroid_true)) if klt_pred is not None else None
            )

            raft_pred = raft.track(CONDITION, camera, start_idx, end_idx, tuple(centroid0))
            raft_drift = float(np.linalg.norm(np.array(raft_pred) - centroid_true))

            rows.append(
                {
                    "camera": camera,
                    "gap_index": gap_i,
                    "start_frame_idx": start_idx,
                    "end_frame_idx": end_idx,
                    "gap_len_frames": gap_len,
                    "baseline_hold_drift_px": round(baseline_drift, 3),
                    "klt_drift_px": round(klt_drift, 3) if klt_drift is not None else None,
                    "raft_drift_px": round(raft_drift, 3),
                }
            )

        print(f"{camera}: done ({len(gaps)} gaps)")

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(out)} rows)")
    print(
        out.groupby("camera")[["baseline_hold_drift_px", "klt_drift_px", "raft_drift_px"]]
        .median()
        .to_string()
    )


if __name__ == "__main__":
    sys.exit(main())
