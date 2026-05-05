import copy


class DataStore:

    def __init__(self):
        self.states = []
        self.current_index = -1

    def push_state(self, state):
        self.states = self.states[:self.current_index + 1]

        self.states.append(copy.deepcopy(state))

        self.current_index += 1

    def undo(self):
        if self.current_index <= 0:
            return None

        self.current_index -= 1

        return self.states[self.current_index]

    def redo(self):

        if self.current_index >= len(self.states) - 1:
            return None

        self.current_index += 1

        return self.states[self.current_index]

    def current(self):

        if self.current_index < 0:
            return None

        return self.states[self.current_index]