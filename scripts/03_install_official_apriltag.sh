#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$ROOT/scripts/activate-project.sh"

VERSION=${APRILTAG_VERSION:-v3.4.5}
EXPECTED_COMMIT_PREFIX=${APRILTAG_COMMIT_PREFIX:-94be783}
REPOSITORY=https://github.com/AprilRobotics/apriltag.git
SRC_ROOT="$HOME/.local/src/apriltag-${VERSION}"
PREFIX="$HOME/.local/opt/apriltag/${VERSION#v}"
CURRENT="$HOME/.local/opt/apriltag/current"

for cmd in git cmake ninja pkg-config cc sha256sum ldd; do
  command -v "$cmd" >/dev/null || {
    echo "Missing $cmd. Install build-essential cmake ninja-build pkg-config first."
    exit 1
  }
done
[[ -x "$UV_PROJECT_ENVIRONMENT/bin/python" ]] || {
  echo "Project Python environment missing: $UV_PROJECT_ENVIRONMENT"
  exit 1
}

if [[ ! -d "$SRC_ROOT/.git" ]]; then
  git clone "$REPOSITORY" "$SRC_ROOT"
fi

git -C "$SRC_ROOT" remote set-url origin "$REPOSITORY"
git -C "$SRC_ROOT" fetch --tags --force origin
git -C "$SRC_ROOT" reset --hard
git -C "$SRC_ROOT" clean -ffdx
git -C "$SRC_ROOT" checkout --detach "$VERSION"
COMMIT=$(git -C "$SRC_ROOT" rev-parse HEAD)
[[ "$COMMIT" == "$EXPECTED_COMMIT_PREFIX"* ]] || {
  echo "Unexpected commit for $VERSION: $COMMIT"
  exit 1
}

rm -rf "$SRC_ROOT/build" "$PREFIX"
cmake -S "$SRC_ROOT" -B "$SRC_ROOT/build" -GNinja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DBUILD_SHARED_LIBS=ON \
  -DPython3_EXECUTABLE="$UV_PROJECT_ENVIRONMENT/bin/python"
cmake --build "$SRC_ROOT/build" --parallel
cmake --install "$SRC_ROOT/build"

mkdir -p "$(dirname "$CURRENT")"
ln -sfn "$PREFIX" "$CURRENT"

MODULE=$(find "$SRC_ROOT/build" "$PREFIX" -type f \
  \( -name 'apriltag*.so' -o -name 'apriltag*.py' \) | head -1 || true)
if [[ -n "$MODULE" ]]; then
  MODULE_DIR=$(dirname "$MODULE")
  SITE=$($UV_PROJECT_ENVIRONMENT/bin/python -c \
    'import site; print(site.getsitepackages()[0])')
  printf '%s\n' "$MODULE_DIR" > "$SITE/aprilrobotics_apriltag.pth"
fi

SOURCE_ARCHIVE="$SRC_ROOT/build/apriltag-source-${VERSION}.tar"
git -C "$SRC_ROOT" archive --format=tar --output="$SOURCE_ARCHIVE" "$COMMIT"
SOURCE_SHA256=$(sha256sum "$SOURCE_ARCHIVE" | awk '{print $1}')
LIBRARY=$(find "$PREFIX" -type f -name 'libapriltag.so*' | head -1 || true)
PYTHON_MODULE=$("$UV_PROJECT_ENVIRONMENT/bin/python" - <<'PY'
import importlib.util
spec = importlib.util.find_spec("apriltag")
print(spec.origin if spec and spec.origin else "")
PY
)

mkdir -p "$ROOT/environment"
cat > "$ROOT/environment/apriltag-install.json" <<EOF_JSON
{
  "repository": "$REPOSITORY",
  "release": "$VERSION",
  "commit": "$COMMIT",
  "source_archive_sha256": "$SOURCE_SHA256",
  "source": "$SRC_ROOT",
  "prefix": "$PREFIX",
  "library": "$LIBRARY",
  "python_module": "$PYTHON_MODULE",
  "python_version": "$($UV_PROJECT_ENVIRONMENT/bin/python -VV 2>&1)",
  "compiler": "$(cc --version | head -1)",
  "cmake": "$(cmake --version | head -1)",
  "ninja": "$(ninja --version)",
  "installed_at": "$(date --iso-8601=seconds)"
}
EOF_JSON

export LD_LIBRARY_PATH="$CURRENT/lib:${LD_LIBRARY_PATH:-}"
if [[ -n "$LIBRARY" ]]; then
  ldd "$LIBRARY" > "$ROOT/environment/apriltag-ldd.txt"
fi

uv run omrpr verify-apriltag
"$UV_PROJECT_ENVIRONMENT/bin/python" - <<'PY'
from apriltag import apriltag

detector = apriltag("tag36h11")
assert detector is not None
print("Official AprilTag tag36h11 detector construction: PASS")
PY

echo "Official AprilRobotics AprilTag installed at $PREFIX"
