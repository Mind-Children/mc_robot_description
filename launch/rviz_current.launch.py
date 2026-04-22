#!/usr/bin/env python3
import os
import xml.etree.ElementTree as ET

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def _collect_zero_params(urdf_path: str) -> dict:
    """Build a dict of {'zeros.<joint_name>': 0.0} for every actuatable joint.

    Skip fixed joints (no position) and mimic joints (driven by their master).
    Passed to joint_state_publisher_gui so its sliders start at 0 instead of
    the default midpoint of joint limits.
    """
    tree = ET.parse(urdf_path)
    zeros = {}
    for j in tree.getroot().findall('joint'):
        if j.get('type') == 'fixed':
            continue
        if j.find('mimic') is not None:
            continue
        zeros[f'zeros.{j.get("name")}'] = 0.0
    return zeros


def generate_launch_description():
    # --- Launch arguments ---
    use_jsp_gui = LaunchConfiguration('use_joint_state_publisher_gui')
    publish_initial_joints = LaunchConfiguration('publish_initial_joints')
    rviz_config = LaunchConfiguration('rviz_config')

    # --- URDF ---
    robot_description_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'urdfs',
        'mc_one.urdf'
    )

    with open(robot_description_path, 'r') as f:
        robot_description = f.read()

    # Force jsp_gui sliders to start at 0 for every actuatable joint.
    jsp_zero_params = _collect_zero_params(robot_description_path)

    # --- RViz config (default to packaged animation.rviz; override via arg) ---
    default_rviz_config_path = os.path.join(
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
        parameters=[jsp_zero_params],
        remappings=[('/joint_states', '/current_joint_states')],
        output='screen',
    )

    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
    )

    # One-shot initializer: publishes a single all-zero JointState to
    # /current_joint_states, then exits. This seeds the TF tree so RViz shows
    # the robot immediately (instead of waiting for mc_core to come online).
    init_joints_once = ExecuteProcess(
        cmd=['ros2', 'run', 'mc_robot_description', 'init_joint_states_once.py'],
        condition=IfCondition(publish_initial_joints),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_joint_state_publisher_gui',
            default_value='false',
            description='Whether to start joint_state_publisher_gui',
        ),
        DeclareLaunchArgument(
            'publish_initial_joints',
            default_value='true',
            description='If true, publishes one JointState with all joints at 0 '
                        'to /current_joint_states at startup to seed the TF tree.',
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=default_rviz_config_path,
            description='Path to the RViz2 .rviz config file to load.',
        ),
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz2_node,
        init_joints_once,
    ])
