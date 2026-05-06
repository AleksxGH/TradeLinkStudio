from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from app.services.config_manager import ConfigManager
from app.services.app_paths import AppPaths
from app.services.project_manager import ProjectManager
from app.ui.about_window import AboutWindow
from app.ui.main_window import MainWindow
from app.ui.new_project_dialogue import NewProjectDialog
from app.ui.settings_dialogue import SettingsDialog


class HomeWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.config = ConfigManager()
        self.config.load()

        self.paths = AppPaths()

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
        self.settings_btn = QPushButton("Settings")
        self.about_btn = QPushButton("About")
        layout.addWidget(self.new_btn)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.about_btn)

        self.setLayout(layout)

        self.new_btn.clicked.connect(self.new_project)
        self.open_btn.clicked.connect(self.open_project)
        self.settings_btn.clicked.connect(self.open_settings)
        self.about_btn.clicked.connect(self.open_about)

    def new_project(self):

        if self.config.get("use_standard_dirs"):
            project = ProjectManager.create_default_project(
                self.paths
            )

            self.main_window = MainWindow(project, self)
            self.main_window.show()
            self.close()
            return

        dialog = NewProjectDialog(self)

        if dialog.exec_():
            project = ProjectManager.create_custom_project(
                dialog.project_name,
                dialog.project_dir
            )

            self.main_window = MainWindow(project, self)
            self.main_window.show()
            self.close()

    def open_project(self):
        base_dir = QFileDialog.getExistingDirectory(
            self,
            "Open Project",
            self.paths.projects_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if not base_dir:
            return

        result = ProjectManager.load_project(base_dir)

        if result is None:
            QMessageBox.critical(
                self,
                "Open project error",
                "Не удалось открыть проект.\n"
                "Проверьте структуру папки проекта."
            )
            return

        project, datastore = result
        self.main_window = MainWindow(project, self, datastore)
        self.main_window.show()
        self.close()

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        dialog.exec_()

    def open_about(self):
        self.about_window = AboutWindow(self)
        self.about_window.show()
        self.hide()