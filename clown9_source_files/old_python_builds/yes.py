import sys
import os
import a2s
import webbrowser
import unicodedata
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QFrame
)
from PyQt5.QtGui import QFont, QIcon, QColor, QBrush

SERVER_ADDRESS = ('79.127.217.197', 22912)

class ServerQueryThread(QThread):
    result = pyqtSignal(object, object, object)

    def run(self):
        try:
            info = a2s.info(SERVER_ADDRESS)
            players = a2s.players(SERVER_ADDRESS)
            self.result.emit('success', info, players)
        except Exception as e:
            self.result.emit('error', str(e), None)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("clown9.exe")
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon("sourceclown.ico"))

        self.connecting_dots = 0
        self.player_data = []
        self.player_data_time = None
        self.sound_played_minute = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Top Info
        self.top_frame = QHBoxLayout()
        self.layout.addLayout(self.top_frame)

        # Server Info
        self.server_info_frame = QVBoxLayout()
        self.top_frame.addLayout(self.server_info_frame, 1)

        self.map_label = QLabel("Loading...")
        self.map_label.setFont(QFont("Arial", 14))
        self.server_info_frame.addWidget(self.map_label)

        self.player_count_label = QLabel("Players: -/-")
        self.player_count_label.setFont(QFont("Arial", 12))
        self.server_info_frame.addWidget(self.player_count_label)

        # Map Cycle Info
        self.map_cycle_frame = QVBoxLayout()
        self.top_frame.addLayout(self.map_cycle_frame, 1)

        self.current_map_label = QLabel("Current map: Loading...")
        self.current_map_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.current_map_label.setAlignment(Qt.AlignCenter)
        self.map_cycle_frame.addWidget(self.current_map_label)

        self.adjacent_label = QLabel("")
        self.adjacent_label.setFont(QFont("Arial", 10))
        self.adjacent_label.setAlignment(Qt.AlignCenter)
        self.map_cycle_frame.addWidget(self.adjacent_label)

        self.countdown_label = QLabel("")
        self.countdown_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.map_cycle_frame.addWidget(self.countdown_label)

        self.time_label = QLabel("")
        self.time_label.setFont(QFont("Arial", 10))
        self.time_label.setAlignment(Qt.AlignCenter)
        self.map_cycle_frame.addWidget(self.time_label)

        # Player Table
        self.players_frame = QVBoxLayout()
        self.layout.addLayout(self.players_frame, 3)

        self.players_table = QTableWidget(0, 3)
        self.players_table.setHorizontalHeaderLabels(['Player Name', 'Score', 'Time Played'])
        self.players_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.players_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.players_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.players_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.players_table.setSelectionMode(QTableWidget.NoSelection)
        self.players_frame.addWidget(self.players_table)

        self.no_players_label = QLabel("NO PLAYERS ONLINE")
        self.no_players_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.no_players_label.setStyleSheet("color: red")
        self.no_players_label.setAlignment(Qt.AlignCenter)
        self.no_players_label.hide()
        self.players_frame.addWidget(self.no_players_label)

        # Bottom Controls
        self.bottom_frame = QHBoxLayout()
        self.layout.addLayout(self.bottom_frame)

        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.clicked.connect(self.refresh_data)
        self.bottom_frame.addWidget(self.refresh_button)

        self.auto_refresh_check = QCheckBox("Auto-refresh every 5 seconds")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.stateChanged.connect(self.toggle_auto_refresh)
        self.bottom_frame.addWidget(self.auto_refresh_check)

        self.bottom_frame.addStretch()

        # Status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.layout.addWidget(self.status_bar)

        # Bottom left link
        self.link_label = QLabel('<a href="https://gaq9.com" style="color:blue;">gaq9.com</a>')
        self.link_label.setFont(QFont("Arial", 10, QFont.Underline))
        self.link_label.setOpenExternalLinks(True)
        self.layout.addWidget(self.link_label, alignment=Qt.AlignLeft | Qt.AlignBottom)

        # Bottom right info
        self.kulcs_label = QLabel('<b>Key means Kulcs in Hungarian</b>')
        self.kulcs_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.layout.addWidget(self.kulcs_label, alignment=Qt.AlignRight | Qt.AlignBottom)

        # Timers
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_data)
        self.toggle_auto_refresh()

        self.update_map_timer = QTimer()
        self.update_map_timer.timeout.connect(self.update_map_display)
        self.update_map_timer.start(50)

        self.update_players_timer = QTimer()
        self.update_players_timer.timeout.connect(self.update_player_durations)
        self.update_players_timer.start(1000)

        self.connecting_anim_timer = QTimer()
        self.connecting_anim_timer.timeout.connect(self.animate_connecting)
        self.connecting_anim_timer.start(500)

        self.refresh_data()

    def toggle_auto_refresh(self):
        if self.auto_refresh_check.isChecked():
            self.auto_refresh_timer.start(5000)
        else:
            self.auto_refresh_timer.stop()

    def get_map_based_on_utc_hour(self, hour=None):
        if hour is None:
            hour = datetime.utcnow().hour
        map_hours = {
            0: "askask", 1: "ask", 2: "ask", 3: "askask", 4: "ask", 5: "dustbowl",
            6: "askask", 7: "ask", 8: "ask", 9: "askask", 10: "ask", 11: "dustbowl",
            12: "askask", 13: "ask", 14: "ask", 15: "askask", 16: "ask", 17: "dustbowl",
            18: "askask", 19: "ask", 20: "dustbowl", 21: "askask", 22: "ask", 23: "dustbowl"
        }
        return map_hours[hour]

    def get_adjacent_maps(self):
        current_hour = datetime.utcnow().hour
        current_minute = datetime.utcnow().minute
        current_second = datetime.utcnow().second

        prev_hour = current_hour - 1
        if prev_hour < 0:
            prev_hour = 23
        prev_map = self.get_map_based_on_utc_hour(prev_hour)

        next_hour = current_hour + 1
        if next_hour > 23:
            next_hour = 0
        next_map = self.get_map_based_on_utc_hour(next_hour)

        seconds_remaining = (60 - current_second) % 60
        minutes_remaining = (59 - current_minute) % 60

        return prev_map, next_map, minutes_remaining, seconds_remaining

    def update_map_display(self):
        utc_now = datetime.utcnow()
        local_now = datetime.now()

        utc_time = utc_now.strftime("%H:%M:%S")
        local_time = local_now.strftime("%H:%M:%S")

        current_map = self.get_map_based_on_utc_hour()
        prev_map, next_map, mins_left, secs_left = self.get_adjacent_maps()

        self.time_label.setText(f"UTC: {utc_time} | Local: {local_time}")
        self.current_map_label.setText(f"Current Map Cycle: {current_map}")
        self.adjacent_label.setText(f"Previous Map Cycle: {prev_map} | Next Map Cycle: {next_map}")
        self.countdown_label.setText(f"Next cycle in: {mins_left:02d}m {secs_left:02d}s")

        # Only play at exactly xx:59:00
        if utc_now.minute == 59 and utc_now.second == 0:
            if self.sound_played_minute != utc_now.hour:
                sound_path = os.path.join(os.getcwd(), "AIM_Sound.mp3")
                if os.path.exists(sound_path):
                    try:
                        import playsound
                        playsound.playsound(sound_path, False)
                    except Exception:
                        pass
                self.sound_played_minute = utc_now.hour
        elif utc_now.minute != 59:
            self.sound_played_minute = None

    def refresh_data(self):
        self.status_bar.setText("Querying server...")
        self.refresh_button.setEnabled(False)
        self.query_thread = ServerQueryThread()
        self.query_thread.result.connect(self.process_query_result)
        self.query_thread.start()

    def animate_connecting(self):
        self.connecting_dots = (self.connecting_dots + 1) % 4
        self.update_player_durations()

    def clean_player_name(self, name):
        if not name or name.lower() == "unknown":
            dots = '.' * self.connecting_dots
            return f"connecting{dots}"
        try:
            name = unicodedata.normalize('NFKC', name)
            name = ''.join(c for c in name if c.isprintable())
            return name
        except Exception:
            return name

    def process_query_result(self, status, info, players):
        if status == 'success':
            map_name = info.map_name if info.map_name else "unknown"
            self.map_label.setText(f"Map: {map_name}")
            self.player_count_label.setText(f"Players: {info.player_count}/{info.max_players}")

            self.players_table.setRowCount(0)
            self.player_data = []
            for player in players:
                self.player_data.append({
                    "name": player.name,
                    "score": player.score,
                    "duration": float(player.duration)
                })
            self.player_data_time = datetime.now()

            if len(self.player_data) == 0:
                self.no_players_label.show()
            else:
                self.no_players_label.hide()

            for pdata in self.player_data:
                name = self.clean_player_name(pdata["name"])
                minutes = int(pdata["duration"]) // 60
                seconds = int(pdata["duration"]) % 60
                duration_str = f"{minutes}:{seconds:02d}"
                row = self.players_table.rowCount()
                self.players_table.insertRow(row)
                self.players_table.setItem(row, 0, QTableWidgetItem(name))
                self.players_table.setItem(row, 1, QTableWidgetItem(str(pdata["score"])))
                self.players_table.setItem(row, 2, QTableWidgetItem(duration_str))

            self.status_bar.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')} | {len(self.player_data)} players online")
        else:
            self.status_bar.setText("Error querying server, retrying...")
            QTimer.singleShot(1000, self.refresh_data)
        self.refresh_button.setEnabled(True)

    def update_player_durations(self):
        if self.player_data and self.player_data_time:
            elapsed = (datetime.now() - self.player_data_time).total_seconds()
            for idx, pdata in enumerate(self.player_data):
                name = self.clean_player_name(pdata["name"])
                updated_duration = pdata["duration"] + elapsed
                minutes = int(updated_duration) // 60
                seconds = int(updated_duration) % 60
                duration_str = f"{minutes}:{seconds:02d}"
                self.players_table.setItem(idx, 0, QTableWidgetItem(name))
                self.players_table.setItem(idx, 1, QTableWidgetItem(str(pdata["score"])))
                self.players_table.setItem(idx, 2, QTableWidgetItem(duration_str))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())