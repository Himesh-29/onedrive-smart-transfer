# OneDrive Smart Transfer

A simple Windows app to copy your coding projects to OneDrive without backing up all the heavy build files. It automatically skips folders like `node_modules`, `venv`, and `build` so your OneDrive doesn't fill up instantly.

![App Demo GIF](https://github.com/placeholder-demo-gif.gif)
*(Placeholder: Upload a short GIF of a transfer here)*

## Why this exists

When you sync programming projects to OneDrive, it usually tries to upload thousands of tiny files from dependency folders. This takes forever and wastes space. This app detects what kind of project you're dropping in and automatically filters out the junk before transferring. 

Everything runs completely offline on your machine. No data is sent anywhere.

## Features

- **Drag and Drop**: Move files and folders directly from Windows File Explorer into the application.
- **Smart Tech Stack Detection**: Automatically identifies the type of project (Node.js, Python, Java, Rust, Flutter, Go, C#, C++, Ruby, PHP, etc.) based on standard marker files like `package.json` or `Cargo.toml`.
- **Auto-Exclusion**: Automatically skips over 100 common build artifacts including `node_modules`, `venv`, `__pycache__`, `build`, `target`, and `.gradle`.
- **Fully Configurable**: Easily add, remove, or toggle exclusion patterns through a simple interface.
- **Copy or Move**: Choose whether to keep the original files where they are or move them to the destination.
- **Background Transfer Queue**: Run multiple transfers simultaneously. The queue provides individual progress bars, transfer speeds, and estimated completion times.
- **Native Error Handling**: When a file fails to transfer, you'll get standard Windows-style prompts to Retry, Skip, or Skip All.
- **System Theme Support**: The interface automatically matches your Windows light or dark mode setting, or you can change it manually.
- **Privacy First**: Operates 100% offline. It does not read your file contents, access your registry, or send any telemetry.
- **Persistent Settings**: Your preferences and exclusion rules are saved and will still be there the next time you open the app.

## Setup and Usage

**Step 1: Download and Run**
Grab the latest `OneDriveSmartTransfer-Windows.zip` from the Releases page, extract it, and double-click `OneDriveSmartTransfer.exe`. There is no installer.

**Step 2: First-Time Configuration**
When you open it for the first time, the app will ask where you want to save its configuration files. It's usually best to select a folder inside your OneDrive so your settings are backed up and synced across your computers.

![Welcome Screen](https://github.com/user-attachments/assets/8abc35c5-30a4-41c1-9ab1-fb2f532307e2)
![Configuration File Setup Location](https://github.com/user-attachments/assets/8abc35c5-30a4-41c1-9ab1-fb2f532307e2)


**Step 3: Transferring Files**
Drag and drop your project folder directly into the main window. 

![Main Window Placeholder](https://github.com/placeholder-main-window.png)
*(Placeholder: Screenshot of the main drop zone)*

**Step 4: Choose Destination**
Select where inside your OneDrive you want the project to go.

**Step 5: Review and Start**
The app will show you exactly which files it's going to transfer and which ones it's going to skip. You can edit the exclusion list in the settings if you need to. Click start when you're ready.

![Settings Placeholder](https://github.com/placeholder-settings-screen.png)
*(Placeholder: Screenshot of the settings/exclusion rules window)*

## Supported Projects

The app automatically recognizes and filters out build files for:
- Node.js / JavaScript (`node_modules`, `.next`, etc)
- Python (`venv`, `__pycache__`, `dist`, etc)
- Java (`target`, `build`, etc)
- C# / .NET (`bin`, `obj`, etc)
- C / C++ (`build`, `Debug`, etc)
- Rust (`target`)
- Go (`vendor`)
- And many others (PHP, Ruby, Flutter, Android, iOS, Unity).

Note: Version control folders like `.git` are kept by default since you usually want those backed up.

## Building from source

If you want to run the code yourself instead of using the pre-built executable:

1. Clone the repository
2. Set up a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate`
4. Install requirements: `pip install -r requirements.txt`
5. Run it: `python src/app.py`

To build the executable yourself, just run `python build_exe.py` after installing the requirements.

## Project Structure

If you're interested in how the application is built, here is a quick overview of the main files and what they do:

- `src/app.py`: The main entry point of the application. It handles the initial launch and the first-run configuration wizard.
- `src/ui/`: Contains all the graphical interface components.
  - `main_window.py`: The primary window where you drag and drop files.
  - `settings_dialog.py`: The window where you manage your exclusion rules.
  - `transfer_queue.py`: The interface that displays active and queued transfers.
- `src/core/`: Contains the underlying logic.
  - `exclusion_manager.py`: Handles the rules for what gets skipped during a transfer.
  - `stack_detector.py`: Scans project folders to figure out what programming language they use.
  - `transfer_engine.py`: The engine that safely copies or moves files in the background and reports progress.
- `config/default_exclusions.json`: A list of the default, built-in rules for what files to skip for each language.
- `build_exe.py`: A helper script that uses PyInstaller to bundle the application into a standalone executable.
