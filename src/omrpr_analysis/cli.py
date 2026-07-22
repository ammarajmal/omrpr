from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import typer
from rich.console import Console

from . import __version__
from .bag_audit import audit_tree
from .inventory import build_inventory
from .paths import ProjectPaths
from .pipeline import STEPS, approve, approved

app = typer.Typer(help="OMRPR clean-room research pipeline", no_args_is_help=True)
pipeline_app = typer.Typer(help="Review and manage Step 00-12 gates")
app.add_typer(pipeline_app, name="pipeline")
console = Console()


@app.command()
def version() -> None:
    console.print(f"omrpr-analysis {__version__}")


@app.command()
def doctor() -> None:
    paths = ProjectPaths.discover()
    failed = False
    required = [
        paths.root / "AGENTS.md",
        paths.root / "LEGACY_ANALYSIS_REPORT.md",
        paths.raw,
        paths.interim,
        paths.processed,
        paths.metadata,
    ]
    for path in required:
        ok = path.exists()
        failed |= not ok
        console.print(f"{'OK' if ok else 'MISSING':7} {path}")
    forbidden = ["pupil_apriltags"]
    for module in forbidden:
        present = importlib.util.find_spec(module) is not None
        failed |= present
        console.print(f"{'FORBIDDEN' if present else 'OK':9} module {module}")
    if failed:
        raise typer.Exit(1)


@app.command()
def inventory(checksum: bool = typer.Option(False, "--checksum")) -> None:
    out = build_inventory(ProjectPaths.discover(), checksum=checksum)
    console.print(out)


@app.command("bag-audit")
def bag_audit() -> None:
    paths = ProjectPaths.discover()
    out = paths.interim / "bag-audit/topic_audit.csv"
    console.print(audit_tree(paths.raw / "camera/rosbag", out))


@app.command("verify-apriltag")
def verify_apriltag() -> None:
    spec = importlib.util.find_spec("apriltag")
    if spec is None:
        console.print("Official apriltag Python module is not importable.")
        raise typer.Exit(1)
    install = ProjectPaths.discover().root / "environment/apriltag-install.json"
    if not install.exists():
        console.print("Missing environment/apriltag-install.json")
        raise typer.Exit(1)
    data = json.loads(install.read_text(encoding="utf-8"))
    console.print(f"Official AprilTag {data['release']} at {data['commit']}")


@pipeline_app.command("status")
def pipeline_status() -> None:
    for step, title in STEPS.items():
        console.print(f"{'APPROVED' if approved(step) else 'PENDING':8} Step {step:02d}: {title}")


@pipeline_app.command("approve")
def pipeline_approve(
    step: int = typer.Option(..., "--step"),
    evidence: Path = typer.Option(..., "--evidence"),  # noqa: B008
) -> None:
    console.print(approve(step, evidence))
