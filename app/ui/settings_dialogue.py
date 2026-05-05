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

        self.weighted_checkbox = PyQt5.QtWidgets.QCheckBox(
            "Weighted mode"
        )

        self.normalization_checkbox = PyQt5.QtWidgets.QCheckBox(
            "Normalization"
        )

        precision_layout = PyQt5.QtWidgets.QHBoxLayout()

        precision_label = PyQt5.QtWidgets.QLabel(
            "Decimal precision"
        )

        self.precision_spinbox = PyQt5.QtWidgets.QSpinBox()
        self.precision_spinbox.setRange(0, 10)

        precision_layout.addWidget(precision_label)
        precision_layout.addStretch()
        precision_layout.addWidget(self.precision_spinbox)

        self.layout.addWidget(self.standard_dirs_checkbox)
        self.layout.addWidget(self.weighted_checkbox)
        self.layout.addWidget(self.normalization_checkbox)
        self.layout.addLayout(precision_layout)

    def _load_values(self):

        self.standard_dirs_checkbox.setChecked(
            self.config.get("use_standard_dirs")
        )

        self.weighted_checkbox.setChecked(
            self.config.get("weighted_mode")
        )

        self.normalization_checkbox.setChecked(
            self.config.get("normalization")
        )

        self.precision_spinbox.setValue(
            self.config.get("decimal_precision")
        )

    def _connect_signals(self):

        self.standard_dirs_checkbox.stateChanged.connect(
            self._save
        )

        self.weighted_checkbox.stateChanged.connect(
            self._save
        )

        self.normalization_checkbox.stateChanged.connect(
            self._save
        )

        self.precision_spinbox.valueChanged.connect(
            self._save
        )

    def _save(self):

        self.config.set(
            "use_standard_dirs",
            self.standard_dirs_checkbox.isChecked()
        )

        self.config.set(
            "weighted_mode",
            self.weighted_checkbox.isChecked()
        )

        self.config.set(
            "normalization",
            self.normalization_checkbox.isChecked()
        )

        self.config.set(
            "decimal_precision",
            self.precision_spinbox.value()
        )

        self.config.save()