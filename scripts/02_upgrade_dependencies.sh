#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT/scripts/activate-project.sh"
cd "$ROOT"

branch=$(git branch --show-current 2>/dev/null || true)
if [[ "$branch" != maintenance/dependency-upgrade-* ]]; then
  echo "Refusing broad dependency upgrade on branch: ${branch:-detached}"
  echo "Create a maintenance branch first, for example:"
  echo "  git switch -c maintenance/dependency-upgrade-$(date +%Y-%m)"
  exit 2
fi

uv self update || true
uv lock --upgrade --python 3.12.13
uv sync --python 3.12.13 --all-groups --locked
uv run ruff format .
uv run ruff check . --fix
uv run mypy src/omrpr_analysis
env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest --cov=omrpr_analysis
uv tree > outputs/reports/dependency-tree.txt
uv run python scripts/write_environment_report.py
bash scripts/06_project_readiness.sh

echo "Review pyproject.toml and uv.lock before committing."
