import os
import json
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout,
                               QFrame, QTextEdit, QLineEdit)
from PySide6.QtGui import QIcon, QFontDatabase
from PySide6.QtCore import Qt, QPoint, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from .constants import IMAGE_DIR, LOGO_ICON, NERD_FONT_SYMBOLS


class ChatWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Chat with Karu")
        self.setWindowIcon(QIcon(str(LOGO_ICON)))
        self.setMinimumSize(400, 500)
        self.drag_pos = QPoint()

        # API and Chat State
        self.network_manager = QNetworkAccessManager(self)
        self.chat_history = []
        
        self.api_key = os.getenv("GEMINI_API_KEY") or ""

        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={self.api_key}"
        
        self.system_instruction = (
            "You are a cute and friendly fox named Karu, a desktop pet living on the user's screen. "
            "You are supportive user's best friend and always ready to help. "
            "Reply concisely with a slightly sassy, clever, and cute fox personality. "
            "Occasionally use words like '*Yip*', '*Flickers ear*', 'Hmph', '*Chuffs*', '*Purr*. "
            "Never say you are an AI model or a language model. You are a fox named Karu."
        )

        self._setup_ui()
        self._apply_stylesheet()
        self._load_icon_font()
        self._connect_signals()
        
        if not self.api_key:
            self._append_message("Error", "GEMINI_API_KEY is missing. Please set it in your .env file.")
            self.send_button.setDisabled(True)
            self.input_box.setDisabled(True)


    def _setup_ui(self):
        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("CentralFrame")
        self.main_layout = QVBoxLayout(self.central_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.setCentralWidget(self.central_frame)

        # Title Bar
        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 0, 0)
        title_bar_layout.setSpacing(10)
        title_label = QLabel("Chat with Karu")
        title_label.setStyleSheet(
            "font-weight: bold; color: #2b1b00; letter-spacing: 0.5px;"
        )
        self.minimize_button = QPushButton("—")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setObjectName("WindowButton")
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setObjectName("WindowButton")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.close_button)
        self.main_layout.addWidget(title_bar)
        
        # Chat History
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("ChatDisplay")
        self.main_layout.addWidget(self.chat_display, 1)

        # Input Area
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Say something... (Press Enter)")
        self.input_box.setObjectName("InputBox")
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("SendButton")
        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.send_button)
        self.main_layout.addLayout(input_layout)

    # Helper for layout
    def setCentralWidget(self, widget):
        layout = QVBoxLayout(self)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            #CentralFrame {
                background-color: #fff4e6;
                color: #2b1b00;
                font-family: "Press Start 2P", "VT323", "Courier New", monospace;
                font-size: 12px;
                letter-spacing: 0.4px;
                border: 3px solid #f7b267;
                border-radius: 10px;
                padding: 4px;
            }
            #TitleBar {
                background-color: #ffc387;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 3px solid #f7a440;
                min-height: 34px;
            }
            #WindowButton {
                font-size: 12px;
                font-weight: bold;
                border: 2px solid #2b1b00;
                background-color: #ffe0b8;
                color: #2b1b00;
                border-radius: 4px;
                min-width: 28px;
            }
            #WindowButton:hover {
                background-color: #ffd18a;
            }
            #ChatDisplay {
                background-color: #fff0e0;
                border: 2px solid #f7a440;
                color: #2b1b00;
                font-size: 12px;
                selection-background-color: #ffb570;
                selection-color: #2b1b00;
                padding: 10px;
            }
            #InputBox {
                background-color: #ffe9d6;
                border: 2px solid #f7a440;
                border-radius: 6px;
                padding: 8px 12px;
                color: #2b1b00;
                font-size: 12px;
            }
            #InputBox:focus {
                border-color: #ffb570;
            }
            #SendButton {
                background-color: #ffb570;
                color: #2b1b00;
                font-weight: bold;
                border: 2px solid #2b1b00;
                border-radius: 6px;
                padding: 10px 14px;
            }
            #SendButton:hover {
                background-color: #ffc387;
            }
            #SendButton:disabled {
                background-color: #e6d3bd;
                color: #7a6040;
                border-color: #c8a273;
            }
        """)

    def _load_icon_font(self):
        """Load Nerd Font symbols for inline icons; fall back silently if missing."""
        self.icon_font_family = "Symbols Nerd Font"
        if not NERD_FONT_SYMBOLS.exists():
            return
        font_id = QFontDatabase.addApplicationFont(str(NERD_FONT_SYMBOLS))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                self.icon_font_family = families[0]
    
    def _connect_signals(self):
        self.minimize_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.hide)
        self.send_button.clicked.connect(self.send_message)
        self.input_box.returnPressed.connect(self.send_message)
        self.network_manager.finished.connect(self._handle_gemini_response)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on the title bar
            if self.main_layout.itemAt(0).widget().geometry().contains(event.pos()):
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.drag_pos = QPoint()

    def send_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return

        self._append_message("You", user_text)
        self.chat_history.append({"role": "user", "parts": [{"text": user_text}]})
        self.input_box.clear()
        self._call_gemini_api()

    def _call_gemini_api(self):
        self.send_button.setDisabled(True)
        self.input_box.setDisabled(True)
        self.chat_display.append("<i style='color:#7A6040'>Karu is thinking...</i>")

        # Format chat history for API
        api_history = []
        for msg in self.chat_history:
            # Ensure role is 'user' or 'model'
            if msg['role'] in ['user', 'model']:
                api_history.append(msg)
        
        payload = {
            "contents": api_history,
            "systemInstruction": {
                "parts": [{"text": self.system_instruction}]
            },
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
            }
        }
        
        request = QNetworkRequest(QUrl(self.api_url))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        
        try:
            request_body = json.dumps(payload).encode('utf-8')
            self.network_manager.post(request, request_body)
        except Exception as e:
            self._append_message("Error", f"Could not send message: {e}")
            self.send_button.setDisabled(False)
            self.input_box.setDisabled(False)

    def _handle_gemini_response(self, reply):
        self.send_button.setDisabled(False)
        self.input_box.setDisabled(False)
        # Remove "Karu is thinking..."
        self.chat_display.undo() 

        if reply.error() != QNetworkReply.NetworkError.NoError:
            error_msg = reply.errorString()
            self._append_message("Error", f"Network Error: {error_msg}")
            reply.deleteLater()
            return

        try:
            response_data = reply.readAll().data()
            if not response_data:
                self._append_message("Error", "Received empty response from server.")
                reply.deleteLater()
                return
                
            response_json = json.loads(response_data)
            
            if 'candidates' in response_json:
                model_text = response_json['candidates'][0]['content']['parts'][0]['text']
                self._append_message("Karu", model_text)
                self.chat_history.append({"role": "model", "parts": [{"text": model_text}]})
            elif 'error' in response_json:
                error_details = response_json['error'].get('message', 'Unknown error')
                self._append_message("Error", f"API Error: {error_details}")
            else:
                self._append_message("Error", "Received an unexpected response.")

        except Exception as e:
            self._append_message("Error", f"Failed to parse response: {e}")
        
        reply.deleteLater()

    def _append_message(self, sender, text):
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        icon_user = (
            f"<span style=\"font-family: '{self.icon_font_family}'; font-size: 14px;\"></span> You"
        )
        icon_karu = (
            f"<span style=\"font-family: '{self.icon_font_family}'; font-size: 14px;\"></span> Karu"
        )
        label = icon_karu if sender == "Karu" else icon_user if sender == "You" else sender

        if sender == "You":
            html = (
                "<p style='text-align: left; margin: 4px 5px; padding: 10px; "
                "background-color: #ffd6a5; color: #2b1b00; border: 2px solid #2b1b00; "
                "border-radius: 8px; box-shadow: 2px 2px 0 #d38c52;'>"
                f"<b>{label}:</b><br>{text}</p>"
            )
        elif sender == "Karu":
            html = (
                "<p style='text-align: left; margin: 4px 5px; padding: 10px; "
                "background-color: #ffb570; color: #2b1b00; border: 2px solid #2b1b00; "
                "border-radius: 8px; box-shadow: 2px 2px 0 #d38c52;'>"
                f"<b>{label}:</b><br>{text}</p>"
            )
        else:
            html = (
                "<p style='color: #4e1a0c; margin: 4px 5px; padding: 10px; background-color: #ffdeda; "
                "border: 2px solid #d16f4f; border-radius: 8px; box-shadow: 2px 2px 0 #c15a3a;'>"
                f"<b>{label}:</b><br>{text}</p>"
            )
        
        self.chat_display.append(html)
        
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())


    def closeEvent(self, event):
        self.hide()
        event.ignore()