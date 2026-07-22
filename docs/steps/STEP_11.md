# Step 11 — Manuscript outputs and consistency audit

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
uv run omrpr pipeline approve --step 11 --evidence outputs/reports/step_11_review.md
```
