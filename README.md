# ROS 2 Warehouse Robot

A milestone-based simulation of a mobile warehouse robot using **Ubuntu 24.04**, **ROS 2 Jazzy**, **Gazebo Harmonic**, and a TurtleBot3-derived visual mesh. Each Git tag records a tested stage of development.

**Current milestone: `v0.5.0` — ROS 2–Gazebo integration.** This version brings the Gazebo robot's LiDAR, differential-drive commands, odometry, simulated time, and odometry TF into ROS 2. SLAM, warehouse obstacles, Nav2, and the desktop dashboard are introduced in later milestones.

## Prerequisites

- ROS 2 Jazzy and Gazebo Harmonic installed and available in your terminal.
- ROS–Gazebo bridge and TF tools:

```bash
sudo apt install ros-jazzy-ros-gz-bridge ros-jazzy-tf2-ros
```

Your normal terminal must already have the ROS 2 environment sourced. Do not start a second Gazebo instance for this test.

## Project layout

```text
ros2-warehouse-control/
├── simulation/
│   ├── worlds/empty_world.sdf
│   ├── models/mobile_robot/{model.config,model.sdf,meshes/}
│   ├── config/bridge.yaml
│   └── launch/bridge_sim.launch.py
├── .gitignore
└── README.md
```

`bridge.yaml` is reused from the final tested project. The model's numerical parameters remain those of the tested SDF. The launch file uses project-relative paths rather than the old `~/gazebo_tutorials` path.

## Quick start

**Terminal 1 — start Gazebo and the ROS 2 bridge together:**

```bash
cd ~/ros2-warehouse-control
ros2 launch "$PWD/simulation/launch/bridge_sim.launch.py"
```

**Terminal 2 — verify ROS 2 topics:**

```bash
ros2 topic list | grep -E '^/(scan|odom|cmd_vel|clock|tf)$'
ros2 topic echo /scan --once --qos-reliability best_effort
ros2 topic echo /odom --once
```

The `/scan` topic should contain a `sensor_msgs/msg/LaserScan` message, and `/odom` a `nav_msgs/msg/Odometry` message. The empty world can result in infinite or maximum-range measurements.

**Test velocity control through ROS 2:**

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.2}, angular: {z: 0.0}}'
```

The robot should move forward in Gazebo. Stop the publisher with **Ctrl+C**, then send a stop command:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0}, angular: {z: 0.0}}'
```

Test rotation similarly with `linear.x: 0.0` and `angular.z: 0.5` if desired.

## ROS interface

| ROS topic | Direction | Gazebo topic | Type |
|---|---|---|---|
| `/scan` | Gazebo → ROS | `/scan` | `sensor_msgs/msg/LaserScan` |
| `/odom` | Gazebo → ROS | `/model/mobile_robot/odometry` | `nav_msgs/msg/Odometry` |
| `/cmd_vel` | ROS → Gazebo | `/cmd_vel` | `geometry_msgs/msg/Twist` |
| `/clock` | Gazebo → ROS | `/clock` | `rosgraph_msgs/msg/Clock` |
| `/tf` | Gazebo → ROS | `/model/mobile_robot/tf` | `tf2_msgs/msg/TFMessage` |

A static TF publisher supplies `chassis → laser_frame` at `(-0.16, 0, 0.905) m`, as in the working project. Nav2 and localization are not part of this milestone.

## Version history

| Tag | Milestone |
|---|---|
| `v0.1.0` | Empty Gazebo world |
| `v0.2.0` | Mobile robot chassis, wheels, and joints |
| `v0.3.0` | Gazebo differential drive |
| `v0.4.0` | 360° LiDAR |
| `v0.5.0` | ROS 2 bridge, odometry, TF, and commands |

Tags are created only after their milestone passes testing.

## Reproduce any previous version

```bash
git clone https://github.com/muhazawan04/ros2-warehouse-control.git
cd ros2-warehouse-control
git tag --list
git switch --detach v0.3.0
```

Use the README from that checked-out version to run it. Return to current development with `git switch main`. To develop from an old release, create a branch: `git switch -c experiment-v0.3 v0.3.0`.

## Version-control workflow

Once tested:

```bash
git diff
git status
git add simulation/config/bridge.yaml simulation/launch/bridge_sim.launch.py README.md
git commit -m "v0.5.0: Bridge Gazebo robot to ROS 2"
git tag -a v0.5.0 -m "ROS 2 Gazebo bridge"
git push origin main
git push origin v0.5.0
```

## Mesh attribution

The original robot visual meshes are TurtleBot3-derived third-party assets. Retain applicable attribution and verify their source license before redistribution.
