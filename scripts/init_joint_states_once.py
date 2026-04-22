#!/usr/bin/env python3
"""
Seed /current_joint_states with an all-zero sensor_msgs/JointState so the TF
tree is built and RViz can render the robot even before mc_core (or any other
joint-state publisher) comes online.

The script keeps republishing periodically until BOTH:
  1. the tf tree is actually usable (a root->leaf lookup succeeds), and
  2. at least one *external* subscriber has connected to /tf (e.g. RViz).
It then sends a few extra updates so the consumer's tf buffer is well filled,
and exits. If neither condition is met within MAX_WAIT_S, it logs a warning
and exits anyway.

This replaces the original "publish once and exit" behavior, which lost the
single /tf broadcast if RViz subscribed late (race condition that surfaced
whenever RViz startup was a bit slower, e.g. loading a bind-mounted config).
"""
import os
import time
import xml.etree.ElementTree as ET

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import tf2_ros
from ament_index_python.packages import get_package_share_directory


PUBLISH_PERIOD_S = 0.5
MAX_WAIT_S = 30.0
POST_CONSUMER_ROUNDS = 5


def parse_urdf(urdf_path: str):
    """Return (movable_joint_names, root_link, any_leaf_link)."""
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    joints = root.findall('joint')

    movable = []
    for j in joints:
        if j.get('type') == 'fixed':
            continue
        if j.find('mimic') is not None:
            continue
        movable.append(j.get('name'))

    parents = {
        j.find('parent').get('link')
        for j in joints if j.find('parent') is not None
    }
    children = {
        j.find('child').get('link')
        for j in joints if j.find('child') is not None
    }

    root_link = next(iter(parents - children), None)
    leaf_link = next(iter(children - parents), None)
    return movable, root_link, leaf_link


def main():
    rclpy.init()
    node = Node('init_joint_states_once')
    logger = node.get_logger()

    urdf_path = os.path.join(
        get_package_share_directory('mc_robot_description'),
        'urdfs', 'mc_one.urdf',
    )
    joint_names, root_link, leaf_link = parse_urdf(urdf_path)
    logger.info(
        f'Seeding {len(joint_names)} joints; '
        f'watching tf chain {root_link} -> {leaf_link}'
    )

    pub = node.create_publisher(JointState, '/current_joint_states', 10)
    tf_buffer = tf2_ros.Buffer()
    # Creating the listener counts as 1 subscriber on /tf (and /tf_static).
    tf_listener = tf2_ros.TransformListener(tf_buffer, node)  # noqa: F841

    msg = JointState()
    msg.name = joint_names
    msg.position = [0.0] * len(joint_names)

    deadline = time.monotonic() + MAX_WAIT_S
    tf_tree_ok = False
    consumer_seen = False

    while time.monotonic() < deadline:
        msg.header.stamp = node.get_clock().now().to_msg()
        pub.publish(msg)
        # Spin so our TransformListener can process incoming /tf messages.
        rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)

        if not tf_tree_ok and root_link and leaf_link:
            if tf_buffer.can_transform(
                root_link, leaf_link, rclpy.time.Time()
            ):
                tf_tree_ok = True
                logger.info(
                    f'tf chain {root_link} -> {leaf_link} established'
                )

        # Subtract our own TransformListener; anything left is an external
        # consumer (RViz, tf2_echo, ...).
        external_tf_subs = max(0, node.count_subscribers('/tf') - 1)
        if tf_tree_ok and external_tf_subs >= 1:
            consumer_seen = True
            logger.info(
                f'{external_tf_subs} external /tf consumer(s) detected; '
                f'sending {POST_CONSUMER_ROUNDS} more updates then exiting.'
            )
            for _ in range(POST_CONSUMER_ROUNDS):
                msg.header.stamp = node.get_clock().now().to_msg()
                pub.publish(msg)
                rclpy.spin_once(node, timeout_sec=PUBLISH_PERIOD_S)
            break

    if not consumer_seen:
        external = max(0, node.count_subscribers('/tf') - 1)
        logger.warn(
            f'Timed out after {MAX_WAIT_S}s '
            f'(tf_tree_ok={tf_tree_ok}, external_tf_subs={external}); '
            f'exiting anyway.'
        )

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
