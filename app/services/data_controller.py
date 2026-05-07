from app.services.logging_service import log_debug, log_error


class DataController:

    def __init__(self, project, datastore, engine, config=None):

        self.project = project
        self.datastore = datastore
        self.engine = engine
        self.config = config

    def set_state(self, matrix, vertices, quotas, subset_size, **extra_state):

        state = {
            "matrix": matrix,
            "vertices": vertices,
            "quotas": quotas,
            "subset_size": subset_size
        }

        state.update(extra_state)

        self.datastore.push(state)
        log_debug(f"set_state: vertices={len(vertices)}, subset_size={subset_size}")

        self.project.is_dirty = True

        return self.recompute()

    def update_matrix(self, matrix):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["matrix"] = matrix

        self.datastore.push(state)
        log_debug("update_matrix")

        self.project.is_dirty = True

        return self.recompute()

    def update_quotas(self, quotas):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["quotas"] = quotas

        self.datastore.push(state)
        log_debug("update_quotas")

        self.project.is_dirty = True

        return self.recompute()

    def update_vertices(self, vertices):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["vertices"] = vertices

        self.datastore.push(state)
        log_debug("update_vertices")

        self.project.is_dirty = True

        return self.recompute()

    def update_subset_size(self, subset_size):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["subset_size"] = subset_size

        self.datastore.push(state)
        log_debug(f"update_subset_size: {subset_size}")

        self.project.is_dirty = True

        return self.recompute()

    def undo(self):

        # Возвращаем предыдущее сохранённое состояние и не выполняем recompute здесь:
        # UI должен сначала применить состояние, затем при необходимости вызвать recompute.
        state = self.datastore.undo()

        if state is None:
            log_debug("undo: nothing to undo")
            return None

        self.project.is_dirty = True
        log_debug("undo: moved to previous state")
        return state

    def redo(self):

        # Аналогично undo: возвращаем состояние, recompute выполняется извне по необходимости
        state = self.datastore.redo()

        if state is None:
            log_debug("redo: nothing to redo")
            return None

        self.project.is_dirty = True
        log_debug("redo: moved to next state")
        return state

    def get_current(self):

        return self.datastore.current()

    def recompute(self):

        state = self.datastore.current()

        if state is None:

            return None

        try:
            result = self.engine.compute(state, self.config)
            self.project.computed = True
            log_debug("recompute: success")
            return result
        except Exception as exc:
            log_error(f"recompute failed: {exc}")
            return None


    def can_undo(self):

        return self.datastore.current_index > 0

    def can_redo(self):

        return self.datastore.current_index < len(self.datastore.states) - 1