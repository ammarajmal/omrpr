#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT/scripts/activate-project.sh"

VERSION=${APRILTAG_VERSION:-v3.4.5}
EXPECTED_COMMIT_PREFIX=${APRILTAG_COMMIT_PREFIX:-94be783}
SRC_ROOT="$HOME/.local/src/apriltag-${VERSION}"
PREFIX="$HOME/.local/opt/apriltag/${VERSION#v}"
CURRENT="$HOME/.local/opt/apriltag/current"

for cmd in git cmake ninja pkg-config; do
  command -v "$cmd" >/dev/null || {
    echo "Missing $cmd. Install build-essential cmake ninja-build pkg-config first."
    exit 1
  }
done

if [[ ! -d "$SRC_ROOT/.git" ]]; then
  git clone https://github.com/AprilRobotics/apriltag.git "$SRC_ROOT"
fi

git -C "$SRC_ROOT" fetch --tags --force origin
git -C "$SRC_ROOT" reset --hard
git -C "$SRC_ROOT" clean -ffd
git -C "$SRC_ROOT" checkout --detach "$VERSION"
COMMIT=$(git -C "$SRC_ROOT" rev-parse HEAD)
[[ "$COMMIT" == "$EXPECTED_COMMIT_PREFIX"* ]] || {
  echo "Unexpected commit for $VERSION: $COMMIT"
  exit 1
}

rm -rf "$SRC_ROOT/build"
cmake -S "$SRC_ROOT" -B "$SRC_ROOT/build" -GNinja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DPython3_EXECUTABLE="$UV_PROJECT_ENVIRONMENT/bin/python"
cmake --build "$SRC_ROOT/build"
cmake --install "$SRC_ROOT/build"

mkdir -p "$(dirname "$CURRENT")"
ln -sfn "$PREFIX" "$CURRENT"

# Locate the upstream-built Python extension and add its directory to this venv.
MODULE=$(find "$SRC_ROOT/build" "$PREFIX" -type f \
  \( -name 'apriltag*.so' -o -name 'apriltag*.py' \) | head -1 || true)
if [[ -n "$MODULE" ]]; then
  MODULE_DIR=$(dirname "$MODULE")
  SITE=$($UV_PROJECT_ENVIRONMENT/bin/python -c \
    'import site; print(site.getsitepackages()[0])')
  printf '%s\n' "$MODULE_DIR" > "$SITE/aprilrobotics_apriltag.pth"
fi

cat > "$ROOT/environment/apriltag-install.json" <<EOF
{
  "repository": "https://github.com/AprilRobotics/apriltag.git",
  "release": "$VERSION",
  "commit": "$COMMIT",
  "source": "$SRC_ROOT",
  "prefix": "$PREFIX"
}
EOF

export LD_LIBRARY_PATH="$CURRENT/lib:${LD_LIBRARY_PATH:-}"
uv run omrpr verify-apriltag
