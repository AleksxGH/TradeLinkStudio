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

            "use_default_project_path": True,
            "custom_project_path": "",

            "use_project_export_folder": True
        }

    def load(self):
        if not os.path.exists(self.config_path):
            self.save()
            return self.data

        with open(self.config_path, "r", encoding="utf-8") as file:
            loaded = json.load(file)

        removed_weighted = "weighted_mode" in loaded
        removed_normalization = "normalization" in loaded
        removed_precision = "decimal_precision" in loaded
        loaded.pop("weighted_mode", None)
        loaded.pop("normalization", None)
        loaded.pop("decimal_precision", None)
        merged = dict(self.data)
        merged.update(loaded)
        self.data = merged

        if removed_precision or removed_weighted or removed_normalization:
            self.save()

        return self.data

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value