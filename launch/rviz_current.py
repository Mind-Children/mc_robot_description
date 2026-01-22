#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

robot_description_path = os.path.join(get_package_share_directory('mc_robot_description'),'urdfs','mc_one.urdf')

user_context_path = os.environ.get('USER_CONTEXT_PATH')
if user_context_path is None:
    user_context_path = '.'

with open(robot_description_path, 'r') as f:
    robot_description = f.read()

robot_state_publisher_node = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    name='robot_state_publisher',
    parameters=[{'robot_description': robot_description}],
    remappings=[('/joint_states', '/current_joint_states')]
)

rviz2_node = Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    arguments=['-d',os.path.join(user_context_path,'rviz/animation.rviz')],
)

def generate_launch_description():
    ld = LaunchDescription()
    ld.add_entity(robot_state_publisher_node)
    ld.add_entity(rviz2_node)
    return ld