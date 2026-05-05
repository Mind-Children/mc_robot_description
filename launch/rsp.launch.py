#!/usr/bin/env python3
"""Headless robot_state_publisher launch.

Runs robot_state_publisher only (no RViz, no JSP-GUI). The base machine
launches this so static URDF transforms (base_link -> laser, base_link -> imu,
...) exist locally for slam_toolbox / ekf / rf2o without depending on the
laptop being up.

Also fires init_joint_states_once.py to seed /current_joint_states with zeros,
so the TF tree contains every actuatable joint immediately at startup
(prevents 'Lookup failed' floods until mc_core comes online).
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    publish_initial_joints = LaunchConfiguration('publish_initial_joints')

    robot_description_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'urdfs',
        'mc_one.urdf'
    )
    with open(robot_description_path, 'r') as f:
        robot_description = f.read()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        remappings=[('/joint_states', '/current_joint_states')],
        output='screen',
    )

    init_joints_once = ExecuteProcess(
        cmd=['ros2', 'run', 'mc_robot_description', 'init_joint_states_once.py'],
        condition=IfCondition(publish_initial_joints),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'publish_initial_joints',
            default_value='true',
            description='If true, publishes one JointState with all joints at 0 '
                        'to /current_joint_states at startup to seed the TF tree.',
        ),
        robot_state_publisher_node,
        init_joints_once,
    ])
