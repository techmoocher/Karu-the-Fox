### MUSIC PLAYER ###
'''
Music Player - A simple music player interface for Karu the Fox desktop pet.
'''
from random import randint
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                               QPushButton, QHBoxLayout,
                               QListWidget, QSlider,
                               QListWidgetItem, QFrame)
from PySide6.QtGui import QPixmap, QIcon, QFont, QFontDatabase
from PySide6.QtCore import Qt, QUrl, QPoint
from PySide6.QtMultimedia import QMediaPlayer
from .constants import IMAGE_DIR, MUSIC_DIR


class MusicPlayerWindow(QWidget):
    def __init__(self, media_player, tray_actions, parent=None):
        super().__init__(parent)
        self.media_player = media_player
        self.tray_actions = tray_actions
        self.playlist = []
        self.current_index = -1
        self.playback_mode = 'loop_all'
        self.is_muted = False
        self.volume = 1.0
        self.drag_pos = QPoint()

        self.icon_font_family = None
        self.glyph_available = self._load_icon_font()
        self.glyphs = {
            'prev': "󰒮",
            'next': "󰒭",
            'play': "",
            'pause': "",
            'loop': "",
            'shuffle': "",
            'vol_mute': "󰖁",
            'vol_low': "󰕿",
            'vol_mid': "󰖀",
            'vol_high': "󰕾",
        }

        ### Window Flags and Attributes ###
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Music with Karu")
        self.setWindowIcon(QIcon(str(IMAGE_DIR / "logo.png")))
        self.setMinimumSize(420, 220)

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
        self._set_button_icon(self.prev_button, 'prev', "Prev", 16)
        self.prev_button.setFixedSize(44, 44); self.prev_button.setObjectName("ControlButton")
        self.prev_button.setToolTip("Previous")

        # Play/Pause Button (glyph-based, smaller)
        self.play_pause_button = QPushButton()
        self._set_button_icon(self.play_pause_button, 'play', "Play", 17)
        self.play_pause_button.setFixedSize(56, 56)
        self.play_pause_button.setObjectName("PlayPauseButton")
        self.play_pause_button.setToolTip("Play")

        # Next Button
        self.next_button = QPushButton()
        self._set_button_icon(self.next_button, 'next', "Next", 16)
        self.next_button.setFixedSize(44, 44); self.next_button.setObjectName("ControlButton")
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
        self._set_button_icon(self.loop_button, 'loop', "Loop", 16)
        self.loop_button.setFixedSize(40, 40); self.loop_button.setObjectName("ControlButton")
        self.loop_button.setToolTip("Loop All")

        # Playlist Button
        self.songs_list_button = QPushButton("Playlist")
        self.songs_list_button.setObjectName("PlaylistButton")
        self.songs_list_button.setToolTip("Show / Hide Playlist")

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

        options_layout.addWidget(self.loop_button)
        options_layout.addStretch()
        options_layout.addLayout(volume_layout)
        options_layout.addStretch()
        options_layout.addWidget(self.songs_list_button)

        # Playlist Widget
        self.song_list_widget = QListWidget()
        self.song_list_widget.setVisible(False)

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

    def _load_icon_font(self):
        """Load Nerd Font symbols if present; return True if loaded."""
        try:
            from .constants import NERD_FONT_SYMBOLS
        except Exception:
            return False

        if not NERD_FONT_SYMBOLS.exists():
            return False

        font_id = QFontDatabase.addApplicationFont(str(NERD_FONT_SYMBOLS))
        if font_id == -1:
            return False

        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            return False

        self.icon_font_family = families[0]
        return True

    def _set_button_icon(self, button, glyph_key, fallback_text, font_size):
        """Apply glyph if available; otherwise fall back to readable text."""
        if self.glyph_available and self.icon_font_family and glyph_key in self.glyphs:
            button.setText(self.glyphs[glyph_key])
            button.setFont(QFont(self.icon_font_family, font_size))
        else:
            button.setText(fallback_text)

    def _connect_signals(self):
        self.minimize_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.hide)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.next_button.clicked.connect(self.next_song)
        self.prev_button.clicked.connect(self.prev_song)
        self.loop_button.clicked.connect(self.change_playback_mode)
        self.songs_list_button.clicked.connect(self.toggle_song_list)
        self.song_list_widget.itemDoubleClicked.connect(self.play_from_list)
        self.media_player.playbackStateChanged.connect(self.update_play_pause_icon)
        self.media_player.positionChanged.connect(self.update_slider_position)
        self.media_player.durationChanged.connect(self.set_slider_range)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)
        self.progress_slider.sliderMoved.connect(self.media_player.setPosition)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_button.clicked.connect(self.toggle_mute)
        self.update_volume_icon()
        
    def _format_time(self, ms):
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    ### Music Directory Scanner ###
    def scan_music_directory(self):
        music_dir = MUSIC_DIR
        self.playlist = []
        self.song_list_widget.clear()
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

                song_data = {"title": title, "artist": artist, "path": mp3_path, "thumbnail": thumbnail_path}
                self.playlist.append(song_data)
                item = QListWidgetItem(f"{song_data['title']} - {song_data['artist']}")
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
        if self.playback_mode == 'loop_one': self.play_song(self.current_index)
        elif self.playback_mode == 'shuffle': self.play_song(randint(0, len(self.playlist) - 1))
        else: self.play_song((self.current_index + 1) % len(self.playlist))

    def prev_song(self):
        if not self.playlist: return
        self.play_song((self.current_index - 1 + len(self.playlist)) % len(self.playlist))

    def toggle_play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            if self.current_index == -1 and self.playlist:
                self.play_song(randint(0, len(self.playlist) - 1)) 
            else:
                self.media_player.play()

    def change_playback_mode(self):
        if self.playback_mode == 'loop_all': 
            self.playback_mode = 'loop_one'
            self._set_button_icon(self.loop_button, 'loop', "Loop 1", 16)
            self.loop_button.setToolTip("Loop One")
            self.tray_actions['loop'].setText("Mode: Loop One")
        elif self.playback_mode == 'loop_one': 
            self.playback_mode = 'shuffle'
            self._set_button_icon(self.loop_button, 'shuffle', "Shuffle", 16)
            self.loop_button.setToolTip("Shuffle")
            self.tray_actions['loop'].setText("Mode: Shuffle")
        else: 
            self.playback_mode = 'loop_all'
            self._set_button_icon(self.loop_button, 'loop', "Loop", 16)
            self.loop_button.setToolTip("Loop All")
            self.tray_actions['loop'].setText("Mode: Loop All")

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
        if self.is_muted or self.volume == 0:
            self._set_button_icon(self.volume_button, 'vol_mute', "Mute", 14)
        elif self.volume < 0.34:
            self._set_button_icon(self.volume_button, 'vol_low', "Low", 14)
        elif self.volume < 0.67:
            self._set_button_icon(self.volume_button, 'vol_mid', "Mid", 14)
        else:
            self._set_button_icon(self.volume_button, 'vol_high', "High", 14)

    def toggle_song_list(self):
        self.song_list_widget.setVisible(not self.song_list_widget.isVisible())

    def play_from_list(self, item):
        self.play_song(self.song_list_widget.row(item))

    def update_play_pause_icon(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._set_button_icon(self.play_pause_button, 'pause', "Pause", 17)
            self.play_pause_button.setToolTip("Pause")
            self.tray_actions['play_pause'].setText("Pause")
        else:
            self._set_button_icon(self.play_pause_button, 'play', "Play", 17)
            self.play_pause_button.setToolTip("Play")
            self.tray_actions['play_pause'].setText("Play")

    def update_slider_position(self, position):
        self.progress_slider.setValue(position)
        self.current_time_label.setText(self._format_time(position))

    def set_slider_range(self, duration):
        self.progress_slider.setRange(0, duration)
        self.total_time_label.setText(self._format_time(duration))

    def handle_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_song()

    def closeEvent(self, event):
        self.hide()
        event.ignore()