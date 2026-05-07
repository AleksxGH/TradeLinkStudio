from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtWidgets import QMessageBox
from app.services.logging_service import log_debug, log_error

class DataFrameModel(QAbstractTableModel):

    def __init__(self, df, editable=False, on_change=None, precision=None):
        super().__init__()
        self._df = df.copy()
        self._editable = editable
        self._on_change = on_change
        self._precision = precision

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
            if self._precision is None:
                return f"{f:.7f}".rstrip("0").rstrip(".")
            return f"{f:.{self._precision}f}".rstrip("0").rstrip(".")

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or not self._editable:
            return False

        try:
            # Попытаемся конвертировать ввод в число
            # Поддержим ввод с запятой (заменим на точку) с предупреждением
            raw = value
            if isinstance(raw, str) and "," in raw:
                # Покажем предупреждение при использовании запятой как разделителя
                log_debug(f"User entered comma as decimal separator: {raw}")
                QMessageBox.warning(None, "Invalid format", "Please use '.' as decimal separator. Comma will be converted automatically.")
                raw = raw.replace(',', '.')

            float_value = float(raw)
            self._df.iloc[index.row(), index.column()] = float_value
            self.dataChanged.emit(index, index)
            
            if self._on_change:
                self._on_change()
            
            return True
        except Exception as exc:
            # Неверный формат ввода — предупредим пользователя и залогируем
            log_error(f"Invalid cell input: {value} -> {exc}")
            QMessageBox.warning(None, "Invalid input", "Please enter a numeric value using digits and '.' as a decimal separator.")
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
                try:
                    return str(self._df.columns[section])
                except Exception:
                    return ""
            else:
                try:
                    return str(self._df.index[section])
                except Exception:
                    return ""
        return None

    def get_dataframe(self):
        """Возвращает текущий DataFrame"""
        return self._df.copy()
