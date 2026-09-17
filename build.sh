#!/bin/bash
set -Eeuo pipefail   # -E: the ERR trap below must reach inside functions

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

# ---- STOP ON THE FIRST ERROR, AND SAY SO ----------------------------------
# A failed `docker build` ends thousands of lines of --progress=plain output
# with a single ERROR line, and the shell then returns to a prompt -- which,
# scrolled back to, looks exactly like a build that finished. The EXIT trap
# below prints its banner AFTER all of docker's output, so a failure is the
# last thing on screen rather than the first thing off it, and the script
# always exits non-zero so a caller can tell.
#
# mc_one_codey/jetson/build.sh carries the long version of why: five runs of
# it died part-way through unnoticed on 2026-09-16, and a stale image went on
# running on the robot for two hours.
STEP="startup"
FAILED_AT=""
trap 'FAILED_AT="line ${LINENO}: ${BASH_COMMAND}"' ERR
trap 'build_failed $?' EXIT

build_failed() {
    local code="$1"
    if [ "$code" -eq 0 ]; then return 0; fi
    echo >&2
    echo "############################################################" >&2
    if [ "$code" -eq 130 ] || [ "$code" -eq 143 ]; then
        echo "  BUILD INTERRUPTED while working on: ${STEP}" >&2
    else
        echo "  BUILD FAILED while working on: ${STEP}" >&2
        echo "  ${FAILED_AT:-(no command recorded)} -> exit ${code}" >&2
    fi
    if [ "$STEP" != "startup" ]; then
        echo "  Nothing after this point was built." >&2
    fi
    echo "############################################################" >&2
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TAG="${1:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo latest)}"
IMAGE="mindchildren/mc_robot_description:${TAG}"

echo ">>> building ${IMAGE}"
STEP="image ${IMAGE}"
docker build -t "$IMAGE" \
    --build-arg BASE_IMAGE=ros:jazzy-ros-base-noble \
    --progress=plain .

echo "============================================================"
docker images "$IMAGE" \
    --format '  {{.Repository}}:{{.Tag}}  {{.ID}}  {{.Size}}  {{.CreatedSince}}'
echo "  next:  ./rviz.sh            (sliders)"
echo "         ./rviz.sh --no-jsp   (zero pose)"
echo "============================================================"
