import json
import os

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.services.app_paths import AppPaths
from app.services.config_manager import ConfigManager
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
        self.all_projects = []
        self.main_window = None
        self.about_window = None
        self.version_text = self._load_version()
        self.setWindowTitle("TradeLink Studio")
        self.resize(1360, 820)
        self.setWindowIcon(QIcon("resources/icons/app.ico"))
        self._init_ui()
        self.refresh_projects_list()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = QWidget()
        left_panel.setFixedWidth(340)
        left_panel.setStyleSheet("background-color: #E0E8F9;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(10)

        brand_row = QHBoxLayout()
        brand_icon = QLabel()
        brand_icon.setPixmap(QIcon("resources/icons/app.ico").pixmap(QSize(80, 80)))
        brand_icon.setStyleSheet("border-radius: 12px; background-color: transparent;")
        brand_row.addWidget(brand_icon, 0, Qt.AlignTop)

        brand_text = QVBoxLayout()
        brand_label = QLabel("TradeLink Studio")
        brand_label.setFont(QFont("Open Sans", 200, QFont.Normal))
        brand_label.setStyleSheet("color: #000000;")
        version_label = QLabel(self.version_text)
        version_label.setFont(QFont("Open Sans", 20, QFont.Normal))
        version_label.setStyleSheet("color: #000000;")
        brand_text.addWidget(brand_label)
        brand_text.addWidget(version_label)
        brand_row.addLayout(brand_text)
        brand_row.addStretch(1)
        left_layout.addLayout(brand_row)
        left_layout.addSpacing(24)

        self.menu_buttons = {}
        for text, icon_path, callback in [
            (" Home", "resources/icons/main_menu_icon.png", self.go_home),
            (" New Project", "resources/icons/new_project_icon.png", self.new_project),
            (" Open Project", "resources/icons/open_project_icon.png", self.open_project),
            (" Settings", "resources/icons/settings_icon.png", self.open_settings),
        ]:
            button = self._menu_button(text, icon_path, callback)
            self.menu_buttons[text] = button
            left_layout.addWidget(button)

        left_layout.addStretch(1)

        about_button = self._menu_button("About", "resources/icons/about_icon.png", self.open_about)
        self.menu_buttons["About"] = about_button
        left_layout.addWidget(about_button)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(44, 32, 44, 32)
        right_layout.setSpacing(14)

        title_label = QLabel("Welcome to TradeLink Studio")
        title_label.setObjectName("appTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Open Sans", 40, QFont.Normal))
        title_label.setStyleSheet("color: #000000;")
        right_layout.addWidget(title_label)

        top_actions = QHBoxLayout()
        top_actions.setSpacing(44)
        top_actions.addStretch(1)
        top_actions.addWidget(self._action_card("resources/icons/new_project_icon.png", "New Project", self.new_project))
        top_actions.addWidget(self._action_card("resources/icons/open_project_icon.png", "Open Project", self.open_project))
        top_actions.addStretch(1)
        right_layout.addLayout(top_actions)

        projects_frame = QFrame()
        projects_frame.setStyleSheet("""
            QFrame {
                background-color: #F7F8FB;
                border: 1px solid #D7DEEB;
                border-radius: 10px;
            }
        """)
        projects_frame.setMinimumHeight(300)

        projects_layout = QVBoxLayout(projects_frame)
        projects_layout.setContentsMargins(14, 14, 14, 14)
        projects_layout.setSpacing(12)

        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(8)
        search_row.addWidget(self._icon_label("resources/icons/search_icon.png", 30), 0, Qt.AlignVCenter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search project")
        self.search_input.setFixedHeight(38)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CFD6E4;
                border-radius: 7px;
                background-color: #FFFFFF;
                padding: 6px 10px;
                color: #000000;
            }
        """)
        self.search_input.textChanged.connect(self.filter_projects)
        search_row.addWidget(self.search_input, 1)
        projects_layout.addLayout(search_row)

        self.projects_scroll = QScrollArea()
        self.projects_scroll.setWidgetResizable(True)
        self.projects_scroll.setFrameShape(QFrame.NoFrame)
        self.projects_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #EEF2F7;
                width: 10px;
                margin: 2px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #BCC8DA;
                min-height: 24px;
                border-radius: 5px;
            }
        """)

        self.projects_container = QWidget()
        self.projects_container_layout = QVBoxLayout(self.projects_container)
        self.projects_container_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_container_layout.setSpacing(8)
        self.projects_scroll.setWidget(self.projects_container)
        projects_layout.addWidget(self.projects_scroll, 1)

        right_layout.addWidget(projects_frame, 1)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_container, 1)

    def _menu_button(self, text, icon_path, callback):
        button = QPushButton(text)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(30, 30))
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(44)
        button.setFont(QFont("Open Sans", 22, QFont.Normal))
        button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #000000;
                font-weight: 400;
                text-align: left;
                padding: 10px 16px;
                spacing: 30px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.06);
                border-radius: 6px;
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);
            }
        """)
        button.clicked.connect(callback)
        return button

    def _action_card(self, icon_path, text, callback):
        card = QWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignHCenter)

        button = QToolButton()
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(64, 64))
        button.setFixedSize(96, 96)
        button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        button.setStyleSheet("""
            QToolButton {
                border: 2px solid #2F2F2F;
                border-radius: 16px;
                background-color: #F8F9FB;
            }
            QToolButton:hover {
                background-color: #EEF3FF;
            }
            QToolButton:pressed {
                background-color: #E3EBFF;
            }
        """)
        button.clicked.connect(callback)

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Open Sans", 20, QFont.Normal))
        label.setStyleSheet("color: #000000;")

        card_layout.addWidget(button, 0, Qt.AlignHCenter)
        card_layout.addWidget(label)
        return card

    def _icon_label(self, icon_path, size=16):
        label = QLabel()
        label.setPixmap(QIcon(icon_path).pixmap(QSize(size, size)))
        label.setFixedSize(size, size)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("border: none;")
        return label

    def _load_user_data(self):
        """Load custom project paths from user_data.json"""
        user_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_data.json")
        try:
            if os.path.exists(user_data_path):
                with open(user_data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("custom_projects", [])
        except Exception:
            pass
        return []

    def _save_user_data(self, custom_projects):
        """Save custom project paths to user_data.json"""
        user_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_data.json")
        try:
            with open(user_data_path, "w", encoding="utf-8") as f:
                json.dump({"custom_projects": custom_projects}, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Failed to save user data: {exc}")

    def _add_custom_project(self, project_path):
        """Add a custom project path to user_data.json"""
        custom_projects = self._load_user_data()
        abs_path = os.path.abspath(project_path)
        if abs_path not in custom_projects:
            custom_projects.append(abs_path)
            self._save_user_data(custom_projects)

    def _remove_custom_project(self, project_path):
        """Remove a custom project path from user_data.json"""
        custom_projects = self._load_user_data()
        abs_path = os.path.abspath(project_path)
        if abs_path in custom_projects:
            custom_projects.remove(abs_path)
            self._save_user_data(custom_projects)

    def refresh_projects_list(self):
        self.all_projects = []
        projects_dir = self.paths.projects_dir
        
        # Load default projects
        if os.path.exists(projects_dir):
            try:
                for item in sorted(os.listdir(projects_dir), key=str.lower):
                    item_path = os.path.join(projects_dir, item)
                    if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "data", "project.json")):
                        self.all_projects.append({"name": item, "path": item_path})
            except Exception as exc:
                QMessageBox.warning(self, "Error", f"Failed to load projects: {exc}")
        
        # Load custom projects
        custom_projects = self._load_user_data()
        valid_custom_projects = []
        for custom_path in custom_projects:
            if os.path.isdir(custom_path) and os.path.exists(os.path.join(custom_path, "data", "project.json")):
                project_name = os.path.basename(custom_path)
                self.all_projects.append({"name": project_name, "path": custom_path, "is_custom": True})
                valid_custom_projects.append(custom_path)
        
        # Update user_data.json with only valid custom projects
        if len(valid_custom_projects) != len(custom_projects):
            self._save_user_data(valid_custom_projects)
        
        self.display_projects(self.all_projects)

    def display_projects(self, projects):
        while self.projects_container_layout.count():
            item = self.projects_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not projects:
            empty_label = QLabel("The projects directory is empty")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setFont(QFont("Open Sans", 20, QFont.Normal))
            empty_label.setStyleSheet("color: #7F8898;")
            self.projects_container_layout.addWidget(empty_label)
            self.projects_container_layout.addStretch(1)
            return

        for project in projects:
            self.projects_container_layout.addWidget(self.create_project_item(project))

        self.projects_container_layout.addStretch(1)

    def create_project_item(self, project):
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E1E6F0;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #FDFEFE;
                border: 1px solid #CFD8E8;
            }
        """)
        item_frame.setCursor(Qt.PointingHandCursor)

        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(14, 12, 10, 12)
        item_layout.setSpacing(12)

        project_icon = QLabel()
        project_icon.setPixmap(QIcon("resources/icons/project_icon.png").pixmap(QSize(30, 30)))
        project_icon.setStyleSheet("border: none;")
        item_layout.addWidget(project_icon)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        project_name = QLabel(project["name"])
        project_name.setFont(QFont("Open Sans", 20, QFont.Normal))
        project_name.setStyleSheet("color: #000000; border: none;")

        project_path = QLabel(project["path"])
        project_path.setFont(QFont("Open Sans", 20, QFont.Normal))
        project_path.setStyleSheet("color: #000000; border: none;")

        info_layout.addWidget(project_name)
        info_layout.addWidget(project_path)
        item_layout.addLayout(info_layout, 1)

        menu_btn = QPushButton()
        menu_btn.setIcon(QIcon("resources/icons/menu_dots_icon.png"))
        menu_btn.setIconSize(QSize(18, 18))
        menu_btn.setFixedSize(28, 28)
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #EEF2F7;
                border-radius: 6px;
            }
        """)

        menu = QMenu(self)
        rename_action = menu.addAction(QIcon("resources/icons/rename_icon.png"), "Rename")
        duplicate_action = menu.addAction(QIcon("resources/icons/dublicate_icon.png"), "Duplicate")
        delete_action = menu.addAction(QIcon("resources/icons/delete_icon.png"), "Delete")

        rename_action.triggered.connect(lambda: self.rename_project_action(project["name"]))
        duplicate_action.triggered.connect(lambda: self.duplicate_project(project))
        delete_action.triggered.connect(lambda: self.delete_project(project))

        menu_btn.clicked.connect(lambda: menu.exec_(menu_btn.mapToGlobal(menu_btn.rect().bottomRight())))
        item_layout.addWidget(menu_btn)

        for child in item_frame.findChildren(QLabel):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        def open_project_on_click(event):
            if event.button() == Qt.LeftButton:
                self.load_project(project["path"])
            else:
                event.ignore()

        item_frame.mousePressEvent = open_project_on_click
        return item_frame

    def filter_projects(self, search_text):
        text = search_text.strip().lower()
        if not text:
            self.display_projects(self.all_projects)
            return
        filtered = [project for project in self.all_projects if text in project["name"].lower()]
        self.display_projects(filtered)

    def load_project(self, project_path):
        result = ProjectManager.load_project(project_path)
        if result is None:
            QMessageBox.critical(self, "Open project error", "Failed to open project.\nCheck the project folder structure.")
            return
        project, datastore = result
        self.main_window = MainWindow(project, self, datastore)
        self.main_window.show()
        self.hide()

    def rename_project_action(self, project_name):
        new_name, ok = QInputDialog.getText(self, "Rename Project", "New name:", text=project_name)
        if ok and new_name.strip():
            old_path = os.path.join(self.paths.projects_dir, project_name)
            new_path = os.path.join(self.paths.projects_dir, new_name.strip())
            try:
                os.rename(old_path, new_path)
                self.refresh_projects_list()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to rename: {exc}")

    def duplicate_project(self, project):
        import shutil

        copy_name = f"{project['name']}_copy"
        new_path = os.path.join(self.paths.projects_dir, copy_name)
        try:
            shutil.copytree(project["path"], new_path)
            self.refresh_projects_list()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Failed to duplicate: {exc}")

    def delete_project(self, project):
        reply = QMessageBox.question(
            self,
            "Delete Project",
            f"Are you sure you want to delete '{project['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            import shutil

            try:
                # Remove from custom projects if applicable
                if project.get("is_custom"):
                    self._remove_custom_project(project["path"])
                
                shutil.rmtree(project["path"])
                self.refresh_projects_list()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to delete: {exc}")

    def _load_version(self):
        version_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "version.json")
        try:
            with open(version_path, "r", encoding="utf-8") as version_file:
                data = json.load(version_file)
                version = str(data.get("version", "v.0.1-pre-release"))
                return version
        except Exception:
            return "v.0.1-pre-release"

    def go_home(self):
        self.refresh_projects_list()

    def new_project(self):
        if self.config.get("use_standard_dirs"):
            project = ProjectManager.create_default_project(self.paths)
            self.main_window = MainWindow(project, self)
            self.main_window.show()
            self.hide()
            return

        dialog = NewProjectDialog(self)
        if dialog.exec_():
            project = ProjectManager.create_custom_project(dialog.project_name, dialog.project_dir)
            # Add to custom projects tracking
            self._add_custom_project(dialog.project_dir)
            self.main_window = MainWindow(project, self)
            self.main_window.show()
            self.hide()

    def open_project(self):
        base_dir = QFileDialog.getExistingDirectory(
            self,
            "Open Project",
            self.paths.projects_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if base_dir:
            self.load_project(base_dir)

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        dialog.exec_()

    def open_about(self):
        self.about_window = AboutWindow(self)
        self.about_window.show()
