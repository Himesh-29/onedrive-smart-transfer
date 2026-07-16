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


def get_app_dir() -> str:
    """Get the directory where the application is running from."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_pointer_path() -> str:
    """Get the path to the configuration pointer file."""
    return os.path.join(get_app_dir(), "ost_config_path.txt")


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

    # Step 1: Tell user about settings
    messagebox.showinfo(
        "Welcome to OneDrive Smart Transfer",
        "Welcome! Before we begin, we need to choose where to save your configuration.\n\n"
        "It is recommended to select a folder inside your OneDrive so your settings sync across computers.",
        parent=root,
    )
    
    # Prompt for config directory
    config_dir = filedialog.askdirectory(
        title="Select Folder to Save Configuration",
        parent=root,
    )
    
    if not config_dir:
        # Fallback to local app data if user cancels
        config_dir = config.get_default_config_dir()
        messagebox.showinfo("Default Used", f"Using default location:\n{config_dir}", parent=root)

    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "onedrive_smart_transfer_config.json")
    config.config_path = config_path

    # Save a pointer file next to the EXE
    pointer_path = get_pointer_path()
    try:
        with open(pointer_path, "w", encoding="utf-8") as f:
            f.write(config_path)
    except OSError:
        # If we can't write next to the EXE (e.g., Program Files), silently ignore
        # and rely on the fallback mechanism or default paths.
        pass

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

    Checks the pointer file next to the EXE. Falls back to default config dir.

    Returns:
        Path to the config file if found, None otherwise.
    """
    # 1. Check pointer file
    pointer_path = get_pointer_path()
    if os.path.isfile(pointer_path):
        try:
            with open(pointer_path, "r", encoding="utf-8") as f:
                saved_path = f.read().strip()
            if os.path.isfile(saved_path):
                return saved_path
        except OSError:
            pass

    # 2. Check default fallback
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
