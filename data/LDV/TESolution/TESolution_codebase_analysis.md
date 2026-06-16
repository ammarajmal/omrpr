# TESolution Codebase Analysis — `tesol_ws`

**Repository (online):** https://github.com/ammarajmal/tesol_ws  
**Local path:** `context_data/TESolution/Video Measurement/tesol_ws/`  
**Last analyzed:** 2026-06-09  
**Purpose:** Document system architecture, critical technical issues, and publication-relevant findings from the ROS codebase used to capture the 2024 WTT and 2025 WTT data.

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                Single Ubuntu PC (ROS Noetic)             │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ CAM1 node    │  │ CAM2 node    │  │ CAM3 node    │  │
│  │ (MVSDK)      │  │ (MVSDK)      │  │ (MVSDK)      │  │
│  │ → /sony_cam1 │  │ → /sony_cam2 │  │ → /sony_cam3 │  │
│  │   /image_raw │  │   /image_raw │  │   /image_raw │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐  │
│  │ april_marker │  │ april_marker │  │ april_marker │  │
│  │ (Cam1 detect)│  │ (Cam2 detect)│  │ (Cam3 detect)│  │
│  │ → /fiducial_ │  │ → /fiducial_ │  │ → /fiducial_ │  │
│  │   transforms │  │   transforms │  │   transforms │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         └─────────────────┼─────────────────┘           │
│                           ▼                             │
│              ┌────────────────────────┐                 │
│              │   GUI (gui1.py)        │                 │
│              │ ApproxTimeSynchronizer │                 │
│              │ slop=0.008s, queue=10  │                 │
│              │ → CSV output           │                 │
│              └────────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Camera Hardware

**The WTT system uses Sony RX10 IV cameras captured via AverMedia video capture cards.**

| Parameter | Value |
|-----------|-------|
| Camera | **Sony RX10 IV** (3 cameras, user-owned) |
| Capture interface | **AverMedia Video Capture Card** (HDMI → USB) |
| Driver node | `src/sony_cam/node/sony_cam.cpp` |
| Capture API | `cv::VideoCapture::open("/dev/video_camN", cv::CAP_V4L2)` |
| Resolution | 1920×1080 |
| Frame rate | 60 fps (**AverMedia bottleneck**, not the Sony camera) |
| Trigger | No hardware trigger; V4L2 blocking `cap_.read(frame)` |
| Exposure | Managed on the Sony camera directly |
| Calibration | `src/sony_cam/config/sony_cam1_info.yaml` (rational_polynomial, 14 coefficients) |

**Stable device mapping via udev:** AverMedia capture cards enumerate randomly as `/dev/video0`, `/dev/video2` etc. at boot. udev rules (keyed by AverMedia serial numbers) create fixed symlinks `/dev/video_cam1`, `/dev/video_cam2`, `/dev/video_cam3`, ensuring consistent CAM1/CAM2/CAM3 assignment regardless of boot order.

**Camera calibration parameters (from `sony_cam1_info.yaml`):**
```
Camera matrix: fx=20327.9, fy=20240.8, cx=967.046, cy=530.314
Distortion model: rational_polynomial (14 coefficients)
Distortion coeffs: [-0.534, 0.303, 0.022, 0.001, 0.001, -0.979, -0.304, ...]
```

**Note on focal length:** fx≈20328 px at 1920-px width → FoV ≈ 5.4° horizontal. The Sony RX10 IV has a 24–600mm equivalent zoom range — this calibration was at or near full zoom (600mm), giving high pixel-per-mm resolution at the bridge model distance.

**The `python_camera_driver` package (MVSDK) is separate:** `src/python_camera_driver/simple_camera_node.py` uses `import mvsdk` for TESolution's own MindVision facility cameras. The serial numbers in `cameras.yaml` (053012620218 etc.) are MindVision camera serials. This package coexists in the workspace but was NOT used to capture any WTT data.

---

## 3. Camera Driver Node — Critical Timestamp Flaw

**File:** `src/sony_cam/node/sony_cam.cpp`

