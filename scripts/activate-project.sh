# Source this file: source scripts/activate-project.sh
export OMRPR_PROJECT_ROOT="${OMRPR_PROJECT_ROOT:-/mnt/space/adev/projects/active/omrpr-analysis}"
export OMRPR_DATA_ROOT="${OMRPR_DATA_ROOT:-/mnt/space/adev/datasets/omrpr}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/Projects-runtime/research/omrpr-analysis/.venv}"
export UV_LINK_MODE="copy"
export APRILTAG_PREFIX="${APRILTAG_PREFIX:-$HOME/.local/opt/apriltag/current}"
export LD_LIBRARY_PATH="$APRILTAG_PREFIX/lib:${LD_LIBRARY_PATH:-}"
