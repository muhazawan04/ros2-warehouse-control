# ROS 2 Warehouse Robot

A differential-drive mobile robot simulation built with **ROS 2 Jazzy** and **Gazebo Harmonic**, using TurtleBot3-derived visual meshes. The repository is developed in tagged milestones; each tag contains the files needed for that stage.

**Current release: v0.6.0 — 2D LiDAR SLAM.** The robot can be driven around a test environment while SLAM Toolbox builds an occupancy-grid map. Warehouse logistics, Nav2 autonomous navigation, and the desktop dashboard are not included in this release.

## Requirements

- Ubuntu 24.04 with ROS 2 Jazzy and Gazebo Harmonic
- A sourced ROS 2 environment
- ROS–Gazebo bridge, TF tools, SLAM Toolbox, and map server:

```bash
sudo apt install ros-jazzy-ros-gz-bridge ros-jazzy-tf2-ros \
  ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server ros-jazzy-rviz2
```

## Quick start

Clone the repository and check out this version if needed:

```bash
git clone https://github.com/muhazawan04/ros2-warehouse-control.git
cd ros2-warehouse-control
git switch --detach v0.6.0
```

Start **Gazebo, the ROS 2 bridge, TF, and SLAM Toolbox** in one terminal:

```bash
ros2 launch "$PWD/simulation/launch/slam_sim.launch.py"
```

In a second terminal, start RViz:

```bash
ros2 run rviz2 rviz2 --ros-args -p use_sim_time:=true
```

In RViz, set **Fixed Frame** to `map` and add the `Map` display on `/map`, a `LaserScan` display on `/scan`, and optionally `TF`. Use a suitable QoS setting for the map display if it does not appear.

## Drive and map

Move the robot forward by publishing velocity commands:

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.2}, angular: {z: 0.0}}'
```

Press **Ctrl+C**, then send a stop command:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0}, angular: {z: 0.0}}'
```

To turn in place, use `linear.x: 0.0` and `angular.z: 0.5`. Explore near the walls and obstacles; the map should grow as the robot moves. The test world is approximately 10 m × 10 m with several obstacles.

Check for map data:

```bash
ros2 topic echo /map --once --qos-durability transient_local
```

Save the generated map after exploring:

```bash
mkdir -p simulation/maps
ros2 run nav2_map_server map_saver_cli \
  -f "$PWD/simulation/maps/slam_test_map" --ros-args -p use_sim_time:=true
```

This writes `slam_test_map.yaml` and `slam_test_map.pgm`. Maps are generated at runtime and are not required to launch SLAM.

## Project layout

```text
simulation/
├── worlds/
│   ├── empty_world.sdf
│   └── slam_world.sdf
├── models/mobile_robot/       # SDF robot and meshes
├── config/
│   ├── bridge.yaml            # ROS–Gazebo topics
│   └── slam.yaml              # SLAM Toolbox parameters
├── launch/
│   ├── bridge_sim.launch.py   # Previous stage
│   └── slam_sim.launch.py     # SLAM test launch
└── maps/                      # Optional saved maps
```

## ROS interfaces

| Topic | Purpose |
|---|---|
| `/cmd_vel` | Robot velocity commands |
| `/scan` | LiDAR measurements |
| `/odom` | Wheel odometry |
| `/tf` | Robot and map transforms |
| `/map` | Occupancy grid from SLAM Toolbox |
| `/clock` | Simulation time |

## Release history

| Tag | Capability |
|---|---|
| v0.1.0 | Basic Gazebo world |
| v0.2.0 | Mobile robot model |
| v0.3.0 | Differential-drive control |
| v0.4.0 | LiDAR sensor |
| v0.5.0 | ROS 2–Gazebo bridge |
| **v0.6.0** | **SLAM Toolbox and map saving** |

To switch between installed versions, run `git switch --detach <tag>`. To return to the current development branch, use `git switch main` (after saving any outstanding changes).

## Asset attribution

The robot uses TurtleBot3-derived visual meshes. Preserve the relevant third-party notices and verify their original licensing terms before redistributing assets.
