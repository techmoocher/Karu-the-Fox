### POMODORO TIMER ###
'''
Pomodoro Timer - A Pomodoro timer widget for Karu the Fox desktop pet.
'''

from PySide6.QtWidgets import (QWidget, QLabel,
                               QVBoxLayout, QHBoxLayout,
                               QPushButton, QSlider,
                               QComboBox, QFrame,
                               QSystemTrayIcon, QDialog)
from PySide6.QtCore import Qt, QTimer, QPoint, QUrl
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from .constants import IMAGE_DIR, LOGO_ICON, MUSIC_DIR


class PomodoroWindow(QWidget):
    THEMES = {
        "Pastel Blue": {
            "bg": "#D8E9FF",
            "panel": "#BED9FF",
            "accent": "#5B8DEF",
            "text": "#112542",
        },
        # "Soft Blue": {
        #     "bg": "#E9F4FF",
        #     "panel": "#D6EAFF",
        #     "accent": "#6EA8FF",
        #     "text": "#0D233F",
        # },
        "Pastel Pink": {
            "bg": "#FFE4EF",
            "panel": "#FFD1E4",
            "accent": "#FF7AA2",
            "text": "#3F0D21",
        },
        # "Soft Pink": {
        #     "bg": "#FFE8F2",
        #     "panel": "#FFD8EA",
        #     "accent": "#FF9AC3",
        #     "text": "#3C1226",
        # },
        "Pastel Orange": {
            "bg": "#FFF0DC",
            "panel": "#FFE2C4",
            "accent": "#FF9B42",
            "text": "#3D1F0F",
        },
        # "Soft Orange": {
        #     "bg": "#FFF3E3",
        #     "panel": "#FFE6CC",
        #     "accent": "#FFAE60",
        #     "text": "#3A2313",
        # },
        "Pastel Red": {
            "bg": "#FFE1E1",
            "panel": "#FFCACA",
            "accent": "#FF6B6B",
            "text": "#3D0F0F",
        },
        # "Soft Red": {
        #     "bg": "#FFE8E8",
        #     "panel": "#FFD3D3",
        #     "accent": "#FF8A8A",
        #     "text": "#3A1010",
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

        self.total_seconds = 25 * 60
        self.remaining_seconds = self.total_seconds
        self.is_running = False
        self.alert_dialog = None
        self.fox_icons = self._load_fox_icons()
        self.fox_icon_frame_top = True

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        self.tomato_sprites = self._load_tomato_sprites()
        self.tray_icon = tray_icon if tray_icon is not None else self._init_tray_icon()

        self.alert_player = QMediaPlayer(self)
        self.alert_audio = QAudioOutput(self)
        self.alert_player.setAudioOutput(self.alert_audio)
        try:
            self.alert_player.setLoops(QMediaPlayer.Loops.Infinite)
        except Exception:
            pass

        self._setup_ui()
        self._apply_theme("Pastel Orange")
        self._update_time_display()
        self._set_tomato_sprite("neutral")
        self._set_fox_icon("empty")
        self._update_reset_state()

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
        title_row.addSpacing(6)

        self.fox_icon_label = QLabel()
        self.fox_icon_label.setFixedSize(40, 40)
        self.fox_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row.addWidget(self.fox_icon_label)
        title_row.addStretch()

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

    def _update_reset_state(self):
        """Enable reset only after a run has started and the timer is not running."""
        can_reset = (not self.is_running) and (
            self.remaining_seconds < self.total_seconds or self.remaining_seconds == 0
        )
        self.reset_button.setEnabled(can_reset)

    def set_preferences(self, *, duration_minutes: int, theme: str):
        """Apply persisted pomodoro preferences (duration/theme)."""
        minutes = max(10, min(60, int(duration_minutes or 25)))
        theme_name = theme if theme in self.THEMES else "Pastel Orange"

        self.duration_slider.blockSignals(True)
        self.duration_slider.setValue(minutes)
        self.duration_slider.blockSignals(False)

        self.total_seconds = minutes * 60
        if not self.is_running:
            self.remaining_seconds = self.total_seconds
            self._update_time_display()

        self.theme_box.blockSignals(True)
        self.theme_box.setCurrentText(theme_name)
        self.theme_box.blockSignals(False)
        self._apply_theme(theme_name)
        self._update_reset_state()

    def get_preferences(self):
        """Return current pomodoro settings for persistence."""
        return {
            "duration": max(10, min(60, int(self.duration_slider.value()))),
            "theme": self.theme_box.currentText() or "Pastel Orange",
        }


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
        # Fallback: legacy single ticking sprite
        legacy_tick = IMAGE_DIR / "pomodoro" / "tomato-ticking.png"
        if legacy_tick.exists() and "ticking" not in sprites:
            sprites["ticking"] = [QPixmap(str(legacy_tick)), QPixmap(str(legacy_tick))]
        return sprites

    def _load_fox_icons(self):
        icon_map = {
            "empty": "fox-hourglass-empty.png",
            "half_top": "fox-hourglass-half-top.png",
            "half_bottom": "fox-hourglass-half-bottom.png",
        }
        icons = {}
        for key, filename in icon_map.items():
            path = IMAGE_DIR / "pomodoro" / filename
            if path.exists():
                icons[key] = QPixmap(str(path))
        return icons

    def _set_fox_icon(self, key):
        pix = self.fox_icons.get(key)
        if pix and self.fox_icon_label:
            self.fox_icon_label.setPixmap(
                pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            )
        elif self.fox_icon_label:
            self.fox_icon_label.clear()

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
                pix.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            )
        else:
            self.tomato_label.clear()

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

    def _duration_changed(self, value):
        if self.is_running:
            return
        self.total_seconds = value * 60
        self.remaining_seconds = self.total_seconds
        self.duration_label.setText(f"Duration: {value} min")
        self._update_time_display()
        self._update_reset_state()

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
        self._set_tomato_sprite("ticking", self.tomato_frame_index)
        self.fox_icon_frame_top = True
        self._set_fox_icon("half_top")
        self._update_reset_state()
        self._stop_alert_sound()

    def _pause_timer(self):
        self.is_running = False
        self.timer.stop()
        self.start_button.setText("Resume")
        self._set_tomato_sprite("neutral")
        self._set_fox_icon("empty")
        self._update_reset_state()
        self._stop_alert_sound()

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
        self._set_fox_icon("empty")
        self._update_reset_state()
        self._stop_alert_sound()

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
        if "ticking" not in self.tomato_sprites:
            self._set_tomato_sprite("neutral")
            return
        self.tomato_frame_index ^= 1
        self._set_tomato_sprite("ticking", self.tomato_frame_index)
        # Toggle fox hourglass between top/bottom halves
        if self.fox_icons:
            self.fox_icon_frame_top = not self.fox_icon_frame_top
            self._set_fox_icon("half_top" if self.fox_icon_frame_top else "half_bottom")

    def _handle_timer_completion(self):
        self.timer.stop()
        self.is_running = False
        self.start_button.setText("Start")
        self.duration_slider.setEnabled(True)
        self.time_label.setText("DONE!")
        self._set_tomato_sprite("vibrate")
        self._set_fox_icon("empty")
        self._update_reset_state()
        self._notify_time_up()

    def _notify_time_up(self):
        self._start_alert_sound()
        self._show_alert_dialog()
        if self.tray_icon and self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage("Pomodoro", "Time is up!", self.tray_icon.icon(), 5000)

    def _start_alert_sound(self):
        alert_path = MUSIC_DIR / "pomodoro-alert.mp3"
        if not alert_path.exists():
            return
        try:
            self.alert_player.setSource(QUrl.fromLocalFile(str(alert_path)))
            self.alert_audio.setVolume(1.0)
            self.alert_player.play()
        except Exception:
            pass

    def _stop_alert_sound(self):
        try:
            self.alert_player.stop()
        except Exception:
            pass

    def _show_alert_dialog(self):
        if self.alert_dialog:
            self.alert_dialog.raise_()
            self.alert_dialog.activateWindow()
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Time's up!")
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        msg = QLabel("Pomodoro complete. Take a short break or start another round.")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)
        dialog.finished.connect(self._clear_alert_dialog)
        self.alert_dialog = dialog
        dialog.show()

    def _clear_alert_dialog(self):
        if self.alert_dialog:
            self.alert_dialog.deleteLater()
        self.alert_dialog = None
        self._stop_alert_sound()

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