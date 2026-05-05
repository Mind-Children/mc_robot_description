#!/usr/bin/env python3
"""RViz launch with optional robot_state_publisher / JSP-GUI.

Standalone use (developer laptop without the rest of the stack):
    ros2 launch mc_robot_description rviz_current.launch.py
  → starts RSP + init_joints_once + RViz, ready to inspect URDF in isolation.

Co-deployed with base (laptop in mc_one_codey/laptop/compose.yaml):
    ros2 launch mc_robot_description rviz_current.launch.py \
        use_robot_state_publisher:=false
  → RSP and the joint seed are running on the base machine
    (rsp.launch.py). Laptop only needs RViz to render what base publishes.

Launch args:
  use_robot_state_publisher    bool, default true.
      Set false when an external RSP is already publishing /robot_description
      and /tf_static (e.g. on the base machine).
  use_joint_state_publisher_gui bool, default false.
      If true, opens the JSP-GUI sliders for manual joint testing.
  publish_initial_joints       bool, default true.
      Effective only when use_robot_state_publisher is true. Fires
      init_joint_states_once.py once at startup so non-fixed joints have a
      definite zero pose immediately, before mc_core comes online.
  rviz_config                  path, default = packaged animation.rviz.
"""
import os
import xml.etree.ElementTree as ET

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
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
    use_jsp_gui = LaunchConfiguration('use_joint_state_publisher_gui')
    use_rsp = LaunchConfiguration('use_robot_state_publisher')
    publish_initial_joints = LaunchConfiguration('publish_initial_joints')
    rviz_config = LaunchConfiguration('rviz_config')

    robot_description_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'urdfs',
        'mc_one.urdf'
    )
    with open(robot_description_path, 'r') as f:
        robot_description = f.read()

    # Force jsp_gui sliders to start at 0 for every actuatable joint.
    jsp_zero_params = _collect_zero_params(robot_description_path)

    default_rviz_config_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'rviz',
        'animation.rviz'
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        condition=IfCondition(use_rsp),
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

    # Seed the TF tree with zeros for every actuatable joint so the model
    # appears immediately on startup (before mc_core publishes real servo
    # positions). Skipped when use_robot_state_publisher is false — in that
    # case whoever owns the RSP also owns this seed.
    init_joints_once = ExecuteProcess(
        cmd=['ros2', 'run', 'mc_robot_description', 'init_joint_states_once.py'],
        condition=IfCondition(
            PythonExpression(["'", use_rsp, "' == 'true' and '", publish_initial_joints, "' == 'true'"])
        ),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_robot_state_publisher',
            default_value='true',
            description='Whether to start robot_state_publisher (and the '
                        'init_joint_states seed). Set false when an external '
                        'RSP is already publishing (e.g. on base via '
                        'rsp.launch.py).',
        ),
        DeclareLaunchArgument(
            'use_joint_state_publisher_gui',
            default_value='false',
            description='Whether to start joint_state_publisher_gui',
        ),
        DeclareLaunchArgument(
            'publish_initial_joints',
            default_value='true',
            description='If true, publishes one JointState with all joints at '
                        '0 to /current_joint_states at startup to seed the TF '
                        'tree. Only effective when use_robot_state_publisher '
                        'is true.',
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
