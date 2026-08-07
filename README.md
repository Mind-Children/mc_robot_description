# mc_robot_description — MC1 (next-gen, seattle-lab branch)

**Single source of truth for the next-gen MC robot model.** This public repo
holds the one canonical URDF; everything that needs the model — ROS nodes,
the Isaac simulation (`mc_simulation`), offline tools — depends on this
package instead of keeping a copy. The old MC-ONE (Codey) description lives
on in the `main` branch.

## Contents

```
urdf/mc1.urdf     canonical model — the old Codey BODY with the new 6-DOF
                  arms (v2, 2026-08-07). Body joint names are the old ones:
                  knees (+ hips mimic x-1, the level-keeping parallelogram),
                  torso_rotate (the waist), neck_turn, head_nod,
                  chest_camera (the realsense pitch axis),
                  <side>_{thumb,index,middle,ring,pinky} (+ mimic segments),
                  left/right_wheel. Arms are <side>_arm_joint_1..6 with
                  their own DH-style frames, hands hang off the TCPs.
                  Sensor frames: laser, imu, 4 downward cliff TOF, 2 bumper
                  limit switches, chest_camera_sensor, head_camera_link.
                  Camera OPTICAL frames are deliberately NOT here — the
                  realsense ROS driver publishes them on hardware, the
                  Isaac bridge in sim.
                  Body segments are the old-Codey geometry, i.e. placeholder
                  until the next-gen design lands in Onshape.
meshes/mc1/       STL meshes (base_link/waist_link/realsense are leftovers
                  from the retired bench-unit model — unreferenced)
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

## Visualize / iterate on the model

This package is standalone-runnable: one docker image with RViz, joint
sliders and `check_urdf`, independent of the robot stack.

```bash
./build.sh          # once (tag = current branch); only needed again when
                    # the image tooling changes, NOT after model edits
./rviz.sh           # RViz + a slider per joint
./rviz.sh --no-jsp  # zero pose, no sliders
./rviz.sh --gpu     # nvidia runtime (software GL otherwise — fine, slower)
```

**Model edits need no rebuild**: `rviz.sh` bind-mounts `urdf/ meshes/ rviz/
launch/` over the installed share dir, so the loop is *edit → rerun
`./rviz.sh`*. Sliders start every joint at 0 (not at the middle of its
limits, which is the joint_state_publisher default and makes an asymmetric
model look broken); mimic joints (`hips`, the finger segments) follow their
master automatically.

Render what the running stack publishes instead of driving it yourself —
same DDS domain as the robot/sim:

```bash
ROS_DOMAIN_ID=42 ./rviz.sh --external
```

Validate without a display:

```bash
docker run --rm -v "$PWD/urdf:/urdf:ro" \
  mindchildren/mc_robot_description:seattle-lab check_urdf /urdf/mc1.urdf
```

Inside any container that already has the package (e.g. `mc_one`), the
launch file works directly:

```bash
ros2 launch mc_robot_description display.launch.py joints:=gui|zero|external
```
