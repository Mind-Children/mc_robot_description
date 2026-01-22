#!/bin/bash
set -e

if [ -z "${DISPLAY}" ]; then
    echo "DISPLAY is not set"
    exit 1
fi

XAUTH="${XAUTHORITY:-$HOME/.Xauthority}"
if [ ! -f "$XAUTH" ]; then
    echo "Xauthority file not found: $XAUTH"
    exit 1
fi

docker run --rm -it \
  --network host \
  -v "$(pwd)":/context \
  -e DISPLAY="$DISPLAY" \
  -e XAUTHORITY=/root/.Xauthority \
  -v "$XAUTH":/root/.Xauthority:ro \
  -e QT_X11_NO_MITSHM=1 \
  mindchildren/mc_robot_description:v0.1 \
  ros2 launch mc_robot_description rviz_goal.py