import os

from launch import LaunchDescription
from launch.actions import (
    ExecuteProcess,
    SetEnvironmentVariable,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    world_file = os.path.join(
        project_dir, "worlds", "warehouse_world.sdf"
    )

    models_path = os.path.join(
        project_dir, "models"
    )

    bridge_config = os.path.join(
        project_dir, "config", "bridge.yaml"
    )

    slam_config = os.path.join(
        project_dir, "config", "slam.yaml"
    )

    # Gazebo model search path
    existing_path = os.environ.get("GZ_SIM_RESOURCE_PATH", "")

    resource_path = os.pathsep.join(
        path for path in [models_path, existing_path] if path
    )

    set_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=resource_path
    )

    # 1. Gazebo simulation
    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", world_file],
        output="screen"
    )

    # 2. ROS 2 ↔ Gazebo bridge
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        output="screen",
        parameters=[
            {
                "config_file": bridge_config,
                "use_sim_time": True
            }
        ]
    )

    # 3. Static TF: chassis → laser_frame
    lidar_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="lidar_static_tf",
        arguments=[
            "--x", "-0.16",
            "--y", "0",
            "--z", "0.905",
            "--roll", "0",
            "--pitch", "0",
            "--yaw", "0",
            "--frame-id", "chassis",
            "--child-frame-id", "laser_frame"
        ],
        output="screen"
    )

    # 4. SLAM Toolbox
    # SLAM Toolbox with automatic lifecycle activation
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("slam_toolbox"),
                "launch",
                "online_async_launch.py"
            )
        ),
        launch_arguments={
            "slam_params_file": slam_config,
            "use_sim_time": "true",
            "autostart": "true"
        }.items()
    )

    return LaunchDescription([
        set_resource_path,
        gazebo,
        bridge,
        lidar_tf,
        slam
    ])