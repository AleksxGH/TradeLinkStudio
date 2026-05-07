import pandas as pd
import copy
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableView,
    QLabel,
    QSplitter,
    QSpinBox,
    QDialog,
    QLineEdit,
    QInputDialog,
    QScrollArea,
    QProgressBar
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from app.data.exporter import save_results
from app.data.loader import read_data
from app.core.project import Project
from app.core.engine import ComputeEngine
from app.services.config_manager import ConfigManager
from app.services.data_controller import DataController
from app.services.project_manager import ProjectManager
from app.services.resource_utils import icon_path
from app.services.validators import validate_project_name, validate_vertex_names
from app.ui.dataframe_model import DataFrameModel
from app.core.datastore import DataStore
from app.services.logging_service import log_debug, log_error


class _TaskWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, task):
        super().__init__()
        self._task = task

    def run(self):
        try:
            self.finished.emit(self._task())
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):

    def __init__(self, current_project: Project, parent=None, datastore=None):

        super().__init__()

        self.parent_window = parent

        self.project = current_project
        
        self.config = ConfigManager()
        self.config.load()

        self.datastore = datastore if datastore is not None else DataStore()
        self.controller = DataController(
            self.project,
            self.datastore,
            ComputeEngine(),
            self.config
        )
        
        # Флаг для отслеживания изменений
        self.is_dirty = False
        self._busy_thread = None
        self._busy_worker = None

        self.project.decimal_precision = getattr(self.project, "decimal_precision", 6)
        self.project.show_weighted_pivotal = getattr(self.project, "show_weighted_pivotal", True)
        self.project.show_normalized = getattr(self.project, "show_normalized", True)

        self.setWindowTitle(f"TradeLink Studio - {self.project.title}")
        self.resize(1400, 800)
        self.setWindowIcon(QIcon(icon_path("app.ico")))

        self._init_ui()
        
        # Инициализация пустых таблиц для нового проекта
        self._initialize_empty_tables()

    def _init_ui(self):

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # ===== TOOLBAR =====
        button_layout = QHBoxLayout()

        self.home_button = QPushButton("Home")
        self.load_button = QPushButton("Load data")
        
        # Создаём кнопки undo/redo с иконками
        self.undo_button = QPushButton()
        self.undo_button.setIcon(QIcon(icon_path("undo.png")))
        self.undo_button.setToolTip("Undo (Ctrl+Z)")
        
        self.redo_button = QPushButton()
        self.redo_button.setIcon(QIcon(icon_path("redo.png")))
        self.redo_button.setToolTip("Redo (Ctrl+Y)")
        
        self.calc_button = QPushButton("Calculate indices")
        self.export_button = QPushButton()
        self.export_button.setIcon(QIcon(icon_path("export_icon.png")))
        self.export_button.setToolTip("Export")
        
        self.save_button = QPushButton()
        self.save_button.setIcon(QIcon(icon_path("save.png")))
        self.save_button.setToolTip("Save project")
        
        self.rename_vertices_button = QPushButton("Rename Vertices")

        for button in [
            self.home_button,
            self.load_button,
            self.calc_button,
            self.rename_vertices_button,
        ]:
            self._mark_main_action_button(button)

        for button in [self.undo_button, self.redo_button, self.export_button, self.save_button]:
            self._mark_icon_action_button(button)

        self.calc_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.undo_button.setEnabled(False)
        self.redo_button.setEnabled(False)
        
        # Сделаем кнопки undo/redo и save квадратными и компактными
        self.undo_button.setMaximumWidth(40)
        self.undo_button.setMaximumHeight(40)
        self.redo_button.setMaximumWidth(40)
        self.redo_button.setMaximumHeight(40)
        self.export_button.setMaximumWidth(40)
        self.export_button.setMaximumHeight(40)
        self.save_button.setMaximumWidth(40)
        self.save_button.setMaximumHeight(40)

        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)
        button_layout.addWidget(self.calc_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # ===== STATUS LABEL =====
        status_layout = QHBoxLayout()
        self.status_label = QLabel("No data loaded")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setFixedWidth(160)
        self.loading_bar.hide()

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.loading_bar)
        main_layout.addLayout(status_layout)

        # ===== SUBSET SIZE CONTROL =====
        subset_layout = QHBoxLayout()
        subset_label = QLabel("Subset size (k):")
        self.subset_spinbox = QSpinBox()
        self.subset_spinbox.setMinimum(1)
        self.subset_spinbox.setMaximum(100)
        self.subset_spinbox.setValue(2)
        self.subset_spinbox.setEnabled(False)
        self.subset_spinbox.valueChanged.connect(self._on_subset_size_changed)
        
        subset_layout.addWidget(subset_label)
        subset_layout.addWidget(self.subset_spinbox)

        precision_label = QLabel("Precision:")
        self.precision_spinbox = QSpinBox()
        self.precision_spinbox.setMinimum(0)
        self.precision_spinbox.setMaximum(10)
        self.precision_spinbox.setValue(self.project.decimal_precision)
        self.precision_spinbox.valueChanged.connect(self._on_precision_changed)

        subset_layout.addWidget(precision_label)
        subset_layout.addWidget(self.precision_spinbox)
        subset_layout.addStretch()
        main_layout.addLayout(subset_layout)

        # ===== QUOTAS (TOP) =====
        quotas_label = QLabel("Quotas:")
        quotas_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(quotas_label)

        self.quotas_table = QTableView()
        self._configure_data_table(self.quotas_table)
        self.quotas_table.setMaximumHeight(80)
        main_layout.addWidget(self.quotas_table)

        # ===== SPLITTER: Matrix (LEFT) | Indices (RIGHT) =====
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Input Matrix
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        input_label = QLabel("Input Matrix:")
        input_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(input_label)
        
        # Buttons for expanding/shrinking matrix
        matrix_controls_layout = QHBoxLayout()
        self._mark_main_action_button(self.rename_vertices_button)
        self.expand_matrix_button = QPushButton("Expand Matrix")
        self.shrink_matrix_button = QPushButton("Shrink Matrix")
        self._mark_main_action_button(self.expand_matrix_button)
        self._mark_main_action_button(self.shrink_matrix_button)
        self.rename_vertices_button.clicked.connect(self._rename_vertices)
        self.expand_matrix_button.clicked.connect(self._expand_matrix)
        self.shrink_matrix_button.clicked.connect(self._shrink_matrix)
        matrix_controls_layout.addWidget(self.rename_vertices_button)
        matrix_controls_layout.addWidget(self.expand_matrix_button)
        matrix_controls_layout.addWidget(self.shrink_matrix_button)
        matrix_controls_layout.addStretch()
        left_layout.addLayout(matrix_controls_layout)

        self.matrix_table = QTableView()
        self._configure_data_table(self.matrix_table)
        left_layout.addWidget(self.matrix_table)

        splitter.addWidget(left_container)

        # Right side: Indices
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        indices_label = QLabel("Calculated Indices:")
        indices_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(indices_label)

        indices_controls_layout = QHBoxLayout()
        self.weighted_visibility_button = QPushButton("Show/Hide PI's weighted version")
        self.weighted_visibility_button.setCheckable(True)
        self.weighted_visibility_button.setChecked(self.project.show_weighted_pivotal)
        self.weighted_visibility_button.clicked.connect(self._on_indices_visibility_changed)
        self._mark_main_action_button(self.weighted_visibility_button)

        self.normalized_visibility_button = QPushButton("Show/Hide normalized columns")
        self.normalized_visibility_button.setCheckable(True)
        self.normalized_visibility_button.setChecked(self.project.show_normalized)
        self.normalized_visibility_button.clicked.connect(self._on_indices_visibility_changed)
        self._mark_main_action_button(self.normalized_visibility_button)

        indices_controls_layout.addWidget(self.weighted_visibility_button)
        indices_controls_layout.addWidget(self.normalized_visibility_button)
        indices_controls_layout.addStretch()
        right_layout.addLayout(indices_controls_layout)

        self.indices_table = QTableView()
        self._configure_data_table(self.indices_table)
        right_layout.addWidget(self.indices_table)

        splitter.addWidget(right_container)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter, 1)

        # Connect buttons
        self.home_button.clicked.connect(self.to_home)
        self.load_button.clicked.connect(self.upload_data)
        self.undo_button.clicked.connect(self.on_undo)
        self.redo_button.clicked.connect(self.on_redo)
        self.calc_button.clicked.connect(self.calculate_indices)
        self.export_button.clicked.connect(self.export_data)
        self.save_button.clicked.connect(self.save_project)

    def _mark_main_action_button(self, button):
        button.setProperty("mainAction", "true")
        button.style().unpolish(button)
        button.style().polish(button)

    def _mark_icon_action_button(self, button):
        button.setProperty("iconAction", "true")
        button.style().unpolish(button)
        button.style().polish(button)

    def _configure_data_table(self, table):
        table.setAlternatingRowColors(True)
        table.setObjectName("dataTable")
        table.style().unpolish(table)
        table.style().polish(table)

    def _dataframe_from_split(self, split_data):
        if not split_data:
            return pd.DataFrame()

        try:
            return pd.DataFrame(
                split_data.get("data", []),
                index=split_data.get("index", []),
                columns=split_data.get("columns", []),
            )
        except Exception:
            return pd.DataFrame()

    def _build_indices_dataframe(self, result, vertices, subset_size):
        data = {}
        data["Copeland"] = [result.get("copeland", {}).get(vertex, 0) for vertex in vertices]
        data["Copeland (norm)"] = result.get("copeland_norm", [])

        bundle_col = f"BI (s={subset_size})"
        data[bundle_col] = [result.get("bundle", {}).get(vertex, 0) for vertex in vertices]
        data[f"{bundle_col} (norm)"] = result.get("bundle_norm", [])

        pivotal_col = f"PI (s={subset_size})"
        data[pivotal_col] = [result.get("pivotal", {}).get(vertex, 0) for vertex in vertices]
        data[f"{pivotal_col} (norm)"] = result.get("pivotal_norm", [])

        pi_prime_col = f"PI' (w, s={subset_size})"
        data[pi_prime_col] = [result.get("pi_prime", {}).get(vertex, 0) for vertex in vertices]
        data[f"{pi_prime_col} (norm)"] = result.get("pi_prime_norm", [])

        return pd.DataFrame(data, index=vertices)

    def _apply_indices_visibility(self, full_df, precision=None, include_weighted=None, include_normalized=None):
        if full_df is None or full_df.empty:
            return pd.DataFrame()

        if precision is None:
            precision = self.precision_spinbox.value() if hasattr(self, "precision_spinbox") else 6

        if include_weighted is None:
            include_weighted = self.weighted_visibility_button.isChecked() if hasattr(self, "weighted_visibility_button") else True

        if include_normalized is None:
            include_normalized = self.normalized_visibility_button.isChecked() if hasattr(self, "normalized_visibility_button") else True

        visible_columns = []
        for column in full_df.columns:
            is_weighted_column = column.startswith("PI'")
            is_normalized_column = column.endswith(" (norm)")

            if is_weighted_column and not include_weighted:
                continue

            if is_normalized_column:
                if not include_normalized:
                    continue

                if is_weighted_column and not include_weighted:
                    continue

            visible_columns.append(column)

        view_df = full_df.loc[:, visible_columns].copy()
        return view_df.round(precision)

    def _update_indices_visibility_controls(self):
        self.weighted_visibility_button.setEnabled(True)
        self.normalized_visibility_button.setEnabled(True)
        self._update_indices_visibility_button_texts()

    def _update_indices_visibility_button_texts(self):
        return

    def _set_loading_state(self, is_loading, message=None):
        if is_loading:
            if message:
                self.status_label.setText(message)
            self.loading_bar.show()
            for widget in (
                self.home_button,
                self.load_button,
                self.undo_button,
                self.redo_button,
                self.calc_button,
                self.export_button,
                self.save_button,
                self.rename_vertices_button,
                self.expand_matrix_button,
                self.shrink_matrix_button,
                self.weighted_visibility_button,
                self.normalized_visibility_button,
                self.precision_spinbox,
                self.subset_spinbox,
            ):
                widget.setEnabled(False)
            QApplication.processEvents()
            return

        self.loading_bar.hide()

    def _start_background_task(self, task, busy_message, success_handler, error_handler=None):
        if self._busy_thread is not None:
            return

        self._set_loading_state(True, busy_message)

        thread = QThread(self)
        worker = _TaskWorker(task)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(success_handler)
        worker.failed.connect(error_handler if error_handler is not None else self._handle_background_task_error)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_background_task_refs)

        self._busy_thread = thread
        self._busy_worker = worker
        thread.start()

    def _clear_background_task_refs(self):
        self._busy_thread = None
        self._busy_worker = None

    def _restore_controls_after_background_task(self):
        self.loading_bar.hide()
        self.home_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.rename_vertices_button.setEnabled(True)
        self.expand_matrix_button.setEnabled(True)
        self.shrink_matrix_button.setEnabled(True)
        self.weighted_visibility_button.setEnabled(True)
        self.normalized_visibility_button.setEnabled(True)
        self.precision_spinbox.setEnabled(True)
        self.subset_spinbox.setEnabled(True)
        self._update_undo_redo_buttons()

    def _handle_background_task_error(self, error_message):
        self._restore_controls_after_background_task()
        QMessageBox.critical(self, "Error", error_message)

    def _sync_indices_state(self, target_state=None):
        current_state = target_state if target_state is not None else self.datastore.current()
        if current_state is None:
            return

        current_state["decimal_precision"] = self.precision_spinbox.value()
        current_state["show_weighted_pivotal"] = self.weighted_visibility_button.isChecked()
        current_state["show_normalized"] = self.normalized_visibility_button.isChecked()

        if self.project.results_full_df is not None:
            current_state["indices_full"] = self.project.results_full_df.to_dict(orient="split")

        if self.project.results_df is not None:
            current_state["indices"] = self.project.results_df.to_dict(orient="split")

    def _refresh_indices_view(self):
        current_state = self.datastore.current()
        if current_state is None:
            return

        full_split = current_state.get("indices_full") or current_state.get("indices")
        full_df = self._dataframe_from_split(full_split)
        if full_df.empty:
            return

        self._show_indices(current_state)

    def _on_precision_changed(self, value):
        self.project.decimal_precision = value
        self.project.is_dirty = True
        self.save_button.setEnabled(True)
        current_state = self.datastore.current()
        if current_state is None:
            return

        new_state = copy.deepcopy(current_state)
        new_state["decimal_precision"] = value
        self._sync_indices_state(new_state)
        state_changed = self.datastore.push(new_state)
        self._show_indices(new_state)
        self.indices_table.viewport().update()
        QApplication.processEvents()
        if state_changed:
            self.project.is_dirty = True
            self.save_button.setEnabled(True)
        self._update_undo_redo_buttons()

    def _on_indices_visibility_changed(self):
        self.project.show_weighted_pivotal = self.weighted_visibility_button.isChecked()
        self.project.show_normalized = self.normalized_visibility_button.isChecked()
        self.project.is_dirty = True
        self.save_button.setEnabled(True)
        current_state = self.datastore.current()
        if current_state is None:
            return

        new_state = copy.deepcopy(current_state)
        new_state["show_weighted_pivotal"] = self.project.show_weighted_pivotal
        new_state["show_normalized"] = self.project.show_normalized
        self._sync_indices_state(new_state)
        state_changed = self.datastore.push(new_state)
        self._show_indices(new_state)
        self.indices_table.viewport().update()
        QApplication.processEvents()
        if state_changed:
            self.is_dirty = True
            self.project.is_dirty = True
            self.save_button.setEnabled(True)
            self._update_calc_button()
        self._update_undo_redo_buttons()



    def to_home(self):

        if not self.is_dirty and not self.project.is_dirty:
            self.parent_window.refresh_projects_list()
            self.parent_window.show()
            self.close()
            return

        reply = QMessageBox.question(
            self,
            "Unsaved project",
            "Save project before leaving?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Cancel:
            return

        if reply == QMessageBox.Yes:
            ProjectManager.save_project(self.project, self.datastore)

        self.parent_window.refresh_projects_list()
        self.parent_window.show()
        self.close()

    def upload_data(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "Data files (*.csv *.xlsx)"
        )

        if not file_path:
            return

        def task():
            return read_data(file_path)

        def on_success(result):
            _df, vertices, subset_size, quotas, graph = result

            state = {
                "matrix": graph,
                "vertices": vertices,
                "quotas": quotas,
                "subset_size": subset_size,
                "decimal_precision": self.precision_spinbox.value(),
                "show_weighted_pivotal": self.weighted_visibility_button.isChecked(),
                "show_normalized": self.normalized_visibility_button.isChecked(),
                "project_title": self.project.title,
            }

            state_changed = self.datastore.push(state)

            self._show_quotas(quotas, vertices)
            self._show_matrix(graph, vertices)

            self.subset_spinbox.setEnabled(True)
            self.subset_spinbox.setMaximum(len(vertices))
            self.subset_spinbox.blockSignals(True)
            self.subset_spinbox.setValue(subset_size)
            self.subset_spinbox.blockSignals(False)

            self.precision_spinbox.blockSignals(True)
            self.precision_spinbox.setValue(self.project.decimal_precision)
            self.precision_spinbox.blockSignals(False)

            self._update_indices_visibility_controls()

            self.save_button.setEnabled(True)
            self.calc_button.setEnabled(True)
            self.export_button.setEnabled(False)
            self.is_dirty = False
            self.project.is_dirty = False
            self.project.computed = False
            self.project.quotas = quotas
            self.project.vertices = vertices
            self.project.subset_size = subset_size
            self.project.decimal_precision = self.precision_spinbox.value()
            self.project.show_weighted_pivotal = self.weighted_visibility_button.isChecked()
            self.project.show_normalized = self.normalized_visibility_button.isChecked()

            self.status_label.setText(f"Loaded: {file_path} | Vertices: {len(vertices)}")
            self._restore_controls_after_background_task()
            self._update_undo_redo_buttons()

            QMessageBox.information(self, "Success", "File uploaded")

        def on_error(error_message):
            self._restore_controls_after_background_task()
            log_error(f"Error uploading file {file_path}: {error_message}")
            QMessageBox.critical(self, "Error", error_message)

        self._start_background_task(task, f"Loading: {file_path}", on_success, on_error)

    def calculate_indices(self):
        """Вычисляет индексы из текущего состояния таблиц"""
        state = self.datastore.current()
        if not state:
            QMessageBox.warning(self, "Error", "No data loaded")
            return

        try:
            quotas_df = self.quotas_model.get_dataframe()
            matrix_df = self.matrix_model.get_dataframe()

            quotas = {col: quotas_df.at[0, col] for col in quotas_df.columns}

            import networkx as nx
            vertices = list(matrix_df.index)
            graph = nx.DiGraph()

            for vertex in vertices:
                graph.add_node(vertex)

            for i, source in enumerate(vertices):
                for j, target in enumerate(vertices):
                    weight = matrix_df.iat[i, j]
                    if weight != 0:
                        graph.add_edge(source, target, weight=weight)

            new_state = {
                "quotas": quotas,
                "matrix": graph,
                "subset_size": self.subset_spinbox.value(),
                "vertices": vertices,
                "project_title": self.project.title,
                "decimal_precision": self.precision_spinbox.value(),
                "show_weighted_pivotal": self.weighted_visibility_button.isChecked(),
                "show_normalized": self.normalized_visibility_button.isChecked(),
            }

            state_changed = self.datastore.push(new_state)
            working_state = copy.deepcopy(new_state)

        except Exception as e:
            log_error(f"Error preparing indices calculation: {e}")
            QMessageBox.critical(self, "Error", f"Error calculating indices:\n{str(e)}")
            return

        def task():
            return self.controller.engine.compute(working_state, self.config)

        def on_success(result):
            if result is None:
                self._restore_controls_after_background_task()
                QMessageBox.warning(self, "Error", "Failed to calculate indices")
                return

            vertices_local = new_state.get("vertices", [])
            subset_size = new_state.get("subset_size", 0)
            full_df = self._build_indices_dataframe(result, vertices_local, subset_size)

            current_state = self.datastore.current()
            if current_state is not None:
                current_state["decimal_precision"] = self.precision_spinbox.value()
                current_state["show_weighted_pivotal"] = self.weighted_visibility_button.isChecked()
                current_state["show_normalized"] = self.normalized_visibility_button.isChecked()
                current_state["indices_full"] = full_df.to_dict(orient="split")

            self._show_indices(current_state)

            self.project.results_df = self.indices_table.model().get_dataframe() if hasattr(self.indices_table.model(), "get_dataframe") else None
            self.project.results_full_df = full_df
            self.project.vertices = vertices_local
            self.project.quotas = quotas
            self.project.subset_size = subset_size
            self.project.decimal_precision = self.precision_spinbox.value()
            self.project.show_weighted_pivotal = self.weighted_visibility_button.isChecked()
            self.project.show_normalized = self.normalized_visibility_button.isChecked()
            self.project.computed = True

            if current_state is not None and self.project.results_df is not None:
                current_state["indices"] = self.project.results_df.to_dict(orient="split")

            self.is_dirty = False
            self.project.is_dirty = True
            self.save_button.setEnabled(True)
            self.export_button.setEnabled(self.project.results_df is not None and not self.project.results_df.empty)
            self._restore_controls_after_background_task()
            self._update_calc_button()
            self._update_undo_redo_buttons()

        def on_error(error_message):
            self._restore_controls_after_background_task()
            log_error(f"Error calculating indices: {error_message}")
            QMessageBox.critical(self, "Error", f"Error calculating indices:\n{error_message}")

        self._start_background_task(task, "Calculating indices...", on_success, on_error)

    def _on_subset_size_changed(self, value):
        """Отмечает данные как грязные при изменении subset_size"""
        current_state = self.datastore.current()
        if current_state is not None:
            new_state = copy.deepcopy(current_state)
            self._sync_current_state_from_ui(new_state)
            state_changed = self.datastore.push(new_state)
            if state_changed:
                self.is_dirty = True
                self.project.is_dirty = True
                self.project.computed = False
                self.project.results_df = None
                self.export_button.setEnabled(False)
        self._update_calc_button()
        self._update_undo_redo_buttons()

    def _mark_data_dirty(self):
        """Отмечает данные как грязные и обновляет статус кнопки"""
        current_state = self.datastore.current()
        if current_state is not None:
            new_state = copy.deepcopy(current_state)
            self._sync_current_state_from_ui(new_state)
            state_changed = self.datastore.push(new_state)
            if state_changed:
                self.is_dirty = True
                self.project.is_dirty = True
                self.project.computed = False
                self.project.results_df = None
                self.export_button.setEnabled(False)
        self._update_calc_button()
        self._update_undo_redo_buttons()

    def _update_calc_button(self):
        """Обновляет статус кнопки Calculate в зависимости от is_dirty"""
        self.calc_button.setEnabled(self.is_dirty)

    def _update_undo_redo_buttons(self):
        """Обновляет статус кнопок Undo/Redo"""
        self.undo_button.setEnabled(self.controller.can_undo())
        self.redo_button.setEnabled(self.controller.can_redo())

    def on_undo(self):
        """Отмена последнего изменения"""
        state = self.controller.undo()
        if state is None:
            QMessageBox.information(self, "Undo", "Nothing to undo")
            return

        # Применяем состояние к UI (включая precision и флаги видимости)
        self._apply_state_to_ui(state)
        # Принудительно обновляем spinbox виджеты
        self.precision_spinbox.update()
        self.subset_spinbox.update()
        
        # Обрабатываем все pending события для визуального обновления
        QApplication.processEvents()

        # Убедимся, что текущее состояние datastore содержит ключи precision/subset/flags
        try:
            current = self.datastore.current()
            if current is not None:
                if "decimal_precision" in state:
                    current["decimal_precision"] = state.get("decimal_precision")
                if "subset_size" in state:
                    current["subset_size"] = state.get("subset_size")
                if "show_weighted_pivotal" in state:
                    current["show_weighted_pivotal"] = state.get("show_weighted_pivotal")
                if "show_normalized" in state:
                    current["show_normalized"] = state.get("show_normalized")
        except Exception:
            pass

        # Попробуем пересчитать индексы, если требуется (не прерываем работу при ошибке)
        try:
            self.controller.recompute()
        except Exception:
            pass

        self._update_undo_redo_buttons()
        self.is_dirty = True
        self._update_calc_button()

    def on_redo(self):
        """Повтор отменённого изменения"""
        state = self.controller.redo()
        if state is None:
            QMessageBox.information(self, "Redo", "Nothing to redo")
            return

        self._apply_state_to_ui(state)
        # Принудительно обновляем spinbox виджеты
        self.precision_spinbox.update()
        self.subset_spinbox.update()
        
        # Обрабатываем все pending события для визуального обновления
        QApplication.processEvents()
        try:
            current = self.datastore.current()
            if current is not None:
                if "decimal_precision" in state:
                    current["decimal_precision"] = state.get("decimal_precision")
                if "subset_size" in state:
                    current["subset_size"] = state.get("subset_size")
                if "show_weighted_pivotal" in state:
                    current["show_weighted_pivotal"] = state.get("show_weighted_pivotal")
                if "show_normalized" in state:
                    current["show_normalized"] = state.get("show_normalized")
        except Exception:
            pass

        try:
            self.controller.recompute()
        except Exception:
            pass

        self._update_undo_redo_buttons()
        self.is_dirty = True
        self._update_calc_button()






    def export_data(self):

        self._sync_current_state_from_ui()

        current_state = self.datastore.current()
        if current_state is not None and self.indices_table.model() is not None:
            indices_model = self.indices_table.model()
            if hasattr(indices_model, "get_dataframe"):
                self.project.results_df = indices_model.get_dataframe()
                self.project.vertices = current_state.get("vertices", [])
                self.project.quotas = current_state.get("quotas", {})
                self.project.subset_size = current_state.get("subset_size", self.subset_spinbox.value())

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "Excel files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            save_results(
                project=self.project,
                file_path=file_path,
                matrix=current_state.get("matrix") if current_state is not None else None
            )

            QMessageBox.information(
                self,
                "Export",
                f"Saved to:\n{file_path}"
            )

        except Exception as e:
            log_error(f"Export error saving to {file_path}: {e}")
            QMessageBox.critical(self, "Export Error", str(e))

    def save_project(self):

        try:
            self._sync_current_state_from_ui()

            ProjectManager.save_project(
                self.project,
                self.datastore
            )

            self.is_dirty = False
            self.project.is_dirty = False

            QMessageBox.information(
                self,
                "Saving",
                f"Project {self.project.title} saved"
            )
        except Exception as e:
            log_error(f"Saving project {self.project.title} failed: {e}")
            QMessageBox.critical(self, "Saving Error", str(e))

    def _show_quotas(self, quotas, vertices):
        """Отображает квоты вершин (редактируемая таблица)"""
        import pandas as pd

        quotas_data = {vertex: quotas.get(vertex, 0) for vertex in vertices}

        df = pd.DataFrame(
            [quotas_data],
            columns=vertices
        )

        self.quotas_model = DataFrameModel(df, editable=True, on_change=self._mark_data_dirty)
        self.quotas_table.setModel(self.quotas_model)
        self.quotas_table.resizeColumnsToContents()

    def _show_matrix(self, matrix, vertices):
        """Отображает матрицу входных данных (редактируемая таблица)"""
        import networkx as nx

        if isinstance(matrix, nx.DiGraph):
            matrix_array = nx.to_numpy_array(matrix, nodelist=vertices)
        else:
            matrix_array = matrix

        df = pd.DataFrame(
            matrix_array,
            index=vertices,
            columns=vertices
        )

        self.matrix_model = DataFrameModel(df, editable=True, on_change=self._mark_data_dirty)
        self.matrix_table.setModel(self.matrix_model)
        self.matrix_table.resizeColumnsToContents()

    def _show_indices(self, state):
        """Отображает вычисленные индексы с учетом текущих флагов видимости и precision."""
        if not state:
            self.indices_table.setModel(DataFrameModel(pd.DataFrame(), editable=False, precision=self.precision_spinbox.value()))
            self.export_button.setEnabled(False)
            self.project.results_df = None
            self.project.results_full_df = None
            self.project.vertices = []
            self.project.quotas = {}
            self.project.subset_size = 0
            self.project.computed = False
            return

        full_split = state.get("indices_full") or state.get("indices")
        full_df = self._dataframe_from_split(full_split)
        if full_df.empty:
            self.indices_table.setModel(DataFrameModel(pd.DataFrame(), editable=False, precision=self.precision_spinbox.value()))
            self.export_button.setEnabled(False)
            self.project.results_df = None
            self.project.results_full_df = None
            self.project.computed = False
            return

        precision = state.get("decimal_precision", self.precision_spinbox.value())
        show_weighted = state.get("show_weighted_pivotal", self.weighted_visibility_button.isChecked())
        show_normalized = state.get("show_normalized", self.normalized_visibility_button.isChecked())

        df = self._apply_indices_visibility(
            full_df,
            precision=precision,
            include_weighted=show_weighted,
            include_normalized=show_normalized,
        )

        self.indices_table.setModel(DataFrameModel(df, editable=False, precision=precision))
        self.indices_table.resizeColumnsToContents()
        self.export_button.setEnabled(not df.empty)
        self.project.results_full_df = full_df.copy()
        self.project.results_df = df.copy()
        self.project.vertices = list(df.index)
        self.project.computed = not df.empty

        current_state = self.datastore.current()
        if current_state is not None:
            self.project.quotas = current_state.get("quotas", {})
            self.project.subset_size = current_state.get("subset_size", 0)

        self.project.decimal_precision = precision
        self.project.show_weighted_pivotal = show_weighted
        self.project.show_normalized = show_normalized

    def _apply_state_to_ui(self, state):
        """Синхронизирует интерфейс с сохраненным состоянием"""
        if not state:
            return

        project_title = state.get("project_title")
        if project_title:
            if project_title != self.project.title:
                try:
                    ProjectManager.rename_project_directory(self.project, project_title)
                except (FileExistsError, ValueError):
                    self.project.title = project_title

            self.setWindowTitle(f"TradeLink Studio - {self.project.title}")
            self.project.title = project_title

        quotas = state.get("quotas", {})
        vertices = state.get("vertices", [])
        matrix = state.get("matrix")
        subset_size = state.get("subset_size", 0)
        precision = state.get("decimal_precision", self.project.decimal_precision)
        show_weighted = state.get("show_weighted_pivotal", self.project.show_weighted_pivotal)
        show_normalized = state.get("show_normalized", self.project.show_normalized)

        self._show_quotas(quotas, vertices)
        self._show_matrix(matrix, vertices)

        # Обновляем precision spinbox с явным отключением и обновлением
        self.precision_spinbox.valueChanged.disconnect(self._on_precision_changed)
        self.precision_spinbox.setValue(precision)
        self.precision_spinbox.update()
        self.precision_spinbox.valueChanged.connect(self._on_precision_changed)

        self.weighted_visibility_button.blockSignals(True)
        self.weighted_visibility_button.setChecked(show_weighted)
        self.weighted_visibility_button.blockSignals(False)

        self.normalized_visibility_button.blockSignals(True)
        self.normalized_visibility_button.setChecked(show_normalized)
        self.normalized_visibility_button.blockSignals(False)

        self._update_indices_visibility_button_texts()

        self._update_indices_visibility_controls()
        self._show_indices(state)

        self.project.quotas = quotas
        self.project.vertices = vertices
        self.project.subset_size = subset_size
        self.project.decimal_precision = precision
        self.project.show_weighted_pivotal = show_weighted
        self.project.show_normalized = show_normalized
        self.project.computed = bool(state.get("indices") or state.get("indices_full"))

        # Обновляем subset spinbox с явным отключением и обновлением
        self.subset_spinbox.valueChanged.disconnect(self._on_subset_size_changed)
        self.subset_spinbox.setMaximum(max(len(vertices), 1))
        self.subset_spinbox.setValue(min(subset_size, max(len(vertices), 1)))
        self.subset_spinbox.update()
        self.subset_spinbox.valueChanged.connect(self._on_subset_size_changed)

    def _sync_current_state_from_ui(self, target_state=None):
        """Обновляет текущий snapshot в datastore перед сохранением"""
        state = target_state if target_state is not None else self.datastore.current()
        if state is None:
            return

        quotas_df = self.quotas_model.get_dataframe()
        matrix_df = self.matrix_model.get_dataframe()
        vertices = list(matrix_df.index)

        import networkx as nx
        graph = nx.DiGraph()
        for vertex in vertices:
            graph.add_node(vertex)

        for i, source in enumerate(vertices):
            for j, target in enumerate(vertices):
                weight = matrix_df.iat[i, j]
                if weight != 0:
                    graph.add_edge(source, target, weight=weight)

        state["matrix"] = graph
        state["vertices"] = vertices
        state["quotas"] = {col: quotas_df.at[0, col] for col in quotas_df.columns}
        state["subset_size"] = self.subset_spinbox.value()
        state["project_title"] = self.project.title
        state["decimal_precision"] = self.precision_spinbox.value()
        state["show_weighted_pivotal"] = self.weighted_visibility_button.isChecked()
        state["show_normalized"] = self.normalized_visibility_button.isChecked()

        if self.is_dirty:
            state.pop("indices", None)
        elif self.indices_table.model() is not None:
            indices_model = self.indices_table.model()
            if hasattr(indices_model, "get_dataframe"):
                indices_df = indices_model.get_dataframe()
                state["indices"] = indices_df.to_dict(orient="split")

        if self.project.results_full_df is not None:
            state["indices_full"] = self.project.results_full_df.to_dict(orient="split")

    def _initialize_empty_tables(self):
        """Инициализирует пустые таблицы для нового проекта"""
        # Проверяем, есть ли уже данные в datastore
        current_state = self.datastore.current()
        if current_state is not None:
            # Данные уже загружены, отображаем их
            self._apply_state_to_ui(current_state)

            vertices = current_state.get("vertices", [])

            self.status_label.setText(f"Loaded project | Vertices: {len(vertices)}")
            self.save_button.setEnabled(True)
            self.is_dirty = False
            self._update_undo_redo_buttons()
            return
        
        # Создаём пустую матрицу 3x3
        vertices = ["V1", "V2", "V3"]
        quotas_data = {v: 0 for v in vertices}
        
        # Инициализируем datastore с пустым состоянием
        import networkx as nx
        graph = nx.DiGraph()
        for vertex in vertices:
            graph.add_node(vertex)
        
        self.controller.set_state(
            matrix=graph,
            vertices=vertices,
            quotas=quotas_data,
            subset_size=2,
            decimal_precision=self.precision_spinbox.value(),
            show_weighted_pivotal=self.weighted_visibility_button.isChecked(),
            show_normalized=self.normalized_visibility_button.isChecked(),
            project_title=self.project.title
        )
        
        # Отображаем таблицы
        self._show_quotas(quotas_data, vertices)
        self._show_matrix(graph, vertices)
        
        # Обновляем spinbox
        self.subset_spinbox.setEnabled(True)
        self.subset_spinbox.setMaximum(len(vertices))
        self.subset_spinbox.blockSignals(True)
        self.subset_spinbox.setValue(2)
        self.subset_spinbox.blockSignals(False)

        self.precision_spinbox.blockSignals(True)
        self.precision_spinbox.setValue(self.project.decimal_precision)
        self.precision_spinbox.blockSignals(False)

        self._update_indices_visibility_controls()
        
        self.status_label.setText(f"Empty project | Vertices: {len(vertices)}")
        self.save_button.setEnabled(True)
        self.calc_button.setEnabled(False)
        self.is_dirty = False
        self._update_undo_redo_buttons()

    def _expand_matrix(self):
        """Расширяет матрицу, добавляя новую строку и столбец (с поддержкой undo/redo)"""
        if not self.matrix_model:
            QMessageBox.warning(self, "Error", "No matrix loaded")
            return
        
        state = self.datastore.current()
        if state is None:
            QMessageBox.warning(self, "Error", "No data loaded")
            return
        
        current_df = self.matrix_model.get_dataframe()
        vertices = list(current_df.index)
        
        # Генерируем новое имя вершины
        import re

        numeric_groups = {}
        pattern = re.compile(r"^(?P<prefix>[A-Za-z_]+?)(?P<number>\d+)$")

        for vertex in vertices:
            match = pattern.match(str(vertex).strip())
            if not match:
                continue

            prefix = match.group("prefix")
            number = int(match.group("number"))
            group_key = prefix.casefold()

            if group_key not in numeric_groups:
                numeric_groups[group_key] = {
                    "prefix": prefix,
                    "numbers": set(),
                }

            numeric_groups[group_key]["numbers"].add(number)

        if numeric_groups:
            chosen_group = max(
                numeric_groups.values(),
                key=lambda group: (len(group["numbers"]), max(group["numbers"]))
            )
            prefix = chosen_group["prefix"]
            next_number = max(chosen_group["numbers"]) + 1
        else:
            prefix = "v"
            next_number = 1

        existing_vertices = {str(vertex).strip().casefold() for vertex in vertices}
        new_vertex = f"{prefix}{next_number}"
        while new_vertex.casefold() in existing_vertices:
            next_number += 1
            new_vertex = f"{prefix}{next_number}"
        
        # Добавляем новую строку и столбец в матрицу
        current_df[new_vertex] = 0
        current_df.loc[new_vertex] = 0
        vertices_updated = list(current_df.index)
        
        # Обновляем квоты
        quotas_df = self.quotas_model.get_dataframe()
        quotas_df[new_vertex] = 0
        quotas = {col: quotas_df.at[0, col] for col in quotas_df.columns}
        
        # Создаём граф с новой вершиной
        import networkx as nx
        graph = nx.DiGraph()
        for vertex in vertices_updated:
            graph.add_node(vertex)
        
        for i, source in enumerate(vertices_updated):
            for j, target in enumerate(vertices_updated):
                weight = current_df.iat[i, j]
                if weight != 0:
                    graph.add_edge(source, target, weight=weight)
        
        # Обновляем состояние через controller (добавляет в историю)
        self.controller.set_state(
            matrix=graph,
            vertices=vertices_updated,
            quotas=quotas,
            subset_size=self.subset_spinbox.value(),
            decimal_precision=self.precision_spinbox.value(),
            show_weighted_pivotal=self.weighted_visibility_button.isChecked(),
            show_normalized=self.normalized_visibility_button.isChecked(),
            project_title=self.project.title
        )
        
        # Обновляем UI
        self._show_quotas(quotas, vertices_updated)
        self._show_matrix(graph, vertices_updated)
        
        self.subset_spinbox.setMaximum(len(vertices_updated))
        self.status_label.setText(f"Expanded matrix to {len(vertices_updated)}x{len(vertices_updated)}")
        self.is_dirty = True
        self.project.is_dirty = True
        self.project.computed = False
        self.project.results_df = None
        self.export_button.setEnabled(False)
        self._update_calc_button()
        self._update_undo_redo_buttons()

    def _shrink_matrix(self):
        """Уменьшает матрицу, удаляя последнюю строку и столбец (с поддержкой undo/redo)"""
        if not self.matrix_model:
            QMessageBox.warning(self, "Error", "No matrix loaded")
            return
        
        current_df = self.matrix_model.get_dataframe()
        if len(current_df) <= 1:
            QMessageBox.warning(self, "Error", "Cannot shrink matrix below 1x1")
            return
        
        state = self.datastore.current()
        if state is None:
            QMessageBox.warning(self, "Error", "No data loaded")
            return
        
        # Удаляем последнюю вершину
        last_vertex = current_df.index[-1]
        current_df = current_df.drop(last_vertex, axis=0)
        current_df = current_df.drop(last_vertex, axis=1)
        vertices_updated = list(current_df.index)
        
        # Обновляем квоты
        quotas_df = self.quotas_model.get_dataframe()
        quotas_df = quotas_df.drop(last_vertex, axis=1)
        quotas = {col: quotas_df.at[0, col] for col in quotas_df.columns}
        
        # Создаём граф с удалённой вершиной
        import networkx as nx
        graph = nx.DiGraph()
        for vertex in vertices_updated:
            graph.add_node(vertex)
        
        for i, source in enumerate(vertices_updated):
            for j, target in enumerate(vertices_updated):
                weight = current_df.iat[i, j]
                if weight != 0:
                    graph.add_edge(source, target, weight=weight)
        
        # Обновляем состояние через controller (добавляет в историю)
        subset_value = self.subset_spinbox.value()
        if subset_value > len(vertices_updated):
            subset_value = len(vertices_updated)
        
        self.controller.set_state(
            matrix=graph,
            vertices=vertices_updated,
            quotas=quotas,
            subset_size=subset_value,
            decimal_precision=self.precision_spinbox.value(),
            show_weighted_pivotal=self.weighted_visibility_button.isChecked(),
            show_normalized=self.normalized_visibility_button.isChecked(),
            project_title=self.project.title
        )
        
        # Обновляем UI
        self._show_quotas(quotas, vertices_updated)
        self._show_matrix(graph, vertices_updated)
        
        self.subset_spinbox.blockSignals(True)
        self.subset_spinbox.setMaximum(len(vertices_updated))
        self.subset_spinbox.setValue(subset_value)
        self.subset_spinbox.blockSignals(False)
        
        self.status_label.setText(f"Shrunk matrix to {len(vertices_updated)}x{len(vertices_updated)}")
        self.is_dirty = True
        self.project.is_dirty = True
        self.project.computed = False
        self.project.results_df = None
        self.export_button.setEnabled(False)
        self._update_calc_button()
        self._update_undo_redo_buttons()

    def _rename_vertices(self):
        """Позволяет переименовать вершины"""
        state = self.datastore.current()
        if state is None:
            QMessageBox.warning(self, "Error", "No data loaded")
            return
        
        vertices = state.get("vertices", [])
        
        # Создаём диалог для переименования
        dialog = QDialog(self)
        dialog.setWindowTitle("Rename Vertices")
        dialog.resize(500, 420)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter new names for vertices:"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        name_inputs = {}
        for vertex in vertices:
            h_layout = QHBoxLayout()
            h_layout.addWidget(QLabel(f"Current: {vertex}"))
            line_edit = QLineEdit()
            line_edit.setText(vertex)
            name_inputs[vertex] = line_edit
            h_layout.addWidget(line_edit)
            scroll_layout.addLayout(h_layout)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        
        if dialog.exec_():
            raw_names = [name_inputs[old].text() for old in vertices]
            is_valid_names, error_message, normalized_names = validate_vertex_names(raw_names)
            if not is_valid_names:
                QMessageBox.warning(self, "Error", error_message)
                return

            new_names = {old: new for old, new in zip(vertices, normalized_names)}
            
            # Переименовываем в датафреймах и графе
            quotas_df = self.quotas_model.get_dataframe()
            matrix_df = self.matrix_model.get_dataframe()
            
            # Переименовываем в датафреймах
            quotas_df = quotas_df.rename(columns=new_names)
            matrix_df = matrix_df.rename(index=new_names, columns=new_names)
            
            # Переименовываем в графе
            import networkx as nx
            graph = state.get("matrix")
            if isinstance(graph, nx.DiGraph):
                mapping = new_names
                graph = nx.relabel_nodes(graph, mapping)
            
            # Обновляем квоты
            quotas = {col: quotas_df.at[0, col] for col in quotas_df.columns}
            new_vertices = list(matrix_df.index)
            
            # Сохраняем изменения через controller
            self.controller.set_state(
                matrix=graph,
                vertices=new_vertices,
                quotas=quotas,
                subset_size=state.get("subset_size", 2),
                decimal_precision=self.precision_spinbox.value(),
                show_weighted_pivotal=self.weighted_visibility_button.isChecked(),
                show_normalized=self.normalized_visibility_button.isChecked(),
                project_title=self.project.title
            )
            
            # Обновляем UI
            self._show_quotas(quotas, new_vertices)
            self._show_matrix(graph, new_vertices)
            
            self.status_label.setText("Vertices renamed")
            self._update_undo_redo_buttons()

    def _rename_project(self):
        """Позволяет переименовать проект"""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Project",
            "Enter new project name:",
            text=self.project.title
        )
        
        if ok and new_name.strip():
            is_valid_name, error_message, normalized_name = validate_project_name(new_name)
            if not is_valid_name:
                QMessageBox.warning(
                    self,
                    "Rename Project",
                    error_message
                )
                return

            try:
                ProjectManager.rename_project_directory(self.project, normalized_name)
            except FileExistsError:
                QMessageBox.warning(
                    self,
                    "Rename Project",
                    "A project folder with this name already exists"
                )
                return
            except ValueError as exc:
                QMessageBox.warning(
                    self,
                    "Rename Project",
                    str(exc)
                )
                return

            state = self.datastore.current() or {}
            state["project_title"] = self.project.title
            self.datastore.push(state)

            self.setWindowTitle(f"TradeLink Studio - {self.project.title}")
            self.project.is_dirty = True
            self.save_button.setEnabled(True)
            self.status_label.setText(f"Project renamed to {self.project.title}")
            self._update_undo_redo_buttons()
