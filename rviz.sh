#!/bin/bash
set -euo pipefail

# Look at the model: RViz in docker, X11 to the host display.
#
#   ./rviz.sh                sliders for every joint (joint_state_publisher_gui)
#   ./rviz.sh --no-jsp       zero pose, no sliders
#   ./rviz.sh --external     publish nothing — render what the sim / the real
#                            robot puts on /mc_hardware_interface/current_joint_states
#   ./rviz.sh --gpu          use the nvidia runtime (smoother; software GL
#                            otherwise, which is fine for a static model)
#   ./rviz.sh -- <args>      extra ros2 launch args, e.g.
#                            -- rviz_config:=/model/rviz/mc1.rviz
#
# MODEL ITERATION: urdf/ meshes/ rviz/ launch/ are bind-mounted OVER the
# installed share dir, so an edit takes effect on the next run — ./build.sh
# is only needed when the image tooling changes.
#
# --external talks to the running stack, so it needs the same DDS domain:
#   ROS_DOMAIN_ID=42 ./rviz.sh --external

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TAG="${MC_DESCRIPTION_TAG:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo latest)}"
IMAGE="mindchildren/mc_robot_description:${TAG}"
SHARE=/ros2_ws/install/mc_robot_description/share/mc_robot_description

JOINTS=gui
GPU_ARGS=()
EXTRA=()

while [ $# -gt 0 ]; do
    case "$1" in
        --jsp)      JOINTS=gui; shift ;;
        --no-jsp)   JOINTS=zero; shift ;;
        --external) JOINTS=external; shift ;;
        --gpu)      GPU_ARGS=(--runtime=nvidia
                              -e NVIDIA_VISIBLE_DEVICES=all
                              -e NVIDIA_DRIVER_CAPABILITIES=all); shift ;;
        -h|--help)  sed -n '3,22p' "$0"; exit 0 ;;
        --)         shift; EXTRA+=("$@"); break ;;
        *)          EXTRA+=("$1"); shift ;;
    esac
done

if [ -z "${DISPLAY:-}" ]; then
    echo "DISPLAY is not set — run this from a graphical session." >&2
    exit 1
fi
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "image ${IMAGE} not found — run ./build.sh first." >&2
    exit 1
fi

# Let the container's root talk to the host X server (same approach as the
# desktop sim entry). Harmless if xhost is unavailable.
xhost +local:root >/dev/null 2>&1 || true

XAUTH_ARGS=()
XAUTH="${XAUTHORITY:-$HOME/.Xauthority}"
if [ -f "$XAUTH" ]; then
    XAUTH_ARGS=(-v "${XAUTH}:/root/.Xauthority:ro" -e XAUTHORITY=/root/.Xauthority)
fi

echo ">>> ${IMAGE}  joints:=${JOINTS}  (model mounted live from $(pwd))"

# -it only from a real terminal: docker refuses -i when stdin is not a tty,
# which would break background/CI invocations.
TTY_ARGS=()
[ -t 0 ] && TTY_ARGS=(-it)

exec docker run --rm "${TTY_ARGS[@]}" \
    --network host \
    -e DISPLAY="$DISPLAY" \
    -e QT_X11_NO_MITSHM=1 \
    -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    "${XAUTH_ARGS[@]}" \
    "${GPU_ARGS[@]}" \
    -v "$(pwd)/urdf:${SHARE}/urdf:ro" \
    -v "$(pwd)/meshes:${SHARE}/meshes:ro" \
    -v "$(pwd)/rviz:${SHARE}/rviz:ro" \
    -v "$(pwd)/launch:${SHARE}/launch:ro" \
    -v "$(pwd):/model:ro" \
    "$IMAGE" \
    ros2 launch mc_robot_description display.launch.py \
        "joints:=${JOINTS}" "${EXTRA[@]}"
