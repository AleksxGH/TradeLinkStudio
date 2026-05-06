import os
import sys


class AppPaths:

    def __init__(self, base_dir=None):

        self.base_dir = base_dir or self._default_base()

        self.projects_dir = os.path.join(self.base_dir, "Projects")

        os.makedirs(self.projects_dir, exist_ok=True)

    def _default_base(self):

        if sys.platform == "win32":
            return os.path.join(
                os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
                "TradeLink Studio"
            )

        return os.path.join(
            os.path.expanduser("~"),
            "TradeLink Studio"
        )

    def get_project_path(self, name):

        return os.path.join(self.projects_dir, name)

    def get_next_project_name(self):

        existing = []

        if not os.path.exists(self.projects_dir):
            return "Untitled_1"

        for name in os.listdir(self.projects_dir):

            if name.startswith("Untitled_"):

                try:
                    num = int(name.split("_")[1])
                    existing.append(num)
                except:
                    pass

        return f"Untitled_{max(existing, default=0) + 1}"