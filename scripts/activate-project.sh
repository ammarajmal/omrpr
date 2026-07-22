# Source this file: source scripts/activate-project.sh
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/omrpr-analysis"
export UV_LINK_MODE="copy"
export APRILTAG_PREFIX="$HOME/.local/opt/apriltag/current"
export LD_LIBRARY_PATH="$APRILTAG_PREFIX/lib:${LD_LIBRARY_PATH:-}"
