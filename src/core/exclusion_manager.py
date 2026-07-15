"""
Exclusion pattern manager for OneDrive Smart Transfer.

Manages tech-stack-based exclusion patterns using a config-driven dict/map.
Users can add, remove, toggle, import, export, and reset patterns.
All changes persist immediately to the config file.
"""

import json
import os
import fnmatch
from typing import Optional

from src.utils.resource_path import resource_path


# Cache for the default exclusions so we don't re-read from disk each time
_default_exclusions_cache: Optional[dict] = None


def load_default_exclusions() -> dict:
    """Load the default exclusion patterns from the bundled JSON config.

    Returns:
        Dictionary of exclusion categories with their patterns.
    """
    global _default_exclusions_cache
    if _default_exclusions_cache is not None:
        return _default_exclusions_cache

    config_file = resource_path(os.path.join("config", "default_exclusions.json"))
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            _default_exclusions_cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _default_exclusions_cache = {}

    return _default_exclusions_cache


class ExclusionManager:
    """Manages exclusion patterns with user customization support.

    The exclusion system works in layers:
      1. Default patterns loaded from config/default_exclusions.json
      2. User overrides (additions, removals, toggles) stored in user config

    User overrides are structured as:
    {
        "category_id": {
            "disabled_patterns": ["pattern1"],  # defaults that user turned off
            "added_patterns": ["pattern2"],      # user-added patterns
            "category_enabled": true             # toggle entire category
        }
    }
    """

    def __init__(self, user_overrides: Optional[dict] = None):
        """Initialize with default patterns and optional user overrides.

        Args:
            user_overrides: User's customizations from the config file.
        """
        self._defaults = load_default_exclusions()
        self._user_overrides = user_overrides or {}
        self._on_change_callback = None

    def set_on_change_callback(self, callback) -> None:
        """Set a callback that fires when exclusions change.

        Args:
            callback: A callable that receives the updated user_overrides dict.
        """
        self._on_change_callback = callback

    def _notify_change(self) -> None:
        """Notify the callback that exclusions have changed."""
        if self._on_change_callback:
            self._on_change_callback(self._user_overrides)

    def get_categories(self) -> list[dict]:
        """Get all exclusion categories with their current state.

        Returns:
            List of category dicts with keys:
              - id: category identifier
              - name: human-readable name
              - enabled: whether the category is active
              - patterns: list of pattern dicts with 'name', 'enabled', 'is_default'
        """
        categories = []
        for cat_id, cat_data in self._defaults.items():
            overrides = self._user_overrides.get(cat_id, {})
            cat_enabled = overrides.get("category_enabled", True)
            disabled_patterns = set(overrides.get("disabled_patterns", []))
            added_patterns = overrides.get("added_patterns", [])

            # Combine default dir and file patterns
            all_default_patterns = (
                cat_data.get("exclude_dirs", []) + cat_data.get("exclude_files", [])
            )

            patterns = []
            # Default patterns
            for p in all_default_patterns:
                patterns.append({
                    "name": p,
                    "enabled": p not in disabled_patterns,
                    "is_default": True,
                })
            # User-added patterns
            for p in added_patterns:
                patterns.append({
                    "name": p,
                    "enabled": True,
                    "is_default": False,
                })

            categories.append({
                "id": cat_id,
                "name": cat_data.get("name", cat_id),
                "enabled": cat_enabled,
                "marker_files": cat_data.get("marker_files", []),
                "patterns": patterns,
            })

        return categories

    def get_active_exclusions(self, active_category_ids: Optional[list[str]] = None) -> dict:
        """Get the currently active exclusion dirs and files.

        Args:
            active_category_ids: If provided, only these categories are used.
                                 If None, all enabled categories are used.

        Returns:
            Dict with 'dirs' (set of dir names/patterns) and 'files' (set of file patterns).
        """
        exclude_dirs = set()
        exclude_files = set()

        for cat_id, cat_data in self._defaults.items():
            if active_category_ids is not None and cat_id not in active_category_ids:
                # Skip categories not detected, but always include "general_always"
                if cat_id != "general_always":
                    continue

            overrides = self._user_overrides.get(cat_id, {})
            if not overrides.get("category_enabled", True):
                continue

            disabled = set(overrides.get("disabled_patterns", []))
            added = overrides.get("added_patterns", [])

            for d in cat_data.get("exclude_dirs", []):
                if d not in disabled:
                    exclude_dirs.add(d)

            for f in cat_data.get("exclude_files", []):
                if f not in disabled:
                    exclude_files.add(f)

            # User-added patterns — treat as dirs unless they contain wildcards
            for p in added:
                if "*" in p or "." in p:
                    exclude_files.add(p)
                else:
                    exclude_dirs.add(p)

        return {"dirs": exclude_dirs, "files": exclude_files}

    def toggle_pattern(self, category_id: str, pattern_name: str, enabled: bool) -> None:
        """Toggle a specific pattern on or off.

        Args:
            category_id: The category this pattern belongs to.
            pattern_name: The pattern to toggle.
            enabled: Whether to enable (True) or disable (False) the pattern.
        """
        if category_id not in self._user_overrides:
            self._user_overrides[category_id] = {}

        overrides = self._user_overrides[category_id]
        disabled = set(overrides.get("disabled_patterns", []))

        if enabled:
            disabled.discard(pattern_name)
        else:
            disabled.add(pattern_name)

        overrides["disabled_patterns"] = list(disabled)
        self._notify_change()

    def toggle_category(self, category_id: str, enabled: bool) -> None:
        """Toggle an entire category on or off.

        Args:
            category_id: The category to toggle.
            enabled: Whether to enable or disable the category.
        """
        if category_id not in self._user_overrides:
            self._user_overrides[category_id] = {}
        self._user_overrides[category_id]["category_enabled"] = enabled
        self._notify_change()

    def add_pattern(self, category_id: str, pattern: str) -> bool:
        """Add a user-defined exclusion pattern to a category.

        Args:
            category_id: The category to add to.
            pattern: The exclusion pattern (dir name or file glob).

        Returns:
            True if added successfully, False if it already exists.
        """
        if category_id not in self._user_overrides:
            self._user_overrides[category_id] = {}

        overrides = self._user_overrides[category_id]
        added = overrides.get("added_patterns", [])

        if pattern in added:
            return False

        # Check if it's already a default pattern
        cat_data = self._defaults.get(category_id, {})
        all_defaults = cat_data.get("exclude_dirs", []) + cat_data.get("exclude_files", [])
        if pattern in all_defaults:
            return False

        added.append(pattern)
        overrides["added_patterns"] = added
        self._notify_change()
        return True

    def remove_pattern(self, category_id: str, pattern: str) -> None:
        """Remove a pattern (default patterns are disabled, custom patterns are deleted).

        Args:
            category_id: The category to remove from.
            pattern: The pattern to remove.
        """
        if category_id not in self._user_overrides:
            self._user_overrides[category_id] = {}

        overrides = self._user_overrides[category_id]

        # If it's a user-added pattern, remove it
        added = overrides.get("added_patterns", [])
        if pattern in added:
            added.remove(pattern)
            overrides["added_patterns"] = added
        else:
            # If it's a default pattern, disable it
            self.toggle_pattern(category_id, pattern, False)

        self._notify_change()

    def reset_to_defaults(self) -> None:
        """Reset all exclusion patterns to defaults, removing all user overrides."""
        self._user_overrides.clear()
        self._notify_change()

    def get_user_overrides(self) -> dict:
        """Get the current user overrides for persistence.

        Returns:
            The user overrides dictionary (to be saved to config).
        """
        return self._user_overrides

    def export_config(self, filepath: str) -> bool:
        """Export the current exclusion configuration to a JSON file.

        Args:
            filepath: Path to save the export.

        Returns:
            True if exported successfully.
        """
        try:
            export_data = {
                "defaults": self._defaults,
                "user_overrides": self._user_overrides,
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False

    def import_config(self, filepath: str) -> bool:
        """Import exclusion configuration from a JSON file.

        Args:
            filepath: Path to the import file.

        Returns:
            True if imported successfully.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                import_data = json.load(f)
            if "user_overrides" in import_data:
                self._user_overrides = import_data["user_overrides"]
                self._notify_change()
                return True
        except (OSError, json.JSONDecodeError, KeyError):
            pass
        return False


def should_exclude_dir(dirname: str, exclude_dirs: set[str]) -> bool:
    """Check if a directory name should be excluded.

    Args:
        dirname: The directory name (not full path).
        exclude_dirs: Set of directory name patterns to exclude.

    Returns:
        True if the directory should be excluded.
    """
    for pattern in exclude_dirs:
        if fnmatch.fnmatch(dirname, pattern):
            return True
    return False


def should_exclude_file(filename: str, exclude_files: set[str]) -> bool:
    """Check if a file name should be excluded.

    Args:
        filename: The file name (not full path).
        exclude_files: Set of file name patterns to exclude.

    Returns:
        True if the file should be excluded.
    """
    for pattern in exclude_files:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False
