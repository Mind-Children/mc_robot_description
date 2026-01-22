# Mind Children MC-ONE Robot Description Package

ROS2 package containing the official robot description assets for Mind Children robots.

## Robot Description

This package provides the MC-ONE URDF model and associated meshes for visualization and downstream tooling. The URDF lives in `urdfs/mc_one.urdf`, while mesh assets are stored under `meshes/`.

## RViz Launch Files

The RViz launch files start `robot_state_publisher` and visualize the robot in RViz using a shared config.

- `rviz_current` launches RViz wired to `/current_joint_states` for displaying the live robot state.
- `rviz_goal` launches RViz wired to `/goal_joint_states` for previewing goal poses.