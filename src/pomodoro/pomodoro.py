from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import QPoint, QTimer, Qt, QUrl
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QComboBox, QDialog,
							   QFrame, QHBoxLayout,
							   QLabel, QPushButton,
							   QSlider, QVBoxLayout,
							   QWidget, QSystemTrayIcon)

from ..constants import IMAGE_DIR, LOGO_ICON, MUSIC_DIR
from .assets import load_fox_icons, load_tomato_sprites
from .themes import DEFAULT_THEME, THEMES as THEME_MAP, build_stylesheet, resolve_theme
from .utils import can_reset_timer, clamp_duration_minutes, seconds_to_clock


class PomodoroWindow(QWidget):
	THEMES = THEME_MAP

	tomato_sprites: dict[str, QPixmap | list[QPixmap]]
	fox_icons: dict[str, QPixmap | list[QPixmap]]

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
		self.fox_icons = load_fox_icons(IMAGE_DIR)
		self.fox_icon_frame_top = True

		self.timer = QTimer(self)
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self._tick)

		self.tomato_sprites = load_tomato_sprites(IMAGE_DIR)
		self.tray_icon = tray_icon if tray_icon is not None else self._init_tray_icon()

		self.alert_player = QMediaPlayer(self)
		self.alert_audio = QAudioOutput(self)
		self.alert_player.setAudioOutput(self.alert_audio)
		try:
			self.alert_player.setLoops(QMediaPlayer.Loops.Infinite)
		except Exception:
			pass

		self._setup_ui()
		self.theme_box.blockSignals(True)
		self.theme_box.setCurrentText(DEFAULT_THEME)
		self.theme_box.blockSignals(False)
		self._apply_theme(DEFAULT_THEME)
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
		self.min_button.setToolTip("Minimize pomodoro")
		self.min_button.clicked.connect(self.showMinimized)
		controls.addWidget(self.min_button)

		self.close_button = QPushButton("x")
		self.close_button.setObjectName("TitleButton")
		self.close_button.setFixedSize(28, 24)
		self.close_button.setToolTip("Close pomodoro")
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
		can_reset = can_reset_timer(
			self.is_running, self.remaining_seconds, self.total_seconds
		)
		self.reset_button.setEnabled(can_reset)

	def set_preferences(self, *, duration_minutes: int, theme: str):
		minutes = clamp_duration_minutes(duration_minutes)
		theme_name = theme if theme in self.THEMES else DEFAULT_THEME

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
		return {
			"duration": clamp_duration_minutes(self.duration_slider.value()),
			"theme": self.theme_box.currentText() or DEFAULT_THEME,
		}

	def _set_fox_icon(self, key):
		sprite = self.fox_icons.get(key)
		pix: QPixmap | None
		if isinstance(sprite, QPixmap):
			pix = sprite
		elif isinstance(sprite, list) and sprite:
			pix = sprite[0]
		else:
			pix = None

		if pix is not None and self.fox_icon_label:
			self.fox_icon_label.setPixmap(
				pix.scaled(
					40,
					40,
					Qt.AspectRatioMode.KeepAspectRatio,
					Qt.TransformationMode.FastTransformation,
				)
			)
		elif self.fox_icon_label:
			self.fox_icon_label.clear()

	def _init_tray_icon(self):
		icon = QIcon(str(LOGO_ICON)) if LOGO_ICON and LOGO_ICON.exists() else QIcon()
		tray = QSystemTrayIcon(icon, self)
		tray.setVisible(True)
		return tray

	def _set_tomato_sprite(self, key, frame_index=0):
		sprite = self.tomato_sprites.get(key)
		pix: QPixmap | None
		if isinstance(sprite, list):
			if not sprite:
				return
			pix = sprite[frame_index % len(sprite)]
		elif isinstance(sprite, QPixmap):
			pix = sprite
		else:
			pix = None

		if pix is not None:
			self.tomato_label.setPixmap(
				pix.scaled(
					250,
					250,
					Qt.AspectRatioMode.KeepAspectRatio,
					Qt.TransformationMode.FastTransformation,
				)
			)
		else:
			self.tomato_label.clear()

	def _apply_theme(self, name):
		colors = resolve_theme(name)
		self.setStyleSheet(build_stylesheet(colors))

	def _duration_changed(self, value):
		if self.is_running:
			return
		minutes = clamp_duration_minutes(value)
		self.total_seconds = minutes * 60
		self.remaining_seconds = self.total_seconds
		self.duration_label.setText(f"Duration: {minutes} min")
		self._update_time_display()
		self._update_reset_state()

	def toggle_timer(self):
		if self.is_running:
			self._pause_timer()
			return
		if self.remaining_seconds <= 0 or self.remaining_seconds > 60 * 60:
			self.remaining_seconds = clamp_duration_minutes(self.total_seconds // 60) * 60
			self.total_seconds = self.remaining_seconds
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
		self.time_label.setText(seconds_to_clock(self.remaining_seconds))

	def _animate_running_assets(self):
		if "ticking" not in self.tomato_sprites:
			self._set_tomato_sprite("neutral")
			return
		self.tomato_frame_index ^= 1
		self._set_tomato_sprite("ticking", self.tomato_frame_index)
		if self.fox_icons:
			self.fox_icon_frame_top = not self.fox_icon_frame_top
			self._set_fox_icon(
				"half_top" if self.fox_icon_frame_top else "half_bottom"
			)

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
			self.tray_icon.showMessage(
				"Pomodoro", "Time is up!", self.tray_icon.icon(), 5000
			)

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
		if (
			event.buttons() == Qt.MouseButton.LeftButton
			and not self.drag_pos.isNull()
		):
			self.move(event.globalPosition().toPoint() - self.drag_pos)

	def mouseReleaseEvent(self, event):
		self.drag_pos = QPoint()

	def closeEvent(self, event):
		self.hide()
		event.ignore()