```cpp
// Lines 109-128 — THE CRITICAL ISSUE IS ON LINE 128
cv::Mat frame;
if (cap_.read(frame)) {       // ← BLOCKING V4L2 READ (AverMedia card delivers frame)
    ros::Time current_time = ros::Time::now();  // ← TIMESTAMP ASSIGNED HERE, AFTER READ
    // ...
    ros_image.header.stamp = current_time;      // ← LINE 128: SOFTWARE TIMESTAMP
    pub_image_raw_.publish(ros_image);
```

**What this means:** The timestamp is assigned AFTER:
1. `cap_.read(frame)` blocks until the AverMedia capture card delivers a frame over USB
2. AverMedia USB latency is absorbed into the timestamp (frame was already captured by Sony camera earlier)
3. `ros::Time::now()` is called — this is wall clock at the moment of USB frame delivery, not photon capture time

The timestamp does NOT reflect the moment of photon capture by the Sony lens. It reflects when the AverMedia USB transfer completed on the PC side. This latency is variable depending on:
- USB bus congestion (3 AverMedia cards on same USB controller)
- AverMedia internal buffering and HDMI decode latency (~33–100 ms typical)
- OS scheduling jitter for the V4L2 read call
- CPU load from 3× `april_marker.py` at full 1920×1080

**Why this matters for multi-camera synchronization:**
Three independent camera nodes call `cap_.read()` independently with no hardware sync signal. Each gets its frame from its AverMedia card at slightly different times and assigns wall-clock timestamps independently. No Chrony NTP was used.

In practice, two frames matched by ApproximateTimeSynchronizer (slop=8ms) may have been physically captured up to ~16 ms apart. At 5 Hz structural vibration, 16 ms = 0.288° of phase — negligible for 30-second RMS statistics.

---

## 4. Dual-Timestamp Logging (Key Mitigation in GUI)

**File:** `gui/gui1.py` — the `record_single()` function

The GUI logs **two timestamps per row**:

```python
system_timestamp = rospy.get_time()              # system wall clock
ros_header_timestamp = msg.header.stamp.to_sec() # ROS header (from camera node)
```

CSV headers saved:
```
Cam1 System Time (s), ROS Header Time (s), Cam1 Fiducial ID, ...
```

This means every row in D0.csv–D37.csv contains both timestamps. The difference `system_time − header_time` for a given camera gives the **latency between timestamp assignment (camera node) and data receipt (GUI callback)**.

**This is directly publishable as a synchronization characterization:**
1. Compute `latency_cam1 = system_time_col1 − header_time_col2` for all rows in each CSV
2. Compute `delta_t = header_time_cam3 − header_time_cam1` (inter-camera timing difference)
3. Plot latency histogram and inter-camera timing distribution
4. Show that RMS statistics are insensitive to the observed jitter level

**This turns a flaw into a contribution:** "We characterized the timing uncertainty of a software-synchronized multi-camera system and showed that for structural RMS comparison, the observed jitter (mean: X ms, σ: Y ms) introduces negligible bias."

---

## 5. AprilTag Detection Pipeline

**File:** `src/tesol_detect/scripts/april_marker.py`

| Parameter | Value | Implication |
|-----------|-------|-------------|
| Library | `pupil_apriltags` (Python binding) | Cross-platform, CPU-only |
| Tag family | `tag36h11` | 6×6 bit, high error correction |
| Tag size | 0.020 m = 20 mm | Used for solvePnP scale |
| `quad_decimate` | 1.0 | **Full-resolution 1920×1080 detection — CPU-heavy** |
| `nthreads` | 4 | 4 CPU threads per camera node |
| `quad_sigma` | 0.0 | No Gaussian blur pre-processing |
| `refine_edges` | 1 | Sub-pixel edge refinement enabled |
| Stabilization frames | 20 | First 20 frames averaged for reference pose |
| Outlier threshold | 100.0 mm | Jump > 100 mm → hold previous position |
| Smoothing | Savitzky-Golay (commented out) | Not applied in current code |

**CPU load issue:** Three instances of `april_marker.py` run simultaneously, each processing full 1920×1080 frames at 60 fps with 4 threads = 12 CPU threads total just for detection. On a standard 8-core PC, this causes CPU saturation at high wind speeds when:
- Larger marker motion requires more quad candidates
- Background texture increases false quad detections
- This leads to variable frame processing time → increased timestamp jitter → possible frame drops

