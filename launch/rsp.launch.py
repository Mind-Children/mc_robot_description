#!/usr/bin/env python3
"""Headless robot_state_publisher for the MC1 full-body model.

Runs robot_state_publisher only (no RViz, no JSP-GUI), remapping
/joint_states -> /current_joint_states — the topic the rest of the stack
publishes measured joints on. The desktop sim stack (and later the real
base machine) launches this so the static URDF transforms
(base_link -> laser / imu / tof_* / realsense chain / head_camera) exist
for navigation and perception consumers.

Joint seeding: unlike the old-Codey rsp.launch.py there is no
init-once script here — in simulation the sim bridge publishes a merged
/current_joint_states continuously from the first Isaac step, and on the
real robot the hardware-interface bridges do the same.
"""
import os

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    robot_description_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'urdf',
        'mc1.urdf',
    )
    with open(robot_description_path, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            remappings=[('/joint_states', '/current_joint_states')],
            output='screen',
        ),
    ])
