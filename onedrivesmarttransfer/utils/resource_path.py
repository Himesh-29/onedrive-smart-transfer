"""
PyInstaller-compatible resource path resolver.

When the app is packaged with PyInstaller, bundled data files are extracted
to a temporary directory (sys._MEIPASS). This utility ensures paths work
both in development and in the packaged .exe.
"""

import os
import sys


def resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource, works for dev and PyInstaller.

    Args:
        relative_path: Path relative to the project root (in dev) or
                       the PyInstaller bundle root (in packaged mode).

    Returns:
        Absolute path to the resource.
    """
    # PyInstaller sets sys._MEIPASS to the temp extraction directory
    # In development: go from src/utils/ → src/ → project_root/
    base_path = getattr(
        sys, "_MEIPASS",
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    return os.path.join(base_path, relative_path)
