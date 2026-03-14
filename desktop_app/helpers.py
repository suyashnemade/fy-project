"""
Helper functions for the desktop application.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

from core.config import SEARCH_HISTORY_PATH
from core.logger import get_logger

logger = get_logger(__name__)

MAX_HISTORY = 20


def human_size(nbytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def open_in_explorer(filepath: str | Path):
    """Open the containing folder in Explorer and select the file."""
    filepath = os.path.normpath(str(filepath))
    if sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", filepath])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", filepath])
    else:
        subprocess.Popen(["xdg-open", os.path.dirname(filepath)])


def open_in_default_viewer(filepath: str | Path):
    """Open file in the system default viewer."""
    filepath = os.path.normpath(str(filepath))
    if sys.platform == "win32":
        os.startfile(filepath)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])


def load_search_history() -> list:
    """Load search history from disk."""
    if SEARCH_HISTORY_PATH.exists():
        try:
            with open(SEARCH_HISTORY_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load search history: {e}")
            return []
    return []


def save_search_history(history: list):
    """Save search history to disk."""
    SEARCH_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(SEARCH_HISTORY_PATH, "w") as f:
            json.dump(history[:MAX_HISTORY], f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save search history: {e}")
