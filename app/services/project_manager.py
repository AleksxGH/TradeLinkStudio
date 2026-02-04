import os
import json_tricks as json
from app.core.project import Project


class ProjectManager:
    @staticmethod
    def create_project(project_name : str, project_dir : str):
        return Project(project_name, project_dir)

    @staticmethod
    def save_project(project: Project):
        try:
            json_filename = f"{project.title}.json"
            json_path = os.path.join(project.project_dir, json_filename)

            project_data = {
                "title": project.title,
                "base_dir": project.base_dir,
                "project_dir": project.project_dir,
                "source_path": project.source_path,
                "subset_size": project.subset_size,
                "quotas": project.quotas,
                "vertices": project.vertices,
                "matrix": project.matrix,
                "results": project.results,
            }

            # Обработка DataFrame объектов
            if project.df_original is not None:
                # Сохраняем DataFrame как CSV и запоминаем путь
                csv_filename = f"{project.title}_original.csv"
                csv_path = os.path.join(project.project_dir, csv_filename)
                project.df_original.to_csv(csv_path, index=False)
                project_data["df_original_path"] = csv_path

            if project.results_df is not None:
                # Сохраняем results_df как CSV и запоминаем путь
                results_csv_filename = f"{project.title}_results.csv"
                results_csv_path = os.path.join(project.project_dir, results_csv_filename)
                project.results_df.to_csv(results_csv_path, index=False)
                project_data["results_df_path"] = results_csv_path

            # Сохраняем в JSON файл
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)

            print(f"Проект сохранен: {json_path}")
            return True

        except Exception as e:
            print(f"Ошибка при сохранении проекта: {str(e)}")
            return False

