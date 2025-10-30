import sys
import dotenv
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QApplication
from src.desktop_pet import DesktopPet

dotenv.load_dotenv()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    sys.exit(app.exec())