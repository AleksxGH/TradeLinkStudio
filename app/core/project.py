import re

class Project:

    def __init__(self):
        self.title = None
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

    def rename(self, new_name: str):
        """
        Переименовывает проект с проверкой допустимых символов.
        Допустимы: буквы, цифры, пробел, _ и -.
        Ограничение длины: 1–100 символов.
        """
        if not new_name:
            raise ValueError("Project name cannot be empty.")

        if len(new_name) > 100:
            raise ValueError("Project name is too long (max 100 characters).")

        # Проверка на недопустимые символы
        if not re.match(r'^[\w\-\s]+$', new_name, re.UNICODE):
            raise ValueError(
                "Project name contains invalid characters. "
                "Only letters, digits, spaces, '-' and '_' are allowed."
            )

        self.title = new_name
        return self.title