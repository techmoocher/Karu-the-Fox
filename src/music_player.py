### MUSIC PLAYER ###
'''
Music Player - A simple music player interface for Karu the Fox desktop pet.
'''
from random import randint
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                               QPushButton, QHBoxLayout,
                               QListWidget, QSlider, QStyle,
                               QListWidgetItem, QFrame)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QUrl, QSize, QPoint
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

        ### Icons ###
        self.icons = {
            'loop_all': QIcon(str(IMAGE_DIR / "control-buttons" / "loop-all.png")),
            'loop_one': QIcon(str(IMAGE_DIR / "control-buttons" / "loop-1.png")),
            'shuffle': QIcon(str(IMAGE_DIR / "control-buttons" / "shuffle.png")),
            'volume_full': QIcon(str(IMAGE_DIR / "control-buttons" / "volume-full.png")),
            'volume_half': QIcon(str(IMAGE_DIR / "control-buttons" / "volume-half.png")),
            'volume_muted': QIcon(str(IMAGE_DIR / "control-buttons" / "volume-muted.png")),
            'play': QIcon(str(IMAGE_DIR / "control-buttons" / "play.png")),
            'pause': QIcon(str(IMAGE_DIR / "control-buttons" / "pause.png"))
        }

        ### Window Flags and Attributes ###
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Fox Music")
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
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setToolTip("Seek")
        self.total_time_label = QLabel("0:00")
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

        # Play/Pause Button
        self.play_pause_button = QPushButton()
        self.play_pause_button.setIcon(self.icons['play'])
        self.play_pause_button.setFixedSize(64, 64); self.play_pause_button.setIconSize(QSize(40, 40)); self.play_pause_button.setObjectName("PlayPauseButton")
        self.play_pause_button.setToolTip("Play")

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
        self.loop_button.setIcon(self.icons['loop_all'])
        self.loop_button.setFixedSize(40, 40); self.loop_button.setIconSize(QSize(24, 24)); self.loop_button.setObjectName("ControlButton")
        self.loop_button.setToolTip("Loop All")

        # Playlist Button
        self.songs_list_button = QPushButton("Playlist")
        self.songs_list_button.setObjectName("PlaylistButton")
        self.songs_list_button.setToolTip("Show / Hide Playlist")

        # Volume Button
        volume_layout = QHBoxLayout()
        self.volume_button = QPushButton()
        self.volume_button.setFixedSize(40, 40); self.volume_button.setIconSize(QSize(24, 24)); self.volume_button.setObjectName("ControlButton")
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

        title_label = QLabel("Fox Music")
        title_label.setStyleSheet("font-weight: bold; color: #ffa01e;")
        
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
            #CentralFrame {
                background-color: #282c34;
                color: #abb2bf;
                font-family: Arial, sans-serif;
                border-radius: 15px;
            }
            #TitleBar {
                background-color: #21252b;
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }
            #WindowButton {
                font-size: 14px;
                font-weight: bold;
            }
            #WindowButton:hover {
                background-color: #353b45;
            }
            #TitleLabel {
                font-size: 22px; font-weight: bold; color: #ffffff;
            }
            #ArtistLabel {
                font-size: 16px; color: #9ab;
            }
            #Thumbnail {
                border: 1px solid #353b45; border-radius: 10px; background-color: #21252b;
            }
            
            #ControlButton, #PlaylistButton {
                background-color: transparent; border: none;
            }
            #ControlButton:hover, #PlaylistButton:hover {
                background-color: #353b45;
            }
            #ControlButton:pressed, #PlaylistButton:pressed {
                background-color: #21252b;
            }
            #PlayPauseButton {
                border-radius: 32px; background-color: #353b45;
            }
            #PlayPauseButton:hover {
                background-color: #414855;
            }
            #PlayPauseButton:pressed {
                background-color: #21252b;
            }
            #PlaylistButton {
                font-size: 14px; padding: 5px 15px; border: 1px solid #353b45; border-radius: 15px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #282c34; height: 6px; background: #353b45; margin: 2px 0; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #61afef; border: 1px solid #61afef; width: 14px; height: 14px; margin: -4px 0; border-radius: 7px;
            }
            QListWidget {
                background-color: #21252b; border: 1px solid #353b45; font-size: 14px; padding: 5px;
            }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background-color: #61afef; color: #282c34; }
            QToolTip { background-color: #21252b; color: #abb2bf; border: 1px solid #353b45; padding: 4px; border-radius: 3px; }
        """)

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
            self.loop_button.setIcon(self.icons['loop_one'])
            self.loop_button.setToolTip("Loop One")
            self.tray_actions['loop'].setText("Mode: Loop One")
        elif self.playback_mode == 'loop_one': 
            self.playback_mode = 'shuffle'
            self.loop_button.setIcon(self.icons['shuffle'])
            self.loop_button.setToolTip("Shuffle")
            self.tray_actions['loop'].setText("Mode: Shuffle")
        else: 
            self.playback_mode = 'loop_all'
            self.loop_button.setIcon(self.icons['loop_all'])
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
            self.volume_button.setIcon(self.icons['volume_muted'])
        elif self.volume < 0.5:
            self.volume_button.setIcon(self.icons['volume_half'])
        else:
            self.volume_button.setIcon(self.icons['volume_full'])

    def toggle_song_list(self):
        self.song_list_widget.setVisible(not self.song_list_widget.isVisible())
        self.adjustSize()

    def play_from_list(self, item):
        self.play_song(self.song_list_widget.row(item))

    def update_play_pause_icon(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_pause_button.setIcon(self.icons['pause'])
            self.play_pause_button.setToolTip("Pause")
            self.tray_actions['play_pause'].setText("Pause")
        else:
            self.play_pause_button.setIcon(self.icons['play'])
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