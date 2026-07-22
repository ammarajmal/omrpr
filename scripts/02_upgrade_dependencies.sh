#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT/scripts/activate-project.sh"
cd "$ROOT"
uv self update || true
uv lock --upgrade
uv sync --all-groups --locked
uv run ruff format .
uv run ruff check . --fix
uv run mypy src/omrpr_analysis
uv run pytest
uv tree > outputs/reports/dependency-tree.txt
uv run python scripts/write_environment_report.py
