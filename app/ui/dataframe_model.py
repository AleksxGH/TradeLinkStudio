from PyQt5.QtCore import QAbstractTableModel, Qt

class DataFrameModel(QAbstractTableModel):

    def __init__(self, df):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        value = self._df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole:
            import pandas as pd
            if pd.isna(value) or value == 0:
                return ""
            try:
                f = float(value)
            except Exception:
                return str(value)

            if f.is_integer():
                return str(int(f))
            # Округляем до 5 значащих цифр после запятой, убираем лишние нули
            return f"{f:.5f}".rstrip("0").rstrip(".")

        return None

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        else:
            return str(self._df.index[section])
