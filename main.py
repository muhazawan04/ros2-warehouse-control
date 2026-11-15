import hashlib
import math
import sys
from pathlib import Path

import yaml
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFormLayout, QFrame,
    QGraphicsItem, QGraphicsScene, QGraphicsView, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from core.ros_interface import ROSInterface

ROOT = Path(__file__).resolve().parent
DEFAULT_MAP = ROOT / 'simulation/maps/warehouse_map.yaml'
STATIONS_FILE = ROOT / 'config/stations.yaml'
COLORS = {'pickup': '#38bdf8', 'delivery': '#fb923c', 'dock': '#22c55e'}


class MapView(QGraphicsView):
    clicked_map = Signal(float, float)
    clicked_station = Signal(str)

    def __init__(self):
        super().__init__()
        self.scene_obj = QGraphicsScene(self)
        self.setScene(self.scene_obj)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet('background:#111827; border:0;')
        self.map_loaded = False
        self.edit_mode = False
        self.stations = {}
        self.robot_marker = None
        self.robot_pose = None
        self.map_path = None
        self.map_id = None

    def load_map(self, yaml_path):
        yaml_path = Path(yaml_path).expanduser().resolve()
        try:
            metadata = yaml.safe_load(yaml_path.read_text())
            image_path = (yaml_path.parent / metadata['image']).resolve()
            pixmap = QPixmap(str(image_path))
            if pixmap.isNull():
                raise ValueError(f'Could not load map image: {image_path}')
            resolution = float(metadata['resolution'])
            origin = [float(v) for v in metadata['origin']]
            if resolution <= 0 or len(origin) < 3:
                raise ValueError('Invalid map resolution or origin')
            fingerprint = hashlib.sha256(
                image_path.read_bytes() +
                f'{resolution}|{origin[:3]}'.encode()
            ).hexdigest()[:16]
        except Exception as exc:
            QMessageBox.critical(self, 'Map loading failed', str(exc))
            return False

        self.scene_obj.clear()
        self.map_item = self.scene_obj.addPixmap(pixmap)
        self.scene_obj.setSceneRect(self.map_item.boundingRect())
        self.resolution = resolution
        self.origin_x, self.origin_y, self.origin_yaw = origin[:3]
        self.map_path = yaml_path
        self.map_id = fingerprint
        self.map_loaded = True
        self.robot_marker = None
        self.draw_stations()
        self.create_robot_marker()
        self.fitInView(self.scene_obj.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        return True

    def map_to_scene_point(self, x, y):
        dx, dy = x - self.origin_x, y - self.origin_y
        c, s = math.cos(self.origin_yaw), math.sin(self.origin_yaw)
        mx = (c * dx + s * dy) / self.resolution
        my = (-s * dx + c * dy) / self.resolution
        return QPointF(mx, self.map_item.pixmap().height() - 1 - my)

    def scene_to_map_point(self, point):
        lx = point.x() * self.resolution
        ly = (self.map_item.pixmap().height() - 1 - point.y()) * self.resolution
        c, s = math.cos(self.origin_yaw), math.sin(self.origin_yaw)
        return (self.origin_x + c * lx - s * ly,
                self.origin_y + s * lx + c * ly)

    def draw_stations(self):
        if not self.map_loaded:
            return
        for item in list(self.scene_obj.items()):
            if item.data(0) == 'station':
                self.scene_obj.removeItem(item)
        for station_id, data in self.stations.items():
            center = self.map_to_scene_point(data['x'], data['y'])
            color = QColor(COLORS[data['type']])
            circle = self.scene_obj.addEllipse(-7, -7, 14, 14,
                                               QPen(QColor('#ffffff'), 1.5),
                                               QBrush(color))
            circle.setPos(center)
            circle.setZValue(20)
            circle.setData(0, 'station')
            circle.setData(1, station_id)
            circle.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
            label = self.scene_obj.addText(station_id)
            label.setDefaultTextColor(color)
            label.setPos(center + QPointF(10, -25))
            label.setZValue(21)
            label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
            label.setData(0, 'station')
            label.setData(1, station_id)
            # Heading tick on the marker, rotated in map image coordinates.
            heading = self.scene_obj.addLine(0, 0, 17, 0, QPen(color, 3))
            heading.setPos(center)
            heading.setRotation(-math.degrees(data['yaw'] - self.origin_yaw))
            heading.setZValue(19)
            heading.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
            heading.setData(0, 'station')
            heading.setData(1, station_id)

    def create_robot_marker(self):
        arrow = QPolygonF([QPointF(15, 0), QPointF(-9, -9),
                           QPointF(-5, 0), QPointF(-9, 9)])
        self.robot_marker = self.scene_obj.addPolygon(
            arrow, QPen(QColor('white'), 2), QBrush(QColor('#a3e635')))
        self.robot_marker.setZValue(30)
        self.robot_marker.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.robot_marker.setVisible(False)
        if self.robot_pose is not None:
            self.update_robot(*self.robot_pose)

    def update_robot(self, x, y, yaw):
        self.robot_pose = (x, y, yaw)
        if not self.map_loaded or self.robot_marker is None:
            return
        self.robot_marker.setPos(self.map_to_scene_point(x, y))
        self.robot_marker.setRotation(-math.degrees(yaw - self.origin_yaw))
        self.robot_marker.setVisible(True)

    def mousePressEvent(self, event):
        if self.map_loaded and event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.position().toPoint())
            if self.edit_mode and self.map_item.contains(pos):
                self.clicked_map.emit(*self.scene_to_map_point(pos))
                event.accept()
                return
            for item in self.scene_obj.items(pos):
                if item.data(0) == 'station':
                    self.clicked_station.emit(item.data(1))
                    event.accept()
                    return
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        self.scale(1.15 if event.angleDelta().y() > 0 else 1 / 1.15,
                   1.15 if event.angleDelta().y() > 0 else 1 / 1.15)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.map_loaded and not getattr(self, '_resized_once', False):
            self.fitInView(self.scene_obj.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self._resized_once = True


class WarehouseControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Warehouse Control Center — Station Editor')
        self.resize(1500, 850)
        self.stations = {}
        self.missions = []
        self.pending_action = None
        self.nav_available = False
        self.nav_busy = False
        self.mission_active = False
        self.mission_cancelling = False
        self.mission_steps = []
        self.mission_step_index = 0
        self.setup_ui()
        self.apply_style()
        if DEFAULT_MAP.exists():
            self.set_map(DEFAULT_MAP)
        else:
            self.statusBar().showMessage('Select a map YAML with Load Map')
        self.ros = ROSInterface()
        self.ros.pose_updated.connect(self.update_robot_position)
        self.ros.connection_changed.connect(self.update_connection)
        self.ros.error_occurred.connect(self.show_ros_error)
        self.ros.navigation_available.connect(self.nav_availability_changed)
        self.ros.navigation_status.connect(self.nav_status_changed)
        self.ros.navigation_finished.connect(self.nav_finished)
        self.ros.start()

    def heading(self, text):
        label = QLabel(text)
        label.setObjectName('sectionTitle')
        return label

    def setup_ui(self):
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        layout = QVBoxLayout(wrapper)
        header = QHBoxLayout()
        title = QLabel('Warehouse Control Center')
        title.setObjectName('mainTitle')
        header.addWidget(title)
        header.addStretch()
        self.connection_label = QLabel('● WAITING FOR LOCALIZATION')
        header.addWidget(self.connection_label)
        layout.addLayout(header)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left = QFrame()
        left.setObjectName('card')
        l = QVBoxLayout(left)
        l.addWidget(self.heading('Delivery Management'))
        form = QFormLayout()
        self.pickup_combo = QComboBox()
        self.delivery_combo = QComboBox()
        form.addRow('Pickup', self.pickup_combo)
        form.addRow('Delivery', self.delivery_combo)
        l.addLayout(form)
        add_delivery = QPushButton('+ Add Delivery to Queue')
        add_delivery.clicked.connect(self.add_delivery)
        l.addWidget(add_delivery)
        l.addWidget(self.heading('Mission Queue'))
        self.queue_list = QListWidget()
        l.addWidget(self.queue_list)
        remove_delivery = QPushButton('Remove Selected')
        remove_delivery.clicked.connect(self.remove_delivery)
        l.addWidget(remove_delivery)
        self.start_button = QPushButton('▶ Start Delivery')
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_delivery)
        l.addWidget(self.start_button)
        self.cancel_mission_button = QPushButton('■ Cancel Delivery')
        self.cancel_mission_button.setEnabled(False)
        self.cancel_mission_button.clicked.connect(self.cancel_delivery)
        l.addWidget(self.cancel_mission_button)
        self.mission_label = QLabel('No active delivery')
        self.mission_label.setWordWrap(True)
        l.addWidget(self.mission_label)

        l.addWidget(self.heading('Station Editor'))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('e.g. B1, D2, Dock')
        self.type_combo = QComboBox()
        self.type_combo.addItem('Pickup', 'pickup')
        self.type_combo.addItem('Delivery', 'delivery')
        self.type_combo.addItem('Dock', 'dock')
        sf = QFormLayout()
        sf.addRow('Name', self.name_input)
        sf.addRow('Type', self.type_combo)
        l.addLayout(sf)
        self.place_button = QPushButton('📍 Place Station on Map')
        self.place_button.clicked.connect(self.start_placing)
        l.addWidget(self.place_button)
        self.station_list = QListWidget()
        self.station_list.itemSelectionChanged.connect(self.selected_station_changed)
        l.addWidget(self.station_list)
        move_button = QPushButton('Move Selected on Map')
        move_button.clicked.connect(self.start_moving)
        l.addWidget(move_button)
        yaw_button = QPushButton('Change Selected Orientation')
        yaw_button.clicked.connect(self.change_yaw)
        l.addWidget(yaw_button)
        rename_button = QPushButton('Rename Selected')
        rename_button.clicked.connect(self.rename_selected)
        l.addWidget(rename_button)
        delete_button = QPushButton('Delete Selected')
        delete_button.clicked.connect(self.delete_selected)
        l.addWidget(delete_button)
        save_button = QPushButton('Save Stations')
        save_button.clicked.connect(self.save_stations)
        l.addWidget(save_button)
        self.navigate_station_button = QPushButton('▶ Navigate to Selected Station')
        self.navigate_station_button.setEnabled(False)
        self.navigate_station_button.clicked.connect(self.navigate_selected_station)
        l.addWidget(self.navigate_station_button)
        self.cancel_nav_button = QPushButton('■ Cancel Navigation')
        self.cancel_nav_button.setEnabled(False)
        self.cancel_nav_button.clicked.connect(self.cancel_navigation)
        l.addWidget(self.cancel_nav_button)

        middle = QFrame()
        middle.setObjectName('card')
        m = QVBoxLayout(middle)
        mh = QHBoxLayout()
        mh.addWidget(self.heading('Warehouse Map'))
        mh.addStretch()
        load_button = QPushButton('Load Map YAML')
        load_button.clicked.connect(self.choose_map)
        mh.addWidget(load_button)
        m.addLayout(mh)
        self.map_view = MapView()
        self.map_view.clicked_map.connect(self.place_at)
        self.map_view.clicked_station.connect(self.select_station)
        m.addWidget(self.map_view)
        self.map_help = QLabel('Mouse wheel: zoom  •  drag: pan  •  click marker: select')
        m.addWidget(self.map_help)

        right = QFrame()
        right.setObjectName('card')
        r = QVBoxLayout(right)
        r.addWidget(self.heading('Robot Status'))
        self.robot_status = QLabel('WAITING')
        r.addWidget(self.robot_status)
        r.addWidget(self.heading('Position (map frame)'))
        self.position_label = QLabel('X: --\nY: --\nYaw: --')
        r.addWidget(self.position_label)
        r.addWidget(self.heading('Nav2'))
        self.nav_status_label = QLabel('Checking Nav2 action server...')
        self.nav_status_label.setWordWrap(True)
        r.addWidget(self.nav_status_label)
        r.addWidget(self.heading('Selected Station'))
        self.station_info = QLabel('None')
        self.station_info.setWordWrap(True)
        r.addWidget(self.station_info)
        r.addStretch()
        r.addWidget(QLabel('Delivery missions use saved station coordinates.'))

        for panel in (left, middle, right):
            splitter.addWidget(panel)
        splitter.setSizes([350, 850, 260])
        self.statusBar().showMessage('Ready')

    def set_map(self, path):
        if not self.map_view.load_map(path):
            return
        self.load_stations()
        self.statusBar().showMessage(f'Map loaded: {path}')

    def choose_map(self):
        if self.mission_active:
            QMessageBox.information(self, 'Delivery running', 'Finish or cancel the delivery before editing the map or stations.')
            return
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open ROS map YAML', str(DEFAULT_MAP.parent), 'YAML (*.yaml *.yml)')
        if filename:
            self.set_map(filename)

    def load_stations(self):
        self.stations = {}
        if STATIONS_FILE.exists():
            try:
                content = yaml.safe_load(STATIONS_FILE.read_text()) or {}
                if content.get('map_id') == self.map_view.map_id:
                    self.stations = content.get('stations', {}) or {}
                else:
                    # Start with an empty station list when the map differs.
                    # Do not interrupt application startup.
                    self.stations = {}
            except Exception as exc:
                QMessageBox.warning(self, 'Station file error', str(exc))
        self.refresh_stations()

    def refresh_stations(self):
        self.map_view.stations = self.stations
        self.map_view.draw_stations()
        self.station_list.clear()
        for key, data in sorted(self.stations.items()):
            self.station_list.addItem(f'{key}  ({data["type"]})')
        current_pickup = self.pickup_combo.currentText()
        current_delivery = self.delivery_combo.currentText()
        self.pickup_combo.clear()
        self.delivery_combo.clear()
        self.pickup_combo.addItems(sorted(
            k for k, v in self.stations.items() if v['type'] == 'pickup'))
        self.delivery_combo.addItems(sorted(
            k for k, v in self.stations.items() if v['type'] == 'delivery'))
        if current_pickup:
            self.pickup_combo.setCurrentText(current_pickup)
        if current_delivery:
            self.delivery_combo.setCurrentText(current_delivery)
        self.refresh_queue()
        self.update_navigation_buttons()

    def selected_id(self):
        item = self.station_list.currentItem()
        return item.text().split('  (', 1)[0] if item else None

    def select_station(self, name):
        for i in range(self.station_list.count()):
            if self.station_list.item(i).text().startswith(name + '  ('):
                self.station_list.setCurrentRow(i)
                break

    def selected_station_changed(self):
        name = self.selected_id()
        if not name:
            self.station_info.setText('None')
            return
        s = self.stations.get(name)
        if s is None:
            self.station_info.setText('None')
            return
        self.station_info.setText(
            f'{name} — {s["type"]}\nX: {s["x"]:.2f} m\n'
            f'Y: {s["y"]:.2f} m\nYaw: {math.degrees(s["yaw"]):.1f}°')

    def start_placing(self):
        if self.mission_active:
            QMessageBox.information(self, 'Delivery running', 'Finish or cancel the delivery before editing the map or stations.')
            return
        name = self.name_input.text().strip()
        if not self.map_view.map_loaded:
            QMessageBox.warning(self, 'No map', 'Load a map first.')
            return
        if not name:
            QMessageBox.information(self, 'Station name', 'Enter a station name first.')
            return
        if name in self.stations:
            QMessageBox.warning(self, 'Duplicate station', 'This station name already exists.')
            return
        self.pending_action = ('add', name)
        self.map_view.edit_mode = True
        self.map_help.setText(f'Click a FREE SPACE position for station {name} (Esc not required: click button again to replace)')

    def start_moving(self):
        if self.mission_active:
            QMessageBox.information(self, 'Delivery running', 'Finish or cancel the delivery before editing the map or stations.')
            return
        name = self.selected_id()
        if not name:
            QMessageBox.information(self, 'Select station', 'Select a station first.')
            return
        self.pending_action = ('move', name)
        self.map_view.edit_mode = True
        self.map_help.setText(f'Click the new navigation position for {name}')

    def place_at(self, x, y):
        if self.pending_action is None:
            return
        action, name = self.pending_action
        self.pending_action = None
        self.map_view.edit_mode = False
        self.map_help.setText('Mouse wheel: zoom  •  drag: pan  •  click marker: select')
        previous_deg = math.degrees(self.stations[name]['yaw']) if action == 'move' else 0.0
        degrees, accepted = QInputDialog.getDouble(
            self, 'Robot stopping orientation',
            f'Yaw for {name} (degrees, ROS map frame):',
            previous_deg, -180.0, 180.0, 1)
        if not accepted:
            return
        station_type = (self.type_combo.currentData() if action == 'add'
                        else self.stations[name]['type'])
        self.stations[name] = {
            'type': station_type, 'x': round(x, 4),
            'y': round(y, 4), 'yaw': round(math.radians(degrees), 6)}
        self.refresh_stations()
        self.select_station(name)
        self.statusBar().showMessage(
            f'{name}: x={x:.2f}, y={y:.2f}, yaw={degrees:.1f}°. Save Stations to persist.')

    def change_yaw(self):
        if self.mission_active:
            QMessageBox.information(self, 'Delivery running', 'Finish or cancel the delivery before editing the map or stations.')
            return
        name = self.selected_id()
        if not name:
            return
        degrees, ok = QInputDialog.getDouble(
            self, 'Station orientation', 'Yaw (degrees):',
            math.degrees(self.stations[name]['yaw']), -180, 180, 1)
        if ok:
            self.stations[name]['yaw'] = round(math.radians(degrees), 6)
            self.refresh_stations()
            self.select_station(name)

    def rename_selected(self):
        if self.mission_active:
            QMessageBox.information(self, 'Delivery running', 'Finish or cancel the delivery before editing the map or stations.')
            return
        name = self.selected_id()
        if not name:
            return
        new_name, ok = QInputDialog.getText(
            self, 'Rename station', 'New name:', text=name)
        new_name = new_name.strip()
        if ok and new_name and (new_name == name or new_name not in self.stations):
            if new_name != name:
                self.stations[new_name] = self.stations.pop(name)
                self.missions = [
                    {'pickup': new_name if m['pickup'] == name else m['pickup'],
                     'delivery': new_name if m['delivery'] == name else m['delivery']}
                    for m in self.missions]
            self.refresh_stations()
            self.select_station(new_name)
        elif ok:
            QMessageBox.warning(self, 'Invalid name', 'Name is empty or already exists.')

    def delete_selected(self):
        if self.mission_active:
            QMessageBox.information(self, 'Delivery running', 'Finish or cancel the delivery before editing the map or stations.')
            return
        name = self.selected_id()
        if not name:
            return
        reply = QMessageBox.question(self, 'Delete station', f'Delete {name}?')
        if reply == QMessageBox.StandardButton.Yes:
            del self.stations[name]
            self.missions = [m for m in self.missions
                             if name not in (m['pickup'], m['delivery'])]
            self.refresh_stations()

    def save_stations(self):
        if not self.map_view.map_loaded:
            return
        STATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if STATIONS_FILE.exists():
            try:
                old = yaml.safe_load(STATIONS_FILE.read_text()) or {}
                old_id = old.get('map_id')
                if old_id and old_id != self.map_view.map_id:
                    backup = STATIONS_FILE.with_name(f'stations_{old_id}.yaml')
                    if not backup.exists():
                        backup.write_text(STATIONS_FILE.read_text())
            except Exception:
                pass
        content = {'map_id': self.map_view.map_id,
                   'map_yaml': str(self.map_view.map_path),
                   'stations': self.stations}
        STATIONS_FILE.write_text(yaml.safe_dump(content, sort_keys=False))
        self.statusBar().showMessage(f'Saved {len(self.stations)} stations to {STATIONS_FILE}')

    def add_delivery(self):
        pickup = self.pickup_combo.currentText()
        delivery = self.delivery_combo.currentText()
        if not pickup or not delivery:
            QMessageBox.information(self, 'Missing station',
                                    'Place at least one pickup and delivery station first.')
            return
        self.missions.append({'pickup': pickup, 'delivery': delivery})
        self.refresh_queue()

    def refresh_queue(self):
        self.queue_list.clear()
        for i, mission in enumerate(self.missions, 1):
            prefix = '▶ ' if self.mission_active and i == 1 else ''
            self.queue_list.addItem(
                f'{prefix}#{i}  {mission["pickup"]} → {mission["delivery"]} → Dock')
        self.update_navigation_buttons()

    def remove_delivery(self):
        if self.mission_active:
            QMessageBox.information(self, 'Delivery running', 'Cancel or finish the active delivery before changing the queue.')
            return
        row = self.queue_list.currentRow()
        if row >= 0:
            self.missions.pop(row)
            self.refresh_queue()

    def update_robot_position(self, x, y, yaw):
        self.position_label.setText(
            f'X: {x:.2f} m\nY: {y:.2f} m\nYaw: {math.degrees(yaw):.1f}°')
        self.map_view.update_robot(x, y, yaw)

    def update_connection(self, connected):
        # This indicates a received AMCL pose, not full robot health.
        self.connection_label.setText('● AMCL POSE RECEIVED' if connected
                                      else '● WAITING FOR AMCL POSE')
        self.connection_label.setStyleSheet(
            'color:#22c55e' if connected else 'color:#fb7185')
        self.robot_status.setText('POSE AVAILABLE' if connected else 'NO POSE')

    def nav_availability_changed(self, available):
        self.nav_available = available
        self.update_navigation_buttons()
        if not available and not self.nav_busy:
            self.nav_status_label.setText('Nav2 action server unavailable')
        elif available and not self.nav_busy:
            self.nav_status_label.setText('Nav2 ready — select a station to navigate')

    def update_navigation_buttons(self):
        # Only the mission manager or single-goal tester may control Nav2 at once.
        if not hasattr(self, 'start_button'):
            return
        ready = self.nav_available and not self.nav_busy and not self.mission_active
        self.start_button.setEnabled(ready and bool(self.missions))
        self.navigate_station_button.setEnabled(ready)
        self.cancel_nav_button.setEnabled(self.nav_busy and not self.mission_active)
        self.cancel_mission_button.setEnabled(self.mission_active and not self.mission_cancelling)

    def start_delivery(self):
        if self.mission_active or self.nav_busy or not self.nav_available:
            return
        if not self.missions:
            QMessageBox.information(self, 'Queue empty', 'Add a delivery to the queue first.')
            return

        mission = self.missions[0]
        pickup = mission['pickup']
        delivery = mission['delivery']
        # Require a properly typed dock. Never guess its position or use a shelf position.
        docks = [name for name, station in self.stations.items()
                 if station.get('type') == 'dock']
        if len(docks) != 1:
            QMessageBox.warning(self, 'Dock required',
                'Create exactly one station of type Dock before starting a delivery.\n'
                'Place its goal in free space and test it individually.')
            return
        dock = docks[0]
        for station_name, expected_type in ((pickup, 'pickup'), (delivery, 'delivery'), (dock, 'dock')):
            station = self.stations.get(station_name)
            if not station or station.get('type') != expected_type:
                QMessageBox.warning(self, 'Invalid station',
                    f'{station_name} is missing or is no longer a {expected_type} station.')
                return

        steps = []
        for station_name in (pickup, delivery, dock):
            station = self.stations[station_name]
            steps.append((station_name, float(station['x']), float(station['y']),
                          float(station['yaw'])))
        response = QMessageBox.question(
            self, 'Start delivery mission',
            f'Execute {pickup} → {delivery} → {dock}?\n\n'
            'Each destination must be in free navigable space.\n'
            'This only simulates pickup/drop-off; no package is handled yet.')
        if response != QMessageBox.StandardButton.Yes:
            return
        self.mission_steps = steps  # Frozen for this mission.
        self.mission_step_index = 0
        self.mission_active = True
        self.mission_cancelling = False
        self.refresh_queue()
        self.send_mission_step()

    def send_mission_step(self):
        station_name, x, y, yaw = self.mission_steps[self.mission_step_index]
        phase = ('Pickup', 'Delivery', 'Return to dock')[self.mission_step_index]
        self.nav_busy = True
        self.mission_label.setText(
            f'{phase} ({self.mission_step_index + 1}/3): {station_name}')
        self.update_navigation_buttons()
        self.ros.navigate_to(station_name, x, y, yaw)

    def cancel_delivery(self):
        if not self.mission_active or self.mission_cancelling:
            return
        self.mission_cancelling = True
        self.mission_label.setText('Cancelling delivery...')
        self.update_navigation_buttons()
        self.ros.cancel_navigation()

    def finish_delivery(self, completed, message):
        self.mission_active = False
        self.mission_cancelling = False
        self.mission_steps = []
        if completed and self.missions:
            self.missions.pop(0)
        self.mission_label.setText(
            ('✓ Delivery completed. Robot returned to dock.' if completed
             else f'⚠ Delivery stopped: {message}. Job remains queued.'))
        self.refresh_queue()

    def navigate_selected_station(self):
        if self.mission_active or self.nav_busy or not self.nav_available:
            return
        name = self.selected_id()
        if not name:
            QMessageBox.information(self, 'Select station',
                                    'Select a station from the Station Editor list first.')
            return
        station = self.stations.get(name)
        if station is None:
            QMessageBox.warning(self, 'Missing station', 'Station not found.')
            return
        if not self.map_view.map_loaded:
            return
        reply = QMessageBox.question(
            self, 'Send Nav2 goal',
            f'Navigate to {name}?\n\n'
            f'X: {station["x"]:.2f} m\nY: {station["y"]:.2f} m\n'
            f'Yaw: {math.degrees(station["yaw"]):.1f}°\n\n'
            'Check that this pose is in free space beside the station.')
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.nav_busy = True
        self.update_navigation_buttons()
        self.ros.navigate_to(name, station['x'], station['y'], station['yaw'])

    def cancel_navigation(self):
        self.ros.cancel_navigation()

    def nav_status_changed(self, message):
        self.nav_status_label.setText(message)
        self.statusBar().showMessage(message)

    def nav_finished(self, success, message):
        self.nav_busy = False
        self.nav_status_label.setText(('✓ ' if success else '⚠ ') + message)
        if self.mission_active:
            if self.mission_cancelling:
                self.finish_delivery(False, 'Cancelled by operator')
            elif not success:
                self.finish_delivery(False, message)
            elif self.mission_step_index < len(self.mission_steps) - 1:
                self.mission_step_index += 1
                self.send_mission_step()
            else:
                self.finish_delivery(True, message)
        self.update_navigation_buttons()

    def show_ros_error(self, error):
        print(f'ROS 2 ERROR: {error}', flush=True)
        self.statusBar().showMessage(f'ROS 2 ERROR: {error}')

    def closeEvent(self, event):
        self.ros.stop()
        super().closeEvent(event)

    def apply_style(self):
        self.setStyleSheet('''
            QMainWindow, QWidget { background:#0b1220; color:#e5e7eb;
                font-family:"DejaVu Sans"; font-size:12px; }
            QFrame#card { background:#151e2e; border:1px solid #273449;
                border-radius:10px; }
            QLabel#mainTitle { font-size:24px; font-weight:bold; }
            QLabel#sectionTitle { font-size:15px; font-weight:bold;
                color:#f8fafc; margin-top:5px; }
            QComboBox, QLineEdit, QListWidget { background:#0f172a;
                border:1px solid #334155; border-radius:5px; padding:6px; }
            QComboBox QAbstractItemView { background:#1e293b; color:white; }
            QPushButton { background:#334155; border:0; border-radius:6px;
                padding:9px; font-weight:bold; }
            QPushButton:hover { background:#475569; }
            QPushButton:disabled { color:#64748b; background:#263142; }
            QStatusBar { color:#94a3b8; }
        ''')


def main():
    app = QApplication(sys.argv)
    window = WarehouseControl()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
