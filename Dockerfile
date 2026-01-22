ARG BASE_IMAGE=ros:jazzy-ros-base-noble
FROM ${BASE_IMAGE}

ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-rviz2 \
    ros-jazzy-joint_state_publisher_gui \
    realsense2_description \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------------
# build platform workspace
# -------------------------------------------------------------------

COPY . /ros2_ws/src/mc_robot_description

# --- Build mc_robot_description ---
RUN . /opt/ros/$ROS_DISTRO/setup.sh && \
    cd /ros2_ws && \
    colcon build --cmake-args -DBUILD_TESTING=OFF --packages-select mc_robot_description 

# -------------------------------------------------------------------
# Final entry point
# -------------------------------------------------------------------
ENTRYPOINT ["/ros2_ws/src/mc_robot_description/entrypoint.sh"]
