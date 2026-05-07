import os
import PyQt5.QtWidgets
from PyQt5.QtGui import QIcon
import webbrowser
import urllib.parse
from app.services.resource_utils import icon_path, resource_path


class AboutWindow(PyQt5.QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent

        self.setWindowTitle("TradeLink Studio - About")
        self.resize(1360, 820)
        self.setWindowIcon(QIcon(icon_path("app.ico")))

        self._init_ui()

    def _init_ui(self):
        central_widget = PyQt5.QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = PyQt5.QtWidgets.QVBoxLayout(central_widget)

        button_layout = PyQt5.QtWidgets.QHBoxLayout()

        self.home_button = PyQt5.QtWidgets.QPushButton("Home")
        self.contact_button = PyQt5.QtWidgets.QPushButton("Contact Support")

        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.contact_button)
        button_layout.addStretch()

        self.info_browser = PyQt5.QtWidgets.QTextBrowser()

        html_path = resource_path("resources", "ui", "about.html")

        with open(html_path, "r", encoding="utf-8") as file:
            html_content = file.read()
            self.info_browser.setHtml(html_content)

        self.info_browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background-color: #E6E9EF;
            }
        """)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.info_browser)

        self.home_button.clicked.connect(self.to_home)
        self.contact_button.clicked.connect(self.to_contact)

    def to_home(self):
        self.parent_window.show()
        self.close()

    def to_contact(self):
        recipient = "admishchenko@edu.hse.ru"

        subject = "TradeLink Studio Support Request"
        body = "Describe your issue here"

        mailto_link = (
            f"mailto:{recipient}"
            f"?subject={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(body)}"
        )

        webbrowser.open(mailto_link)