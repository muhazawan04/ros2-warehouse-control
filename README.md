# ROS 2 Warehouse Control Center

A simulated autonomous warehouse robot built with **ROS 2 Jazzy**, **Gazebo Harmonic**, **Nav2**, and a **PySide6** desktop application. The system provides a warehouse simulation, mapping and localization, and a desktop interface for monitoring the robot and managing named stations.

## Features

- Differential-drive mobile robot with simulated 2D LiDAR.
- Warehouse environment with shelving and pickup/delivery locations.
- 2D mapping with SLAM Toolbox; localization on a saved map with AMCL.
- Autonomous point-to-point navigation with Nav2.
- PySide6 dashboard with a warehouse map and live robot position/orientation.
- Map-based station editing with named pickup, delivery, and dock locations.
- Delivery request queue in the desktop interface.

**Release:** `v1.0.0` — Desktop dashboard integration. Mission execution controls may depend on the ROS interface included in your checkout; test them in simulation before relying on them.

## Requirements

- Ubuntu 24.04
- ROS 2 Jazzy
- Gazebo Harmonic (Gazebo Sim 8)
- Nav2, SLAM Toolbox, `ros_gz_bridge`, `tf2_ros`, and RViz2
- Python 3.12, `python3-venv`, and the Python dependencies in `requirements.txt`

For autonomous frontier exploration, the separate `frontier_exploration_ros2` ROS 2 package must also be installed and available in your sourced workspace.

## Installation

Clone the repository:

```bash
git clone https://github.com/muhazawan04/ros2-warehouse-control.git
cd ros2-warehouse-control
```

Install ROS dependencies through your existing ROS 2 Jazzy installation, then set up the desktop environment:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Source ROS 2 Jazzy and your ROS 2 workspace as appropriate for your machine. The virtual environment uses `--system-site-packages` so the dashboard can access ROS Python packages such as `rclpy`.

## Running the system

### Saved-map navigation mode

Start the warehouse simulation and localization:

```bash
cd ~/ros2-warehouse-control
ros2 launch "$PWD/simulation/launch/delivery.launch.py"
```

If the delivery launch does **not** already start Nav2 navigation servers, start them in a second terminal:

```bash
cd ~/ros2-warehouse-control
ros2 launch nav2_bringup navigation_launch.py \
  use_sim_time:=true \
  params_file:="$PWD/simulation/config/nav2_delivery_params.yaml" \
  autostart:=true
```

Start the desktop application in another terminal:

```bash
cd ~/ros2-warehouse-control
source .venv/bin/activate
python main.py
```

The desktop application requires a valid saved map at `simulation/maps/warehouse_map.yaml` (with the associated image file) for the warehouse display.

### Mapping mode

To build or update the map, stop the saved-map localization session and launch SLAM mode instead:

```bash
cd ~/ros2-warehouse-control
ros2 launch "$PWD/simulation/launch/warehouse.launch.py"
```

Use RViz2 to monitor mapping:

```bash
ros2 run rviz2 rviz2 --ros-args -p use_sim_time:=true
```

Set RViz2's fixed frame to `map` and add the `/map` and `/scan` displays. Do not run SLAM Toolbox and AMCL concurrently as competing `map → odom` transform publishers.

To save a map:

```bash
cd ~/ros2-warehouse-control
ros2 run nav2_map_server map_saver_cli \
  -f "$PWD/simulation/maps/warehouse_map" \
  --ros-args -p use_sim_time:=true
```

## Dashboard usage

1. Start the saved-map simulation with AMCL and Nav2.
2. Launch `python main.py`.
3. Check the robot's live map marker and localization status.
4. Add or select pickup, delivery, and dock stations on the map. Position navigation goals in free space next to obstacles, not inside them.
5. Save station locations so they can be reused on the same map.
6. Create delivery requests in the queue. Verify navigation functions in simulation before using them with a physical robot.

**Map compatibility:** Station coordinates are tied to a particular occupancy map. If you replace the map, check or recreate station positions before navigation.

## Project layout

```text
ros2-warehouse-control/
├── main.py                    # PySide6 desktop application
├── core/                      # ROS 2 interface and application logic
├── ui/                        # UI components
├── config/                    # Saved station definitions
├── simulation/
│   ├── worlds/                # Gazebo worlds
│   ├── models/                # Robot model and meshes
│   ├── launch/                # Simulation launch files
│   ├── config/                # ROS–Gazebo bridge, SLAM and Nav2 settings
│   └── maps/                  # Occupancy-grid maps
├── requirements.txt
└── README.md
```

## Troubleshooting

- **Dashboard won't appear:** Run `python -u main.py` in a terminal and inspect any errors. A station/map mismatch should not block the main window from opening.
- **No robot position:** Check that AMCL is running and `/amcl_pose` is available (`ros2 topic info /amcl_pose -v`).
- **No LiDAR scan:** Check `/scan` and the Gazebo bridge configuration.
- **Nav2 goals fail:** Confirm the map, localization, TF frames, obstacle clearance, and configured goal tolerances.

## Versions

Git tags capture the project at each milestone. To use this release:

```bash
git fetch --tags
git switch --detach v1.0.0
```

To return to the latest development branch:

```bash
git switch main
```

Previous tags document the progression from the Gazebo world and robot model through LiDAR, ROS 2 integration, SLAM, warehouse navigation, and localization.

## Third-party assets

The robot uses TurtleBot3-derived mesh assets. Retain the relevant upstream copyright, license, and attribution notices when redistributing these files.
