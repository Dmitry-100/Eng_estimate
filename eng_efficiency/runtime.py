from __future__ import annotations

import os
from pathlib import Path
import sys


APP_DIR_NAME = "EngEstimate"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def bundled_resource(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def writable_data_dir() -> Path:
    if is_frozen():
        if os.name == "nt":
            appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return appdata / APP_DIR_NAME
        return Path.home() / f".{APP_DIR_NAME.lower()}"

    return resource_root() / "data"


def workbook_path() -> Path:
    return bundled_resource("Engineering Efficiency Measurement.xlsx")


def projects_storage_path() -> Path:
    return writable_data_dir() / "projects.json"
