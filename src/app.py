"""
OneDrive Smart Transfer — Application Entry Point.

A Windows desktop application for transferring project files to OneDrive
while automatically excluding build artifacts (node_modules, venv, etc.).

100% offline • No file contents read • No registry access • No telemetry
"""

import os
import sys

# Ensure the project root is in the Python path
# This allows imports like `from src.core.config_manager import ConfigManager`
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config_manager import ConfigManager
from src.core.onedrive_finder import detect_onedrive_path
from src.ui.main_window import MainWindow
from src.ui.theme_manager import theme_manager


def run_first_setup(config: ConfigManager) -> None:
    """Run the first-time setup wizard.

    Asks the user for:
      1. Where to store config files
      2. Confirms the detected OneDrive path

    Args:
        config: The config manager instance.
    """
    import customtkinter as ctk
    from tkinter import filedialog, messagebox

    # Initialize with system theme for the setup dialog
    ctk.set_appearance_mode("system")

    # Use a simple root window for dialogs
    root = ctk.CTk()
    root.withdraw()

    # Step 1: Ask where to store config
    messagebox.showinfo(
        "Welcome to OneDrive Smart Transfer",
        "Welcome! Before we begin, please choose where to store your settings.\n\n"
        "This includes your exclusion patterns, theme preferences, and other settings.\n"
        "A simple JSON file will be created at the location you choose.",
        parent=root,
    )

    default_dir = config.get_default_config_dir()
    config_dir = filedialog.askdirectory(
        title="Choose Settings Storage Location",
        initialdir=os.path.dirname(default_dir),
        parent=root,
    )

    if not config_dir:
        config_dir = default_dir

    config_path = os.path.join(config_dir, "onedrive_smart_transfer_config.json")
    config.config_path = config_path

    # Step 2: Detect and confirm OneDrive path
    detected = detect_onedrive_path()
    if detected:
        confirm = messagebox.askyesno(
            "OneDrive Detected",
            f"We found your OneDrive folder at:\n\n{detected}\n\n"
            "Is this correct?\n\n"
            "Click 'Yes' to use this path, or 'No' to choose a different folder.",
            parent=root,
        )
        if confirm:
            config.set("onedrive_path", detected)
        else:
            folder = filedialog.askdirectory(
                title="Select Your OneDrive Folder",
                parent=root,
            )
            if folder:
                config.set("onedrive_path", folder)
    else:
        messagebox.showinfo(
            "OneDrive Not Found",
            "We couldn't automatically detect your OneDrive folder.\n\n"
            "Please select your OneDrive folder in the next dialog.\n"
            "You can change this later in Settings.",
            parent=root,
        )
        folder = filedialog.askdirectory(
            title="Select Your OneDrive Folder",
            parent=root,
        )
        if folder:
            config.set("onedrive_path", folder)

    # Mark first run complete and save
    config.mark_first_run_complete()
    config.save()

    root.destroy()


def find_existing_config() -> str | None:
    """Try to find an existing config file.

    Checks the default config directory for an existing config.

    Returns:
        Path to the config file if found, None otherwise.
    """
    config = ConfigManager()
    default_dir = config.get_default_config_dir()
    default_path = os.path.join(default_dir, "onedrive_smart_transfer_config.json")
    if os.path.isfile(default_path):
        return default_path
    return None


def main():
    """Main application entry point."""
    # Try to find an existing config
    config = ConfigManager()
    existing_config = find_existing_config()

    if existing_config:
        config.config_path = existing_config
        config.load()
    else:
        # Check if this is the first run
        run_first_setup(config)

    # If the config was loaded and it's still marked as first run, run setup
    if config.is_first_run:
        run_first_setup(config)

    # Launch the main application
    app = MainWindow(config_manager=config)
    app.mainloop()


if __name__ == "__main__":
    main()
