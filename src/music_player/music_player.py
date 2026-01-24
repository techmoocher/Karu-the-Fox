from PySide6.QtWidgets import (QDialog, QFrame,
							   QHBoxLayout, QLabel,
							   QListWidget, QListWidgetItem,
							   QPushButton, QSlider,
							   QStyle, QTextBrowser,
							   QVBoxLayout, QWidget)
from PySide6.QtCore import QPoint, Qt, QUrl, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtMultimedia import QMediaPlayer

from .constants import IMAGE_DIR, MUSIC_DIR, MUSIC_PLAYER_ICON_DIR
from .styles import HELP_HTML, MUSIC_PLAYER_STYLESHEET
from .utils import format_song_label, format_time
from .playlist_control import (
	build_shuffle_queue,
	ensure_shuffle_queue,
	remove_from_shuffle_queue,
	scan_music_directory,
)


class MusicPlayerWindow(QWidget):
	def __init__(self, media_player, tray_actions, parent=None):
		super().__init__(parent)
		self.media_player = media_player
		self.tray_actions = tray_actions
		self.playlist = []
		self.current_index = -1
		self.playback_mode = "normal"
		self.is_muted = False
		self.volume = 1.0
		self.drag_pos = QPoint()
		self._control_icon_size = QSize(22, 22)
		self._play_icon_size = QSize(32, 32)
		self._shuffle_queue = []

		self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
		self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
		self.setWindowTitle("Music with Karu")
		self.setWindowIcon(QIcon(str(IMAGE_DIR / "logo.png")))
		self.setMinimumSize(420, 220)
		self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

		self._setup_ui()
		self._apply_stylesheet()
		self._connect_signals()
		self.scan_music_directory()
		self.update_volume_icon()

	def closeEvent(self, event):
		self.hide()
		event.ignore()

	def _setup_ui(self):
		"""Construct the music player window layout."""
		self.central_frame = QFrame(self)
		self.central_frame.setObjectName("CentralFrame")
		self.main_layout = QVBoxLayout(self.central_frame)
		self.main_layout.setContentsMargins(0, 0, 0, 15)
		self.main_layout.setSpacing(10)

		self.setCentralWidget(self.central_frame)
		self._setup_title_bar()

		content_layout = QVBoxLayout()
		content_layout.setContentsMargins(20, 10, 20, 10)
		content_layout.setSpacing(15)

		info_layout = QHBoxLayout()
		info_layout.setSpacing(20)
		self.thumbnail_label = QLabel()
		self.thumbnail_label.setFixedSize(100, 100)
		self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.thumbnail_label.setObjectName("Thumbnail")

		title_artist_layout = QVBoxLayout()
		title_artist_layout.setContentsMargins(0, 5, 0, 5)
		self.title_label = QLabel("Welcome to Your Pet Music Player")
		self.title_label.setObjectName("TitleLabel")
		self.artist_label = QLabel("Select a song to start")
		self.artist_label.setObjectName("ArtistLabel")
		title_artist_layout.addWidget(self.title_label)
		title_artist_layout.addWidget(self.artist_label)
		title_artist_layout.addStretch()

		info_layout.addWidget(self.thumbnail_label)
		info_layout.addLayout(title_artist_layout)

		progress_layout = QHBoxLayout()
		self.current_time_label = QLabel("0:00")
		self.current_time_label.setObjectName("TimeLabel")
		self.progress_slider = QSlider(Qt.Orientation.Horizontal)
		self.progress_slider.setToolTip("Seek")
		self.total_time_label = QLabel("0:00")
		self.total_time_label.setObjectName("TimeLabel")
		progress_layout.addWidget(self.current_time_label)
		progress_layout.addWidget(self.progress_slider)
		progress_layout.addWidget(self.total_time_label)

		controls_layout = QHBoxLayout()
		self.prev_button = QPushButton()
		self.prev_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
		self.prev_button.setFixedSize(48, 48)
		self.prev_button.setIconSize(QSize(28, 28))
		self.prev_button.setObjectName("ControlButton")
		self.prev_button.setToolTip("Previous")

		self.play_pause_button = QPushButton()
		self.play_pause_button.setFixedSize(56, 56)
		self.play_pause_button.setObjectName("PlayPauseButton")
		self.play_pause_button.setToolTip("Play / Pause")
		self.play_pause_button.setIcon(self._get_icon("play.png"))
		self.play_pause_button.setIconSize(self._play_icon_size)

		self.next_button = QPushButton()
		self.next_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
		self.next_button.setFixedSize(48, 48)
		self.next_button.setIconSize(QSize(28, 28))
		self.next_button.setObjectName("ControlButton")
		self.next_button.setToolTip("Next")

		controls_layout.addStretch()
		controls_layout.addWidget(self.prev_button)
		controls_layout.addWidget(self.play_pause_button)
		controls_layout.addWidget(self.next_button)
		controls_layout.addStretch()

		options_layout = QHBoxLayout()
		self.loop_button = QPushButton()
		self.loop_button.setIcon(self._get_icon("normal.png"))
		self.loop_button.setIconSize(self._control_icon_size)
		self.loop_button.setFixedSize(40, 40)
		self.loop_button.setObjectName("ControlButton")
		self.loop_button.setToolTip("Change Playback Mode")

		volume_layout = QHBoxLayout()
		self.volume_button = QPushButton()
		self.volume_button.setFixedSize(40, 40)
		self.volume_button.setObjectName("ControlButton")
		self.volume_button.setToolTip("Mute / Unmute")
		self.volume_slider = QSlider(Qt.Orientation.Horizontal)
		self.volume_slider.setFixedWidth(120)
		self.volume_slider.setRange(0, 100)
		self.volume_slider.setValue(100)
		self.volume_slider.setToolTip("Volume")
		volume_layout.addWidget(self.volume_button)
		volume_layout.addWidget(self.volume_slider)

		self.help_button = QPushButton()
		self.help_button.setFixedSize(36, 36)
		self.help_button.setIcon(self._get_misc_icon("help.png"))
		self.help_button.setIconSize(QSize(18, 18))
		self.help_button.setObjectName("ControlButton")
		self.help_button.setToolTip("Help / Shortcuts")

		options_layout.addWidget(self.loop_button)
		options_layout.addStretch()
		options_layout.addLayout(volume_layout)
		options_layout.addStretch()
		options_layout.addWidget(self.help_button)

		self.song_list_widget = QListWidget()
		self.song_list_widget.setVisible(True)
		self.song_list_widget.setMinimumHeight(140)
		self.song_list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

		content_layout.addLayout(info_layout)
		content_layout.addLayout(progress_layout)
		content_layout.addLayout(controls_layout)
		content_layout.addLayout(options_layout)

		self.main_layout.addLayout(content_layout)
		self.main_layout.addWidget(self.song_list_widget)

	def _setup_title_bar(self):
		title_bar = QFrame()
		title_bar.setObjectName("TitleBar")
		title_bar_layout = QHBoxLayout(title_bar)
		title_bar_layout.setContentsMargins(10, 0, 0, 0)
		title_bar_layout.setSpacing(10)

		title_label = QLabel("Dance with Karu")
		title_label.setStyleSheet("font-weight: bold; color: #000000;")

		self.minimize_button = QPushButton("—")
		self.close_button = QPushButton("✕")
		self.minimize_button.setFixedSize(30, 30)
		self.close_button.setFixedSize(30, 30)
		self.minimize_button.setObjectName("WindowButton")
		self.close_button.setObjectName("WindowButton")

		title_bar_layout.addWidget(title_label)
		title_bar_layout.addStretch()
		title_bar_layout.addWidget(self.minimize_button)
		title_bar_layout.addWidget(self.close_button)

		self.main_layout.addWidget(title_bar)

	def setCentralWidget(self, widget):
		layout = QVBoxLayout(self)
		layout.addWidget(widget)
		layout.setContentsMargins(0, 0, 0, 0)

	def _apply_stylesheet(self):
		self.setStyleSheet(MUSIC_PLAYER_STYLESHEET)

	def _connect_signals(self):
		self.minimize_button.clicked.connect(self.showMinimized)
		self.close_button.clicked.connect(self.hide)
		self.play_pause_button.clicked.connect(self.toggle_play_pause)
		self.next_button.clicked.connect(self.next_song)
		self.prev_button.clicked.connect(self.prev_song)
		self.loop_button.clicked.connect(self.change_playback_mode)
		self.song_list_widget.itemDoubleClicked.connect(self.play_from_list)
		self.media_player.playbackStateChanged.connect(self.update_play_pause_icon)
		self.media_player.positionChanged.connect(self.update_slider_position)
		self.media_player.durationChanged.connect(self.set_slider_range)
		self.media_player.mediaStatusChanged.connect(self.handle_media_status)
		self.progress_slider.sliderMoved.connect(self.media_player.setPosition)
		self.volume_slider.valueChanged.connect(self.set_volume)
		self.volume_button.clicked.connect(self.toggle_mute)
		self.help_button.clicked.connect(self.show_help)
		self.song_list_widget.installEventFilter(self)
		self.update_volume_icon()

	def _get_icon(self, filename):
		path = MUSIC_PLAYER_ICON_DIR / filename
		return QIcon(str(path)) if path.exists() else QIcon()

	def _get_misc_icon(self, filename):
		path = IMAGE_DIR / "others" / filename
		return QIcon(str(path)) if path.exists() else QIcon()

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.MouseButton.LeftButton:
			self.move(event.globalPosition().toPoint() - self.drag_pos)

	def scan_music_directory(self):
		self.song_list_widget.clear()
		self._shuffle_queue = []
		self.playlist = scan_music_directory(MUSIC_DIR)

		for song_data in self.playlist:
			item = QListWidgetItem(format_song_label(song_data["title"], song_data["artist"]))
			self.song_list_widget.addItem(item)

		if not self.playlist:
			self.title_label.setText("No music found")
			self.artist_label.setText("Check ./music folder structure")

	def set_initial_position(self, position):
		self.media_player.setPosition(position)
		try:
			self.media_player.durationChanged.disconnect()
		except RuntimeError:
			pass
		self.media_player.durationChanged.connect(self.set_slider_range)

	def play_song(self, index):
		if 0 <= index < len(self.playlist):
			self.current_index = index
			song = self.playlist[index]
			self.media_player.setSource(QUrl.fromLocalFile(str(song["path"].absolute())))
			self.media_player.play()
			self.title_label.setText(song["title"])
			self.artist_label.setText(song["artist"])
			if song["thumbnail"]:
				self.thumbnail_label.setPixmap(
					QPixmap(str(song["thumbnail"])).scaled(
						100,
						100,
						Qt.AspectRatioMode.KeepAspectRatio,
						Qt.TransformationMode.SmoothTransformation,
					)
				)
			else:
				self.thumbnail_label.setPixmap(QPixmap())
				self.thumbnail_label.setText("No Art")
			self.song_list_widget.setCurrentRow(index)

	def next_song(self):
		if not self.playlist:
			return

		if self.playback_mode == "shuffle":
			self._ensure_shuffle_queue()
			if not self._shuffle_queue:
				return
			next_index = self._shuffle_queue.pop(0)
			self.play_song(next_index)
		elif self.playback_mode == "normal":
			if self.current_index == -1:
				self.play_song(0)
			elif self.current_index < len(self.playlist) - 1:
				self.play_song(self.current_index + 1)
		else:
			self.play_song((self.current_index + 1) % len(self.playlist))

	def prev_song(self):
		if not self.playlist:
			return
		if self.playback_mode == "normal":
			if self.current_index > 0:
				self.play_song(self.current_index - 1)
		else:
			self.play_song((self.current_index - 1 + len(self.playlist)) % len(self.playlist))

	def toggle_play_pause(self):
		if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
			self.media_player.pause()
		else:
			if self.current_index == -1 and self.playlist:
				if self.playback_mode == "shuffle":
					self._ensure_shuffle_queue()
					if self._shuffle_queue:
						self.play_song(self._shuffle_queue.pop(0))
					else:
						self.play_song(0)
				else:
					self.play_song(0)
			else:
				self.media_player.play()

		if self.playback_mode == "shuffle" and self.current_index != -1:
			self._remove_from_shuffle_queue(self.current_index)

	def change_playback_mode(self):
		if self.playback_mode == "normal":
			self.apply_playback_mode("loop_all")
		elif self.playback_mode == "loop_all":
			self.apply_playback_mode("shuffle")
		else:
			self.apply_playback_mode("normal")

	def apply_playback_mode(self, mode):
		if mode == "shuffle":
			self.playback_mode = "shuffle"
			self.loop_button.setIcon(self._get_icon("shuffle.png"))
			self.loop_button.setToolTip("Shuffle")
			self.tray_actions["loop"].setText("Mode: Shuffle")
			self._build_shuffle_queue()
		elif mode == "loop_all":
			self.playback_mode = "loop_all"
			self.loop_button.setIcon(self._get_icon("loop.png"))
			self.loop_button.setToolTip("Loop All")
			self.tray_actions["loop"].setText("Mode: Loop All")
			self._shuffle_queue = []
		else:
			self.playback_mode = "normal"
			self.loop_button.setIcon(self._get_icon("normal.png"))
			self.loop_button.setToolTip("Normal Order")
			self.tray_actions["loop"].setText("Mode: Normal")
			self._shuffle_queue = []

	def set_volume(self, value):
		self.volume = value / 100.0
		self.media_player.audioOutput().setVolume(self.volume)
		if self.is_muted and value > 0:
			self.is_muted = False
		self.update_volume_icon()

	def toggle_mute(self):
		self.is_muted = not self.is_muted
		self.media_player.audioOutput().setMuted(self.is_muted)
		self.update_volume_icon()
		self.tray_actions["mute"].setText("Unmute" if self.is_muted else "Mute")

	def update_volume_icon(self):
		icon = self._get_icon("volume-muted.png" if (self.is_muted or self.volume == 0) else "volume.png")
		self.volume_button.setIcon(icon)
		self.volume_button.setIconSize(self._control_icon_size)

	def play_from_list(self, item):
		self.apply_playback_mode("normal")
		self.play_song(self.song_list_widget.row(item))

	def update_play_pause_icon(self, state):
		if state == QMediaPlayer.PlaybackState.PlayingState:
			self.play_pause_button.setIcon(self._get_icon("pause.png"))
			self.play_pause_button.setIconSize(self._play_icon_size)
			self.play_pause_button.setToolTip("Pause")
			self.tray_actions["play_pause"].setText("Pause")
		else:
			self.play_pause_button.setIcon(self._get_icon("play.png"))
			self.play_pause_button.setIconSize(self._play_icon_size)
			self.play_pause_button.setToolTip("Play")
			self.tray_actions["play_pause"].setText("Play")

	def keyPressEvent(self, event):
		key = event.key()
		if key in (Qt.Key.Key_Up, Qt.Key.Key_K):
			self._move_selection(-1)
			return
		if key in (Qt.Key.Key_Down, Qt.Key.Key_J):
			self._move_selection(1)
			return
		if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
			row = self.song_list_widget.currentRow()
			if 0 <= row < self.song_list_widget.count():
				self.apply_playback_mode("normal")
				self.play_song(row)
			return
		if key == Qt.Key.Key_P:
			self.toggle_play_pause()
			return
		if key == Qt.Key.Key_M:
			self.change_playback_mode()
			return
		super().keyPressEvent(event)

	def _move_selection(self, delta):
		count = self.song_list_widget.count()
		if count == 0:
			return
		current = self.song_list_widget.currentRow()
		if current == -1:
			new_row = 0 if delta > 0 else count - 1
		else:
			new_row = max(0, min(count - 1, current + delta))
		self.song_list_widget.setCurrentRow(new_row)
		self.song_list_widget.scrollToItem(self.song_list_widget.currentItem())

	def eventFilter(self, obj, event):
		if obj == self.song_list_widget and event.type() == event.Type.KeyPress:
			key = event.key()
			if key in (
				Qt.Key.Key_Up,
				Qt.Key.Key_K,
				Qt.Key.Key_Down,
				Qt.Key.Key_J,
				Qt.Key.Key_Return,
				Qt.Key.Key_Enter,
				Qt.Key.Key_P,
				Qt.Key.Key_M,
			):
				self.keyPressEvent(event)
				return True
		return super().eventFilter(obj, event)

	def update_slider_position(self, position):
		self.progress_slider.setValue(position)
		self.current_time_label.setText(format_time(position))

	def set_slider_range(self, duration):
		self.progress_slider.setRange(0, duration)
		self.total_time_label.setText(format_time(duration))

	def handle_media_status(self, status):
		if status == QMediaPlayer.MediaStatus.EndOfMedia:
			if self.playback_mode == "normal" and self.current_index >= len(self.playlist) - 1:
				return
			self.next_song()

	def _build_shuffle_queue(self):
		self._shuffle_queue = build_shuffle_queue(len(self.playlist), self.current_index)

	def _ensure_shuffle_queue(self):
		ensure_shuffle_queue(self._shuffle_queue, len(self.playlist), self.current_index)

	def _remove_from_shuffle_queue(self, index):
		remove_from_shuffle_queue(self._shuffle_queue, index)

	def show_help(self):
		dialog = QDialog(self)
		dialog.setWindowTitle("Music Player Help")
		dialog.setWindowModality(Qt.WindowModality.WindowModal)
		dialog.setFixedSize(360, 320)
		layout = QVBoxLayout(dialog)

		instructions = QTextBrowser(dialog)
		instructions.setReadOnly(True)
		instructions.setOpenExternalLinks(False)
		instructions.setStyleSheet("font-size: 12px;")
		instructions.setHtml(HELP_HTML)

		ok_button = QPushButton("OK", dialog)
		ok_button.clicked.connect(dialog.accept)
		ok_button.setFixedHeight(30)

		layout.addWidget(instructions)
		layout.addWidget(ok_button)
		dialog.exec()


__all__ = ["MusicPlayerWindow"]
