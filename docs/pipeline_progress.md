# OMRPR Pipeline Progress

| Step | Name | Status | Gate | Date | Notes |
|------|------|--------|------|------|-------|
| 00 | Bag Audit | COMPLETE | PASS | 2026-06-23 | All 21 bags; max skew 21.5 ms (e6) |
| 01 | Frame Export | COMPLETE | PASS | 2026-06-23 | Re-verified 21/21; 0 decode failures; worst gap 31.1 ms (e8 cam3) |
| 02 | AprilTag Detection | COMPLETE | PASS | 2026-06-23 | Re-verified; 61/63 streams at 100%; e20 cam1/cam2 60.8-61.3%, max miss 6 |
| 02b | DCG Gate | COMPLETE | PASS | 2026-06-16 | e20 excluded; N=3 threshold |
| 03 | Quality Scoring | COMPLETE | PASS | 2026-06-23 | Re-ran core B0 on e7 then --all; 63/63 streams low_q=0; B0 remains diagnostic-only |
| 04 | Pose Estimation | COMPLETE | PASS | 2026-06-23 | Re-ran on e7 then --all; 63/63 streams OK; worst reproj e20 cam3 1.716 px |
| 05 | Synchronisation | COMPLETE | PASS | 2026-06-23 | Re-ran on e7 then --all; common 60 Hz; normal max start spread 20.03 ms, e20 dropout anomaly 70.94 ms |
| 06 | Baseline Fusion | COMPLETE | PASS | 2026-06-23 | Re-ran on e7 then --all; e7 cam1-cam2 388.0 mm -> 2.0529 mm; e20 cam3 pairs >15 mm |
| 07 | Motion Decompose | COMPLETE | PASS | 2026-06-23 | Re-ran on e7 then --all; e7 cam1-cam2 r=0.999012; low-r warnings only in low-signal e0-e2 |
| 08 | Frequency Analysis | COMPLETE | PASS | 2026-06-23 | User-ran e7 then --all; 21/21 OK; 3 regimes confirmed; zero low_snr flags |
| 09 | Uncertainty | COMPLETE | PASS | 2026-06-23 | Re-ran --smoke-test then --all; 4/4 gates PASS; noise floor 0.0043/0.0052 mm; timing drift 20.0 ms |
| 10 | LDV Comparison | COMPLETE | FAIL/PASS | 2026-06-24 | Re-ran smoke then full; bend r=0.845 FAIL explained; tors r=0.940 PASS; stable ratios 1.339x/0.599x |
| 11 | RTS Smoothing | COMPLETE | PASS | 2026-06-24 | Re-ran on e7 then full default run; 21/21 PASS; 0.00 ms phase; stable ratio 0.999; e0/e1 0.961-0.966 |
| 12 | Figures/Tables | COMPLETE | PASS | 2026-06-24 | Re-ran full generation; 5 figs, 2 tables, 0 violations; fixed stale Step 10 footnote 0.833/17 -> 0.845/18 |
