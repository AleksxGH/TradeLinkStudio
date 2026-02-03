from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTableView,
    QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

import pandas as pd

from app.data.exporter import save_results
from app.data.loader import read_data
from app.core.project import Project
from app.services.index_service import calculate_all_indices
from app.ui.dataframe_model import DataFrameModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TradeLink Studio")
        self.resize(1000, 600)
        self.setWindowIcon(QIcon(
            "C:/Users/user/Desktop/TradeLinkStudio/resources/icons/app.ico"
        ))

        self.project = Project()
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # ---------- Панель кнопок ----------
        button_layout = QHBoxLayout()

        self.load_button = QPushButton("Load data")
        self.calc_button = QPushButton("Calculate indices")
        self.export_button = QPushButton("Export")

        self.calc_button.setEnabled(False)
        self.export_button.setEnabled(False)

        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.calc_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()

        # ---------- Таблица ----------
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)

        # ---------- Статус ----------
        self.status_label = QLabel("No data loaded")
        self.status_label.setAlignment(Qt.AlignLeft)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table_view)
        main_layout.addWidget(self.status_label)

        # ---------- Сигналы ----------
        self.load_button.clicked.connect(self.load_data)
        self.calc_button.clicked.connect(self.calculate_indices)
        self.export_button.clicked.connect(self.export_data)


    def load_data(self):

        print("DEBUG: load_data called")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "Data files (*.csv *.xlsx)"
        )

        if not file_path:
            print("DEBUG: No file selected")
            return

        print("DEBUG: Selected file:", file_path)

        try:
            df, vertices, subset_size, quotas, matrix = read_data(file_path)

            print("DEBUG: File parsed successfully")
            print("Vertices:", len(vertices))
            print("Subset size:", subset_size)
            print("Matrix shape:", matrix.shape)

            self.project.load(
                df,
                file_path,
                vertices,
                subset_size,
                quotas,
                matrix
            )

            # показать матрицу сразу
            import pandas as pd
            from app.ui.dataframe_model import DataFrameModel

            df = pd.DataFrame(matrix, index=vertices, columns=vertices)
            model = DataFrameModel(df)
            self.table_view.setModel(model)

            # включаем кнопки
            self.calc_button.setEnabled(True)

            # обновляем статус
            self.status_label.setText(
                f"Loaded: {file_path} | Vertices: {len(vertices)}"
            )

            QMessageBox.information(self, "Success", "File loaded")

        except Exception as e:
            print("DEBUG ERROR:", e)
            QMessageBox.critical(self, "Error", str(e))

    def calculate_indices(self):
        if self.project.matrix is None:
            return

        calculate_all_indices(self.project)

        model = DataFrameModel(self.project.results_df)
        self.table_view.setModel(model)

        self.table_view.resizeColumnsToContents()
        self.table_view.resizeRowsToContents()
        self.table_view.horizontalHeader().setStretchLastSection(True)

        self.export_button.setEnabled(True)

    def export_data(self):
        """Экспорт результатов проекта в Excel через UI"""
        if not self.project.results:
            QMessageBox.warning(self, "Export", "No data to export!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "",
            "Excel files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            saved_path = save_results(
                project=self.project,
                file_path=file_path
            )
            QMessageBox.information(self, "Export", f"Results saved to:\n{saved_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))