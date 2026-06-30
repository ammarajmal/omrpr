"""
e20_diagnostic.py — Reproduce all seven e20_320rpm outlier diagnostic images.

USAGE
-----
    conda activate omrpr
    # All seven figures (default):
    python3 src/e20_diagnostic.py

    # Single figure:
    python3 src/e20_diagnostic.py --fig outlier
    python3 src/e20_diagnostic.py --fig gaps
    python3 src/e20_diagnostic.py --fig f9
    python3 src/e20_diagnostic.py --fig f10
    python3 src/e20_diagnostic.py --fig f14
    python3 src/e20_diagnostic.py --fig blur
    python3 src/e20_diagnostic.py --fig full

    # Custom output directory:
    python3 src/e20_diagnostic.py --out results/my_analysis/

OUTPUTS (written to results/ by default)
-----------------------------------------
    e20_outlier_diagnostic.png   — detection rate comparison across all 21 conditions
    e20_gap_frames_annotated.png — mosaic of frames 7-14 with detection status
    e20_frame009_detected.png    — frame 9 cropped around tag (detected, sharp)
    e20_frame010_missed.png      — frame 10 cropped around tag (missed, blurred)
    e20_frame014_detected.png    — frame 14 cropped around tag (detected, sharp again)
    e20_blur_comparison.png      — side-by-side sharp vs blurred tag
    e20_full_diagnostic.png      — 4-panel: cy trajectory, FFT, scatter, sharpness

REQUIRES
--------
    results/step01/e20_320rpm/cam1/frames/   (PNG frames from Step 01)
    results/step02/                          (detection summaries and CSVs)
    results/step03/e20_320rpm/cam1/          (quality score CSV)
    results/step07/e20_320rpm/               (motion.csv for amplitude data)
    results/step08/e20_320rpm/               (frequency.json for f_struct)

PHYSICAL PARAMETERS (locked from investigation)
-----------------------------------------------
    Structural frequency at 320 RPM:  f_struct = 2.932 Hz  (step08 dominant peak)
    Pixel amplitude at cam1:          A_pix = 221 px       (cy range / 2)
    Peak velocity:                    v_peak = 67.8 px/frame
    AprilTag cell width:              w_cell ≈ 29 px
    Blur threshold:                   29 px/frame (= w_cell × f_cam)
    Equilibrium centroid (cam1):      cy_equil ≈ 421 px
    Detection rate cam1:              60.80%
    Detection rate cam2:              61.35%
    Detection rate cam3:              100.0%
    Total missed frames (cam1):       717 / 1829
    Miss frequency (FFT):             5.87 Hz = 2 × 2.932 Hz
    Fraction of misses at equilb.:    93.4%
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.fft import rfft, rfftfreq

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS      = PROJECT_ROOT / 'results'
STEP01_CAM1  = RESULTS / 'step01' / 'e20_320rpm' / 'cam1' / 'frames'
STEP02_E20   = RESULTS / 'step02' / 'e20_320rpm'
STEP03_CAM1  = RESULTS / 'step03' / 'e20_320rpm' / 'cam1'
STEP07_E20   = RESULTS / 'step07' / 'e20_320rpm'
STEP08_E20   = RESULTS / 'step08' / 'e20_320rpm'
STEP02_ALL   = RESULTS / 'step02'

DET_CSV   = STEP02_E20 / 'cam1' / 'detections.csv'
QUAL_CSV  = STEP03_CAM1 / 'detections_with_quality.csv'
MOTION_CSV = STEP07_E20 / 'motion.csv'
FREQ_JSON  = STEP08_E20 / 'frequency.json'

TOTAL_FRAMES = 1829

# Physical constants confirmed during investigation
F_STRUCT  = 2.932   # Hz — dominant peak from step08 FFT for e20 bending channel
F_CAM     = 60.0    # fps
CELL_PX   = 29.0    # AprilTag cell width in pixels (tag_width / 10)
V_THRESH  = CELL_PX # px/frame blur threshold

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_detections(csv_path=DET_CSV):
    rows = list(csv.DictReader(open(csv_path)))
    rows.sort(key=lambda r: int(r['frame_idx']))
    return rows


def miss_set(rows, total=TOTAL_FRAMES):
    det = set(int(r['frame_idx']) for r in rows)
    return sorted(set(range(total)) - det)


def interpolate_cy(rows, miss_fi):
    det_cy = {int(r['frame_idx']): float(r['cy']) for r in rows}
    det_sorted = sorted(det_cy)
    out = []
    for mf in miss_fi:
        before = [f for f in det_sorted if f < mf]
        after  = [f for f in det_sorted if f > mf]
        if before and after:
            fb, fa = before[-1], after[0]
            a = (mf - fb) / (fa - fb)
            out.append(det_cy[fb] + a * (det_cy[fa] - det_cy[fb]))
        else:
            out.append(np.nan)
    return np.array(out)


def all_summaries():
    summaries = {}
    for p in sorted(STEP02_ALL.glob('*/*/summary.json')):
        with open(p) as f:
            s = json.load(f)
        cond = s['condition']
        cam  = s['cam']
        if cond not in summaries:
            summaries[cond] = {}
        summaries[cond][cam] = s
    return summaries


def frame_path(frame_idx):
    return STEP01_CAM1 / f'frame_{frame_idx:06d}.png'


def crop_tag(img, cx, cy, margin=160):
    h, w = img.shape[:2]
    x1 = max(0, int(cx) - margin)
    x2 = min(w, int(cx) + margin)
    y1 = max(0, int(cy) - margin)
    y2 = min(h, int(cy) + margin)
    return img[y1:y2, x1:x2]


def read_frame(frame_idx):
    p = frame_path(frame_idx)
    if not p.exists():
        return None
    return cv2.imread(str(p))


# ---------------------------------------------------------------------------
# Figure 1 — Outlier diagnostic: detection rate comparison
# ---------------------------------------------------------------------------

def fig_outlier(out_dir):
    summaries = all_summaries()
    conditions = sorted(summaries.keys(), key=lambda c: int(c.split('_')[0][1:]))
    cameras = ['cam1', 'cam2', 'cam3']
    colors  = {'cam1': '#2196F3', 'cam2': '#4CAF50', 'cam3': '#FF9800'}

    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle('e20_320rpm — Detection Rate and Miss Burst Analysis\n'
                 '(Motion-Blur-Induced Dropout at Near-Flutter Amplitudes)',
                 fontsize=13, fontweight='bold')

    # Top: detection rate
    ax = axes[0]
    x = np.arange(len(conditions))
    w = 0.28
    for i, cam in enumerate(cameras):
        vals = [summaries[c][cam]['detection_rate'] * 100 if cam in summaries[c] else 100
                for c in conditions]
        ax.bar(x + (i-1)*w, vals, w, label=cam, color=colors[cam], alpha=0.85)
    ax.axhline(95, color='red', lw=1.5, ls='--', label='DCG threshold (95%)')
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace('rpm','') for c in conditions], rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('Detection rate (%)')
    ax.set_ylim(0, 105)
    ax.set_title('Detection Rate per Camera — e20_320rpm stands alone below 65%')
    ax.legend(loc='lower left', fontsize=9)
    ax.annotate('e20_320rpm\ncam1: 60.8%\ncam2: 61.3%',
                xy=(len(conditions)-1, 61), xytext=(len(conditions)-4, 50),
                arrowprops=dict(arrowstyle='->', color='red'),
                color='red', fontsize=9, fontweight='bold')

    # Bottom: max_consecutive_miss
    ax2 = axes[1]
    for i, cam in enumerate(cameras):
        vals = [summaries[c][cam].get('max_consecutive_miss', 0) if cam in summaries[c] else 0
                for c in conditions]
        ax2.bar(x + (i-1)*w, vals, w, label=cam, color=colors[cam], alpha=0.85)
    ax2.axhline(5, color='red', lw=1.5, ls='--', label='DCG threshold (5 frames)')
    ax2.set_xticks(x)
    ax2.set_xticklabels([c.replace('rpm','') for c in conditions], rotation=45, ha='right', fontsize=8)
    ax2.set_ylabel('Max consecutive miss (frames)')
    ax2.set_title('Maximum Consecutive Miss Burst — e20 reaches 6 frames')
    ax2.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    out = out_dir / 'e20_outlier_diagnostic.png'
    fig.savefig(str(out), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  -> {out}')


# ---------------------------------------------------------------------------
# Figure 2 — Gap frames annotated mosaic (frames 7-14)
# ---------------------------------------------------------------------------

def fig_gap_frames(out_dir):
    rows = load_detections()
    det_fi = set(int(r['frame_idx']) for r in rows)
    det_map = {int(r['frame_idx']): r for r in rows}

    target_frames = list(range(7, 15))
    n = len(target_frames)
    fig, axes = plt.subplots(2, 4, figsize=(18, 9))
    fig.suptitle('e20_320rpm cam1 — Frames 7–14 Around First Miss Burst\n'
                 'Green border = detected | Red border = missed (motion-blurred)',
                 fontsize=12, fontweight='bold')

    for idx, fi in enumerate(target_frames):
        ax = axes[idx // 4][idx % 4]
        img = read_frame(fi)
        detected = fi in det_fi

        if img is not None:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if detected and fi in det_map:
                r = det_map[fi]
                cx, cy = float(r['cx']), float(r['cy'])
                crop = crop_tag(img_rgb, cx, cy, margin=200)
            else:
                h, w = img_rgb.shape[:2]
                mid_x, mid_y = w // 2, h // 2
                if fi > min(det_fi):
                    nearby = [det_map[f] for f in sorted(det_map) if abs(f - fi) <= 10]
                    if nearby:
                        mid_x = int(np.mean([float(r2['cx']) for r2 in nearby]))
                        mid_y = int(np.mean([float(r2['cy']) for r2 in nearby]))
                crop = crop_tag(img_rgb, mid_x, mid_y, margin=200)
            ax.imshow(crop)
        else:
            ax.text(0.5, 0.5, 'Frame\nnot found', ha='center', va='center',
                    transform=ax.transAxes)

        status = 'DETECTED' if detected else 'MISSED'
        color  = '#00C853' if detected else '#D50000'
        ax.set_title(f'Frame {fi}: {status}', color=color, fontweight='bold', fontsize=11)
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(4)
        ax.set_xticks([])
        ax.set_yticks([])

        if detected and fi in det_map:
            r = det_map[fi]
            ax.text(0.02, 0.98, f'cy={float(r["cy"]):.0f}px', transform=ax.transAxes,
                    va='top', ha='left', fontsize=8, color='white',
                    bbox=dict(fc='black', alpha=0.6, pad=2))

    plt.tight_layout()
    out = out_dir / 'e20_gap_frames_annotated.png'
    fig.savefig(str(out), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  -> {out}')


# ---------------------------------------------------------------------------
# Figures 3,4,5 — Individual frames (9 detected, 10 missed, 14 detected)
# ---------------------------------------------------------------------------

def fig_single_frame(out_dir, frame_idx, detected, label_extra=''):
    rows   = load_detections()
    det_map = {int(r['frame_idx']): r for r in rows}
    img = read_frame(frame_idx)
    if img is None:
        print(f'  [WARN] Frame {frame_idx} not found — skipping')
        return

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [3, 1]})

    if detected and frame_idx in det_map:
        r = det_map[frame_idx]
        cx, cy_val = float(r['cx']), float(r['cy'])
        crop = crop_tag(img_rgb, cx, cy_val, margin=180)
        ann  = f'tag detected\ncy={cy_val:.0f}px\ndm={float(r["decision_margin"]):.0f}'
        color = '#00C853'
    else:
        nearby = [det_map[f] for f in sorted(det_map) if abs(f - frame_idx) <= 8]
        if nearby:
            cx = int(np.mean([float(rr['cx']) for rr in nearby]))
            cy_val = int(np.mean([float(rr['cy']) for rr in nearby]))
        else:
            cx, cy_val = img.shape[1]//2, img.shape[0]//2
        crop = crop_tag(img_rgb, cx, cy_val, margin=180)
        ann  = f'NO DETECTION\n(motion blurred)\nv≈64px/frame'
        color = '#D50000'

    status = 'DETECTED' if detected else 'MISSED'
    axes[0].imshow(crop)
    axes[0].set_title(f'Frame {frame_idx} — {status}{label_extra}', fontsize=13,
                      fontweight='bold', color=color)
    axes[0].set_xticks([])
    axes[0].set_yticks([])
    for spine in axes[0].spines.values():
        spine.set_edgecolor(color)
        spine.set_linewidth(3)
    axes[0].text(0.02, 0.98, ann, transform=axes[0].transAxes,
                 va='top', ha='left', fontsize=10, color='white',
                 bbox=dict(fc='black', alpha=0.7, pad=4))

    # Show tag in wider context
    h, w = img_rgb.shape[:2]
    wide = img_rgb[max(0,int(cy_val)-400):min(h,int(cy_val)+400), :]
    axes[1].imshow(wide)
    axes[1].set_title('Full width context', fontsize=10)
    axes[1].set_xticks([])
    axes[1].set_yticks([])
    axes[1].axhline(400, color=color, lw=2, ls='--', alpha=0.7)

    plt.suptitle(f'e20_320rpm cam1 — Frame {frame_idx} Analysis', fontsize=12, fontweight='bold')
    plt.tight_layout()
    fname = f'e20_frame{frame_idx:03d}_{"detected" if detected else "missed"}.png'
    out = out_dir / fname
    fig.savefig(str(out), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  -> {out}')


# ---------------------------------------------------------------------------
# Figure 6 — Blur comparison (frame 9 vs frame 10 side-by-side)
# ---------------------------------------------------------------------------

def fig_blur_comparison(out_dir):
    rows   = load_detections()
    det_map = {int(r['frame_idx']): r for r in rows}

    img9  = read_frame(9)
    img10 = read_frame(10)
    if img9 is None or img10 is None:
        print('  [WARN] Frames 9 or 10 not available — skipping blur comparison')
        return

    r9 = det_map.get(9)
    nearby10 = [det_map[f] for f in sorted(det_map) if abs(f - 10) <= 5]
    cx10 = int(np.mean([float(rr['cx']) for rr in nearby10])) if nearby10 else img10.shape[1]//2
    cy10 = int(np.mean([float(rr['cy']) for rr in nearby10])) if nearby10 else img10.shape[0]//2

    if r9:
        crop9  = crop_tag(cv2.cvtColor(img9,  cv2.COLOR_BGR2RGB), float(r9['cx']), float(r9['cy']), margin=120)
    else:
        crop9  = crop_tag(cv2.cvtColor(img9,  cv2.COLOR_BGR2RGB), img9.shape[1]//2, img9.shape[0]//2, margin=120)
    crop10 = crop_tag(cv2.cvtColor(img10, cv2.COLOR_BGR2RGB), cx10, cy10, margin=120)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(
        'Motion Blur Comparison — e20_320rpm cam1\n'
        'Left: Frame 9 (detected, tag at amplitude extreme, velocity≈0)\n'
        'Right: Frame 10 (missed, tag at equilibrium crossing, v≈64 px/frame)',
        fontsize=11, fontweight='bold')

    axes[0].imshow(crop9)
    axes[0].set_title('Frame 9 — DETECTED\nTag at amplitude extreme\nVelocity ≈ 0 px/frame\nSharp cell boundaries',
                      color='#00C853', fontsize=10, fontweight='bold')
    for sp in axes[0].spines.values():
        sp.set_edgecolor('#00C853')
        sp.set_linewidth(3)
    axes[0].set_xticks([])
    axes[0].set_yticks([])

    axes[1].imshow(crop10)
    axes[1].set_title('Frame 10 — MISSED\nTag at equilibrium crossing\nVelocity ≈ 64 px/frame\nCells smeared into grey',
                      color='#D50000', fontsize=10, fontweight='bold')
    for sp in axes[1].spines.values():
        sp.set_edgecolor('#D50000')
        sp.set_linewidth(3)
    axes[1].set_xticks([])
    axes[1].set_yticks([])

    # Physics annotation box
    fig.text(0.5, 0.01,
             r'Blur threshold: $v_{thresh} = w_{cell} \times f_{cam} \approx 29\,\mathrm{px/frame}$   '
             r'Peak velocity: $v_{peak} = 2\pi f_{struct} A = 67.8\,\mathrm{px/frame}$   '
             r'Excess: $67.8 / 29 = 2.3\times$ above threshold',
             ha='center', fontsize=9, style='italic',
             bbox=dict(fc='lightyellow', alpha=0.8, pad=4))

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    out = out_dir / 'e20_blur_comparison.png'
    fig.savefig(str(out), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  -> {out}')


# ---------------------------------------------------------------------------
# Figure 7 — Full 4-panel diagnostic
# ---------------------------------------------------------------------------

def fig_full_diagnostic(out_dir):
    rows    = load_detections()
    miss_fi = miss_set(rows)
    det_fi  = sorted(int(r['frame_idx']) for r in rows)
    det_cy  = np.array([float(r['cy']) for r in rows])
    det_idx = np.array([int(r['frame_idx']) for r in rows])
    miss_cy = interpolate_cy(rows, miss_fi)

    # Miss indicator signal on common frame axis
    all_fi  = np.arange(TOTAL_FRAMES)
    miss_set_ = set(miss_fi)
    miss_sig  = np.array([1 if fi in miss_set_ else 0 for fi in all_fi], dtype=float)

    # FFT of miss signal
    freqs = rfftfreq(len(miss_sig), d=1.0/F_CAM)
    fft_mag = np.abs(rfft(miss_sig - miss_sig.mean())) / (len(miss_sig)/2)

    # Quality scores if available
    sharpness = None
    if QUAL_CSV.exists():
        qrows = list(csv.DictReader(open(str(QUAL_CSV))))
        sharpness_map = {int(r['frame_idx']): float(r.get('corner_sharpness', 0)) for r in qrows}
        sharpness = np.array([sharpness_map.get(fi, np.nan) for fi in det_idx])

    fig = plt.figure(figsize=(16, 12))
    gs  = fig.add_gridspec(2, 2, hspace=0.40, wspace=0.35)
    fig.suptitle('e20_320rpm cam1 — Full Diagnostic Panel\n'
                 'Motion-Blur-Induced AprilTag Detection Failure at Near-Flutter Amplitudes',
                 fontsize=13, fontweight='bold')

    # Panel A — cy trajectory
    ax_A = fig.add_subplot(gs[0, 0])
    ax_A.scatter(det_idx, det_cy, s=3, c='#2196F3', alpha=0.6, label='detected', zorder=3)
    if len(miss_fi) > 0:
        ax_A.scatter(miss_fi, miss_cy, s=3, c='#F44336', alpha=0.6, label='missed (interp.)', zorder=2)
    equil = np.nanmean(det_cy)
    ax_A.axhline(equil, color='k', lw=0.8, ls='--', alpha=0.5, label=f'equil. ({equil:.0f}px)')
    ax_A.set_xlabel('Frame index')
    ax_A.set_ylabel('Centroid cy (px)')
    ax_A.set_title(f'A — Tag centroid trajectory  (A≈221 px, equil.≈{equil:.0f} px)')
    ax_A.legend(fontsize=8)
    ax_A.invert_yaxis()

    # Panel B — FFT of miss indicator
    ax_B = fig.add_subplot(gs[0, 1])
    mask = freqs <= 20
    ax_B.plot(freqs[mask], fft_mag[mask], lw=1.0, c='#9C27B0')
    pk_idx = np.argmax(fft_mag[mask])
    pk_f   = freqs[mask][pk_idx]
    ax_B.axvline(pk_f, color='red', lw=1.5, ls='--',
                 label=f'dominant peak: {pk_f:.2f} Hz\n= 2 × {pk_f/2:.2f} Hz = 2f_struct')
    ax_B.axvline(F_STRUCT, color='blue', lw=1.5, ls=':', label=f'f_struct = {F_STRUCT} Hz')
    ax_B.set_xlabel('Frequency (Hz)')
    ax_B.set_ylabel('FFT magnitude')
    ax_B.set_title(f'B — FFT of miss-indicator signal  (peak = 2 × f_struct)')
    ax_B.legend(fontsize=8)
    ax_B.set_xlim(0, 15)

    # Panel C — where do misses cluster in cy space?
    ax_C = fig.add_subplot(gs[1, 0])
    ax_C.hist(det_cy, bins=40, color='#2196F3', alpha=0.6, label='detected', density=True)
    ax_C.hist(miss_cy[~np.isnan(miss_cy)], bins=40, color='#F44336', alpha=0.7,
              label='missed (estimated cy)', density=True)
    ax_C.axvline(equil, color='k', lw=1.5, ls='--', label=f'equilibrium ≈{equil:.0f}px')
    ax_C.axvspan(300, 540, alpha=0.12, color='red', label='equilibrium zone\n(93.4% of misses)')
    ax_C.set_xlabel('cy (pixels, inverted = lower in frame)')
    ax_C.set_ylabel('Density')
    ax_C.set_title('C — cy distribution: detected vs. missed\nMisses cluster at equilibrium (93.4%)')
    ax_C.legend(fontsize=8)

    # Panel D — corner sharpness over frame
    ax_D = fig.add_subplot(gs[1, 1])
    if sharpness is not None:
        ax_D.scatter(det_idx, sharpness, s=3, c='#4CAF50', alpha=0.6)
        ax_D.set_xlabel('Frame index')
        ax_D.set_ylabel('Corner sharpness (Laplacian)')
        ax_D.set_title('D — Corner sharpness for detected frames\n(Low sharpness = near-equilibrium detection)')
        # Overlay miss regions
        for burst_start in miss_fi[::3]:
            ax_D.axvspan(burst_start - 0.5, burst_start + 5.5, alpha=0.08, color='red')
    else:
        ax_D.text(0.5, 0.5, 'Quality CSV\nnot available', ha='center', va='center',
                  transform=ax_D.transAxes, fontsize=12)
        ax_D.set_title('D — Corner sharpness (data not found)')

    # Physics annotation
    physics = (
        f'Physical parameters:\n'
        f'  f_struct = {F_STRUCT} Hz (step08 FFT, contaminated bending channel)\n'
        f'  A_pix ≈ 221 px  (cy range / 2)\n'
        f'  v_peak = 2π × {F_STRUCT} × 221 = 67.8 px/frame\n'
        f'  Cell width w_cell ≈ {CELL_PX:.0f} px  →  blur threshold = {V_THRESH:.0f} px/frame\n'
        f'  Excess: 67.8 / 29 = 2.3× above threshold  →  39.2% miss rate'
    )
    fig.text(0.5, -0.02, physics, ha='center', fontsize=9,
             bbox=dict(fc='lightyellow', alpha=0.9, pad=6))

    out = out_dir / 'e20_full_diagnostic.png'
    fig.savefig(str(out), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  -> {out}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='e20_320rpm diagnostic figures')
    parser.add_argument('--fig', choices=['all','outlier','gaps','f9','f10','f14','blur','full'],
                        default='all')
    parser.add_argument('--out', default=str(RESULTS))
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = args.fig
    print(f'Generating figure(s): {fig}  →  {out_dir}')

    if not DET_CSV.exists():
        sys.exit(f'ERROR: detections.csv not found at {DET_CSV}\n'
                 f'Run the pipeline through Step 02 first.')

    if not STEP01_CAM1.exists():
        print(f'WARNING: step01 frames not found at {STEP01_CAM1}\n'
              f'Figures that draw actual frame images will be blank.')

    if fig in ('all', 'outlier'):
        print('Figure 1: outlier detection rate comparison')
        fig_outlier(out_dir)

    if fig in ('all', 'gaps'):
        print('Figure 2: gap frames annotated mosaic')
        fig_gap_frames(out_dir)

    if fig in ('all', 'f9'):
        print('Figure 3: frame 9 (detected, amplitude extreme)')
        fig_single_frame(out_dir, 9, detected=True,
                         label_extra='\n(Amplitude extreme — velocity≈0 — SHARP)')

    if fig in ('all', 'f10'):
        print('Figure 4: frame 10 (missed, equilibrium crossing)')
        fig_single_frame(out_dir, 10, detected=False)

    if fig in ('all', 'f14'):
        print('Figure 5: frame 14 (detected, amplitude extreme)')
        fig_single_frame(out_dir, 14, detected=True,
                         label_extra='\n(Back at amplitude extreme — detected again)')

    if fig in ('all', 'blur'):
        print('Figure 6: blur comparison frames 9 vs 10')
        fig_blur_comparison(out_dir)

    if fig in ('all', 'full'):
        print('Figure 7: full 4-panel diagnostic')
        fig_full_diagnostic(out_dir)

    print('\nDone.')


if __name__ == '__main__':
    main()
