### Desktop Pet ###
'''
Main component
'''
import json
from random import choice, random, randint
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                               QDialog, QPushButton, QMenu, QSystemTrayIcon,
                               QStyle)
from PySide6.QtGui import (QPixmap, QMovie,
                           QAction, QIcon,
                           QFont, QCursor)
from PySide6.QtCore import Qt, QTimer, QUrl, QPoint
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from .music_player import MusicPlayerWindow
from .onboarding import SpeechBubble, RatingDialog
from .chat import ChatWindow
from .pomodoro import PomodoroWindow
from .constants import (BASE_DIR, IMAGE_DIR,
                        CONFIG_FILE, ENV_FILE,
                        LOGO_ICON)


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        ### Animations Assets ###
        self.assets = {
            'idle': [QPixmap(str(IMAGE_DIR / "fox" / "fox-1.png")), QPixmap(str(IMAGE_DIR / "fox" / "fox-2.png"))],
            'walk_left': [QPixmap(str(IMAGE_DIR / "fox" / "fox-walking-left-1.png")), QPixmap(str(IMAGE_DIR / "fox" / "fox-walking-left-2.png"))],
            'walk_right': [QPixmap(str(IMAGE_DIR / "fox" / "fox-walking-right-1.png")), QPixmap(str(IMAGE_DIR / "fox" / "fox-walking-right-2.png"))],
            'posture_idle_left': QPixmap(str(IMAGE_DIR / "fox" / "fox-idle-left.png")),
            'posture_idle_right': QPixmap(str(IMAGE_DIR / "fox" / "fox-idle-right.png")),
            'shock_left': QPixmap(str(IMAGE_DIR / "fox" / "fox-shock-left.png")),
            'shock_right': QPixmap(str(IMAGE_DIR / "fox" / "fox-shock-right.png")),
            'post_trauma_left': [QPixmap(str(IMAGE_DIR / "fox" / "fox-post-trauma-left-1.png")), QPixmap(str(IMAGE_DIR / "fox" / "fox-post-trauma-left-2.png"))],
            'post_trauma_right': [QPixmap(str(IMAGE_DIR / "fox" / "fox-post-trauma-right-1.png")), QPixmap(str(IMAGE_DIR / "fox" / "fox-post-trauma-right-2.png"))],
            'sleep': QMovie(str(IMAGE_DIR / "fox" / "fox-sleeping.gif")),
        }

        ### Onboarding Questions and Responses ###
        self.questions = ["How's your day going?",
                          "How are you doing?",
                          "How's your day been?"]
        self.responses = {
            1: ["I know it's hard right now, but keep going!", "A bad day doesn't mean a bad life. You've got this!", "I'm always here for you!", "Take a deep breath, you got this!"],
            2: ["Don't worry, you have me by your side.", "Let's find something to make you smile!", "It may be hard but you've got this!"],
            3: ["Let's make the rest of the day a great one!", "Keep it up, you're doing well!", "Not bad, let's see how we can make it better!"],
            4: ["That's great to hear! Let's keep it up.", "Awesome! You're doing great.",  "Let's celebrate your day!"],
            5: ["Wow, how amazing! I'm happy for you.", "That's fantastic!", "Let's celebrate!", "I'm so glad to hear that! Keep shining!"]
        }
        self.bubble = None

        ### Layout ###
        self._layout = QVBoxLayout()
        self.pet_label = QLabel(self)
        self.pet_label.setPixmap(self.assets['idle'][0])
        self._layout.addWidget(self.pet_label)
        self.setLayout(self._layout)
        self.resize(self.assets['idle'][0].size())

        ### Screen Geometry & Initial Position ###
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.available_geometry = QApplication.primaryScreen().availableGeometry()
        initial_x = self.available_geometry.width() - self.width() - 80
        self.move(initial_x, 0)
        self.update_position()

        ### Timers ###
        # Display Check Timer
        self.display_check_timer = QTimer(self)
        self.display_check_timer.timeout.connect(self.check_display_changes)

        # Animation Timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation_frame)

        # State Change Timer
        self.state_change_timer = QTimer(self)
        self.state_change_timer.setSingleShot(True)
        self.state_change_timer.timeout.connect(self.switch_state)

        # Walk Logic Timer
        self.walk_logic_timer = QTimer(self)
        self.walk_logic_timer.timeout.connect(self.update_walk_logic)

        # Post Trauma Timer
        self.post_trauma_timer = QTimer(self)
        self.post_trauma_timer.setSingleShot(True)
        self.post_trauma_timer.timeout.connect(self.resume_from_trauma)

        ### State Initialization ###
        self.state = 'intro'
        self.frame_index = 0
        self.speed = 2
        self.direction = choice([-1, 1])
        self.turn_new_direction = 1
        self.walk_direction_duration = 0
        self.wonder_count = 0
        self.is_dragging = False
        self.drag_start_pos = None

        ### Chat Window Initialization ###
        self.chat_window = ChatWindow()

        ### Music Player Initialization ###
        self.config = self._load_or_create_config()
        self._initialize_music_player()
        self._apply_config_to_player()

        ### Initialization
        self.setup_tray_icon()
        self.pomodoro_window = PomodoroWindow(tray_icon=self.tray_icon)
        self.start_intro_sequence()
        self.show()
        
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.save_config)

    def _initialize_music_player(self):
        self.tray_actions = {
            'play_pause': QAction("Play"),
            'prev': QAction("Previous"),
            'next': QAction("Next"),
            'loop': QAction("Mode: Loop All"),
            'mute': QAction("Mute"),
            'open': QAction("Open Music Player")
        }

        bold_font = QFont()
        bold_font.setBold(True)
        self.tray_actions['open'].setFont(bold_font)

        self.media_player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self._audio_output)
        self.music_player_window = MusicPlayerWindow(self.media_player, self.tray_actions)

    def save_config(self):
        if not self.music_player_window or not self.media_player:
            return
        
        config_data = {}
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            config_data = {}

        config_data.update({
            "last_track_index": self.music_player_window.current_index,
            "volume": self.music_player_window.volume_slider.value(),
            "is_muted": self.media_player.audioOutput().isMuted(),
            "playback_mode": self.music_player_window.playback_mode
        })

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")

    def _load_or_create_config(self):
        default_config = {
            "last_track_index": -1,
            "volume": 100,
            "is_muted": False,
            "playback_mode": "shuffle"
        }

        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
                default_config.update(config_data) 
                return default_config
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            return default_config
        
    def _apply_config_to_player(self):
        win = self.music_player_window
        player = self.media_player
        config = self.config

        # Apply volume
        win.volume_slider.setValue(config['volume'])
        player.audioOutput().setVolume(config['volume'] / 100.0)
        player.audioOutput().setMuted(config['is_muted'])
        win.is_muted = config['is_muted']
        win.update_volume_icon()
        win.tray_actions['mute'].setText("Unmute" if win.is_muted else "Mute")

        # Apply playback mode
        win.playback_mode = config['playback_mode']
        if win.playback_mode == 'loop_one':
            win.loop_button.setIcon(win.icons['loop_one'])
            win.loop_button.setToolTip("Loop One")
            win.tray_actions['loop'].setText("Mode: Loop One")
        elif win.playback_mode == 'shuffle':
            win.loop_button.setIcon(win.icons['shuffle'])
            win.loop_button.setToolTip("Shuffle")
            win.tray_actions['loop'].setText("Mode: Shuffle")
        else: 
            win.playback_mode = 'loop_all'
            win.loop_button.setIcon(win.icons['loop_all'])
            win.loop_button.setToolTip("Loop All")
            win.tray_actions['loop'].setText("Mode: Loop All")

        # Apply last track
        last_index = config['last_track_index']

        if 0 <= last_index < len(win.playlist):
            win.current_index = last_index
            song = win.playlist[last_index]

            win.media_player.setSource(QUrl.fromLocalFile(str(song['path'].absolute())))

            win.title_label.setText(song['title'])
            win.artist_label.setText(song['artist'])
            if song['thumbnail']:
                win.thumbnail_label.setPixmap(QPixmap(str(song['thumbnail'])).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                win.thumbnail_label.setPixmap(QPixmap())
                win.thumbnail_label.setText("No Art")
            win.song_list_widget.setCurrentRow(last_index)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(str(LOGO_ICON)))
        self.tray_icon.setToolTip("Karu the Fox")
        
        tray_menu = QMenu()
        
        self.music_menu = QMenu("Music")

        chat_action = QAction("Chat with Karu", self)
        chat_action.triggered.connect(self.open_chat_window)
        tray_menu.addAction(chat_action)

        pomodoro_action = QAction("Pomodoro Timer", self)
        pomodoro_action.triggered.connect(self.open_pomodoro_window)
        tray_menu.addAction(pomodoro_action)
        
        self.tray_actions['play_pause'].triggered.connect(self.music_player_window.toggle_play_pause)
        self.tray_actions['prev'].triggered.connect(self.music_player_window.prev_song)
        self.tray_actions['next'].triggered.connect(self.music_player_window.next_song)
        self.tray_actions['loop'].triggered.connect(self.music_player_window.change_playback_mode)
        self.tray_actions['mute'].triggered.connect(self.music_player_window.toggle_mute)
        self.tray_actions['open'].triggered.connect(self.open_music_player)

        self.music_menu.addAction(self.tray_actions['open'])
        self.music_menu.addSeparator()
        self.music_menu.addAction(self.tray_actions['play_pause'])
        self.music_menu.addAction(self.tray_actions['prev'])
        self.music_menu.addAction(self.tray_actions['next'])
        self.music_menu.addSeparator()
        self.music_menu.addAction(self.tray_actions['loop'])
        self.music_menu.addAction(self.tray_actions['mute'])
        
        tray_menu.addMenu(self.music_menu)

        self.toggle_action = QAction("Hide", self)
        self.toggle_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(self.toggle_action)
        tray_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def exit_application(self):
        """
        Save state and quit the app from the tray menu.
        """
        self.save_config()
        app = QApplication.instance()
        if app:
            app.quit()

    def open_chat_window(self):
        """
        Shows the chat window.
        """
        self.chat_window.show()
        self.chat_window.activateWindow()

    def open_music_player(self):
        """
        Shows the music player
        """
        self.music_player_window.show()
        self.music_player_window.activateWindow()

    def open_pomodoro_window(self):
        """Show the pixel-style pomodoro timer."""
        self.pomodoro_window.show()
        self.pomodoro_window.activateWindow()

    def start_intro_sequence(self):
        self.music_menu.setEnabled(False)
        hour = datetime.now().hour
        greeting = "Good morning!" if 5 <= hour < 12 else "Good afternoon!" if 12 <= hour < 18 else "Good evening!"
        self.show_bubble(greeting)
        self.animation_timer.start(300)
        QTimer.singleShot(1200, self.ask_question)

    def start_main_lifecycle(self):
        self.music_menu.setEnabled(True)
        if self.bubble:
            self.bubble.hide()
        self.display_check_timer.start(2000)
        self.enter_walking_state()
    
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
            self.toggle_action.setText("Show")
        else:
            self.show()
            self.toggle_action.setText("Hide")

    def closeEvent(self, event):
        self.tray_icon.hide()
        event.accept()

    def ask_question(self):
        question = choice(self.questions)
        self.show_bubble(question, word_wrap=False)
        QTimer.singleShot(2000, lambda: self.show_rating_dialog(question))

    def show_rating_dialog(self, question_text):
        if self.bubble:
            self.bubble.hide()
        dialog = RatingDialog(question_text, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.show_response(dialog.get_rating())
        else:
            self.start_main_lifecycle()

    def show_response(self, rating):
        response_text = choice(self.responses[rating])
        self.show_bubble(response_text)
        QTimer.singleShot(3000, self.start_main_lifecycle)

    def show_bubble(self, text, word_wrap=True):
        if self.bubble:
            self.bubble.deleteLater()
        self.bubble = SpeechBubble(text, self, word_wrap=word_wrap)
        self.bubble.show_smartly_positioned()

    def switch_state(self):
        if self.state == 'walking':
            self.state = 'idling_before_sleep'
            self.walk_logic_timer.stop()
            self.animation_timer.stop()
            idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
            self.pet_label.setPixmap(idle_sprite)
            QTimer.singleShot(randint(700, 1200), self.enter_sleeping_state)
        elif self.state == 'sleeping':
            self.state = 'waking_up'
            self.assets['sleep'].stop()
            idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
            self.pet_label.setPixmap(idle_sprite)
            QTimer.singleShot(randint(700, 1200), self.enter_walking_state)

    def enter_walking_state(self):
        self.state = 'walking'
        self.animation_timer.setInterval(150)
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        self.state_change_timer.start(randint(30, 40) * 1000)
        self.walk_direction_duration = 0
        self.walk_logic_timer.start(1000)

    def enter_sleeping_state(self):
        self.state = 'sleeping'
        self.animation_timer.stop()
        self.pet_label.setMovie(self.assets['sleep'])
        self.assets['sleep'].start()
        self.state_change_timer.start(randint(10, 20) * 1000)

    def update_walk_logic(self):
        if self.state != 'walking':
            return
        self.walk_direction_duration += 1
        r = random()
        if r < 0.04:
            self.initiate_wagging()
        elif r < 0.09:
            self.initiate_pause()
        elif r < 0.14:
            self.initiate_wondering()
        elif r < 0.22:
            self.initiate_turn()
        elif self.walk_direction_duration > 15:
            self.initiate_turn()

    def initiate_pause(self):
        if self.state != 'walking':
            return
        self.state = 'pausing'
        self.walk_logic_timer.stop()
        self.animation_timer.stop()
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(1500, 3000), self.resume_walking)

    def initiate_turn(self, new_direction=None):
        if self.state != 'walking':
            return
        self.state = 'turning'
        self.walk_logic_timer.stop()
        self.animation_timer.stop()
        self.turn_new_direction = new_direction if new_direction is not None else self.direction * -1
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(300, 500), self.complete_turn)

    def complete_turn(self):
        self.direction = self.turn_new_direction
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(300, 500), self.resume_walking)

    def initiate_wondering(self):
        if self.state != 'walking':
            return
        self.state = 'wondering'
        self.walk_logic_timer.stop()
        self.animation_timer.stop()
        self.wonder_count = randint(1, 3)
        self.perform_wonder_step()

    def perform_wonder_step(self):
        self.wonder_count -= 1
        self.direction *= -1
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        if self.wonder_count > 0:
            QTimer.singleShot(randint(600, 1000), self.perform_wonder_step)
        else:
            QTimer.singleShot(randint(500, 800), self.resume_walking)

    def initiate_wagging(self):
        if self.state != 'walking':
            return
        self.state = 'wagging'
        self.walk_logic_timer.stop()
        self.animation_timer.setInterval(300)
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        QTimer.singleShot(randint(1500, 3000), self.resume_walking)

    def resume_walking(self):
        self.state = 'walking'
        self.animation_timer.setInterval(150)
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        self.walk_direction_duration = 0
        self.walk_logic_timer.start(1000)

    def mousePressEvent(self, event):
        if self.state == 'intro':
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPosition()
            self.state_change_timer.stop()
            self.walk_logic_timer.stop()
            self.animation_timer.stop()
            self.assets['sleep'].stop()
            self.state = 'shock'
            shock_sprite = self.assets['shock_right'] if self.direction == 1 else self.assets['shock_left']
            self.pet_label.setPixmap(shock_sprite)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.globalPosition() - self.drag_start_pos
            self.move(self.pos() + delta.toPoint())
            self.drag_start_pos = event.globalPosition()

    def mouseReleaseEvent(self, event):
        if self.state == 'intro':
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.drag_start_pos = None
            self.move(self.x(), self.base_y)
            self.state = 'post_trauma'
            self.frame_index = 0
            self.animation_timer.setInterval(300)
            if not self.animation_timer.isActive():
                self.animation_timer.start()
            self.post_trauma_timer.start(randint(2000, 3000))

    def resume_from_trauma(self):
        self.state = 'recovering'
        self.animation_timer.stop()
        idle_sprite = self.assets['posture_idle_right'] if self.direction == 1 else self.assets['posture_idle_left']
        self.pet_label.setPixmap(idle_sprite)
        QTimer.singleShot(randint(500, 1000), self.start_main_lifecycle)

    def update_animation_frame(self):
        if self.is_dragging:
            return
        if self.state == 'walking':
            if (self.x() >= self.available_geometry.width() - self.width() and self.direction == 1):
                self.initiate_turn(new_direction=-1)
                return
            elif (self.x() <= 0 and self.direction == -1):
                self.initiate_turn(new_direction=1)
                return
            self.move(self.x() + (self.speed * self.direction), self.y())
            frames = self.assets['walk_right'] if self.direction == 1 else self.assets['walk_left']
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.pet_label.setPixmap(frames[self.frame_index])
        elif self.state == 'post_trauma':
            frames = self.assets['post_trauma_right'] if self.direction == 1 else self.assets['post_trauma_left']
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.pet_label.setPixmap(frames[self.frame_index])
        elif self.state in ['intro', 'wagging']:
            frames = self.assets['idle']
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.pet_label.setPixmap(frames[self.frame_index])

    def update_position(self):
        self.available_geometry = QApplication.primaryScreen().availableGeometry()
        self.base_y = self.available_geometry.height() - self.height() - 10
        if not (0 <= self.x() <= self.available_geometry.width() - self.width()):
            x = self.available_geometry.width() - self.width() - 50
            self.move(x, self.base_y)
        else:
            self.move(self.x(), self.base_y)

    def check_display_changes(self):
        current_screen = QApplication.primaryScreen().geometry()
        current_available = QApplication.primaryScreen().availableGeometry()
        if (current_screen != self.screen_geometry or current_available != self.available_geometry):
            self.screen_geometry = current_screen
            self.available_geometry = current_available
            self.update_position()