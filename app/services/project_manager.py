import os
import json

from app.core.project import Project
from app.core.datastore import DataStore


class ProjectManager:

    @staticmethod
    def create_default_project(paths):

        name = paths.get_next_project_name()

        project_dir = paths.get_project_path(name)

        project = Project(name)

        project.project_dir = project_dir

        return project


    @staticmethod
    def create_custom_project(name, user_path):

        project_dir = os.path.join(user_path, name)

        project = Project(name)

        project.project_dir = project_dir

        return project


    @staticmethod
    def save_project(project, datastore):

        if project.project_dir is None:

            raise ValueError("Project directory is not set")

        project_dir = project.project_dir

        data_dir = os.path.join(project_dir, "data")

        export_dir = os.path.join(project_dir, "export")

        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        os.makedirs(export_dir, exist_ok=True)

        payload = {
            "title": project.title,
            "current_index": datastore.current_index,
            "states": datastore.states
        }

        with open(
            os.path.join(data_dir, "project.json"),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(payload, f, indent=2)

        project.is_saved = True
        project.is_dirty = False


    @staticmethod
    def load_project(project_dir):

        data_file = os.path.join(project_dir, "data", "project.json")

        with open(data_file, "r", encoding="utf-8") as f:

            data = json.load(f)

        project = Project(data["title"])

        project.project_dir = project_dir
        project.is_saved = True

        datastore = DataStore()

        datastore.states = data["states"]
        datastore.current_index = data["current_index"]

        return project, datastore