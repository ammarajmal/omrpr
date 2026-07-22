from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from .paths import ProjectPaths


def sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(paths: ProjectPaths, checksum: bool = False) -> Path:
    out = paths.metadata / "inventories/source_inventory.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if paths.raw.exists():
        for file in sorted(p for p in paths.raw.rglob("*") if p.is_file()):
            stat = file.stat()
            rows.append(
                {
                    "relative_path": str(file.relative_to(paths.raw)),
                    "size_bytes": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "suffix": file.suffix.lower(),
                    "sha256": sha256(file) if checksum else "",
                }
            )
    with out.open("w", newline="", encoding="utf-8") as stream:
        wr = csv.DictWriter(
            stream, fieldnames=["relative_path", "size_bytes", "mtime_ns", "suffix", "sha256"]
        )
        wr.writeheader()
        wr.writerows(rows)
    return out
