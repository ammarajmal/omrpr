from __future__ import annotations

import importlib.metadata
import json
import platform
import sys
from pathlib import Path

packages = {dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()}
report = {
    "python": sys.version,
    "executable": sys.executable,
    "platform": platform.platform(),
    "packages": dict(sorted(packages.items(), key=lambda item: item[0].lower())),
}
out = Path("outputs/reports/environment.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(out)
