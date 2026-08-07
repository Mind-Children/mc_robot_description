ARG BASE_IMAGE=ros:jazzy-ros-base-noble
FROM ${BASE_IMAGE}

# Standalone MODEL-INSPECTION image (see ./build.sh + ./rviz.sh).
#
# This image exists only to LOOK at the model — RViz, joint sliders and
# check_urdf — so the URDF can be iterated without the rest of the stack.
# It is NOT how the robot consumes the description: every runtime container
# gets this package baked into mindchildren/mc_one (single URDF authority).
#
# The model files are COPY'd in so the image is self-contained, but
# ./rviz.sh bind-mounts the working tree over the installed share dir —
# edit urdf/ meshes/ rviz/ launch/, rerun ./rviz.sh, no rebuild.

RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-jazzy-rviz2 \
      ros-jazzy-joint-state-publisher \
      ros-jazzy-joint-state-publisher-gui \
      liburdfdom-tools \
 && rm -rf /var/lib/apt/lists/*

COPY . /ros2_ws/src/mc_robot_description

RUN . /opt/ros/$ROS_DISTRO/setup.sh \
 && cd /ros2_ws \
 && colcon build --packages-select mc_robot_description \
      --cmake-args -DBUILD_TESTING=OFF

ENTRYPOINT ["/ros2_ws/src/mc_robot_description/entrypoint.sh"]
CMD ["ros2", "launch", "mc_robot_description", "display.launch.py"]