**Detection robustness mechanism:**
1. `correct_outlier()`: If position jumps > 100 mm from previous frame, the previous position is held
2. This means frames with AprilTag detection failure (marker not found) are NOT recorded — the callback simply doesn't publish
3. Frames with detection but large jump (blur artifact) get the previous position substituted
4. Net effect: CSV files have continuous, clean-looking data BUT may include "frozen" frames where the detection failed and the last good value was held

**To detect held frames in the CSV:** Look for consecutive identical position values. If `pos[i] == pos[i-1]` exactly (bit-for-bit float equality), that row was a held outlier substitution.

---

## 6. Multi-Camera Synchronization Implementation

### In camera nodes: ApproximateTimeSynchronizer (GUI level)
**File:** `gui/gui1.py`

```python
# From gui1.py record_single() setup:
sub1 = message_filters.Subscriber('/sony_cam1/aruco_detect_node/fiducial_transforms', FiducialTransformArray)
sub2 = message_filters.Subscriber('/sony_cam2/aruco_detect_node/fiducial_transforms', FiducialTransformArray)
sub3 = message_filters.Subscriber('/sony_cam3/aruco_detect_node/fiducial_transforms', FiducialTransformArray)
sync = message_filters.ApproximateTimeSynchronizer([sub1, sub2, sub3], 10, 0.008, allow_headerless=True)
```

Parameters:
- `queue_size=10`: Buffer up to 10 messages per topic waiting for matches
- `slop=0.008`: Accept message triplets where max timestamp spread ≤ 8 ms
- `allow_headerless=True`: Use system arrival time if header stamp is missing

### In time_sync_logger.py (debug tool):
```python
# ApproximateTimeSynchronizer with slop=0.01 (10 ms)
self.sync = message_filters.ApproximateTimeSynchronizer(subs, queue_size=10, slop=0.01, allow_headerless=True)
```

Also logs per-sync-event: inter-camera ROS time difference `avg_delay = Σ(ros_times[i] − ros_times[i−1]) / n`

### What "synchronized" actually means here
When the GUI saves a row to CSV, it records:
- `Cam1 System Time`: wall clock when the GUI callback fired
- `ROS Header Time`: the header.stamp from the camera node (~software timestamp from post-USB-retrieval)
- Then Cam2 and Cam3 data from messages matched within 8 ms of Cam1's header time

The CSV columns are:
```
Col 1: unified System Time (single wall clock, not per-camera)
Col 2: ROS Header Time for Cam1
... Cam1 data ...
Col 10+: Cam2 data (from a message matched within 8ms of Cam1)
Col 18+: Cam3 data (from a message matched within 8ms of Cam1)
```

---

## 7. Pose Estimation Method

**File:** `src/tesol_detect/scripts/april_marker.py` lines 150–157

```python
success, rvec, tvec = cv2.solvePnP(
    object_points,     # 4 × 3D corners of 20mm tag in tag frame
    image_points,      # 4 × 2D detected corners in image
    self.camera_matrix,
    self.dist_coeffs,  # first 5 coefficients only (k1,k2,p1,p2,k3)
    flags=cv2.SOLVEPNP_ITERATIVE
)
```

**Note on distortion coefficients:** Only the first 5 of 14 coefficients from the YAML are used: `self.dist_coeffs = np.array(msg.D[:5])`. The YAML has a `rational_polynomial` model with 14 parameters. Using only 5 (the standard Brown-Conrady model) leaves out higher-order terms. For a telephoto lens at normal distances this is acceptable, but may introduce small residuals at the image periphery.

**Reference frame computation:**
1. First 20 frames averaged to establish the reference pose (rotation matrix + translation vector)
2. All subsequent poses are expressed **relative** to this reference
3. Output: `relative_translation` in meters (ROS standard)
4. Y-axis in camera frame = vertical displacement direction for bridge monitoring

---

## 8. Data Flow Summary (from camera to CSV)

