#!/usr/bin/env python3
"""
Publish one sensor_msgs/JointState with every URDF joint at 0 to
/current_joint_states, then exit.

Used at launch to seed the TF tree so RViz shows the robot immediately,
even before mc_core (or any other joint_state publisher) comes online.
"""
import os
import time
import xml.etree.ElementTree as ET

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from ament_index_python.packages import get_package_share_directory


def collect_joint_names(urdf_path: str) -> list[str]:
    """Return names of all joints that need an explicit position value.

    Skip:
      - fixed joints   (RSP computes their TF from <origin> alone)
      - mimic joints   (RSP derives them from the master joint)
    """
    tree = ET.parse(urdf_path)
    names = []
    for j in tree.getroot().findall('joint'):
        if j.get('type') == 'fixed':
            continue
        if j.find('mimic') is not None:
            continue
        names.append(j.get('name'))
    return names


def main():
    rclpy.init()
    node = Node('init_joint_states_once')
    logger = node.get_logger()

    urdf_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'urdfs', 'mc_one.urdf',
    )
    joint_names = collect_joint_names(urdf_path)
    logger.info(f'Will publish zeros for {len(joint_names)} joints: {joint_names}')

    pub = node.create_publisher(JointState, '/current_joint_states', 10)

    # Give RSP time to subscribe so the one-shot message isn't lost.
    # Wait up to 3s for at least one subscriber.
    deadline = time.monotonic() + 3.0
    while pub.get_subscription_count() == 0 and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    if pub.get_subscription_count() == 0:
        logger.warn('No subscribers on /current_joint_states after 3s; publishing anyway.')

    msg = JointState()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.name = joint_names
    msg.position = [0.0] * len(joint_names)
    pub.publish(msg)
    logger.info('Published initial zero JointState, exiting.')

    # Brief pause so the message actually leaves before we tear down.
    time.sleep(0.3)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
