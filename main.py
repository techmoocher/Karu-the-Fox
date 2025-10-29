import sys
import os
import json
import dotenv
from pathlib import Path
from random import choice, random, randint
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QDialog,
                               QPushButton, QHBoxLayout, QRadioButton, QButtonGroup, QMenu,
                               QSystemTrayIcon, QListWidget, QSlider, QStyle, QListWidgetItem,
                               QGraphicsDropShadowEffect, QFrame)
from PySide6.QtGui import QPixmap, QMovie, QAction, QIcon, QCursor, QColor
from PySide6.QtCore import Qt, QTimer, QUrl, QSize, QPoint
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import sys
from PySide6.QtWidgets import QApplication
from src.desktop_pet import DesktopPet

dotenv.load_dotenv()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec())