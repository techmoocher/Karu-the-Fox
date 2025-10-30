### ONBOARDING ###
'''

'''
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QDialog,
                               QPushButton, QHBoxLayout, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt


class SpeechBubble(QWidget):
    def __init__(self, text, parent, word_wrap=True):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setStyleSheet("background-color: white; color: black; border: 1px solid black; border-radius: 10px; padding: 10px;")
        if word_wrap:
            self.label.setWordWrap(True)
            self.label.setMaximumWidth(270)
        self._layout.addWidget(self.label)
        self.setLayout(self._layout)

    def show_smartly_positioned(self):
        parent_geometry = self.parentWidget().geometry()
        x = parent_geometry.center().x() - self.width() / 2
        y_above = parent_geometry.top() - self.height() - 5
        self.move(int(x), int(y_above if y_above > 0 else parent_geometry.bottom() + 5))
        self.show()

### --- Feeling Survey Window --- ###
class RatingDialog(QDialog):
    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How are you feeling?")
        self._layout = QVBoxLayout()
        self._layout.addWidget(QLabel(question))
        emoticons = {1: "😭", 2: "😞", 3: "😑", 4: "😊", 5: "😁"}
        self.button_group = QButtonGroup(self)
        radio_layout = QHBoxLayout()
        for i in range(1, 6):
            radio_button = QRadioButton(emoticons[i])
            radio_layout.addWidget(radio_button)
            self.button_group.addButton(radio_button, i)
        self.button_group.button(3).setChecked(True)
        self._layout.addLayout(radio_layout)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.accept)
        self._layout.addWidget(self.confirm_button)
        self.setLayout(self._layout)

    def get_rating(self):
        return self.button_group.checkedId()