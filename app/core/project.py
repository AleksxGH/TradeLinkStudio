class Project:

    def __init__(self, title):

        self.title = title

        self.results_df = None
        self.vertices = []
        self.quotas = {}
        self.subset_size = 0

        self.current_state_index = 0
        self.state_count = 0
        self.max_history = 50

        self.is_dirty = False
        self.is_saved = False

        self.computed = False