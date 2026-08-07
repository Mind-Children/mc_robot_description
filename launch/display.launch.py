#!/usr/bin/env python3
"""Visualize the MC1 model: robot_state_publisher + RViz (+ joint sliders).

The model-iteration entry point — run it through ./rviz.sh (docker, X11,
live-mounted model files) or directly inside any container that has this
package:

    ros2 launch mc_robot_description display.launch.py
    ros2 launch mc_robot_description display.launch.py joints:=zero
    ros2 launch mc_robot_description display.launch.py joints:=external

Launch args:
  joints        gui (default) | zero | external
      gui       joint_state_publisher_GUI — sliders for every actuatable
                joint, all starting at 0 (not at the limit midpoint, which
                is what the GUI does by default and which makes an
                asymmetric model look broken on startup).
      zero      plain joint_state_publisher pinned to 0 — the model just
                stands there in its zero pose; use when inspecting geometry
                or when something else will publish later.
      external  publish nothing — someone else owns /current_joint_states
                (the Isaac sim bridge, or the real drivers on the robot).
  rviz_config   path to the .rviz file, default = packaged rviz/mc1.rviz.
  use_rsp       bool, default true. false when an external
                robot_state_publisher already serves the model.

Joint-state topic is /current_joint_states everywhere in this stack (the
raw /joint_states name is remapped), so RViz here renders exactly what the
sim or the real robot publishes.
"""
import os
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

JOINT_TOPIC = '/current_joint_states'


def _zero_params(urdf_path: str) -> dict:
    """{'zeros.<joint>': 0.0} for every actuatable joint.

    Fixed joints have no position; mimic joints follow their master. Without
    this the joint_state_publisher GUI starts every slider at the middle of
    its limits, which on this model means the arms boot bent.
    """
    root = ET.parse(urdf_path).getroot()
    return {
        f'zeros.{j.get("name")}': 0.0
        for j in root.findall('joint')
        if j.get('type') != 'fixed' and j.find('mimic') is None
    }


def generate_launch_description():
    joints = LaunchConfiguration('joints')
    rviz_config = LaunchConfiguration('rviz_config')
    use_rsp = LaunchConfiguration('use_rsp')

    share = get_package_share_directory('mc_robot_description')
    urdf_path = os.path.join(share, 'urdf', 'mc1.urdf')
    with open(urdf_path) as f:
        robot_description = f.read()
    zeros = _zero_params(urdf_path)

    def when(mode):
        return IfCondition(PythonExpression(["'", joints, "' == '", mode, "'"]))

    return LaunchDescription([
        DeclareLaunchArgument(
            'joints', default_value='gui',
            description="Joint source: gui (sliders) | zero (pinned at 0) | "
                        "external (someone else publishes)."),
        DeclareLaunchArgument(
            'rviz_config', default_value=os.path.join(share, 'rviz', 'mc1.rviz'),
            description='RViz2 .rviz config to load.'),
        DeclareLaunchArgument(
            'use_rsp', default_value='true',
            description='Start robot_state_publisher (false if an external '
                        'one already serves the model).'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            condition=IfCondition(use_rsp),
            parameters=[{'robot_description': robot_description}],
            remappings=[('/joint_states', JOINT_TOPIC)],
            output='screen',
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            condition=when('gui'),
            parameters=[zeros],
            remappings=[('/joint_states', JOINT_TOPIC)],
            output='screen',
        ),
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            condition=when('zero'),
            parameters=[zeros],
            remappings=[('/joint_states', JOINT_TOPIC)],
            output='screen',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen',
        ),
    ])
