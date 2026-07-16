# OneDrive Smart Transfer

<p align="center">
  <a href="https://pypi.org/project/onedrive-smart-transfer/"><img src="https://img.shields.io/pypi/v/onedrive-smart-transfer.svg?color=blue" alt="PyPI version"></a>&nbsp;
  <a href="https://pypi.org/project/onedrive-smart-transfer/"><img src="https://img.shields.io/pepy/dt/onedrive-smart-transfer.svg?color=blue" alt="PyPI downloads"></a>&nbsp;
  <a href="https://github.com/Himesh-29/onedrive-smart-transfer/stargazers"><img src="https://img.shields.io/github/stars/Himesh-29/onedrive-smart-transfer.svg?color=gold" alt="GitHub stars"></a>&nbsp;
  <a href="https://github.com/Himesh-29/onedrive-smart-transfer/network/members"><img src="https://img.shields.io/github/forks/Himesh-29/onedrive-smart-transfer.svg" alt="GitHub forks"></a>&nbsp;
  <a href="https://github.com/Himesh-29/onedrive-smart-transfer/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Himesh-29/onedrive-smart-transfer.svg" alt="License"></a>&nbsp;
  <img src="https://komarev.com/ghpvc/?username=Himesh-29-onedrive-smart-transfer&style=flat&color=blue&label=VISITORS" alt="Visitors">
</p>

A simple Windows app to copy your coding projects to OneDrive without backing up all the heavy build files. It automatically skips folders like `node_modules`, `venv`, and `build` so your OneDrive doesn't fill up instantly.

![App Demo](https://raw.githubusercontent.com/Himesh-29/onedrive-smart-transfer/main/assets/docs/Transfer%20Completed.png)

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
Grab the latest `OneDriveSmartTransfer-Windows.zip` from the Releases page, extract the folder to a location of your choice, and double-click `OneDriveSmartTransfer.exe`. Because this is a portable application, there is no installation wizard.

**Step 2: First-Time Configuration (Portable Mode)**
When you launch the app for the very first time, it will prompt you to choose a folder to save your configuration file. We recommend selecting a folder inside your OneDrive so that your settings automatically sync across all your computers.

_How it works behind the scenes:_ Because this app is fully portable and respects your privacy (no Registry entries or hidden AppData files), it will generate a tiny text file named `ost_config_path.txt` right next to the `.exe` file. This file acts as a simple pointer so the application remembers where you decided to save your settings on this specific computer. If you ever want to reset the application, simply delete this text file!

![Configuration File Setup Location](https://raw.githubusercontent.com/Himesh-29/onedrive-smart-transfer/main/assets/docs/Configuration%20File%20Setup%20Location.png)
![OneDrive Location Detection or Updation](https://raw.githubusercontent.com/Himesh-29/onedrive-smart-transfer/main/assets/docs/OneDrive%20Location%20Detection%20or%20Updation.png)

**Step 3: Main Window Preview**
Drag and drop your project folder directly into the main window. The application will instantly scan the folder to detect what programming language it uses (like Node.js or Python).

![Main Window Placeholder](https://raw.githubusercontent.com/Himesh-29/onedrive-smart-transfer/main/assets/docs/Main%20Window%20Placeholder.png)

**Step 4: Choose a Destination**
Select a destination folder inside your local OneDrive directory. This is where your cleaned-up project will be copied or moved to.

**Step 5: Review and Transfer**
Before doing anything, the application will show you a preview tree of exactly which files it plans to transfer and which heavy build folders (like `node_modules` or `venv`) it plans to skip. Once you're satisfied, click start to begin the background transfer process!

![Settings General Window](https://raw.githubusercontent.com/Himesh-29/onedrive-smart-transfer/main/assets/docs/Settings%20General%20Window.png)
![Settings Exclusions Window](https://raw.githubusercontent.com/Himesh-29/onedrive-smart-transfer/main/assets/docs/Settings%20Exclusions%20Window.png)
![Transfer Completed](https://raw.githubusercontent.com/Himesh-29/onedrive-smart-transfer/main/assets/docs/Transfer%20Completed.png)

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
5. Run it: `python onedrivesmarttransfer/app.py`

To build the executable yourself, just run `python build_exe.py` after installing the requirements.

## Project Structure

If you're interested in how the application is built, here is a quick overview of the main files and what they do:

- `build_exe.py`: A helper script that uses PyInstaller to bundle the application into a standalone executable.
- `config/default_exclusions.json`: A list of the default, built-in rules for what files to skip for each language.
- `onedrivesmarttransfer/app.py`: The main entry point of the application. It handles the initial launch and the first-run configuration wizard.
- `onedrivesmarttransfer/ui/`: Contains all the graphical interface components.
  - `main_window.py`: The primary window where you drag and drop files.
  - `drop_zone.py`: Handles the drag-and-drop mechanics and visual feedback.
  - `file_explorer.py`: A widget that displays the preview tree of files to be transferred.
  - `settings_dialog.py`: The window where you manage your exclusion rules.
  - `theme_manager.py`: Controls switching between light and dark modes.
  - `transfer_queue.py`: The interface that displays active and queued transfers.
  - `transfer_summary.py`: Displays a pop-up summary after a transfer completes.
- `onedrivesmarttransfer/core/`: Contains the underlying logic.
  - `config_manager.py`: Handles loading and saving your preferences and rules to disk.
  - `exclusion_manager.py`: Handles the rules for what gets skipped during a transfer.
  - `onedrive_finder.py`: Automatically detects where OneDrive is installed on your system.
  - `stack_detector.py`: Scans project folders to figure out what programming language they use.
  - `transfer_engine.py`: The engine that safely copies or moves files in the background and reports progress.
- `onedrivesmarttransfer/utils/`: Contains small helper utilities.
  - `resource_path.py`: Helper utility that ensures file paths work properly whether running from source or from the compiled executable.
