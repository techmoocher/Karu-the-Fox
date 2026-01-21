from typing import TYPE_CHECKING, Optional, cast

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QComboBox,
    QFrame,
    QDialog,
)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, Signal
from PySide6.QtGui import QPixmap, QIcon
from .constants import IMAGE_DIR

if TYPE_CHECKING:
    from .desktop_pet import DesktopPet


class PomodoroWindow(QWidget):
    pomodoro_finished = Signal()

    THEMES = {
        "Pastel Blue": {
            "bg": "#d8e9ff",
            "panel": "#bed9ff",
            "accent": "#5b8def",
            "text": "#112542",
        },
        "Soft Blue": {
            "bg": "#e9f4ff",
            "panel": "#d6eaff",
            "accent": "#6ea8ff",
            "text": "#0d233f",
        },
        "Pastel Pink": {
            "bg": "#ffe4ef",
            "panel": "#ffd1e4",
            "accent": "#ff7aa2",
            "text": "#3f0d21",
        },
        "Soft Pink": {
            "bg": "#ffe8f2",
            "panel": "#ffd8ea",
            "accent": "#ff9ac3",
            "text": "#3c1226",
        },
        "Pastel Orange": {
            "bg": "#fff0dc",
            "panel": "#ffe2c4",
            "accent": "#ff9b42",
            "text": "#3d1f0f",
        },
        "Soft Orange": {
            "bg": "#fff3e3",
            "panel": "#ffe6cc",
            "accent": "#ffae60",
            "text": "#3a2313",
        },
        "Pastel Red": {
            "bg": "#ffe1e1",
            "panel": "#ffcaca",
            "accent": "#ff6b6b",
            "text": "#3d0f0f",
        },
        "Soft Red": {
            "bg": "#ffe8e8",
            "panel": "#ffd3d3",
            "accent": "#ff8a8a",
            "text": "#3a1010",
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Karu Pomodoro")
        self.setMinimumSize(320, 260)
        self.drag_pos = QPoint()

        self.total_seconds = 25 * 60
        self.remaining_seconds = self.total_seconds
        self.is_running = False
        self.awaiting_ack = False
        self.alert_dialog = None

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        self.tomato_sprites = self._load_tomato_sprites()
        self.fox_pixmap = self._load_fox_pixmap()

        self._setup_ui()
        self._apply_theme("Pastel Orange")
        self._update_time_display()
        self._set_tomato_sprite("neutral")
        self._update_reset_state()

    def _setup_ui(self):
        """Build the window UI layout and controls."""
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

        self.fox_label = QLabel()
        self.fox_label.setFixedSize(56, 56)
        self.fox_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_fox_pixmap()
        title_row.insertWidget(0, self.fox_label)

        controls_row = QHBoxLayout()
        controls_row.addStretch()
        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(28, 28)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.close_button = QPushButton("x")
        self.close_button.setFixedSize(28, 28)
        self.close_button.clicked.connect(self.hide)
        controls_row.addWidget(self.minimize_button)
        controls_row.addWidget(self.close_button)
        title_row.addLayout(controls_row)

        self.theme_box = QComboBox()
        self.theme_box.addItems(list(self.THEMES.keys()))
        self.theme_box.currentTextChanged.connect(self._apply_theme)
        title_row.addWidget(self.theme_box)
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

    def _update_reset_state(self):
        """Enable reset only when the timer is idle or paused."""
        self.reset_button.setEnabled(not self.is_running)

    def _load_tomato_sprites(self):
        """Load optional tomato sprites from the pomodoro image folder."""
        sprite_map = {
            "neutral": "tomato-neutral.png",
            "ticking": "tomato-ticking.png",
            "vibrate": "tomato-vibrate.png",
        }
        sprites = {}
        for key, filename in sprite_map.items():
            path = IMAGE_DIR / "pomodoro" / filename
            if path.exists():
                sprites[key] = QPixmap(str(path))
        return sprites

    def _load_fox_pixmap(self):
        """Load optional fox-with-hourglass header art."""
        path = IMAGE_DIR / "pomodoro" / "fox-hourglass.png"
        if path.exists():
            return QPixmap(str(path))
        return None

    def _set_tomato_sprite(self, key):
        pix = self.tomato_sprites.get(key)
        if pix:
            target_size = QSize(min(250, pix.width()), min(250, pix.height()))
            self.tomato_label.setPixmap(
                pix.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            )
        else:
            self.tomato_label.clear()

    def _set_fox_pixmap(self):
        if self.fox_pixmap:
            target_size = QSize(min(64, self.fox_pixmap.width()), min(64, self.fox_pixmap.height()))
            self.fox_label.setPixmap(
                self.fox_pixmap.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            )
        else:
            self.fox_label.clear()

    def _apply_theme(self, name):
        """Apply the selected palette to the widget stylesheet."""
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
                color: {colors['text']};
                font-weight: bold;
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
            QPushButton#ResetButton:disabled, QPushButton:disabled {{
                background-color: {colors['panel']};
                color: {colors['text']};
                border: 2px dashed {colors['text']};
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

    def _duration_changed(self, value):
        """Adjust duration (10–60 minutes) when not running."""
        if self.is_running:
            return
        self.total_seconds = value * 60
        self.remaining_seconds = self.total_seconds
        self.duration_label.setText(f"Duration: {value} min")
        self._update_time_display()

    def toggle_timer(self):
        """Start or pause the timer; initializes remaining time if needed."""
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
        self._set_tomato_sprite("ticking")
        self._update_reset_state()

    def _pause_timer(self):
        """Pause the countdown without resetting progress."""
        self.is_running = False
        self.timer.stop()
        self.start_button.setText("Resume")
        self._set_tomato_sprite("neutral")
        self._update_reset_state()

    def reset_timer(self):
        """Reset timer to the slider-selected duration and re-enable controls."""
        self.timer.stop()
        self.is_running = False
        minutes = self.duration_slider.value()
        self.total_seconds = minutes * 60
        self.remaining_seconds = self.total_seconds
        self.start_button.setText("Start")
        self.duration_slider.setEnabled(True)
        self._update_time_display()
        self._set_tomato_sprite("neutral")
        self._update_reset_state()

    def _tick(self):
        """Advance countdown; when finished, show alert and notify pet."""
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.is_running = False
            self.start_button.setText("Start")
            self.duration_slider.setEnabled(True)
            self.time_label.setText("DONE!")
            self._set_tomato_sprite("vibrate")
            self._update_reset_state()
            self._show_alert_dialog()
            self._nudge_pet_wag()
            self.pomodoro_finished.emit()
            return
        self.remaining_seconds = max(0, self.remaining_seconds - 1)
        self._update_time_display()

    def _update_time_display(self):
        """Render remaining time as MM:SS."""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

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

    def _show_alert_dialog(self):
        """Pop up a modal alert when the timer completes."""
        if self.alert_dialog:
            self.alert_dialog.raise_()
            self.alert_dialog.activateWindow()
            return
        self.alert_dialog = QDialog(self)
        self.alert_dialog.setWindowTitle("Time's up!")
        self.alert_dialog.setModal(True)
        layout = QVBoxLayout(self.alert_dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        msg = QLabel("Pomodoro complete. Take a break or start another round.")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._dismiss_alert)
        layout.addWidget(ok_btn)
        self.awaiting_ack = True
        self.alert_dialog.finished.connect(self._dismiss_alert)
        self.alert_dialog.show()

    def _dismiss_alert(self):
        """Close the alert dialog and clear state."""
        self.awaiting_ack = False
        if self.alert_dialog:
            self.alert_dialog.deleteLater()
            self.alert_dialog = None

    def _nudge_pet_wag(self):
        """Ask parent pet to wag if available; safe no-op otherwise."""
        parent = cast(Optional["DesktopPet"], self.parent())
        if parent and hasattr(parent, "initiate_wagging"):
            parent.initiate_wagging()
