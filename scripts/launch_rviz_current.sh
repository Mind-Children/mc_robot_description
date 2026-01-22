#!/bin/bash
if [ -z "${DISPLAY}" ]; then
    echo "DISPLAY is not set"
    exit 1
fi
xhost +
docker run --rm -it -v "$(pwd)":/context -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --network host mindchildren/mc_robot_description:latest ros2 launch mc_robot_description rviz_current.py