from typing import Callable
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayMenuManager:
    def __init__(
        self,
        parent,
        icon_path,
        tray_actions: dict,
        open_chat: Callable,
        open_pomodoro: Callable,
        toggle_visibility: Callable,
        open_help: Callable,
        exit_app: Callable,
    ):
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(QIcon(str(icon_path)))
        self.tray_icon.setToolTip("Karu the Fox")

        tray_menu = QMenu()

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_action = QAction("Karu the Fox", parent)
        title_action.setFont(title_font)
        title_action.setEnabled(False)
        tray_menu.addAction(title_action)
        tray_menu.addSeparator()

        chat_action = QAction("Chat with Karu", parent)
        chat_action.triggered.connect(open_chat)
        tray_menu.addAction(chat_action)

        pomodoro_action = QAction("Pomodoro Timer", parent)
        pomodoro_action.triggered.connect(open_pomodoro)
        tray_menu.addAction(pomodoro_action)

        self.music_menu = QMenu("Music with Karu", parent)
        self.music_menu.addAction(tray_actions['open'])
        self.music_menu.addSeparator()
        self.music_menu.addAction(tray_actions['play_pause'])
        self.music_menu.addAction(tray_actions['prev'])
        self.music_menu.addAction(tray_actions['next'])
        self.music_menu.addSeparator()
        self.music_menu.addAction(tray_actions['loop'])
        self.music_menu.addAction(tray_actions['mute'])
        tray_menu.addMenu(self.music_menu)

        self.toggle_action = QAction("Hide", parent)
        self.toggle_action.triggered.connect(toggle_visibility)
        tray_menu.addAction(self.toggle_action)
        tray_menu.addSeparator()

        help_font = QFont()
        help_font.setBold(True)
        help_action = QAction("Help", parent)
        help_action.setFont(help_font)
        help_action.triggered.connect(open_help)
        tray_menu.addAction(help_action)

        exit_action = QAction("Exit", parent)
        exit_action.setFont(help_font)
        exit_action.triggered.connect(exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def set_music_menu_enabled(self, enabled: bool):
        self.music_menu.setEnabled(enabled)