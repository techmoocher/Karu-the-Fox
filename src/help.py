from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QHBoxLayout,
                               QLabel, QPushButton,
                               QVBoxLayout)


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Karu the Fox — Help")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setStyleSheet(
            """
            QDialog { background-color: #FFF5EC; border: 1px solid #F2C194; }
            #dialogTitle { font-size: 18px; font-weight: 700; color: #D2641A; }
            #sectionTitle { font-size: 13px; font-weight: 600; color: #B14F0F; }
            QLabel { color: #5D3C23; }
            QPushButton { background-color: #F7B267; border: 1px solid #F0A04B; padding: 6px 14px; border-radius: 6px; font-weight: 600; }
            QPushButton:hover { background-color: #F4A64F; }
            QPushButton:pressed { background-color: #E8923A; }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(10)

        title = QLabel("Karu the Fox")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        intro = QLabel("Your friendly desktop pet with chat, music, pomodoro, and more!")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        how_title = QLabel("How to use")
        how_title.setObjectName("sectionTitle")
        layout.addWidget(how_title)

        how_text = QLabel(
            """
            <ul>
                <li><b>Let him wander</b> around your screen or <b>drag Karu around</b> your screen.</li>
                <li>Open <b>Chat with Karu</b> to talk and enjoy breaks during hard-working days.</li>
                <li>Play your favorite tunes with the <b>Dance with Karu</b> music player.</li>
                <li>Start the <b>Pomodoro Timer</b> to kickstart focus mode.</li>
                <li><b>Hide/Show Karu</b> from the tray for a distraction-free workspace.</li>
                <li>Right-click on the <b>tray icon</b> for <b>quick actions</b>.</li>
            </ul>
            """
        )
        how_text.setWordWrap(True)
        how_text.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(how_text)

        # features_title = QLabel("Features")
        # features_title.setObjectName("sectionTitle")
        # layout.addWidget(features_title)

        # features_text = QLabel(
        #     """
        #     <ul>
        #         <li>Adorable animated fox that reacts and naps.</li>
        #         <li>Built-in music player with playlist controls.</li>
        #         <li>Pomodoro focus cycles with reminders.</li>
        #         <li>Chat window for quick conversations.</li>
        #         <li>Tray shortcuts for everything important.</li>
        #     </ul>
        #     """
        # )
        # features_text.setWordWrap(True)
        # features_text.setTextFormat(Qt.TextFormat.RichText)
        # layout.addWidget(features_text)

        buttons_layout = QHBoxLayout()
        learn_more_btn = QPushButton("Learn more")
        learn_more_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/techmoocher/Karu-the-Fox.git")))
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(learn_more_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_btn)
        layout.addLayout(buttons_layout)

    def show_dialog(self):
        self.show()
        self.raise_()
        self.activateWindow()