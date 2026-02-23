import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from app.ui.home_window import HomeWindow
from style.style_manager import load_styles

def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # путь к временной папке PyInstaller
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("/resources/icons/app.ico"))
    load_styles(app, "style.qss")
    window = HomeWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()