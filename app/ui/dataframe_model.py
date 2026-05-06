from PyQt5.QtCore import QAbstractTableModel, Qt

class DataFrameModel(QAbstractTableModel):

    def __init__(self, df, editable=False, on_change=None):
        super().__init__()
        self._df = df.copy()
        self._editable = editable
        self._on_change = on_change

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        value = self._df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            import pandas as pd
            if pd.isna(value):
                return ""
            try:
                f = float(value)
            except Exception:
                return str(value)

            if f.is_integer():
                return str(int(f))
            return f"{f:.7f}".rstrip("0").rstrip(".")

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or not self._editable:
            return False

        try:
            float_value = float(value)
            self._df.iloc[index.row(), index.column()] = float_value
            self.dataChanged.emit(index, index)
            
            if self._on_change:
                self._on_change()
            
            return True
        except ValueError:
            return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self._editable:
            flags |= Qt.ItemIsEditable
        return flags

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                # Проверяем, что индекс в пределах размера DataFrame
                if section < len(self._df.columns):
                    return str(self._df.columns[section])
                return None
            else:
                # Проверяем, что индекс в пределах размера DataFrame
                if section < len(self._df.index):
                    return str(self._df.index[section])
                return None
        return None

    def get_dataframe(self):
        """Возвращает текущий DataFrame"""
        return self._df.copy()
