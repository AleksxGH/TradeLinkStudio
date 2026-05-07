import json
import os
import urllib.parse
import webbrowser

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QCheckBox,
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
    QStackedWidget,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.services.app_paths import AppPaths
from app.services.config_manager import ConfigManager
from app.services.project_manager import ProjectManager
from app.services.resource_utils import icon_path as resolve_icon_path, resource_path
from app.services.validators import validate_project_name
from app.ui.main_window import MainWindow
from app.ui.new_project_dialogue import NewProjectDialog


class HomeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.config.load()
        self.paths = AppPaths()
        self.all_projects = []
        self.main_window = None
        self.version_text = self._load_version()
        self.setWindowTitle("TradeLink Studio")
        self.resize(1360, 820)
        self.setWindowIcon(QIcon(resolve_icon_path("app.ico")))
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
        brand_icon.setPixmap(QIcon(resolve_icon_path("app.ico")).pixmap(QSize(80, 80)))
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
            (" Home", "main_menu_icon.png", self.go_home),
            (" New Project", "new_project_icon.png", self.new_project),
            (" Open Project", "open_project_icon.png", self.open_project),
            (" Settings", "settings_icon.png", self.open_settings),
        ]:
            button = self._menu_button(text, icon_path, callback)
            self.menu_buttons[text] = button
            left_layout.addWidget(button)

        left_layout.addStretch(1)

        help_button = self._menu_button(" Help", "about_icon.png", self.open_help)
        self.menu_buttons[" Help"] = help_button
        left_layout.addWidget(help_button)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(44, 32, 44, 32)
        right_layout.setSpacing(0)

        self.right_stack = QStackedWidget()
        self.home_page = self._build_home_page()
        self.settings_page = self._build_settings_page()
        self.help_page = self._build_help_page()

        self.right_stack.addWidget(self.home_page)
        self.right_stack.addWidget(self.settings_page)
        self.right_stack.addWidget(self.help_page)
        right_layout.addWidget(self.right_stack)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_container, 1)

    def _build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title_label = QLabel("Welcome to TradeLink Studio")
        title_label.setObjectName("appTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Open Sans", 40, QFont.Normal))
        title_label.setStyleSheet("color: #000000;")
        layout.addWidget(title_label)

        top_actions = QHBoxLayout()
        top_actions.setSpacing(44)
        top_actions.addStretch(1)
        top_actions.addWidget(self._action_card("new_project_icon.png", "New Project", self.new_project))
        top_actions.addWidget(self._action_card("open_project_icon.png", "Open Project", self.open_project))
        top_actions.addStretch(1)
        layout.addLayout(top_actions)

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
        search_row.addWidget(self._icon_label("search_icon.png", 30), 0, Qt.AlignVCenter)

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

        layout.addWidget(projects_frame, 1)
        return page

    def _build_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("Settings")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Open Sans", 44, QFont.Bold))
        title.setStyleSheet("color: #000000;")
        layout.addWidget(title)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #F7F8FB;
                border: 1px solid #D7DEEB;
                border-radius: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)

        self.standard_dirs_checkbox = QCheckBox("Use standard directories")
        self.standard_dirs_checkbox.setFont(QFont("Open Sans", 24, QFont.Normal))
        self.standard_dirs_checkbox.setStyleSheet("color: #000000;")
        self.standard_dirs_checkbox.setChecked(bool(self.config.get("use_standard_dirs")))
        self.standard_dirs_checkbox.stateChanged.connect(self._save_inline_settings)
        card_layout.addWidget(self.standard_dirs_checkbox)
        card_layout.addStretch(1)

        layout.addWidget(card, 1)
        return page

    def _build_help_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        title = QLabel("Help")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Open Sans", 44, QFont.Bold))
        title.setStyleSheet("color: #000000;")
        layout.addWidget(title)

        actions = QHBoxLayout()
        contact_button = QPushButton("Contact Support")
        contact_button.setStyleSheet("color: #000000;")
        contact_button.clicked.connect(self._contact_support)
        actions.addWidget(contact_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.help_browser = QTextBrowser()
        self.help_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #D7DEEB;
                border-radius: 10px;
                background-color: #E6E9EF;
            }
        """)

        try:
            html_path = resource_path("resources", "ui", "about.html")
            with open(html_path, "r", encoding="utf-8") as file:
                self.help_browser.setHtml(file.read())
        except Exception:
            self.help_browser.setText("Help content is unavailable.")

        layout.addWidget(self.help_browser, 1)
        return page

    def _save_inline_settings(self):
        self.config.set("use_standard_dirs", self.standard_dirs_checkbox.isChecked())
        self.config.save()

    def _contact_support(self):
        recipient = "admishchenko@edu.hse.ru"
        subject = "TradeLink Studio Support Request"
        body = "Describe your issue here"
        mailto_link = (
            f"mailto:{recipient}"
            f"?subject={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(body)}"
        )
        webbrowser.open(mailto_link)

    def _menu_button(self, text, icon_name, callback):
        button = QPushButton(text)
        button.setIcon(QIcon(icon_name if os.path.isabs(icon_name) else resolve_icon_path(icon_name)))
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

    def _action_card(self, icon_name, text, callback):
        card = QWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignHCenter)

        button = QToolButton()
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(QIcon(icon_name if os.path.isabs(icon_name) else resolve_icon_path(icon_name)))
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

    def _icon_label(self, icon_name, size=16):
        label = QLabel()
        label.setPixmap(QIcon(icon_name if os.path.isabs(icon_name) else resolve_icon_path(icon_name)).pixmap(QSize(size, size)))
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

    def _resolve_custom_project_entry(self, entry_path):
        """Return project directories for a stored entry (supports legacy parent-folder entries)."""
        resolved = []
        abs_path = os.path.abspath(entry_path)

        # Entry is already a project directory
        if os.path.isdir(abs_path) and os.path.exists(os.path.join(abs_path, "data", "project.json")):
            return [abs_path]

        # Legacy mode: entry points to a parent directory; scan one level deep
        if os.path.isdir(abs_path):
            try:
                for child in os.listdir(abs_path):
                    child_path = os.path.join(abs_path, child)
                    if os.path.isdir(child_path) and os.path.exists(os.path.join(child_path, "data", "project.json")):
                        resolved.append(child_path)
            except Exception:
                return []

        return resolved

    def _remove_custom_project(self, project_path):
        """Remove a custom project path from user_data.json"""
        custom_projects = self._load_user_data()
        abs_path = os.path.abspath(project_path)
        if abs_path in custom_projects:
            custom_projects.remove(abs_path)
            self._save_user_data(custom_projects)

    def _is_default_project_path(self, project_path):
        projects_root = os.path.abspath(self.paths.projects_dir)
        project_abs = os.path.abspath(project_path)
        try:
            return os.path.commonpath([projects_root, project_abs]) == projects_root
        except ValueError:
            return False

    def _ensure_project_registered(self, project_path):
        """Register project in user_data.json if it's outside default directory (idempotent)."""
        if not self._is_default_project_path(project_path):
            self._add_custom_project(project_path)

    def _ensure_project_unregistered(self, project_path):
        """Unregister project from user_data.json if it's a custom project (idempotent, safe)."""
        self._remove_custom_project(project_path)

    def _next_copy_name(self, base_name, parent_dir):
        copy_name = f"{base_name}_copy"
        if not os.path.exists(os.path.join(parent_dir, copy_name)):
            return copy_name

        copy_index = 2
        while True:
            candidate = f"{base_name}_copy_{copy_index}"
            if not os.path.exists(os.path.join(parent_dir, candidate)):
                return candidate
            copy_index += 1

    def _update_project_json_title(self, project_dir, new_title):
        project_file = os.path.join(project_dir, "data", "project.json")
        try:
            if not os.path.exists(project_file):
                return
            with open(project_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["title"] = new_title
            with open(project_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            # Non-critical: copied directory is still usable via folder name.
            pass

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
        seen_paths = {os.path.abspath(project["path"]) for project in self.all_projects}
        for custom_entry in custom_projects:
            resolved_paths = self._resolve_custom_project_entry(custom_entry)
            for custom_path in resolved_paths:
                abs_custom_path = os.path.abspath(custom_path)
                if abs_custom_path in seen_paths:
                    continue
                project_name = os.path.basename(abs_custom_path)
                self.all_projects.append({"name": project_name, "path": abs_custom_path, "is_custom": True})
                valid_custom_projects.append(abs_custom_path)
                seen_paths.add(abs_custom_path)
        
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
        project_icon.setPixmap(QIcon(resolve_icon_path("project_icon.png")).pixmap(QSize(30, 30)))
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
        menu_btn.setIcon(QIcon(resolve_icon_path("menu_dots_icon.png")))
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
        rename_action = menu.addAction(QIcon(resolve_icon_path("rename_icon.png")), "Rename")
        duplicate_action = menu.addAction(QIcon(resolve_icon_path("dublicate_icon.png")), "Duplicate")
        delete_action = menu.addAction(QIcon(resolve_icon_path("delete_icon.png")), "Delete")

        rename_action.triggered.connect(lambda: self.rename_project_action(project))
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
        filtered = [
            project
            for project in self.all_projects
            if text in project["name"].lower() or text in project["path"].lower()
        ]
        self.display_projects(filtered)

    def load_project(self, project_path):
        result = ProjectManager.load_project(project_path)
        if result is None:
            QMessageBox.critical(self, "Open project error", "Failed to open project.\nCheck the project folder structure.")
            return

        project, datastore = result
        self._ensure_project_registered(project.project_dir)

        self.main_window = MainWindow(project, self, datastore)
        self.main_window.show()
        self.hide()

    def rename_project_action(self, project):
        old_name = project["name"]
        old_path = os.path.abspath(project["path"])
        parent_dir = os.path.dirname(old_path)

        new_name, ok = QInputDialog.getText(self, "Rename Project", "New name:", text=old_name)
        if ok and new_name.strip():
            is_valid_name, error_message, normalized_name = validate_project_name(new_name)
            if not is_valid_name:
                QMessageBox.warning(self, "Error", error_message)
                return
            new_path = os.path.join(parent_dir, normalized_name)

            if os.path.abspath(new_path) == old_path:
                return

            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "Project with this name already exists in this directory.")
                return

            try:
                os.rename(old_path, new_path)
                self._ensure_project_unregistered(old_path)
                self._ensure_project_registered(new_path)
                self._update_project_json_title(new_path, normalized_name)
                self.refresh_projects_list()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to rename: {exc}")

    def duplicate_project(self, project):
        import shutil

        source_path = os.path.abspath(project["path"])
        parent_dir = os.path.dirname(source_path)
        copy_name = self._next_copy_name(project["name"], parent_dir)
        new_path = os.path.join(parent_dir, copy_name)

        try:
            shutil.copytree(source_path, new_path)
            self._ensure_project_registered(new_path)
            self._update_project_json_title(new_path, copy_name)
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
                self._ensure_project_unregistered(project["path"])
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
        self.right_stack.setCurrentWidget(self.home_page)
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
            self._ensure_project_registered(project.project_dir)
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
        self.standard_dirs_checkbox.blockSignals(True)
        self.standard_dirs_checkbox.setChecked(bool(self.config.get("use_standard_dirs")))
        self.standard_dirs_checkbox.blockSignals(False)
        self.right_stack.setCurrentWidget(self.settings_page)

    def open_help(self):
        self.right_stack.setCurrentWidget(self.help_page)
