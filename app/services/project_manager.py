import os
import json
import shutil

import networkx as nx
import numpy as np

from app.core.project import Project
from app.core.datastore import DataStore


class ProjectManager:

    @staticmethod
    def _serialize_value(value):

        if isinstance(value, np.generic):

            return value.item()

        if isinstance(value, np.ndarray):

            return [ProjectManager._serialize_value(item) for item in value.tolist()]

        if isinstance(value, nx.DiGraph):

            return {
                "__type__": "DiGraph",
                "nodes": list(value.nodes()),
                "edges": [
                    {
                        "source": source,
                        "target": target,
                        "attributes": ProjectManager._serialize_value(attributes)
                    }
                    for source, target, attributes in value.edges(data=True)
                ]
            }

        if isinstance(value, dict):

            return {
                key: ProjectManager._serialize_value(item)
                for key, item in value.items()
            }

        if isinstance(value, list):

            return [ProjectManager._serialize_value(item) for item in value]

        if isinstance(value, tuple):

            return [ProjectManager._serialize_value(item) for item in value]

        return value


    @staticmethod
    def rename_project_directory(project, new_title):

        new_title = new_title.strip()

        if not new_title:

            raise ValueError("Project title cannot be empty")

        if project.project_dir is None:

            project.title = new_title
            return

        parent_dir = os.path.dirname(project.project_dir)
        new_project_dir = os.path.join(parent_dir, new_title)

        if os.path.abspath(new_project_dir) == os.path.abspath(project.project_dir):

            project.title = new_title
            return

        if os.path.exists(new_project_dir):

            raise FileExistsError("Project folder with this name already exists")

        if not os.path.exists(project.project_dir):

            project.title = new_title
            project.project_dir = new_project_dir
            return

        os.makedirs(parent_dir, exist_ok=True)
        shutil.move(project.project_dir, new_project_dir)

        project.title = new_title
        project.project_dir = new_project_dir


    @staticmethod
    def _deserialize_value(value):

        if isinstance(value, dict):

            if value.get("__type__") == "DiGraph":

                graph = nx.DiGraph()
                graph.add_nodes_from(value.get("nodes", []))

                for edge in value.get("edges", []):

                    graph.add_edge(
                        edge.get("source"),
                        edge.get("target"),
                        **edge.get("attributes", {})
                    )

                return graph

            return {
                key: ProjectManager._deserialize_value(item)
                for key, item in value.items()
            }

        if isinstance(value, list):

            return [ProjectManager._deserialize_value(item) for item in value]

        return value

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

        desired_dir = os.path.join(os.path.dirname(project.project_dir), project.title)

        if os.path.abspath(desired_dir) != os.path.abspath(project.project_dir):

            ProjectManager.rename_project_directory(project, project.title)

        project_dir = project.project_dir

        data_dir = os.path.join(project_dir, "data")

        export_dir = os.path.join(project_dir, "export")

        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        os.makedirs(export_dir, exist_ok=True)

        payload = {
            "title": project.title,
            "current_index": datastore.current_index,
            "states": ProjectManager._serialize_value(datastore.states)
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

        try:

            with open(data_file, "r", encoding="utf-8") as f:

                data = json.load(f)

        except (FileNotFoundError, json.JSONDecodeError):

            return None

        project = Project(data["title"])

        project.project_dir = project_dir
        project.is_saved = True

        datastore = DataStore()

        datastore.states = ProjectManager._deserialize_value(data.get("states", []))
        for state in datastore.states:

            if isinstance(state, dict):

                state.setdefault("project_title", project.title)

        datastore.current_index = data.get("current_index", len(datastore.states) - 1)

        if datastore.current_index >= len(datastore.states):

            datastore.current_index = len(datastore.states) - 1

        if datastore.current_index < -1:

            datastore.current_index = -1

        return project, datastore