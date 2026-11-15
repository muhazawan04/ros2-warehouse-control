# ROS 2 Warehouse Robot

A versioned robotics project developed with **Gazebo Harmonic** and **ROS 2 Jazzy**. The project builds toward an autonomous warehouse delivery robot, introducing and testing one capability at a time.

> **Current milestone: v0.3.0 — Differential-drive control**  
> This milestone includes a Gazebo world, a mesh-based mobile robot, and Gazebo-native velocity control. ROS 2 topic bridging, LiDAR, mapping, navigation, and the desktop dashboard are planned for later milestones.

## Requirements

- Ubuntu 24.04
- Gazebo Harmonic (`gz sim`)
- Git
- ROS 2 Jazzy (needed for later milestones; not required to drive the robot in v0.3.0)

## Project structure

```text
ros2-warehouse-control/
├── simulation/
│   ├── worlds/
│   │   └── empty_world.sdf
│   ├── models/
│   │   └── mobile_robot/
│   │       ├── model.config
│   │       ├── model.sdf
│   │       └── meshes/
│   ├── launch/
│   ├── config/
│   └── maps/
├── .gitignore
└── README.md
```

## Run this version

From a terminal:

```bash
cd ~/ros2-warehouse-control
export GZ_SIM_RESOURCE_PATH="$PWD/simulation/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
gz sim -r simulation/worlds/empty_world.sdf
```

The robot should appear in the world with its chassis, wheels, and caster. The `-r` flag starts the physics simulation immediately.

### Test differential-drive control

In a second terminal, inspect the Gazebo velocity topics:

```bash
gz topic -l | grep cmd_vel
```

Use the **exact topic printed by the command above**. The examples below assume `/model/mobile_robot/cmd_vel`; if your simulator publishes `/cmd_vel`, replace the topic in all three commands with `/cmd_vel`.

**Drive forward:**

```bash
gz topic -t /model/mobile_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.3}, angular: {z: 0.0}'
```

**Rotate:**

```bash
gz topic -t /model/mobile_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.0}, angular: {z: 0.5}'
```

**Stop:**

```bash
gz topic -t /model/mobile_robot/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.0}, angular: {z: 0.0}'
```

> These are **Gazebo Transport** commands, not ROS 2 `/cmd_vel` commands. The ROS–Gazebo bridge is introduced in a later milestone.
>
> **Milestone scope:** v0.3.0 should contain the original tested chassis, wheels, joints, and DiffDrive settings. If you copied the complete final `model.sdf`, check whether it also includes the LiDAR sensor; that functionality belongs to v0.4.0 and should be separated before tagging v0.3.0.

## Version history

| Tag | Milestone | Key capability |
| --- | --- | --- |
| `v0.1.0` | Initial world | Ground, lighting, physics, and Gazebo systems |
| `v0.2.0` | Robot model | TurtleBot3 mesh-based chassis and wheels; physical model and joints |
| `v0.3.0` | Differential drive | Drive and rotate the robot through Gazebo Transport |

Only treat a milestone as released after it has been tested, committed, and tagged.

## Reuse an earlier version

Clone the repository (replace the URL if your repository changes):

```bash
git clone https://github.com/muhazawan04/ros2-warehouse-control.git
cd ros2-warehouse-control
```

List available version tags:

```bash
git tag --list
```

To **inspect or run a specific version without modifying `main`**, use:

```bash
git switch --detach v0.2.0
```

Run that version using its own README and files. To return to the current development branch:

```bash
git switch main
```

If you want to **modify** an older version, create a new branch rather than making commits in detached-HEAD mode:

```bash
git switch -c experiment-from-v0.2.0 v0.2.0
```

Each tagged version preserves the source files committed at that point; Git does not bundle Ubuntu, ROS 2, Gazebo, or installed dependencies.

## Development workflow

After implementing and **testing** a new milestone:

```bash
git status
git diff
git add .
git commit -m "Describe the tested change"
git tag -a v0.3.0 -m "Differential-drive control"
git push origin main
git push origin v0.3.0
```

Replace the tag and messages as appropriate. **Never recreate or move an existing published tag** to represent new changes; use a new version instead.

## Credits

The robot's visual model uses **TurtleBot3-derived meshes**. Mesh origins and applicable third-party license terms should be documented and verified before public redistribution. Robot configuration and integration are maintained in this repository.
