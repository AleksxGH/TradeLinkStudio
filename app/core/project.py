class Project:

    def __init__(self, title):

        self.title = title

        self.current_state_index = 0
        self.state_count = 0
        self.max_history = 50

        self.is_dirty = False
        self.is_saved = False

        self.computed = False