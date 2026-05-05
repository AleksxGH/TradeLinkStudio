import os
import json_tricks as json
from app.core.project import Project


class ProjectManager:

    @staticmethod
    def create_default_project(paths):
        project_name = paths.get_next_project_name()
        return Project(project_name)


    @staticmethod
    def create_project(project_name: str):
        return Project(project_name)


    @staticmethod
    def save_project(project, datastore, paths):

        project_dir = paths.get_project_path(project.title)

        data_dir = os.path.join(project_dir, "data")

        os.makedirs(data_dir, exist_ok=True)

        project_data = {
            "title": project.title,
            "current_index": datastore.current_index,
            "states": datastore.states
        }

        with open(
            os.path.join(data_dir, "project.json"),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(project_data, f, indent=2)

        project.is_saved = True
        project.is_dirty = False