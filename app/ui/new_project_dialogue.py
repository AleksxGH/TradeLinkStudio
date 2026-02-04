import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox
)

class NewProjectDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        self.setWindowTitle("Create New Project")
        self.resize(500, 200)

        self.project_name = None
        self.project_dir = None

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # ---- Project name ----
        layout.addWidget(QLabel("Project name:"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter project name")
        layout.addWidget(self.name_input)

        # ---- Directory ----
        layout.addWidget(QLabel("Project directory:"))

        dir_layout = QHBoxLayout()

        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select folder")

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_folder)

        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)

        layout.addLayout(dir_layout)

        # ---- Buttons ----
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("Create")
        cancel_btn = QPushButton("Cancel")

        ok_btn.clicked.connect(self._validate)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)


    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select project folder")

        if folder:
            self.dir_input.setText(folder)

    def _validate(self):
        name = self.name_input.text().strip()
        directory = self.dir_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Project name cannot be empty")
            return

        if not directory:
            QMessageBox.warning(self, "Error", "Select project directory")
            return

        # Проверяем допустимость имени папки
        invalid_chars = r'<>:"/\|?*'
        if any(c in name for c in invalid_chars):
            QMessageBox.warning(
                self,
                "Error",
                "Project name contains invalid characters"
            )
            return

        full_path = os.path.join(directory, name)

        if os.path.exists(full_path):
            QMessageBox.warning(
                self,
                "Error",
                "Project with this name already exists"
            )
            return

        # Сохраняем результат
        self.project_name = name
        self.project_dir = directory

        self.accept()