class Project:

    def __init__(self):
        self.file_path = None
        self.vertices = None
        self.subset_size = None
        self.quotas = None
        self.matrix = None
        self.results = {}
        self.results_df = None

    def load(self, file_path, vertices, subset_size, quotas, matrix):
        self.file_path = file_path
        self.vertices = vertices
        self.subset_size = subset_size
        self.quotas = quotas
        self.matrix = matrix