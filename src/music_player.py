### MUSIC PLAYER ###
'''
Music Player - A simple music player interface for Karu the Fox desktop pet.
'''
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                               QPushButton, QHBoxLayout,
                               QListWidget, QSlider, QStyle,
                               QListWidgetItem, QFrame, QDialog, QTextBrowser)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QUrl, QSize, QPoint
from PySide6.QtMultimedia import QMediaPlayer
from .constants import IMAGE_DIR, MUSIC_DIR


MUSIC_PLAYER_ICON_DIR = IMAGE_DIR / "music-player"

class MusicPlayerWindow(QWidget):
    def __init__(self, media_player, tray_actions, parent=None):
        super().__init__(parent)
        self.media_player = media_player
        self.tray_actions = tray_actions
        self.playlist = []
        self.current_index = -1
        self.playback_mode = 'normal'
        self.is_muted = False
        self.volume = 1.0
        self.drag_pos = QPoint()
        self._control_icon_size = QSize(22, 22)
        self._play_icon_size = QSize(32, 32)
        self._shuffle_queue = []

        ### Window Flags and Attributes ###
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

    ### UI Setup ###
    def _setup_ui(self):
        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("CentralFrame")
        self.main_layout = QVBoxLayout(self.central_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 15)
        self.main_layout.setSpacing(10)
        
        self.setCentralWidget(self.central_frame)

        self._setup_title_bar()

        ## Content Layout
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

        ## Time and Progress
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

        ## Control Buttons
        # Previous Button
        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton()
        self.prev_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.prev_button.setFixedSize(48, 48); self.prev_button.setIconSize(QSize(28, 28)); self.prev_button.setObjectName("ControlButton")
        self.prev_button.setToolTip("Previous")

        # Play/Pause Button (text-based, smaller)
        self.play_pause_button = QPushButton()
        self.play_pause_button.setFixedSize(56, 56)
        self.play_pause_button.setObjectName("PlayPauseButton")
        self.play_pause_button.setToolTip("Play / Pause")
        self.play_pause_button.setIcon(self._get_icon("play.png"))
        self.play_pause_button.setIconSize(self._play_icon_size)

        # Next Button
        self.next_button = QPushButton()
        self.next_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.next_button.setFixedSize(48, 48); self.next_button.setIconSize(QSize(28, 28)); self.next_button.setObjectName("ControlButton")
        self.next_button.setToolTip("Next")

        # Control Buttons Layout
        controls_layout.addStretch()
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addStretch()

        # Loop mode options
        options_layout = QHBoxLayout()
        self.loop_button = QPushButton()
        self.loop_button.setIcon(self._get_icon("normal.png"))
        self.loop_button.setIconSize(self._control_icon_size)
        self.loop_button.setFixedSize(40, 40); self.loop_button.setObjectName("ControlButton")
        self.loop_button.setToolTip("Change Playback Mode")

        # Volume Button
        volume_layout = QHBoxLayout()
        self.volume_button = QPushButton()
        self.volume_button.setFixedSize(40, 40); self.volume_button.setObjectName("ControlButton")
        self.volume_button.setToolTip("Mute / Unmute")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setRange(0, 100); self.volume_slider.setValue(100)
        self.volume_slider.setToolTip("Volume")
        volume_layout.addWidget(self.volume_button)
        volume_layout.addWidget(self.volume_slider)

        # Help Button
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

        # Playlist Widget
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

    def setCentralWidget(self, widget):
        layout = QVBoxLayout(self)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)

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
    
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            * {
                font-family: "Press Start 2P", "VT323", "Courier New", monospace;
                letter-spacing: 0.5px;
                font-size: 13px;
            }

            #CentralFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #CFE8FF, stop:1 #B6DCFF);
                color: #1F2A44;
                border: 4px solid #1F3D66;
                border-radius: 10px;
            }

            #TitleBar {
                background: #9CD5FF;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                border-bottom: 3px solid #1F3D66;
            }

            #WindowButton {
                background: #7CB8F0;
                border: 3px solid #1F3D66;
                border-radius: 4px;
                color: #0F1B2D;
                font-size: 12px;
                padding: 2px 6px;
            }
            #WindowButton:hover { background: #B6E2FF; }
            #WindowButton:pressed {
                background: #6AA7DD;
                margin-top: 2px;
            }

            #TitleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #0F1B2D;
            }
            #ArtistLabel {
                font-size: 14px;
                color: #294368;
            }
            #Thumbnail {
                border: 3px solid #1F3D66;
                border-radius: 6px;
                background: #E5F3FF;
            }

            #ControlButton, #PlaylistButton, #PlayPauseButton {
                background: #9CD5FF;
                border: 3px solid #1F3D66;
                border-radius: 6px;
                color: #0F1B2D;
                padding: 6px 10px;
                font-size: 13px;
                line-height: 1.2em;
            }
            #ControlButton:hover, #PlaylistButton:hover, #PlayPauseButton:hover { background: #BFE6FF; }
            #ControlButton:pressed, #PlaylistButton:pressed, #PlayPauseButton:pressed {
                background: #7CB8F0;
                margin-top: 2px;
            }
            #PlayPauseButton {
                min-width: 56px;
                min-height: 56px;
                border-radius: 8px;
                background: #8BC7FF;
                font-size: 13px;
            }
            #PlaylistButton { font-size: 13px; padding: 8px 14px; font-weight: bold; }

            QSlider::groove:horizontal {
                border: 3px solid #1F3D66;
                height: 10px;
                background: #E5F3FF;
                margin: 4px 0;
            }
            QSlider::sub-page:horizontal {
                background: #7CB8F0;
                border: 3px solid #1F3D66;
            }
            QSlider::add-page:horizontal {
                background: #CFE8FF;
                border: 3px solid #1F3D66;
            }
            QSlider::handle:horizontal {
                background: #1F3D66;
                border: 2px solid #0F1B2D;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 2px;
            }

            QListWidget {
                background: #E5F3FF;
                border: 3px solid #1F3D66;
                font-size: 12px;
                padding: 6px;
                color: #0F1B2D;
            }
            QListWidget::item { padding: 10px 6px; }
            QListWidget::item:selected {
                background: #7CB8F0;
                color: #0F1B2D;
                border: 2px solid #1F3D66;
            }

            #TimeLabel {
                color: #000000;
                font-weight: bold;
                font-size: 13px;
            }

            QToolTip {
                background: #0F1B2D;
                color: #CFE8FF;
                border: 2px solid #7CB8F0;
                padding: 6px;
                font-size: 10px;
            }
        """)

    def _get_icon(self, filename):
        path = MUSIC_PLAYER_ICON_DIR / filename
        return QIcon(str(path)) if path.exists() else QIcon()

    def _get_misc_icon(self, filename):
        path = IMAGE_DIR / "others" / filename
        return QIcon(str(path)) if path.exists() else QIcon()

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
        
    def _format_time(self, ms):
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

    def _format_song_label(self, title, artist, max_len=42):
        text = f"{title} - {artist}"
        if len(text) > max_len:
            return text[: max_len - 3] + "..."
        return text

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    ### Music Directory Scanner ###
    def scan_music_directory(self):
        music_dir = MUSIC_DIR
        songs = []
        self.song_list_widget.clear()
        self._shuffle_queue = []
        if not music_dir.exists():
            return

        for song_dir in music_dir.iterdir():
            if song_dir.is_dir():
                mp3_files = list(song_dir.glob('*.mp3'))
                if not mp3_files:
                    continue
                
                mp3_path = mp3_files[0]
                title, artist = "Unknown Title", "Unknown Artist"
                filename_stem = mp3_path.stem
                if '_' in filename_stem:
                    parts = filename_stem.split('_', 1)
                    title = parts[0].replace('-', ' ')
                    if len(parts) > 1:
                        artist = parts[1].replace('-', ' ')
                else:
                    title = filename_stem.replace('-', ' ')

                thumbnail_path = None
                for ext in ['.jpg', '.png', '.jfif']:
                    if (song_dir / f"thumbnail{ext}").exists():
                        thumbnail_path = song_dir / f"thumbnail{ext}"
                        break

                songs.append({"title": title, "artist": artist, "path": mp3_path, "thumbnail": thumbnail_path})

        songs.sort(key=lambda s: (s['title'].casefold(), s['artist'].casefold()))
        self.playlist = songs

        for song_data in self.playlist:
            display = self._format_song_label(song_data['title'], song_data['artist'])
            item = QListWidgetItem(display)
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
            self.media_player.setSource(QUrl.fromLocalFile(str(song['path'].absolute())))
            self.media_player.play()
            self.title_label.setText(song['title'])
            self.artist_label.setText(song['artist'])
            if song['thumbnail']:
                self.thumbnail_label.setPixmap(QPixmap(str(song['thumbnail'])).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.thumbnail_label.setPixmap(QPixmap())
                self.thumbnail_label.setText("No Art")
            self.song_list_widget.setCurrentRow(index)

    def next_song(self):
        if not self.playlist: return
        if self.playback_mode == 'shuffle':
            self._ensure_shuffle_queue()
            if not self._shuffle_queue:
                return
            next_index = self._shuffle_queue.pop(0)
            self.play_song(next_index)
        elif self.playback_mode == 'normal':
            if self.current_index == -1:
                self.play_song(0)
            elif self.current_index < len(self.playlist) - 1:
                self.play_song(self.current_index + 1)
        else:
            self.play_song((self.current_index + 1) % len(self.playlist))

    def prev_song(self):
        if not self.playlist: return
        if self.playback_mode == 'normal':
            if self.current_index > 0:
                self.play_song(self.current_index - 1)
        else:
            self.play_song((self.current_index - 1 + len(self.playlist)) % len(self.playlist))

    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            if self.current_index == -1 and self.playlist:
                if self.playback_mode == 'shuffle':
                    self._ensure_shuffle_queue()
                    if self._shuffle_queue:
                        self.play_song(self._shuffle_queue.pop(0))
                    else:
                        self.play_song(0)
                else:
                    self.play_song(0) 
            else:
                self.media_player.play()

        # Keep shuffle queue aligned if user manually starts playback
        if self.playback_mode == 'shuffle' and self.current_index != -1:
            self._remove_from_shuffle_queue(self.current_index)

    def change_playback_mode(self):
        if self.playback_mode == 'normal':
            self.apply_playback_mode('loop_all')
        elif self.playback_mode == 'loop_all':
            self.apply_playback_mode('shuffle')
        else:
            self.apply_playback_mode('normal')

    def apply_playback_mode(self, mode):
        """Apply playback mode and sync button/tray iconography."""
        if mode == 'shuffle':
            self.playback_mode = 'shuffle'
            self.loop_button.setIcon(self._get_icon("shuffle.png"))
            self.loop_button.setToolTip("Shuffle")
            self.tray_actions['loop'].setText("Mode: Shuffle")
            self._build_shuffle_queue()
        elif mode == 'loop_all':
            self.playback_mode = 'loop_all'
            self.loop_button.setIcon(self._get_icon("loop.png"))
            self.loop_button.setToolTip("Loop All")
            self.tray_actions['loop'].setText("Mode: Loop All")
            self._shuffle_queue = []
        else:
            self.playback_mode = 'normal'
            self.loop_button.setIcon(self._get_icon("normal.png"))
            self.loop_button.setToolTip("Normal Order")
            self.tray_actions['loop'].setText("Mode: Normal")
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
        self.tray_actions['mute'].setText("Unmute" if self.is_muted else "Mute")

    def update_volume_icon(self):
        icon = self._get_icon("volume-muted.png" if (self.is_muted or self.volume == 0) else "volume.png")
        self.volume_button.setIcon(icon)
        self.volume_button.setIconSize(self._control_icon_size)

    def play_from_list(self, item):
        self.apply_playback_mode('normal')
        self.play_song(self.song_list_widget.row(item))

    def update_play_pause_icon(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setIcon(self._get_icon("pause.png"))
            self.play_pause_button.setIconSize(self._play_icon_size)
            self.play_pause_button.setToolTip("Pause")
            self.tray_actions['play_pause'].setText("Pause")
        else:
            self.play_pause_button.setIcon(self._get_icon("play.png"))
            self.play_pause_button.setIconSize(self._play_icon_size)
            self.play_pause_button.setToolTip("Play")
            self.tray_actions['play_pause'].setText("Play")

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
                self.apply_playback_mode('normal')
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
            if key in (Qt.Key.Key_Up, Qt.Key.Key_K, Qt.Key.Key_Down, Qt.Key.Key_J,
                       Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_P, Qt.Key.Key_M):
                self.keyPressEvent(event)
                return True
        return super().eventFilter(obj, event)

    def update_slider_position(self, position):
        self.progress_slider.setValue(position)
        self.current_time_label.setText(self._format_time(position))

    def set_slider_range(self, duration):
        self.progress_slider.setRange(0, duration)
        self.total_time_label.setText(self._format_time(duration))

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.playback_mode == 'normal' and self.current_index >= len(self.playlist) - 1:
                return
            self.next_song()

    # Shuffle helpers
    def _build_shuffle_queue(self):
        from random import shuffle
        self._shuffle_queue = list(range(len(self.playlist)))
        if self.current_index in self._shuffle_queue:
            self._shuffle_queue.remove(self.current_index)
        shuffle(self._shuffle_queue)

    def _ensure_shuffle_queue(self):
        if not self._shuffle_queue:
            self._build_shuffle_queue()

    def _remove_from_shuffle_queue(self, index):
        if index in self._shuffle_queue:
            self._shuffle_queue.remove(index)

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
        instructions.setHtml(
            """
            <h2>Keybind</h2>
            <ul>
              <li><b>Up / K</b>: Move selection up</li>
              <li><b>Down / J</b>: Move selection down</li>
              <li><b>Enter</b>: Play selected (switches to Normal)</li>
              <li><b>P</b>: Play/Pause</li>
              <li><b>M</b>: Change Mode</li>
            </ul>
            <h2>Modes</h2>
            <ul>
                <li><b>Normal</b>: Alphabetical order, repeats the playlist upon end</li>
                <li><b>Loop</b>: Repeats the current song</li>
                <li><b>Shuffle</b>: Plays all tracks in random order</li>
            </ul>
            """
        )

        ok_button = QPushButton("OK", dialog)
        ok_button.clicked.connect(dialog.accept)
        ok_button.setFixedHeight(30)

        layout.addWidget(instructions)
        layout.addWidget(ok_button)
        dialog.exec()

    def closeEvent(self, event):
        self.hide()
        event.ignore()