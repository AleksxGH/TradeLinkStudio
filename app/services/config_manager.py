import json
import os

from app.services.app_paths import AppPaths

class ConfigManager:

    def __init__(self):
        self.app_paths = AppPaths()
        self.user_data_dir = os.path.join(self.app_paths.base_dir, "UserData")
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.config_path = os.path.join(self.user_data_dir, "config.json")
        self.legacy_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

        self.data = {
            "use_standard_dirs": True,

            "use_default_project_path": True,
            "custom_project_path": "",

            "use_project_export_folder": True
        }

    def load(self):
        if not os.path.exists(self.config_path):
            # migrate legacy config from app root if present, otherwise create empty template
            if os.path.exists(self.legacy_config_path):
                try:
                    with open(self.legacy_config_path, "r", encoding="utf-8") as file:
                        loaded = json.load(file)
                    self.data.update(loaded)
                    self.save()
                    try:
                        os.remove(self.legacy_config_path)
                    except Exception:
                        pass
                    return self.data
                except Exception:
                    pass

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

        # remove legacy config if it still exists in app root
        if os.path.exists(self.legacy_config_path):
            try:
                os.remove(self.legacy_config_path)
            except Exception:
                pass

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value