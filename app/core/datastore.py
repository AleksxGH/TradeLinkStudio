import copy


class DataStore:

    def __init__(self):

        self.states = []
        self.current_index = -1

    def push(self, state):

        self.states = self.states[:self.current_index + 1]

        self.states.append(copy.deepcopy(state))

        self.current_index += 1

    def current(self):

        if self.current_index < 0:
            return None

        return self.states[self.current_index]

    def undo(self):

        if self.current_index > 0:
            self.current_index -= 1
            return self.current()

        return None

    def redo(self):

        if self.current_index < len(self.states) - 1:
            self.current_index += 1
            return self.current()

        return None
