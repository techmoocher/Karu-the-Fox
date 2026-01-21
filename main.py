import sys
import signal
import dotenv
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.desktop_pet import DesktopPet

dotenv.load_dotenv()

def main():
    app = QApplication(sys.argv)

    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    _ctrl_c_pump = QTimer()
    _ctrl_c_pump.timeout.connect(lambda: None)
    _ctrl_c_pump.start(200)

    pet = DesktopPet()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()