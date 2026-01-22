#!/usr/bin/env python3
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # --- Launch argument ---
    use_jsp_gui = LaunchConfiguration('use_joint_state_publisher_gui')

    # --- URDF ---
    robot_description_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'urdfs',
        'mc_one.urdf'
    )

    with open(robot_description_path, 'r') as f:
        robot_description = f.read()

    # --- RViz config ---
    rviz_config_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'rviz',
        'animation.rviz'
    )

    # --- Nodes ---
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        remappings=[('/joint_states', '/current_joint_states')],
        output='screen',
    )

    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=IfCondition(use_jsp_gui),
        output='screen',
    )

    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_joint_state_publisher_gui',
            default_value='false',
            description='Whether to start joint_state_publisher_gui'
        ),
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz2_node,
    ])