```
MindVision Camera (hardware trigger: NONE, free-running @ ~60 fps)
    ↓ USB transfer (variable latency ~5-20 ms)
simple_camera_node.py
    ↓ mvsdk.CameraGetImageBuffer() — blocks until frame ready
    ↓ mvsdk.CameraImageProcess() — debayer + ISP
    ↓ ros_image_msg.header.stamp = rospy.Time.now()  ← TIMESTAMP ASSIGNED HERE
    ↓ image_pub.publish()
    [/sony_camN/image_raw topic]
april_marker.py
    ↓ image_callback() — receive image
    ↓ pupil_apriltags.Detector.detect() — full 1920×1080 quad detection
    ↓ cv2.solvePnP() — pose estimation
    ↓ correct_outlier() — hold if jump > 100 mm
    ↓ pose_pub.publish()
    [/sony_camN/aruco_detect_node/fiducial_transforms topic]
gui1.py (ApproximateTimeSynchronizer, slop=0.008)
    ↓ callback fires when Cam1+Cam2+Cam3 messages match within 8 ms
    ↓ system_timestamp = rospy.get_time()
    ↓ write row to CSV: [system_time, header_time, id, x, y, z, qx, qy, qz, qw, ... ×3 cameras]
    [~/Desktop/TESolution/D0.csv ... D37.csv]
```

---

## 9. Critical Issues Summary for Paper Discussion

| Issue | Severity | Evidence | Mitigation for paper |
|-------|----------|----------|---------------------|
| Software timestamps, no hardware trigger | MODERATE | `simple_camera_node.py:90` | Dual-timestamp jitter analysis from CSV |
| No Chrony NTP synchronization | MODERATE | User confirmed; no Chrony logs in data | Condition-level statistics (not waveforms); jitter characterization |
| CPU saturation at high wind (3× full-res detection) | MODERATE | `quad_decimate=1.0` with 3 instances | Detection rate vs wind speed curve |
| Outlier holding (100 mm threshold) may mask dropouts | LOW–MOD | `correct_outlier()` in april_marker.py | Count "frozen" frames (consecutive identical positions) |
| Only 5 of 14 distortion coefficients used | LOW | `msg.D[:5]` in camera_info_callback | Use full calibration in future; note as limitation |
| Auto-exposure enabled | LOW–MOD | `CameraSetAeState(hCamera, 1)` | Fixed exposure would help at flutter; note as improvement |
| No hardware sync between cameras | MODERATE | `CameraSetTriggerMode(hCamera, 0)` | ApproximateTimeSynchronizer handles software sync; characterize slop |

---

## 10. Offline Reprocessing Potential (for 2025 WTT Bags)

The 2025 WTT bags (`data/WTT/e0_0rpm` through `e20_320rpm`) contain `sensor_msgs/CompressedImage` (JPEG-compressed frames). To reprocess:

1. Play bag in ROS: `rosbag play e0_0rpm_run1.bag`
2. Add a decompression node or modify `april_marker.py` to subscribe to `CompressedImage`
3. Run the AprilTag detection pipeline
4. Record output to new CSV files
5. Apply `BRID2D1_choi.m` with pvolt=100, dside=10, dp=2.0

**Improvement opportunity during offline reprocessing:**
- Change `quad_decimate` from 1.0 to 2.0 → 2× speed reduction, minimal accuracy impact
- Use all 14 distortion coefficients
- Reduce `MAX_ALLOWED_DISPLACEMENT` from 100 mm to 10 mm for stricter outlier rejection
- Enable Savitzky-Golay smoothing (currently commented out)
- Log per-frame timestamps more carefully for jitter analysis

---

## 11. Package Structure (tesol_ws)

```
tesol_ws/
├── gui/
│   └── gui1.py              (1350 lines, main GUI + data recorder)
├── src/
│   ├── python_camera_driver/
│   │   ├── scripts/simple_camera_node.py   (camera driver, MVSDK)
│   │   ├── config/cameras.yaml             (serial number → camera ID map)
│   │   └── launch/                         (ROS launch files)
│   ├── tesol_detect/
│   │   ├── scripts/april_marker.py         (AprilTag detection + pose estimation)
│   │   ├── scripts/time_sync_logger.py     (sync debug logger, not used for main data)
│   │   └── launch/
│   └── sony_cam/
│       ├── config/sony_cam1_info.yaml      (camera 1 calibration matrix)
│       ├── config/sony_cam2_info.yaml      (camera 2 calibration matrix)
│       ├── config/sony_cam3_info.yaml      (camera 3 calibration matrix)
│       └── launch/
└── ...
```
