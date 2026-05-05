import os
import sys


class AppPaths:

    def __init__(self, base_dir=None):

        self.base_dir = base_dir or self._get_default_base_dir()

        self.projects_dir = os.path.join(
            self.base_dir,
            "Projects"
        )

        os.makedirs(self.projects_dir, exist_ok=True)

    def _get_default_base_dir(self):

        if sys.platform == "win32":

            program_data = os.environ.get("PROGRAMDATA")

            if program_data is None:

                program_data = r"C:\ProgramData"

            return os.path.join(
                program_data,
                "TradeLink Studio"
            )

        return os.path.join(
            os.path.expanduser("~"),
            "TradeLink Studio"
        )

    def get_projects_dir(self):

        return self.projects_dir

    def get_project_path(self, project_name):

        return os.path.join(
            self.projects_dir,
            project_name
        )

    def get_next_project_name(self):

        existing_numbers = []

        if not os.path.exists(self.projects_dir):

            return "Untitled_1"

        for name in os.listdir(self.projects_dir):

            if not name.startswith("Untitled_"):

                continue

            parts = name.split("_")

            if len(parts) != 2:

                continue

            try:
                number = int(parts[1])
                existing_numbers.append(number)

            except ValueError:

                continue

        next_index = max(existing_numbers, default=0) + 1

        return f"Untitled_{next_index