from __future__ import annotations

import json
from pathlib import Path

from .paths import ProjectPaths

STEPS = {
    0: "Source inventory and bag audit",
    1: "Calibration-input audit",
    2: "Fresh camera calibration",
    3: "Official AprilTag verification",
    4: "Static precision characterization",
    5: "WTT detection and pose export",
    6: "Timestamp matching and per-tag fusion",
    7: "Response-channel construction",
    8: "LDV import and preprocessing",
    9: "Condition-level benchmarking",
    10: "Frequency and uncertainty analysis",
    11: "Manuscript outputs and consistency audit",
    12: "Submission readiness",
}


def gate_path(step: int) -> Path:
    return ProjectPaths.discover().root / "state/gates" / f"step_{step:02d}.json"


def approved(step: int) -> bool:
    path = gate_path(step)
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return payload.get("approved") is True


def approve(step: int, evidence: Path) -> Path:
    raise RuntimeError(
        "Legacy Step 00-12 approval is retired. Record evidence and checkpoint "
        "status in the OMRPR-NS-001 progress ledger, then run "
        "structural-vision-research/scripts/research_supervisor.py validate."
    )
