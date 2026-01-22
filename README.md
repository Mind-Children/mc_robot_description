# Mind Children MC-ONE Robot Description Package

ROS2 package containing the official robot description assets for Mind Children robots.

## Robot Description

This package provides the MC-ONE URDF model and associated meshes for visualization and downstream tooling. The URDF lives in `urdfs/mc_one.urdf`, while mesh assets are stored under `meshes/`.


## Tested Usage Scenarios

### Remote Visualization via SSH + Docker (Recommended)

This package is primarily tested and intended for **remote visualization**, where RViz is executed on a remote machine (e.g. Jetson / pi5), and controlled from a local machine via SSH with X11 forwarding.

This setup is useful when:

* The robot or ROS 2 stack runs on a remote computer
* You want to visualize or manipulate the robot model from your local machine
* You want a reproducible, dependency-isolated environment using Docker

---

## Prerequisites

On the **remote machine**:

1. **Docker installed**

2. Build the image once:

   ```bash
   ./build_docker.sh
   ```

3. Ensure X11 forwarding prerequisites:

   * An active X server on the **local machine**
   * SSH login with X11 forwarding enabled

On the **local machine**, connect using:

```bash
ssh -X -C user@remote_machine
```

Notes:

* `-X` enables X11 forwarding
* `-C` enables SSH compression (**strongly recommended** to improve RViz UI responsiveness over network)

---

## X11 / Xauthority Setup

The launch scripts expect a valid `Xauthority` file on the remote machine.

Make sure:

* `$DISPLAY` is set after SSH login
* `$XAUTHORITY` exists (defaults to `~/.Xauthority`)

The provided launch scripts will automatically validate this before starting Docker.

---

## Launching RViz

### Case 1: No other node publishes joint states (GUI control mode)

If **no other ROS 2 nodes** in the current ROS domain are publishing:

* `/current_joint_states`
* `/goal_joint_states`

You can launch RViz with an interactive joint control GUI:

```bash
./scripts/launch_rviz_current.sh --jsp
# or
./scripts/launch_rviz_goal.sh --jsp
```

This starts:

* `robot_state_publisher`
* `joint_state_publisher_gui`
* `rviz2`

Allowing you to manually manipulate joint values via GUI for visualization and testing.

---

### Case 2: Joint states are already published (listener mode)

If there **are existing publishers** (e.g. real robot, controller, simulation) publishing:

* `/current_joint_states` or
* `/goal_joint_states`

Then **do not enable** the GUI, to avoid multiple publishers on the same topic.

Simply run:

```bash
./scripts/launch_rviz_current.sh
# or
./scripts/launch_rviz_goal.sh
```

In this mode, RViz acts purely as a **visualizer**, reflecting the live or goal joint states provided by the system.

---

## Notes on Topic Wiring

* `rviz_current` is wired to `/current_joint_states`
* `rviz_goal` is wired to `/goal_joint_states`
* When `--jsp` is enabled, `joint_state_publisher_gui` is remapped accordingly so it publishes to the expected topic

Make sure only **one source** publishes a given joint state topic at a time.

---
