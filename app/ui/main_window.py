import pandas as pd
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
    QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from app.data.exporter import save_results
from app.data.loader import read_data
from app.core.project import Project
from app.core.engine import ComputeEngine
from app.services.config_manager import ConfigManager
from app.services.data_controller import DataController
from app.services.project_manager import ProjectManager
from app.ui.dataframe_model import DataFrameModel
from app.core.datastore import DataStore


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

        self.setWindowTitle(f"TradeLink Studio - {self.project.title}")
        self.resize(1400, 800)
        self.setWindowIcon(QIcon("/resources/icons/app.ico"))

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
        self.undo_button.setIcon(QIcon("resources/icons/undo.png"))
        self.undo_button.setToolTip("Undo (Ctrl+Z)")
        
        self.redo_button = QPushButton()
        self.redo_button.setIcon(QIcon("resources/icons/redo.png"))
        self.redo_button.setToolTip("Redo (Ctrl+Y)")
        
        self.calc_button = QPushButton("Calculate indices")
        self.export_button = QPushButton("Export")
        
        self.save_button = QPushButton()
        self.save_button.setIcon(QIcon("resources/icons/save.png"))
        self.save_button.setToolTip("Save project")
        
        self.rename_vertices_button = QPushButton("Rename Vertices")
        self.rename_project_button = QPushButton("Rename Project")

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
        self.save_button.setMaximumWidth(40)
        self.save_button.setMaximumHeight(40)

        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)
        button_layout.addWidget(self.calc_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.rename_vertices_button)
        button_layout.addWidget(self.rename_project_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # ===== STATUS LABEL =====
        self.status_label = QLabel("No data loaded")
        self.status_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.status_label)

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
        subset_layout.addStretch()
        main_layout.addLayout(subset_layout)

        # ===== QUOTAS (TOP) =====
        quotas_label = QLabel("Quotas:")
        quotas_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(quotas_label)

        self.quotas_table = QTableView()
        self.quotas_table.setAlternatingRowColors(True)
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
        self.expand_matrix_button = QPushButton("Expand Matrix")
        self.shrink_matrix_button = QPushButton("Shrink Matrix")
        self.expand_matrix_button.clicked.connect(self._expand_matrix)
        self.shrink_matrix_button.clicked.connect(self._shrink_matrix)
        matrix_controls_layout.addWidget(self.expand_matrix_button)
        matrix_controls_layout.addWidget(self.shrink_matrix_button)
        matrix_controls_layout.addStretch()
        left_layout.addLayout(matrix_controls_layout)

        self.matrix_table = QTableView()
        self.matrix_table.setAlternatingRowColors(True)
        left_layout.addWidget(self.matrix_table)

        splitter.addWidget(left_container)

        # Right side: Indices
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)

        indices_label = QLabel("Calculated Indices:")
        indices_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(indices_label)

        self.indices_table = QTableView()
        self.indices_table.setAlternatingRowColors(True)
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
        self.rename_vertices_button.clicked.connect(self._rename_vertices)
        self.rename_project_button.clicked.connect(self._rename_project)
        self.save_button.clicked.connect(self.save_project)



    def to_home(self):

        if not self.is_dirty and not self.project.is_dirty:

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

        try:
            _df, vertices, subset_size, quotas, graph = read_data(file_path)

            self.controller.set_state(
                matrix=graph,
                vertices=vertices,
                quotas=quotas,
                subset_size=subset_size,
                project_title=self.project.title
            )

            self._show_quotas(quotas, vertices)
            self._show_matrix(graph, vertices)

            # Установим spinbox для subset_size
            self.subset_spinbox.setEnabled(True)
            self.subset_spinbox.setMaximum(len(vertices))
            self.subset_spinbox.blockSignals(True)
            self.subset_spinbox.setValue(subset_size)
            self.subset_spinbox.blockSignals(False)

            self.save_button.setEnabled(True)
            self.calc_button.setEnabled(True)  # Активна сразу после загрузки
            self.export_button.setEnabled(False)
            
            # Сброс флага грязных данных
            self.is_dirty = False
            self._update_undo_redo_buttons()

            self.status_label.setText(
                f"Loaded: {file_path} | Vertices: {len(vertices)}"
            )

            QMessageBox.information(self, "Success", "File uploaded")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def calculate_indices(self):
        """Вычисляет индексы из текущего состояния таблиц"""
        state = self.datastore.current()
        if not state:
            QMessageBox.warning(self, "Error", "No data loaded")
            return

        try:
            # Обновляем state из отредактированных таблиц
            quotas_df = self.quotas_model.get_dataframe()
            matrix_df = self.matrix_model.get_dataframe()
            
            # Обновляем квоты (берём из первой строки)
            quotas = {}
            for col in quotas_df.columns:
                quotas[col] = quotas_df.at[0, col]
            
            # Обновляем матрицу в граф
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
            
            # Создаём новое состояние с обновленными данными
            new_state = {
                "quotas": quotas,
                "matrix": graph,
                "subset_size": self.subset_spinbox.value(),
                "vertices": vertices,
                "project_title": self.project.title
            }
            
            # Добавляем в историю
            self.datastore.push(new_state)
            
            # Пересчитываем индексы
            result = self.controller.recompute()

            if result is None:
                QMessageBox.warning(self, "Error", "Failed to calculate indices")
                return

            vertices = new_state.get("vertices", [])
            subset_size = new_state.get("subset_size", 0)

            weighted_mode = self.config.get("weighted_mode")
            normalization = self.config.get("normalization")

            df_data = {}
            norm_data = {}

            # ===== BASE INDICES =====
            df_data["Copeland"] = list(result.get("copeland", {}).values())
            if normalization:
                norm_data["Copeland (norm)"] = result.get("copeland_norm", [])

            bundle_col = f"BI (s={subset_size})"
            df_data[bundle_col] = list(result.get("bundle", {}).values())
            if normalization:
                norm_data[f"{bundle_col} (norm)"] = result.get("bundle_norm", [])

            pivotal_col = f"PI (s={subset_size})"
            df_data[pivotal_col] = list(result.get("pivotal", {}).values())
            if normalization:
                norm_data[f"{pivotal_col} (norm)"] = result.get("pivotal_norm", [])

            if weighted_mode:
                pi_prime_col = f"PI' (w, s={subset_size})"
                df_data[pi_prime_col] = list(result.get("pi_prime", {}).values())
                if normalization:
                    norm_data[f"{pi_prime_col} (norm)"] = result.get("pi_prime_norm", [])

            final_data = {**df_data, **norm_data}

            df = pd.DataFrame(final_data, index=vertices)

            self.project.results_df = df
            self.project.vertices = vertices
            self.project.quotas = quotas
            self.project.subset_size = subset_size
            self.project.computed = True

            current_state = self.datastore.current()
            if current_state is not None:
                current_state["indices"] = df.to_dict(orient="split")

            # Используем нередактируемую модель для результатов
            self.indices_table.setModel(DataFrameModel(df, editable=False))
            self.indices_table.resizeColumnsToContents()
            self.export_button.setEnabled(True)
            
            # Сброс флага грязных данных
            self.is_dirty = False
            self.project.is_dirty = True
            self._update_calc_button()
            self._update_undo_redo_buttons()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error calculating indices:\n{str(e)}")

    def _on_subset_size_changed(self, value):
        """Отмечает данные как грязные при изменении subset_size"""
        self.is_dirty = True
        self.project.is_dirty = True
        self.project.computed = False
        self.project.results_df = None
        self.export_button.setEnabled(False)
        self._sync_current_state_from_ui()
        current_state = self.datastore.current()
        if current_state is not None:
            self.datastore.push(current_state)
        self._update_calc_button()
        self._update_undo_redo_buttons()

    def _mark_data_dirty(self):
        """Отмечает данные как грязные и обновляет статус кнопки"""
        self.is_dirty = True
        self.project.is_dirty = True
        self.project.computed = False
        self.project.results_df = None
        self.export_button.setEnabled(False)
        self._sync_current_state_from_ui()
        current_state = self.datastore.current()
        if current_state is not None:
            self.datastore.push(current_state)
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
        result = self.controller.undo()
        if result is None:
            QMessageBox.information(self, "Undo", "Nothing to undo")
            return
        
        state = self.datastore.current()
        if state:
            self._apply_state_to_ui(state)
        
        self._update_undo_redo_buttons()
        self.is_dirty = True
        self._update_calc_button()

    def on_redo(self):
        """Повтор отменённого изменения"""
        result = self.controller.redo()
        if result is None:
            QMessageBox.information(self, "Redo", "Nothing to redo")
            return
        
        state = self.datastore.current()
        if state:
            self._apply_state_to_ui(state)
        
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

    def _show_indices(self, indices_data):
        """Отображает вычисленные индексы, если они есть"""
        if not indices_data:
            self.indices_table.setModel(DataFrameModel(pd.DataFrame(), editable=False))
            self.export_button.setEnabled(False)
            self.project.results_df = None
            self.project.vertices = []
            self.project.quotas = {}
            self.project.subset_size = 0
            self.project.computed = False
            return

        try:
            df = pd.DataFrame(
                indices_data.get("data", []),
                index=indices_data.get("index", []),
                columns=indices_data.get("columns", [])
            )
        except Exception:
            self.indices_table.setModel(DataFrameModel(pd.DataFrame(), editable=False))
            self.export_button.setEnabled(False)
            return

        self.indices_table.setModel(DataFrameModel(df, editable=False))
        self.indices_table.resizeColumnsToContents()
        self.export_button.setEnabled(not df.empty)
        self.project.results_df = df
        self.project.vertices = list(df.index)
        self.project.computed = not df.empty

        current_state = self.datastore.current()
        if current_state is not None:
            self.project.quotas = current_state.get("quotas", {})
            self.project.subset_size = current_state.get("subset_size", 0)

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

        self._show_quotas(quotas, vertices)
        self._show_matrix(matrix, vertices)
        self._show_indices(state.get("indices"))

        self.project.quotas = quotas
        self.project.vertices = vertices
        self.project.subset_size = subset_size
        self.project.computed = bool(state.get("indices"))
        if self.project.results_df is None and state.get("indices"):
            try:
                self.project.results_df = pd.DataFrame(
                    state["indices"].get("data", []),
                    index=state["indices"].get("index", []),
                    columns=state["indices"].get("columns", [])
                )
            except Exception:
                self.project.results_df = None

        self.subset_spinbox.blockSignals(True)
        self.subset_spinbox.setMaximum(max(len(vertices), 1))
        self.subset_spinbox.setValue(min(subset_size, max(len(vertices), 1)))
        self.subset_spinbox.blockSignals(False)

    def _sync_current_state_from_ui(self):
        """Обновляет текущий snapshot в datastore перед сохранением"""
        state = self.datastore.current()
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

        if self.is_dirty:
            state.pop("indices", None)
        elif self.indices_table.model() is not None:
            indices_model = self.indices_table.model()
            if hasattr(indices_model, "get_dataframe"):
                indices_df = indices_model.get_dataframe()
                state["indices"] = indices_df.to_dict(orient="split")

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
        max_num = 0
        for v in vertices:
            if v.startswith("V"):
                try:
                    num = int(v[1:])
                    max_num = max(max_num, num)
                except ValueError:
                    pass
        new_vertex = f"V{max_num + 1}"
        
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
            project_title=self.project.title
        )
        
        # Обновляем UI
        self._show_quotas(quotas, vertices_updated)
        self._show_matrix(graph, vertices_updated)
        
        self.subset_spinbox.setMaximum(len(vertices_updated))
        self.status_label.setText(f"Expanded matrix to {len(vertices_updated)}x{len(vertices_updated)}")
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
            new_names = {old: name_inputs[old].text().strip() for old in vertices}
            
            # Проверяем пустые имена
            if any(not name for name in new_names.values()):
                QMessageBox.warning(self, "Error", "Vertex names cannot be empty")
                return
            
            # Проверяем дубликаты
            if len(set(new_names.values())) != len(new_names):
                QMessageBox.warning(self, "Error", "Vertex names must be unique")
                return
            
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
            new_name = new_name.strip()

            try:
                ProjectManager.rename_project_directory(self.project, new_name)
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
