import os
import sys


def get_app_base_path():
    """Return base path for resources in source and PyInstaller onefile modes."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resource_path(*parts):
    return os.path.join(get_app_base_path(), *parts)


def icon_path(filename):
    return resource_path("resources", "icons", filename)
