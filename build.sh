#!/bin/bash
set -euo pipefail

# Build the standalone model-inspection image (RViz + joint sliders +
# check_urdf). Only needed ONCE per apt/tooling change — the model files
# themselves are bind-mounted live by ./rviz.sh, so URDF edits do NOT
# require a rebuild.
#
#   ./build.sh              tag = current git branch (e.g. seattle-lab)
#   ./build.sh <tag>        explicit tag
#
# Nothing in the robot stack depends on this image: runtime containers get
# the package from mindchildren/mc_one (single URDF authority).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TAG="${1:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo latest)}"
IMAGE="mindchildren/mc_robot_description:${TAG}"

echo ">>> building ${IMAGE}"
docker build -t "$IMAGE" \
    --build-arg BASE_IMAGE=ros:jazzy-ros-base-noble \
    --progress=plain .

echo "============================================================"
docker images "$IMAGE" \
    --format '  {{.Repository}}:{{.Tag}}  {{.ID}}  {{.Size}}  {{.CreatedSince}}'
echo "  next:  ./rviz.sh            (sliders)"
echo "         ./rviz.sh --no-jsp   (zero pose)"
echo "============================================================"
