import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
# from app.ui.main_window import MainWindow
from app.ui.home_window import HomeWindow

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("/resources/icons/app.ico"))
    app.setStyle("Fusion")
    window = HomeWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()