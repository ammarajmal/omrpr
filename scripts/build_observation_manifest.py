#!/usr/bin/env python3
"""Build the expected G1 observation manifest from reviewed configuration."""

from __future__ import annotations

import csv
from pathlib import Path

from omrpr_analysis.observation_control import load_control, validate_conditions

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "observation_id",
    "campaign",
    "session",
    "condition_id",
    "nominal_rpm",
    "instrument",
    "expected_tag_id",
    "physical_location",
    "primary_observable",
    "units",
    "analysis_role",
    "stable_summary",
    "cross_instrument_alignment",
    "planned_admissibility",
    "permitted_use",
]


def main() -> None:
    control = load_control(ROOT / "configs/observation-control.yaml")
    conditions = validate_conditions(ROOT / "configs/conditions.csv", control)
    campaign = control["campaigns"]["camera"]
    rows: list[dict[str, object]] = []
    for condition in conditions:
        condition_id = condition["condition_id"]
        special = control["special_conditions"].get(condition_id, {})
        for camera, observation in control["camera_observations"].items():
            planned = str(special.get(camera, "pending_measurement"))
            if condition_id == "e20_320rpm" and camera == "cam3":
                permitted = "camera_only_image_plane_diagnostic"
            elif planned == "fail":
                permitted = "failure_diagnostic"
            else:
                permitted = "subject_to_measured_admissibility"
            rows.append(
                {
                    "observation_id": f"{campaign['id']}-{condition_id}-{camera}",
                    "campaign": campaign["id"],
                    "session": campaign["session"],
                    "condition_id": condition_id,
                    "nominal_rpm": condition["rpm"],
                    "instrument": camera,
                    "expected_tag_id": observation["expected_tag_id"],
                    "physical_location": observation["physical_location"],
                    "primary_observable": control["primary_observable"]["name"],
                    "units": control["primary_observable"]["units"],
                    "analysis_role": special.get("role", condition["analysis_role"]),
                    "stable_summary": special.get("stable_summary", True),
                    "cross_instrument_alignment": campaign["cross_instrument_alignment"],
                    "planned_admissibility": planned,
                    "permitted_use": permitted,
                }
            )

    target = ROOT / "configs/observation-manifest.csv"
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} expected observations to {target}")


if __name__ == "__main__":
    main()
