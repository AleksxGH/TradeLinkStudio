import PyQt5.QtWidgets


class SettingsDialog(PyQt5.QtWidgets.QDialog):

    def __init__(self, config, parent=None):
        super().__init__(parent)

        self.config = config

        self.setWindowTitle("Settings")
        self.resize(500, 300)

        self._init_ui()
        self._load_values()
        self._connect_signals()

    def _init_ui(self):

        self.layout = PyQt5.QtWidgets.QVBoxLayout(self)

        self.standard_dirs_checkbox = PyQt5.QtWidgets.QCheckBox(
            "Use standard directories"
        )

        self.layout.addWidget(self.standard_dirs_checkbox)

    def _load_values(self):

        self.standard_dirs_checkbox.setChecked(
            self.config.get("use_standard_dirs")
        )

    def _connect_signals(self):

        self.standard_dirs_checkbox.stateChanged.connect(
            self._save
        )

    def _save(self):

        self.config.set(
            "use_standard_dirs",
            self.standard_dirs_checkbox.isChecked()
        )

        self.config.save()