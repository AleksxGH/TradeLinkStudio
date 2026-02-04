from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from app.services.project_manager import ProjectManager
from app.ui.main_window import MainWindow
from app.core.project import Project
from app.ui.new_project_dialogue import NewProjectDialog


class HomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TradeLink Studio")
        self.resize(1360, 820)
        self.setWindowIcon(QIcon("/resources/icons/app.ico"))
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Кнопки
        self.new_btn = QPushButton("New Project")
        self.open_btn = QPushButton("Open Project")
        self.create_template_btn = QPushButton("Create Template")
        self.settings_btn = QPushButton("Settings")
        self.about_btn = QPushButton("About")

        # Сделаем нерабочими пока кроме New Project
        self.create_template_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.about_btn.setEnabled(False)

        # Добавляем кнопки в layout
        layout.addWidget(self.new_btn)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.create_template_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.about_btn)

        self.setLayout(layout)

        # Подключаем сигнал для New Project
        self.new_btn.clicked.connect(self.new_project)

    def new_project(self):
        dialog = NewProjectDialog(self)

        if dialog.exec_():
            project = ProjectManager.create_project(dialog.project_name, dialog.project_dir)
            self.main_window = MainWindow(project)
            self.main_window.show()
            self.close()