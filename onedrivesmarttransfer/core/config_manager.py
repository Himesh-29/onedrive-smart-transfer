"""
Configuration manager for OneDrive Smart Transfer.

Handles loading/saving user preferences to a JSON config file.
On first launch, asks the user where to store config files.
All config is human-readable JSON — no binary formats, no encryption.
"""

import json
import os
from typing import Any, Optional


# Default configuration values
DEFAULT_CONFIG = {
    "onedrive_path": "",
    "config_storage_path": "",
    "theme": "system",  # "system", "light", or "dark"
    "default_action": "copy",  # "copy" or "move"
    "window_geometry": "",
    "last_destination": "",
    "exclusion_overrides": {},  # User modifications to default exclusions
    "first_run": True,
}


class ConfigManager:
    """Manages persistent user configuration stored as a simple JSON file."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the config manager.

        Args:
            config_path: Path to the config file. If None, uses the default
                         location or prompts the user on first run.
        """
        self._config: dict[str, Any] = dict(DEFAULT_CONFIG)
        self._config_path: Optional[str] = config_path
        self._loaded = False

    @property
    def config_path(self) -> Optional[str]:
        """Get the current config file path."""
        return self._config_path

    @config_path.setter
    def config_path(self, path: str) -> None:
        """Set the config file path."""
        self._config_path = path

    def get_default_config_dir(self) -> str:
        """Get the default directory for config storage.

        Uses LOCALAPPDATA on Windows (e.g., C:\\Users\\<user>\\AppData\\Local).
        Falls back to USERPROFILE if LOCALAPPDATA is not available.
        """
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return os.path.join(local_appdata, "OneDriveSmartTransfer")

        user_profile = os.environ.get("USERPROFILE", "")
        return os.path.join(user_profile, ".onedrive_smart_transfer")

    def load(self) -> dict[str, Any]:
        """Load configuration from the JSON file.

        Returns:
            The loaded configuration dictionary.
        """
        if self._config_path and os.path.isfile(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                # Merge with defaults so new keys are always present
                self._config = {**DEFAULT_CONFIG, **saved_config}
                self._loaded = True
            except (json.JSONDecodeError, OSError):
                # If the config file is corrupted, use defaults
                self._config = dict(DEFAULT_CONFIG)
        else:
            self._config = dict(DEFAULT_CONFIG)

        return self._config

    def save(self) -> bool:
        """Save the current configuration to the JSON file.

        Returns:
            True if saved successfully, False otherwise.
        """
        if not self._config_path:
            return False

        try:
            config_dir = os.path.dirname(self._config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: The configuration key.
            default: Default value if the key doesn't exist.

        Returns:
            The configuration value.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save immediately.

        Args:
            key: The configuration key.
            value: The value to set.
        """
        self._config[key] = value
        self.save()

    @property
    def is_first_run(self) -> bool:
        """Check if this is the first time the app is launched."""
        return self._config.get("first_run", True)

    @property
    def onedrive_path(self) -> str:
        """Get the configured OneDrive path."""
        return self._config.get("onedrive_path", "")

    @onedrive_path.setter
    def onedrive_path(self, path: str) -> None:
        self.set("onedrive_path", path)

    @property
    def theme(self) -> str:
        """Get the configured theme preference."""
        return self._config.get("theme", "system")

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("theme", value)

    @property
    def default_action(self) -> str:
        """Get the default transfer action (copy or move)."""
        return self._config.get("default_action", "copy")

    @default_action.setter
    def default_action(self, value: str) -> None:
        self.set("default_action", value)

    @property
    def last_destination(self) -> str:
        """Get the last used destination folder."""
        return self._config.get("last_destination", "")

    @last_destination.setter
    def last_destination(self, path: str) -> None:
        self.set("last_destination", path)

    @property
    def exclusion_overrides(self) -> dict:
        """Get user's exclusion pattern overrides."""
        return self._config.get("exclusion_overrides", {})

    @exclusion_overrides.setter
    def exclusion_overrides(self, value: dict) -> None:
        self.set("exclusion_overrides", value)

    def mark_first_run_complete(self) -> None:
        """Mark that the first-run setup has been completed."""
        self.set("first_run", False)

    def to_dict(self) -> dict[str, Any]:
        """Return a copy of the full configuration dictionary."""
        return dict(self._config)
