import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from app.ui.home_window import HomeWindow
from style.style_manager import load_styles, load_fonts
from app.services.resource_utils import icon_path

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path("app.ico")))
    load_fonts()  # Load custom fonts first
    load_styles(app, "style/style.qss")
    window = HomeWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()