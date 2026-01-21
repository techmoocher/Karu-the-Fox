import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QPushButton, QSlider,
    QComboBox, QFrame, QSystemTrayIcon,
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QIcon

try:
    from .constants import IMAGE_DIR, LOGO_ICON, CONFIG_FILE
except ImportError:  # Allow running standalone
    SRC_DIR = Path(__file__).resolve().parent
    if str(SRC_DIR.parent) not in sys.path:
        sys.path.append(str(SRC_DIR.parent))
    from constants import IMAGE_DIR, LOGO_ICON, CONFIG_FILE


class PomodoroWindow(QWidget):
    THEMES = {
        "Pastel Blue": {
            "bg": "#D8E9FF",
            "panel": "#BED9FF",
            "accent": "#5B8DEF",
            "text": "#112542",
        },
        # "Soft Blue": {
        #     "bg": "#e9f4ff",
        #     "panel": "#d6eaff",
        #     "accent": "#6ea8ff",
        #     "text": "#0d233f",
        # },
        "Pastel Pink": {
            "bg": "#FFE4EF",
            "panel": "#FFD1E4",
            "accent": "#FF7AA2",
            "text": "#3F0D21",
        },
        # "Soft Pink": {
        #     "bg": "#ffe8f2",
        #     "panel": "#ffd8ea",
        #     "accent": "#ff9ac3",
        #     "text": "#3c1226",
        # },
        "Pastel Orange": {
            "bg": "#FFF0DC",
            "panel": "#FFE2C4",
            "accent": "#FF9B42",
            "text": "#3D1F0F",
        },
        # "Soft Orange": {
        #     "bg": "#fff3e3",
        #     "panel": "#ffe6cc",
        #     "accent": "#ffae60",
        #     "text": "#3a2313",
        # },
        "Pastel Red": {
            "bg": "#FFE1E1",
            "panel": "#FFCACA",
            "accent": "#FF6B6B",
            "text": "#3D0F0F",
        },
        # "Soft Red": {
        #     "bg": "#ffe8e8",
        #     "panel": "#ffd3d3",
        #     "accent": "#ff8a8a",
        #     "text": "#3a1010",
        # },
    }

    def __init__(self, parent=None, tray_icon=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Karu Pomodoro")
        self.setMinimumSize(320, 260)
        self.drag_pos = QPoint()

        self.tomato_frame_index = 0
        self.hourglass_top_frame = True

        self.total_seconds = 25 * 60
        self.remaining_seconds = self.total_seconds
        self.is_running = False

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        self.tomato_sprites = self._load_tomato_sprites()
        self.hourglass_icons = self._load_hourglass_icons()
        self.tray_icon = tray_icon if tray_icon is not None else self._init_tray_icon()

        self._setup_ui()
        self.config = self._load_config()
        self._apply_persisted_preferences()
        self._update_time_display()
        self._set_tomato_sprite("neutral")
        self._set_hourglass_icon("empty")

    def _setup_ui(self):
        self.frame = QFrame(self)
        self.frame.setObjectName("Frame")
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        self.title_label = QLabel("POMODORO")
        self.title_label.setObjectName("Title")
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        title_row.addWidget(self.icon_label)

        self.theme_box = QComboBox()
        self.theme_box.addItems(list(self.THEMES.keys()))
        self.theme_box.currentTextChanged.connect(self._apply_theme)
        title_row.addWidget(self.theme_box)

        controls = QHBoxLayout()
        controls.setSpacing(6)
        self.min_button = QPushButton("-")
        self.min_button.setObjectName("TitleButton")
        self.min_button.setFixedSize(28, 24)
        self.min_button.clicked.connect(self.showMinimized)
        controls.addWidget(self.min_button)

        self.close_button = QPushButton("x")
        self.close_button.setObjectName("TitleButton")
        self.close_button.setFixedSize(28, 24)
        self.close_button.clicked.connect(self.close)
        controls.addWidget(self.close_button)
        title_row.addLayout(controls)
        layout.addLayout(title_row)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setObjectName("TimeLabel")
        layout.addWidget(self.time_label)

        self.tomato_label = QLabel()
        self.tomato_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.tomato_label)

        slider_row = QVBoxLayout()
        self.duration_label = QLabel("Duration: 25 min")
        self.duration_label.setObjectName("Caption")
        self.duration_slider = QSlider(Qt.Orientation.Horizontal)
        self.duration_slider.setRange(10, 60)
        self.duration_slider.setValue(25)
        self.duration_slider.setTickInterval(5)
        self.duration_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.duration_slider.valueChanged.connect(self._duration_changed)
        slider_row.addWidget(self.duration_label)
        slider_row.addWidget(self.duration_slider)
        layout.addLayout(slider_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.toggle_timer)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("ResetButton")
        self.reset_button.clicked.connect(self.reset_timer)
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.reset_button)
        layout.addLayout(button_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.frame)

    def _load_config(self):
        defaults = {"pomodoro_duration": 25, "pomodoro_theme": "Pastel Orange"}
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            defaults.update({
                "pomodoro_duration": data.get("pomodoro_duration", defaults["pomodoro_duration"]),
                "pomodoro_theme": data.get("pomodoro_theme", defaults["pomodoro_theme"]),
            })
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            pass
        return defaults

    def _persist_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            data = {}

        data.update({
            "pomodoro_duration": self.duration_slider.value(),
            "pomodoro_theme": self.theme_box.currentText(),
        })

        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"Error saving pomodoro config: {e}")

    def _apply_persisted_preferences(self):
        theme = self.config.get("pomodoro_theme", "Pastel Orange")
        if theme not in self.THEMES:
            theme = "Pastel Orange"
        self.theme_box.blockSignals(True)
        self.theme_box.setCurrentText(theme)
        self.theme_box.blockSignals(False)
        self._apply_theme(self.theme_box.currentText())

        duration = int(self.config.get("pomodoro_duration", 25))
        duration = max(10, min(60, duration))
        self.duration_slider.blockSignals(True)
        self.duration_slider.setValue(duration)
        self.duration_slider.blockSignals(False)
        self.total_seconds = duration * 60
        self.remaining_seconds = self.total_seconds
        self.duration_label.setText(f"Duration: {duration} min")

    def _load_tomato_sprites(self):
        sprite_map = {
            "neutral": "tomato-neutral.png",
            "ticking": ["tomato-ticking-1.png", "tomato-ticking-2.png"],
            "vibrate": "tomato-vibrate.png",
        }
        sprites = {}
        for key, filename in sprite_map.items():
            if isinstance(filename, list):
                frames = []
                for fname in filename:
                    path = IMAGE_DIR / "pomodoro" / fname
                    if path.exists():
                        frames.append(QPixmap(str(path)))
                if frames:
                    sprites[key] = frames
            else:
                path = IMAGE_DIR / "pomodoro" / filename
                if path.exists():
                    sprites[key] = QPixmap(str(path))
        return sprites

    def _load_hourglass_icons(self):
        icon_map = {
            "half_top": "hourglass-half-top.svg",
            "half_bottom": "hourglass-half-bottom.svg",
            "empty": "hourglass-empty.svg",
        }
        icons = {}
        for key, filename in icon_map.items():
            path = IMAGE_DIR / "pomodoro" / filename
            if path.exists():
                icons[key] = QPixmap(str(path))
        return icons

    def _init_tray_icon(self):
        if LOGO_ICON and LOGO_ICON.exists():
            icon = QIcon(str(LOGO_ICON))
        else:
            icon = QIcon()
        tray = QSystemTrayIcon(icon, self)
        tray.setVisible(True)
        return tray

    def _set_tomato_sprite(self, key, frame_index=0):
        pix = self.tomato_sprites.get(key)
        if isinstance(pix, list):
            if not pix:
                return
            pix = pix[frame_index % len(pix)]
        if pix:
            self.tomato_label.setPixmap(
                pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            self.tomato_label.clear()

    def _set_hourglass_icon(self, key):
        pix = self.hourglass_icons.get(key)
        if pix and self.icon_label:
            scaled = pix.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(scaled)
            self.setWindowIcon(QIcon(scaled))
        elif self.icon_label:
            self.icon_label.clear()

    def _apply_theme(self, name):
        colors = self.THEMES.get(name, self.THEMES["Pastel Orange"])
        self.setStyleSheet(
            f"""
            #Frame {{
                background-color: {colors['bg']};
                border: 3px solid {colors['accent']};
                border-radius: 10px;
                color: {colors['text']};
                font-family: 'Press Start 2P', 'VT323', 'Courier New', monospace;
            }}
            #Title {{
                color: {colors['accent']};
                font-size: 16px;
                letter-spacing: 2px;
                font-weight: bold;
            }}
            #Caption {{
                color: {colors['text']};
                font-size: 12px;
            }}
            #TimeLabel {{
                background-color: {colors['panel']};
                border: 3px solid {colors['accent']};
                border-radius: 8px;
                padding: 16px 12px;
                font-size: 28px;
                letter-spacing: 1px;
                color: #000000;
            }}
            QSlider::groove:horizontal {{
                border: 2px solid {colors['accent']};
                height: 12px;
                background: {colors['panel']};
                margin: 4px 6px;
            }}
            QSlider::handle:horizontal {{
                background: {colors['accent']};
                border: 2px solid {colors['text']};
                width: 18px;
                height: 18px;
                margin: -7px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {colors['accent']};
            }}
            QPushButton {{
                background-color: {colors['accent']};
                color: {colors['bg']};
                border: 3px solid {colors['text']};
                border-radius: 8px;
                padding: 10px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['text']};
                color: {colors['bg']};
            }}
            QPushButton:pressed {{
                background-color: {colors['panel']};
                color: {colors['text']};
            }}
            QPushButton#ResetButton {{
                background-color: {colors['panel']};
                color: {colors['text']};
            }}
            QPushButton#TitleButton {{
                background-color: transparent;
                color: {colors['text']};
                border: 2px solid {colors['accent']};
                border-radius: 6px;
                font-weight: bold;
                padding: 2px 6px;
                min-width: 0px;
            }}
            QPushButton#TitleButton:hover {{
                background-color: {colors['accent']};
                color: {colors['bg']};
            }}
            QPushButton#TitleButton:pressed {{
                background-color: {colors['text']};
                color: {colors['bg']};
            }}
            QComboBox {{
                background-color: {colors['panel']};
                color: {colors['text']};
                border: 2px solid {colors['accent']};
                border-radius: 6px;
                padding: 6px 8px;
            }}
            QComboBox QAbstractItemView {{
                selection-background-color: {colors['accent']};
                selection-color: {colors['bg']};
            }}
            """
        )
        if hasattr(self, "theme_box"):
            self._persist_config()

    def _duration_changed(self, value):
        if self.is_running:
            return
        self.total_seconds = value * 60
        self.remaining_seconds = self.total_seconds
        self.duration_label.setText(f"Duration: {value} min")
        self._update_time_display()
        self._persist_config()

    def toggle_timer(self):
        if self.is_running:
            self._pause_timer()
            return
        # Initialize remaining time when starting fresh
        if self.remaining_seconds <= 0 or self.remaining_seconds > 60 * 60:
            self.remaining_seconds = max(10 * 60, min(60 * 60, self.total_seconds))
        self.is_running = True
        self.timer.start()
        self.start_button.setText("Pause")
        self.duration_slider.setEnabled(False)
        self.tomato_frame_index = 0
        self.hourglass_top_frame = True
        self._set_tomato_sprite("ticking", self.tomato_frame_index)
        self._set_hourglass_icon("half_top")

    def _pause_timer(self):
        self.is_running = False
        self.timer.stop()
        self.start_button.setText("Resume")
        self._set_tomato_sprite("neutral")
        self._set_hourglass_icon("empty")

    def reset_timer(self):
        self.timer.stop()
        self.is_running = False
        minutes = self.duration_slider.value()
        self.total_seconds = minutes * 60
        self.remaining_seconds = self.total_seconds
        self.start_button.setText("Start")
        self.duration_slider.setEnabled(True)
        self._update_time_display()
        self._set_tomato_sprite("neutral")
        self._set_hourglass_icon("empty")

    def _tick(self):
        if self.remaining_seconds <= 0:
            self._handle_timer_completion()
            return
        self.remaining_seconds = max(0, self.remaining_seconds - 1)
        self._update_time_display()
        if self.remaining_seconds <= 0:
            self._handle_timer_completion()
            return
        self._animate_running_assets()

    def _update_time_display(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _animate_running_assets(self):
        self.tomato_frame_index ^= 1
        self.hourglass_top_frame = not self.hourglass_top_frame
        self._set_tomato_sprite("ticking", self.tomato_frame_index)
        self._set_hourglass_icon("half_top" if self.hourglass_top_frame else "half_bottom")

    def _handle_timer_completion(self):
        self.timer.stop()
        self.is_running = False
        self.start_button.setText("Start")
        self.duration_slider.setEnabled(True)
        self.time_label.setText("DONE!")
        self._set_tomato_sprite("vibrate")
        self._set_hourglass_icon("empty")
        self._notify_time_up()

    def _notify_time_up(self):
        if self.tray_icon and self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage("Pomodoro", "Time is up!", self.tray_icon.icon(), 5000)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.drag_pos = QPoint()

    def closeEvent(self, event):
        self.hide()
        event.ignore()