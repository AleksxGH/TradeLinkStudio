import os
import json_tricks as json
from json_tricks import load as json_load
from app.core.project import Project
import pandas as pd

from app.core.result_builder import build_result_table


class ProjectManager:
    @staticmethod
    def create_project(project_name : str, project_dir : str):
        return Project(project_name, project_dir, True)

    @staticmethod
    def save_project(project: Project):
        try:
            json_filename = f"{project.title}.json"
            json_path = os.path.join(project.data_dir, json_filename)

            project_data = {
                "title": project.title,
                "base_dir": project.base_dir,
                "data_dir": project.data_dir,
                "export_dir": project.export_dir,
                "project_dir": project.project_dir,
                "source_path": project.source_path,
                "subset_size": project.subset_size,
                "quotas": project.quotas,
                "vertices": project.vertices,
                "matrix": project.matrix,
                "indices": project.indices,
                "shares": project.shares,
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)

            print(f"[DEBUG] Проект сохранен: {json_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Ошибка при сохранении проекта: {str(e)}")
            return False

    @staticmethod
    def load_project(project_dir: str):
        try:
            print(f"[DEBUG] Старт загрузки проекта: {project_dir}")

            if not os.path.isdir(project_dir):
                raise FileNotFoundError("Папка проекта не найдена")

            data_dir = os.path.join(project_dir, "data")
            if not os.path.isdir(data_dir):
                raise FileNotFoundError("Папка data не найдена")

            # Ищем json-файл проекта
            json_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
            if not json_files:
                raise FileNotFoundError("Файл проекта (.json) не найден")

            json_path = os.path.join(data_dir, json_files[0])
            print(f"[DEBUG] JSON найден: {json_path}")

            with open(json_path, "r", encoding="utf-8") as f:
                project_data = json_load(f)  # json_tricks
            print(f"[DEBUG] JSON успешно прочитан")

            # Создаем объект Project без создания папок
            project = Project(title=None, base_dir=None, create_dirs=False)

            # Восстанавливаем простые поля
            project.title = project_data.get("title")
            project.base_dir = project_data.get("base_dir")
            project.project_dir = project_data.get("project_dir")
            project.data_dir = project_data.get("data_dir")
            project.export_dir = project_data.get("export_dir")
            project.source_path = project_data.get("source_path")
            project.subset_size = project_data.get("subset_size")
            project.vertices = project_data.get("vertices")
            project.indices = project_data.get("indices")
            project.shares = project_data.get("shares")
            project.matrix = project_data.get("matrix")
            project.quotas = project_data.get("quotas")
            print(f"[DEBUG] matrix shape: {None if project.matrix is None else project.matrix.shape}")
            print(f"[DEBUG] quotas shape: {None if project.quotas is None else project.quotas.shape}")

            # Восстанавливаем df_original
            project.original_df = None
            if project.matrix is not None and project.vertices is not None:
                project.original_df = pd.DataFrame(
                    project.matrix,
                    index=project.vertices,
                    columns=project.vertices
                )
                print(f"[DEBUG] df_original восстановлен: shape={project.original_df.shape}")

            # Восстанавливаем results_df через build_result_table
            project.results_df = None
            if project.indices is not None and project.indices is not None:
                try:
                    project.results_df = build_result_table(project)
                    print(f"[DEBUG] results_df восстановлен: shape={project.results_df.shape}")
                except Exception as e:
                    print(f"[WARNING] Не удалось восстановить results_df: {e}")

            print(f"[DEBUG] Проект полностью загружен: {json_path}")
            return project

        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке проекта: {str(e)}")
            return None