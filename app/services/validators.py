INVALID_WINDOWS_CHARS = set('<>:"/\\|?*')
RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def validate_project_name(name):
    normalized = (name or "").strip()

    if not normalized:
        return False, "Project name cannot be empty"

    if any(ch in INVALID_WINDOWS_CHARS for ch in normalized):
        return False, "Project name contains invalid characters"

    if normalized.endswith(".") or normalized.endswith(" "):
        return False, "Project name cannot end with a dot or space"

    if normalized.upper() in RESERVED_WINDOWS_NAMES:
        return False, "Project name is reserved by Windows"

    return True, "", normalized


def validate_vertex_names(names):
    normalized = [(name or "").strip() for name in names]

    if any(not name for name in normalized):
        return False, "Vertex names cannot be empty"

    if any("\n" in name or "\r" in name for name in normalized):
        return False, "Vertex names cannot contain line breaks"

    if len(set(normalized)) != len(normalized):
        return False, "Vertex names must be unique"

    return True, "", normalized
