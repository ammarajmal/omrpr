# Step 01 — Calibration-input audit

## Goal

Complete this stage reproducibly without bypassing prior gates.

## Required evidence

- configuration snapshot;
- input inventory and checksums;
- command and software versions;
- generated outputs;
- tests or verification;
- limitations and exact next action.

## Approval

```bash
uv run omrpr pipeline approve --step 1 --evidence outputs/reports/step_01_review.md
```
