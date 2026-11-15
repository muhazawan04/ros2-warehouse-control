"""ROS 2 AMCL subscriber and single-goal Nav2 client for the warehouse GUI."""
import math
import queue

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from PySide6.QtCore import QThread, Signal


class ROSInterface(QThread):
    pose_updated = Signal(float, float, float)
    connection_changed = Signal(bool)
    navigation_available = Signal(bool)
    navigation_status = Signal(str)
    navigation_finished = Signal(bool, str)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self._commands = queue.Queue()
        self._active_goal = False
        self._goal_handle = None
        self._last_available = None
        self._latest_distance = None

    def navigate_to(self, name, x, y, yaw):
        """Safe to call from the Qt GUI thread."""
        self._commands.put(('navigate', str(name), float(x), float(y), float(yaw)))

    def cancel_navigation(self):
        self._commands.put(('cancel',))

    def run(self):
        context = Context()
        node = None
        executor = None
        try:
            rclpy.init(context=context)
            node = Node(
                'warehouse_control_gui', context=context,
                parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)]
            )
            qos = QoSProfile(
                depth=10, reliability=ReliabilityPolicy.RELIABLE,
                durability=DurabilityPolicy.TRANSIENT_LOCAL
            )
            node.create_subscription(
                PoseWithCovarianceStamped, '/amcl_pose', self._pose_callback, qos
            )
            self._action_client = ActionClient(node, NavigateToPose, '/navigate_to_pose')
            executor = SingleThreadedExecutor(context=context)
            executor.add_node(node)

            cycle = 0
            while self.running and rclpy.ok(context=context):
                executor.spin_once(timeout_sec=0.10)
                cycle += 1
                if cycle % 10 == 0:
                    available = self._action_client.server_is_ready()
                    if available != self._last_available:
                        self._last_available = available
                        self.navigation_available.emit(available)

                while self.running:
                    try:
                        cmd = self._commands.get_nowait()
                    except queue.Empty:
                        break
                    if cmd[0] == 'navigate':
                        if self._active_goal:
                            self.navigation_status.emit('A navigation goal is already active.')
                        elif not self._action_client.server_is_ready():
                            self.navigation_status.emit('Nav2 action server is unavailable.')
                            self.navigation_finished.emit(False, 'Nav2 unavailable')
                        else:
                            self._send_goal(node, *cmd[1:])
                    elif cmd[0] == 'cancel':
                        if self._goal_handle is not None:
                            self.navigation_status.emit('Requesting navigation cancellation...')
                            self._goal_handle.cancel_goal_async()
                        elif self._active_goal:
                            self.navigation_status.emit('Goal still being accepted; please retry cancel shortly.')
        except Exception as exc:
            self.error_occurred.emit(f'{type(exc).__name__}: {exc}')
        finally:
            if executor is not None:
                executor.shutdown()
            if node is not None:
                node.destroy_node()
            if rclpy.ok(context=context):
                rclpy.shutdown(context=context)

    def _pose_callback(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        self.pose_updated.emit(p.x, p.y, yaw)
        # Do not time out while a stationary robot is not producing new poses.
        if not getattr(self, '_pose_seen', False):
            self._pose_seen = True
            self.connection_changed.emit(True)

    def _send_goal(self, node, name, x, y, yaw):
        goal = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = node.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.z = math.sin(yaw / 2)
        pose.pose.orientation.w = math.cos(yaw / 2)
        goal.pose = pose
        self._active_goal = True
        self._goal_handle = None
        self._latest_distance = None
        self.navigation_status.emit(f'Sending goal to {name}...')
        future = self._action_client.send_goal_async(goal, feedback_callback=self._feedback)
        future.add_done_callback(self._goal_response)

    def _goal_response(self, future):
        try:
            handle = future.result()
            if not handle.accepted:
                self._finish(False, 'Navigation goal rejected by Nav2')
                return
            self._goal_handle = handle
            self.navigation_status.emit('Goal accepted — robot navigating')
            handle.get_result_async().add_done_callback(self._goal_result)
        except Exception as exc:
            self._finish(False, f'Failed to send goal: {exc}')

    def _feedback(self, msg):
        distance = msg.feedback.distance_remaining
        if self._latest_distance is None or abs(self._latest_distance - distance) >= 0.3:
            self._latest_distance = distance
            self.navigation_status.emit(f'Navigating — {distance:.1f} m remaining')

    def _goal_result(self, future):
        try:
            status = future.result().status
            if status == GoalStatus.STATUS_SUCCEEDED:
                self._finish(True, 'Destination reached')
            elif status == GoalStatus.STATUS_CANCELED:
                self._finish(False, 'Navigation cancelled')
            elif status == GoalStatus.STATUS_ABORTED:
                self._finish(False, 'Navigation aborted (check Nav2)')
            else:
                self._finish(False, f'Navigation ended with status {status}')
        except Exception as exc:
            self._finish(False, f'Navigation result error: {exc}')

    def _finish(self, success, message):
        self._active_goal = False
        self._goal_handle = None
        self.navigation_status.emit(message)
        self.navigation_finished.emit(success, message)

    def stop(self):
        self.running = False
        self.wait(3000)
