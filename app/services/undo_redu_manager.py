class UndoRedoManager:

    def __init__(self, datastore):

        self.datastore = datastore

    def undo(self):

        if self.datastore.current_index <= 0:
            return None

        self.datastore.current_index -= 1

        return self.datastore.current()

    def redo(self):

        if self.datastore.current_index >= len(self.datastore.states) - 1:
            return None

        self.datastore.current_index += 1

        return self.datastore.current()