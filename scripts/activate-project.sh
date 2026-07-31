#!/usr/bin/env bash

# This script must be sourced:
# source scripts/activate-project.sh

export OMRPR_PROJECT_ROOT="/mnt/space/adev/projects/active/omrpr-analysis"
export OMRPR_DATA_ROOT="/mnt/space/adev/datasets/omrpr"
export UV_PROJECT_ENVIRONMENT="$HOME/Projects-runtime/research/omrpr-analysis/.venv"
export UV_LINK_MODE="copy"
# Prevent ROS 2 Lyrical's Python 3.14 pytest plugins from being auto-loaded
# into this project's Python 3.12 environment.
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export APRILTAG_PREFIX="${APRILTAG_PREFIX:-$HOME/.local/opt/apriltag/current}"
export LD_LIBRARY_PATH="$APRILTAG_PREFIX/lib:${LD_LIBRARY_PATH:-}"

if [[ ! -f "$UV_PROJECT_ENVIRONMENT/bin/activate" ]]; then
    echo "ERROR: OMRPR virtual environment does not exist:" >&2
    echo "  $UV_PROJECT_ENVIRONMENT" >&2
    echo "Run 'uv sync' from the project root first." >&2
    return 1 2>/dev/null || exit 1
fi

# shellcheck disable=SC1091
source "$UV_PROJECT_ENVIRONMENT/bin/activate"
hash -r

if [[ "${VIRTUAL_ENV:-}" != "$UV_PROJECT_ENVIRONMENT" ]]; then
    echo "ERROR: Failed to activate the OMRPR environment." >&2
    return 1 2>/dev/null || exit 1
fi
