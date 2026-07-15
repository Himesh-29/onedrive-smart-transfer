# Architecture & File Structure

The project is modularized into `ui`, `core`, and `utils` to separate the frontend logic from the backend file transfer logic.

## `src/core/` - Business Logic
- **`transfer_engine.py`**: The heart of the app. Runs a background worker thread processing `TransferJob`s. Uses `shutil` for copy/move, handles OS errors, and emits `TransferProgress` updates to a queue.
- **`exclusion_manager.py`**: Manages exclusion patterns. Uses a layered system: defaults loaded from `config/default_exclusions.json` + user overrides.
- **`config_manager.py`**: Persists user settings to the user's AppData/home directory.
- **`stack_detector.py`**: Detects tech stacks based on marker files (like `package.json`, `Cargo.toml`).
- **`onedrive_finder.py`**: Detects the user's OneDrive path via environment variables safely.

## `src/ui/` - Presentation Layer
- **`main_window.py`**: The central `customtkinter` interface integrating all components.
- **`transfer_queue.py`**: WinSCP-style background job queue UI. Reads from the `TransferEngine` progress queue.
- **`settings_dialog.py`**: Tabbed UI for managing exclusion patterns and general settings.
- **`drop_zone.py`**: Handles drag-and-drop file inputs.
- **`file_explorer.py` / `transfer_preview.py`**: Previews files before transfer, indicating excluded items.
- **`theme_manager.py`**: Follows Windows system themes (light/dark mode).

## `src/app.py` - Entry Point
- Handles the first-run setup wizard.
- Initializes `ConfigManager`, detects OneDrive, and launches the `MainWindow`.
