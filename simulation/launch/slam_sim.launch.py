"""Launch the SLAM test world, ROS–Gazebo bridge, robot TF and SLAM Toolbox."""
import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    simulation_dir = Path(__file__).resolve().parents[1]
    world_file = simulation_dir / 'worlds' / 'slam_world.sdf'
    models_dir = simulation_dir / 'models'
    bridge_config = simulation_dir / 'config' / 'bridge.yaml'
    slam_config = simulation_dir / 'config' / 'slam.yaml'

    resource_paths = [str(models_dir)]
    if os.environ.get('GZ_SIM_RESOURCE_PATH'):
        resource_paths.append(os.environ['GZ_SIM_RESOURCE_PATH'])

    slam_launch = Path(get_package_share_directory('slam_toolbox')) / 'launch' / 'online_async_launch.py'

    return LaunchDescription([
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.pathsep.join(resource_paths)),
        ExecuteProcess(cmd=['gz', 'sim', '-r', str(world_file)], output='screen'),
        Node(
            package='ros_gz_bridge', executable='parameter_bridge',
            name='ros_gz_bridge', output='screen',
            parameters=[{'config_file': str(bridge_config), 'use_sim_time': True}],
        ),
        Node(
            package='tf2_ros', executable='static_transform_publisher',
            name='lidar_static_tf',
            arguments=[
                '--x', '-0.16', '--y', '0', '--z', '0.905',
                '--roll', '0', '--pitch', '0', '--yaw', '0',
                '--frame-id', 'chassis', '--child-frame-id', 'laser_frame',
            ],
            output='screen',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(slam_launch)),
            launch_arguments={
                'slam_params_file': str(slam_config),
                'use_sim_time': 'true',
                'autostart': 'true',
            }.items(),
        ),
    ])
