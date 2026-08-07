# mc_robot_description — MC1 (next-gen, seattle-lab branch)

**Single source of truth for the next-gen MC robot model.** This public repo
holds the one canonical URDF; everything that needs the model — ROS nodes,
the Isaac simulation (`mc_simulation`), offline tools — depends on this
package instead of keeping a copy. The old MC-ONE (Codey) description lives
on in the `main` branch.

## Contents

```
urdf/mc1.urdf     canonical model — FULL BODY since M9 (2026-08-06):
                  chassis + passive wheels + legs (knees drive, hips mimic
                  x-1 parallelogram) + waist + dual 6-DOF arms + torso
                  shell + neck/head + old-Codey 5-finger hands at the arm
                  TCPs + sensor frames (laser, imu, 4 down-facing cliff
                  TOF, 2 limit switches, realsense chain, head camera
                  120deg optical). Body segments are PLACEHOLDER geometry
                  ported from the old Codey; they get replaced as the
                  next-gen Onshape design lands.
meshes/mc1/       STL meshes
launch/display.launch.py   robot_state_publisher + joint sliders + RViz
launch/rsp.launch.py       headless RSP (/joint_states -> /current_joint_states)
rviz/mc1.rviz
mc_robot_description/      Python helper — the sanctioned access path
```

⚠ **Arm-mount constraint**: the `<side>_arm_joint_1` mount rpy on `torso`
(`0 -1.309 ±1.5707963`) is the orientation the arm firmware's GravityFF
closed form was generated for. Between the ground and the torso every
joint is either yaw-about-gravity (`waist_joint`) or cancelled by the
hips parallelogram, so the constraint holds in every pose — do NOT
change these rpy values (or insert non-zero-rpy joints above the arms)
without regenerating the firmware gravity model.

## Consuming the model

ROS (ament) — the package is built into the `mindchildren/mc_one` base image,
so every derived container has it:

```python
from mc_robot_description import get_urdf_path
```

Non-ROS loaders (Isaac Lab's UrdfConverter, Pinocchio without ROS) cannot
resolve `package://` URIs — use the resolved export, which rewrites mesh URIs
to absolute paths:

```python
from mc_robot_description import export_resolved_urdf
urdf = export_resolved_urdf()          # temp file, safe to regenerate
```

The helper works both installed (ament_index) and imported straight from a
repo checkout (path-relative) — non-ROS consumers just add the checkout to
`sys.path`.

## Updating the model

Onshape is the design authority. Change the model there, export URDF+meshes
(see `mc_simulation/doc/onshape_to_urdf_workflow.md`), rewrite the mesh URIs
to `package://mc_robot_description/meshes/mc1/`, and land the result **only
here** (commit + tag). No other repo may carry a URDF copy.

## Visualize

```bash
ros2 launch mc_robot_description display.launch.py
```
