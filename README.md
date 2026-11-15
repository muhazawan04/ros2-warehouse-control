# ROS 2 Warehouse Robot

A simulated differential-drive mobile robot for **autonomous warehouse mapping and navigation**, built with **ROS 2 Jazzy**, **Gazebo Harmonic**, **SLAM Toolbox**, and **Nav2**. The robot uses a 2D LiDAR, wheel odometry, and TurtleBot3-derived visual meshes.

**Release v0.9.0 — Autonomous exploration and saved-map navigation.** This release supports two distinct operating modes:

- **Mapping:** the robot explores automatically using frontier exploration, with SLAM generating an occupancy grid.
- **Navigation:** the robot localizes against a saved warehouse map using AMCL and navigates to user-selected goals.

## Requirements

- Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic
- ROS 2 packages for `ros_gz_bridge`, `tf2_ros`, `slam_toolbox`, `rviz2`, Nav2, and the Nav2 map server
- The `frontier_exploration_ros2` package built in a sourced ROS 2 workspace (required only for autonomous exploration)

Install standard packages if needed:

```bash
sudo apt update
sudo apt install ros-jazzy-ros-gz-bridge ros-jazzy-tf2-ros \
  ros-jazzy-slam-toolbox ros-jazzy-rviz2 \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-nav2-map-server
```

For frontier exploration, install [frontier_exploration_ros2](https://github.com/mertgulerx/frontier_exploration_ros2) into your ROS 2 workspace and build it with `colcon`. Source that workspace before starting the explorer.

## Quick start

Clone the repository and check out the release:

```bash
git clone https://github.com/muhazawan04/ros2-warehouse-control.git
cd ros2-warehouse-control
git switch --detach v0.9.0
```

Run commands below from the **project root**. Source ROS 2 and your frontier-exploration workspace in terminals where necessary.

### Mode A — Autonomous mapping

Start each command in a separate terminal:

**1. Gazebo, ROS bridge, and SLAM**

```bash
ros2 launch "$PWD/simulation/launch/warehouse.launch.py"
```

**2. Nav2 navigation**

```bash
ros2 launch nav2_bringup navigation_launch.py \
  use_sim_time:=true \
  params_file:="$PWD/simulation/config/nav2_params.yaml" \
  autostart:=true
```

**3. Autonomous frontier exploration**

```bash
ros2 launch frontier_exploration_ros2 frontier_explorer.launch.py \
  params_file:="$PWD/simulation/config/warehouse_exploration.yaml" \
  use_sim_time:=true autostart:=true
```

**4. Optional visualization**

```bash
ros2 run rviz2 rviz2 --ros-args -p use_sim_time:=true
```

In RViz, set **Fixed Frame** to `map` and add **Map** (`/map`), **LaserScan** (`/scan`), and optionally the frontier markers (`/explore/frontiers`). The robot should choose reachable frontiers and gradually expand the map.

**Save the finished map** while SLAM is running:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f "$PWD/simulation/maps/warehouse_map" \
  --ros-args -p use_sim_time:=true
```

This writes `warehouse_map.yaml` and `warehouse_map.pgm`. An example map from the tested warehouse is included with this release; regenerate it if the world geometry or map frame changes.

### Mode B — Localization and navigation on the saved map

**Stop all mapping-mode processes first**, including SLAM Toolbox, frontier exploration, and the mapping Nav2 instance. Running SLAM and AMCL together can cause conflicting `map → odom` transforms.

Start **Gazebo + ROS bridge + map server + AMCL + Nav2**:

```bash
ros2 launch "$PWD/simulation/launch/delivery.launch.py"
```

Open RViz separately:

```bash
ros2 run rviz2 rviz2 --ros-args -p use_sim_time:=true
```

Set **Fixed Frame** to `map`. Add a **Map** display for `/map` (use **Transient Local** durability if necessary), **LaserScan** for `/scan`, and Nav2's available displays. Send a goal using **Nav2 Goal** to a clear area of the saved map. The robot should navigate using AMCL localization.

The delivery configuration uses the validated **0.50 m position goal tolerance** and **0.25 rad yaw tolerance**. The initial AMCL pose is configured for the warehouse docking start location in the saved map frame.

## Verification

Mapping mode:

```bash
ros2 topic info /map
ros2 action list | grep navigate_to_pose
```

Localization mode:

```bash
ros2 lifecycle get /amcl
ros2 lifecycle get /map_server
ros2 action list | grep navigate_to_pose
```

Both lifecycle nodes should be `active`, and the navigation action should be available. Confirm navigation by sending a goal in RViz2.

## Project layout

```text
simulation/
├── config/
│   ├── bridge.yaml
│   ├── slam.yaml
│   ├── nav2_params.yaml
│   ├── warehouse_exploration.yaml
│   └── nav2_delivery_params.yaml
├── launch/
│   ├── warehouse.launch.py
│   └── delivery.launch.py
├── maps/
│   ├── warehouse_map.yaml
│   └── warehouse_map.pgm
├── models/mobile_robot/
└── worlds/warehouse_world.sdf
```

## Releases

| Version | Capability |
| --- | --- |
| v0.1.0 | Initial Gazebo world |
| v0.2.0 | Robot model |
| v0.3.0 | Differential-drive movement |
| v0.4.0 | LiDAR |
| v0.5.0 | ROS 2–Gazebo bridge |
| v0.6.0 | SLAM Toolbox |
| v0.7.0 | Warehouse environment |
| v0.8.0 | Nav2 navigation with live SLAM |
| **v0.9.0** | **Autonomous exploration, map saving, AMCL, and saved-map navigation** |

To inspect an older version, run `git switch --detach v0.8.0`. To resume development, run `git switch main` (after saving or committing any changes).

## Notes

- This version simulates mapping and navigation; package handling and desktop mission controls are introduced later.
- Navigation goals should be placed in free space with clearance from shelves and walls.
- The TurtleBot3-derived visual meshes remain third-party assets; retain their applicable licensing and attribution when redistributing.
