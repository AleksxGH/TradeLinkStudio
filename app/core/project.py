import re
import os

class Project:

    def __init__(self, title, folder):
        self.title = title
        self.base_dir = folder
        self.project_dir = str(os.path.join(self.base_dir, title))
        self.source_path = None
        self.df_original = None  # исходный DataFrame для экспорта
        self.vertices = None
        self.subset_size = None
        self.quotas = None
        self.matrix = None
        self.results = {}        # словарь индексов + долей для экспорта
        self.results_df = None   # DataFrame для отображения в UI

        os.makedirs(os.path.join(self.base_dir, title))
        os.makedirs(os.path.join(self.project_dir, "data"))
        os.makedirs(os.path.join(self.project_dir, "exports"))

    def load(self, df_original, file_path, vertices, subset_size, quotas, matrix):
        self.source_path = file_path
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