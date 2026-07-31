from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw: Path
    interim: Path
    processed: Path
    metadata: Path

    @classmethod
    def discover(cls) -> ProjectPaths:
        root = Path(__file__).resolve().parents[2]
        return cls(
            root=root,
            raw=root / "data/raw/source",
            interim=root / "data/interim/source",
            processed=root / "data/processed/source",
            metadata=root / "data/metadata/source",
        )
