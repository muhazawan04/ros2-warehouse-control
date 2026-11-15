# ROS 2 Warehouse Robot

A differential-drive robot simulation for mapping and navigating a warehouse using **ROS 2 Jazzy**, **Gazebo Harmonic**, **SLAM Toolbox**, and **Nav2**. The robot uses TurtleBot3-derived visual meshes, a simulated 2D LiDAR, and wheel odometry.

**Release: v0.8.0 — Navigation with live SLAM.** This release adds Nav2 path planning and goal navigation in the warehouse while SLAM Toolbox creates the occupancy map. Autonomous frontier exploration, saved-map localization (AMCL), and the desktop dashboard are not included in this release.

## Requirements

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic

Install the ROS packages if needed:

```bash
sudo apt update
sudo apt install ros-jazzy-ros-gz-bridge ros-jazzy-tf2-ros \
  ros-jazzy-slam-toolbox ros-jazzy-rviz2 \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-map-server
```

Source ROS 2 in each terminal if your shell does not already do so:

```bash
source /opt/ros/jazzy/setup.bash
```

## Quick start

Clone the repository and select this release:

```bash
git clone https://github.com/muhazawan04/ros2-warehouse-control.git
cd ros2-warehouse-control
git switch --detach v0.8.0
```

Start each command in a separate terminal. For terminals 1 and 2, run from the project directory.

**Terminal 1 — Gazebo, ROS–Gazebo bridge, and SLAM**

```bash
ros2 launch "$PWD/simulation/launch/warehouse.launch.py"
```

**Terminal 2 — Nav2 navigation**

```bash
ros2 launch nav2_bringup navigation_launch.py \
  use_sim_time:=true \
  params_file:="$PWD/simulation/config/nav2_params.yaml" \
  autostart:=true
```

**Terminal 3 — RViz2**

```bash
ros2 run rviz2 rviz2 --ros-args -p use_sim_time:=true
```

In RViz2, set **Fixed Frame** to `map`. Add **Map** (`/map`), **LaserScan** (`/scan`), and optionally **TF**, **RobotModel** (if configured), and Nav2's costmap displays. For the Map display, use **Transient Local** durability if needed.

## Test navigation

1. Verify that `/map` updates as the robot moves. If the map is mostly unknown, manually explore a nearby open area using `/cmd_vel` before sending a goal.
2. Check that the navigation action server is available:

   ```bash
   ros2 action list | grep navigate_to_pose
   ```

3. In RViz2, choose **Nav2 Goal** (or **2D Goal Pose**, depending on the toolbar configuration) and select a reachable, mapped, obstacle-free location. Drag to set the desired final heading.
4. Confirm that Nav2 generates a route and the robot drives toward the selected goal. Monitor progress and the resulting map in RViz2.

Do not send velocity commands manually while Nav2 is executing a goal. Avoid placing goals inside shelves, walls, or unexplored space.

## Save an occupancy map

After sufficient exploration, save the map:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f "$PWD/simulation/maps/warehouse_map" \
  --ros-args -p use_sim_time:=true
```

The saved `warehouse_map.yaml` and `warehouse_map.pgm` can be reused for localization in later releases.

## Project structure

```text
simulation/
├── config/
│   ├── bridge.yaml
│   ├── slam.yaml
│   └── nav2_params.yaml
├── launch/
│   └── warehouse.launch.py
├── models/
│   └── mobile_robot/
├── worlds/
│   └── warehouse_world.sdf
└── maps/
```

## Releases

| Version | Capability |
| --- | --- |
| v0.1.0 | Gazebo world |
| v0.2.0 | Mobile robot model |
| v0.3.0 | Differential-drive control |
| v0.4.0 | LiDAR sensor |
| v0.5.0 | ROS 2–Gazebo bridge |
| v0.6.0 | SLAM Toolbox |
| v0.7.0 | Warehouse environment |
| **v0.8.0** | **Nav2 navigation with live SLAM** |

To inspect an earlier release, use `git switch --detach v0.7.0`. Return to the development branch with `git switch main`. Save any local changes before switching.

## Third-party assets

The robot includes TurtleBot3-derived visual meshes. See the upstream TurtleBot3 project for attribution and licensing details; retain applicable notices when redistributing assets.
