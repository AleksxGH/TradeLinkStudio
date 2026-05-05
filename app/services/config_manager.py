import json
import os

class ConfigManager:

    def __init__(self):
        self.config_path = os.path.join(
            os.getcwd(),
            "config.json"
        )

        self.data = {
            "use_standard_dirs": True,
            "weighted_mode": True,
            "normalization": True,
            "decimal_precision": 6,

            "use_default_project_path": True,
            "custom_project_path": "",

            "use_project_export_folder": True
        }

    def load(self):
        if not os.path.exists(self.config_path):
            self.save()
            return self.data

        with open(self.config_path, "r", encoding="utf-8") as file:
            self.data = json.load(file)
        return self.data

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value