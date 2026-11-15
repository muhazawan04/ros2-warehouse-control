# ROS 2 Warehouse Robot

An incremental, version-controlled robotics project built with **Gazebo Harmonic** on **Ubuntu 24.04**, progressing toward **ROS 2 Jazzy**, SLAM, Nav2 and a desktop warehouse-delivery controller.

**Current milestone: `v0.4.0` — Gazebo LiDAR.** The robot uses the original TurtleBot3 visual meshes and the physical/sensor configuration from the final tested warehouse project. This milestone runs directly in Gazebo; ROS 2 bridging is a separate, upcoming step.

## Requirements

- Ubuntu 24.04, Gazebo Harmonic (`gz sim`), Git
- Original working project at `~/Downloads/ros2-warehouse-control/` when running the one-time upgrade script
- ROS 2 Jazzy is required for later milestones, not for the current Gazebo-only scan test

## Layout

```text
ros2-warehouse-control/
├── simulation/
│   ├── worlds/empty_world.sdf
│   └── models/mobile_robot/
│       ├── model.config
│       ├── model.sdf
│       └── meshes/{bases,wheels,sensors}/
├── scripts/upgrade_v0_4.py  # One-time upgrade helper
└── README.md
```

## Run

From the repository root:

```bash
cd ~/ros2-warehouse-control
export GZ_SIM_RESOURCE_PATH="$PWD/simulation/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
gz sim -r simulation/worlds/empty_world.sdf
```

The LiDAR link and `lds.stl` visual are mounted above the chassis. The Gazebo **Sensors** system with Ogre2 publishes a 2D scan on `/scan`.

## Verify LiDAR (Gazebo Transport)

In a separate terminal:

```bash
gz topic -l | grep -E '/scan|cmd_vel'
gz topic -i -t /scan
gz topic -e -t /scan
```

Look for messages of type `gz.msgs.LaserScan`, with **720 rays**, **10 Hz** scan updates, **0.1 m** minimum range, **12.0 m** maximum range, and a 360-degree horizontal sweep. With no nearby obstacles, readings can be at maximum range or infinite; this is not a LiDAR failure. Later we'll add shelves and obstacles to the warehouse world.

Test differential drive (use the exact topic shown by `gz topic -l`):

```bash
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.3}, angular: {z: 0.0}'
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.0}, angular: {z: 0.0}'
```

> This version uses **Gazebo Transport**, not ROS 2 `/scan` or `/cmd_vel`. ROS messages are introduced when we add `ros_gz_bridge`.

## Configuration provenance

The upgrade script copies the `lidar_link`, `lidar_joint`, complete **DiffDrive plugin**, and `lds.stl` from `~/Downloads/ros2-warehouse-control/simulation/models/mobile_robot/`. Sensor parameters: `gpu_lidar`, 720 horizontal samples, ±π rad, 10 Hz, range 0.1–12 m, resolution 0.01 m, scan topic `/scan`, frame `laser_frame`. It also enables the Gazebo Sensors system in the world.

**Correction from the earlier v0.3 example:** The final tested DiffDrive plugin uses **0.80 m wheel separation**, **0.165 m wheel radius**, and `/cmd_vel` (not 0.94 m, 0.20 m, `cmd_vel`). The new version takes the whole plugin directly from the final working model to prevent further mismatches.

## Version history

| Version | Feature |
| --- | --- |
| `v0.1.0` | Empty Gazebo world with ground and physics |
| `v0.2.0` | Mobile robot chassis, TurtleBot3 meshes, wheels, caster and joints |
| `v0.3.0` | Differential-drive Gazebo controller |
| `v0.4.0` | LiDAR model, sensor, and Gazebo scan publishing |

## Reuse a previous milestone

```bash
git clone https://github.com/muhazawan04/ros2-warehouse-control.git
cd ros2-warehouse-control
git tag --list
git switch --detach v0.3.0   # Inspect or run v0.3.0
git switch main            # Return to latest development
```

Read that version's own README for its exact test commands. Create a branch if you want to modify an older tag: `git switch -c experiment-v0.3 v0.3.0`.

## Development workflow

Test the milestone in Gazebo **before** creating a commit and tag. Then run `git add`, `git commit`, `git tag`, `git push` and push the tag. Only tested milestones should receive release tags.

## Mesh attribution

The TurtleBot3 Burger visual meshes are third-party assets. Preserve their original attribution and applicable license when distributing the repository; do not claim the meshes are original designs.
