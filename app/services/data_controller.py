class DataController:

    def __init__(self, project, datastore, engine, config=None):

        self.project = project
        self.datastore = datastore
        self.engine = engine
        self.config = config

    def set_state(self, matrix, vertices, quotas, subset_size, project_title=None):

        state = {
            "matrix": matrix,
            "vertices": vertices,
            "quotas": quotas,
            "subset_size": subset_size,
            "project_title": project_title if project_title is not None else self.project.title
        }

        self.datastore.push(state)

        self.project.is_dirty = True

        return self.recompute()

    def update_matrix(self, matrix):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["matrix"] = matrix
        state.setdefault("project_title", self.project.title)

        self.datastore.push(state)

        self.project.is_dirty = True

        return self.recompute()

    def update_quotas(self, quotas):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["quotas"] = quotas
        state.setdefault("project_title", self.project.title)

        self.datastore.push(state)

        self.project.is_dirty = True

        return self.recompute()

    def update_vertices(self, vertices):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["vertices"] = vertices
        state.setdefault("project_title", self.project.title)

        self.datastore.push(state)

        self.project.is_dirty = True

        return self.recompute()

    def update_subset_size(self, subset_size):

        state = self.datastore.current()

        if state is None:

            state = {}

        state["subset_size"] = subset_size
        state.setdefault("project_title", self.project.title)

        self.datastore.push(state)

        self.project.is_dirty = True

        return self.recompute()

    def undo(self):

        state = self.datastore.undo()

        if state is None:

            return None

        self.project.is_dirty = True

        return self.recompute()

    def redo(self):

        state = self.datastore.redo()

        if state is None:

            return None

        self.project.is_dirty = True

        return self.recompute()

    def get_current(self):

        return self.datastore.current()

    def recompute(self):

        state = self.datastore.current()

        if state is None:

            return None

        result = self.engine.compute(state, self.config)

        self.project.computed = True

        return result


    def can_undo(self):

        return self.datastore.current_index > 0

    def can_redo(self):

        return self.datastore.current_index < len(self.datastore.states) - 1