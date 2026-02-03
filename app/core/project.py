class Project:

    def __init__(self):
        self.file_path = None
        self.vertices = None
        self.subset_size = None
        self.quotas = None
        self.matrix = None
        self.results = {}        # словарь индексов + долей для экспорта
        self.results_df = None   # DataFrame для отображения в UI
        self.df_original = None  # исходный DataFrame для экспорта

    def load(self, df_original, file_path, vertices, subset_size, quotas, matrix):
        self.file_path = file_path
        self.vertices = vertices
        self.subset_size = subset_size
        self.quotas = quotas
        self.matrix = matrix
        self.df_original = df_original  # сохраняем копию исходного Excel