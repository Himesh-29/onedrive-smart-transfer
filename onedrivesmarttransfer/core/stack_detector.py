"""
Tech stack detector for OneDrive Smart Transfer.

Determines the tech stack of a project folder by looking for marker files
(e.g., package.json → Node.js, Cargo.toml → Rust). Only file NAMES are
checked — file contents are NEVER read. This ensures privacy and speed.
"""

import os
import fnmatch
from typing import Optional

from onedrivesmarttransfer.core.exclusion_manager import load_default_exclusions


def detect_stacks(folder_path: str, max_depth: int = 2) -> list[str]:
    """Detect which tech stacks a project folder uses.

    Scans only file names (never contents) in the top levels of the folder
    looking for marker files defined in the exclusion config.

    Args:
        folder_path: Path to the project folder to analyze.
        max_depth: How many levels deep to search for marker files.
                   Default is 2 (root + one level of subdirectories).

    Returns:
        List of detected category IDs (e.g., ["javascript_node", "python"]).
    """
    if not os.path.isdir(folder_path):
        return []

    defaults = load_default_exclusions()
    detected = set()

    # Collect all filenames in the top levels
    filenames_in_project = set()
    try:
        for depth_level in range(max_depth):
            if depth_level == 0:
                # Root level
                try:
                    for entry in os.listdir(folder_path):
                        filenames_in_project.add(entry)
                except OSError:
                    pass
            else:
                # One level deeper — check immediate subdirectories
                try:
                    for entry in os.listdir(folder_path):
                        subdir = os.path.join(folder_path, entry)
                        if os.path.isdir(subdir):
                            try:
                                for sub_entry in os.listdir(subdir):
                                    filenames_in_project.add(sub_entry)
                            except OSError:
                                pass
                except OSError:
                    pass
    except OSError:
        pass

    # Match filenames against marker files for each category
    for cat_id, cat_data in defaults.items():
        marker_files = cat_data.get("marker_files", [])
        if not marker_files:
            continue

        for marker in marker_files:
            if _matches_any_filename(marker, filenames_in_project):
                detected.add(cat_id)
                break

    return list(detected)


def _matches_any_filename(pattern: str, filenames: set[str]) -> bool:
    """Check if a marker file pattern matches any filename in the set.

    Supports both exact names (e.g., 'package.json') and glob patterns
    (e.g., '*.csproj').

    Args:
        pattern: The marker file pattern.
        filenames: Set of filenames to check against.

    Returns:
        True if any filename matches the pattern.
    """
    if "*" in pattern or "?" in pattern:
        # Glob pattern — check each filename
        for fname in filenames:
            if fnmatch.fnmatch(fname, pattern):
                return True
        return False
    else:
        # Exact name match
        return pattern in filenames


def get_stack_display_names(category_ids: list[str]) -> list[str]:
    """Get human-readable names for detected tech stacks.

    Args:
        category_ids: List of category IDs from detect_stacks().

    Returns:
        List of display names (e.g., ["JavaScript / Node.js", "Python"]).
    """
    defaults = load_default_exclusions()
    names = []
    for cat_id in category_ids:
        if cat_id in defaults:
            names.append(defaults[cat_id].get("name", cat_id))
    return names
