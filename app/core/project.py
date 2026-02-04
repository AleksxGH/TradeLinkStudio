import re
import os

class Project:
    def __init__(self, title=None, base_dir=None, create_dirs=False):
        self.title = title
        self.base_dir = base_dir
        self.project_dir = str(os.path.join(self.base_dir, title)) if self.base_dir else None
        self.data_dir = str(os.path.join(self.project_dir, "data")) if self.project_dir else None
        self.export_dir = str(os.path.join(self.project_dir, "export")) if self.project_dir else None
        self.source_path = None
        self.vertices = None
        self.subset_size = None
        self.quotas = None
        self.matrix = None
        self.indices = {}
        self.shares = {}
        self.original_df = None  # исходный DataFrame для экспорта
        self.results_df = None   # DataFrame для отображения в UI

        if create_dirs:
            os.makedirs(os.path.join(self.base_dir, title), exist_ok=True)
            os.makedirs(os.path.join(self.project_dir, "data"), exist_ok=True)
            os.makedirs(os.path.join(self.project_dir, "exports"), exist_ok=True)

    def load(self, df_original, source_path, vertices, subset_size, quotas, matrix):
        self.source_path = source_path
        self.vertices = vertices
        self.subset_size = subset_size
        self.quotas = quotas
        self.matrix = matrix
        self.original_df = df_original

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