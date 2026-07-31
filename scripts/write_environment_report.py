from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def command_output(*args: str) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"unavailable: {exc}"


packages = {
    dist.metadata["Name"]: dist.version
    for dist in importlib.metadata.distributions()
    if dist.metadata["Name"]
}
report = {
    "generated_at": datetime.now(UTC).isoformat(),
    "python": sys.version,
    "executable": sys.executable,
    "platform": platform.platform(),
    "kernel": command_output("uname", "-a"),
    "uv": command_output("uv", "--version"),
    "git_commit": command_output("git", "rev-parse", "HEAD"),
    "git_status": command_output("git", "status", "--short"),
    "project_root": os.environ.get("OMRPR_PROJECT_ROOT"),
    "data_root": os.environ.get("OMRPR_DATA_ROOT"),
    "runtime_environment": os.environ.get("UV_PROJECT_ENVIRONMENT"),
    "packages": dict(sorted(packages.items(), key=lambda item: item[0].lower())),
}
out = Path("outputs/reports/environment.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(out)
