import copy
import json
from app.services.logging_service import log_debug


class DataStore:

    def __init__(self):

        self.states = []
        self.current_index = -1
        self._last_fingerprint = None

    def push(self, state):

        # Сначала формируем отпечаток состояния, чтобы избежать одинаковых подрядных снапшотов
        try:
            fp = self._fingerprint(state)
        except Exception:
            fp = None

        # Если отпечаток совпадает с последним — пропускаем push
        if fp is not None and fp == self._last_fingerprint:
            log_debug("DataStore.push: skipped duplicate snapshot")
            return

        # Обрезаем "впереди" историю при новой ветке
        self.states = self.states[: self.current_index + 1]
        self.states.append(copy.deepcopy(state))
        self.current_index += 1
        self._last_fingerprint = fp
        log_debug(f"DataStore.push: new snapshot index={self.current_index}")

    def current(self):
        # безопасно возвращаем текущее состояние или None,
        # если индекс вне допустимого диапазона
        if self.current_index < 0:
            return None

        if self.current_index >= len(self.states):
            # корректируем некорректный индекс и возвращаем None
            self.current_index = len(self.states) - 1
            if self.current_index < 0:
                return None

        try:
            return self.states[self.current_index]
        except Exception:
            return None

    def _fingerprint(self, state):
        """Compute a lightweight fingerprint for a state to detect duplicates.

        Fingerprint includes vertices order, subset_size, quotas, decimal_precision,
        visibility flags and matrix numeric contents in deterministic order.
        """
        if state is None:
            return None

        try:
            vertices = tuple(state.get("vertices") or [])
            subset = int(state.get("subset_size") or 0)
            quotas = tuple(sorted((k, float(v)) for k, v in (state.get("quotas") or {}).items()))
            precision = int(state.get("decimal_precision") if state.get("decimal_precision") is not None else -1)
            show_w = bool(state.get("show_weighted_pivotal"))
            show_n = bool(state.get("show_normalized"))

            # matrix: try to serialize rows in vertices order
            matrix_rows = []
            mat = state.get("matrix")
            if mat is not None and vertices:
                try:
                    # networkx DiGraph
                    import networkx as nx

                    if isinstance(mat, nx.DiGraph):
                        for src in vertices:
                            row = []
                            for tgt in vertices:
                                try:
                                    w = mat[src][tgt].get("weight", 0)
                                except Exception:
                                    w = 0
                                row.append(float(w))
                            matrix_rows.append(tuple(row))
                    else:
                        # assume 2D array-like
                        for i, src in enumerate(vertices):
                            row = []
                            for j, tgt in enumerate(vertices):
                                try:
                                    row.append(float(mat[i][j]))
                                except Exception:
                                    row.append(0.0)
                            matrix_rows.append(tuple(row))
                except Exception:
                    matrix_rows = []

            fp = (vertices, subset, quotas, precision, show_w, show_n, tuple(matrix_rows))
            return json.dumps(fp, sort_keys=True)
        except Exception:
            return None

    def undo(self):

        # безопасное движение назад по истории
        if self.current_index <= 0:
            # уже в начале истории или пусто
            self.current_index = max(self.current_index, -1)
            return None

        self.current_index = max(self.current_index - 1, -1)
        return self.current()

    def redo(self):

        # безопасное движение вперёд по истории
        if self.current_index >= len(self.states) - 1:
            return None

        self.current_index = min(self.current_index + 1, len(self.states) - 1)
        return self.current()
