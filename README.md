# ⚡ OneDrive Smart Transfer

A **free, open-source, offline-only** Windows desktop application for transferring project files to OneDrive Personal — while **automatically excluding** bloated build artifacts like `node_modules`, `venv`, `__pycache__`, `.next`, `build`, and more.

## 🎯 What It Does

Drop your project folders from Downloads (or anywhere), pick a destination in your OneDrive, and hit **Transfer**. The app automatically detects your tech stack and filters out framework-generated folders that waste OneDrive storage.

## ✨ Features

- **🖱 Drag & Drop** — Drop files/folders directly from Windows File Explorer
- **🧠 Smart Tech Stack Detection** — Automatically identifies Node.js, Python, Java, Rust, Flutter, Go, C#, C++, Ruby, PHP, and more from marker files (e.g., `package.json`, `Cargo.toml`)
- **🚫 Auto-Exclusion** — Skips `node_modules`, `venv`, `__pycache__`, `build`, `target`, `.gradle`, and 100+ other build artifacts
- **📋 Fully Configurable** — Add, remove, or toggle any exclusion pattern via a simple UI (even a 5-year-old can use it!)
- **📦 Copy or Move** — Choose to keep originals or move them
- **📊 WinSCP-Style Transfer Queue** — Multiple background transfers with individual progress bars, speed, and ETA
- **⚠ Windows-Style Error Handling** — Retry / Skip / Skip All prompts when files fail
- **🎨 Light & Dark Mode** — Follows your Windows system theme, or switch manually
- **🔒 Privacy First** — 100% offline, no telemetry, no file contents read, no registry access
- **💾 Persistent Settings** — Your exclusion patterns and preferences survive app restarts

## 🔒 Privacy & Security

This application is designed with privacy as a core principle:

| Principle | Implementation |
|---|---|
| **100% Offline** | No network calls. No telemetry. No analytics. Works without internet. |
| **No File Content Reading** | Only file/directory *names* and sizes are inspected. Contents are never read. |
| **No Registry Access** | OneDrive is detected via environment variables. If detection fails, you're asked to browse. |
| **No Hardcoded Paths** | All paths are dynamically resolved. No usernames or machine-specific data in source code. |
| **User Controls Everything** | The app asks for every piece of information it needs. Nothing happens behind the scenes. |

## 🚀 Quick Start

### Run from Source (Development)

```bash
# 1. Clone the repo
git clone https://github.com/your-username/onedrive-smart-transfer.git
cd onedrive-smart-transfer

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python src/app.py
```

### Build Standalone .exe

```bash
# Build with PyInstaller
python build_exe.py

# Output: dist/OneDriveSmartTransfer/OneDriveSmartTransfer.exe
```

### Create Windows Installer

1. Install [Inno Setup](https://jrsoftware.org/isdl.php)
2. Open `installer/setup_script.iss` in Inno Setup Compiler
3. Click Build → the installer `.exe` will be in `installer/output/`

## 📁 Project Structure

```
OneDrive-Smart-Transfer/
├── src/
│   ├── app.py                    # Entry point with first-run wizard
│   ├── ui/
│   │   ├── main_window.py        # Main window (drop zone, preview, queue)
│   │   ├── drop_zone.py          # Drag-and-drop widget
│   │   ├── destination_picker.py # OneDrive folder browser
│   │   ├── transfer_preview.py   # File tree with exclusion indicators
│   │   ├── transfer_queue.py     # WinSCP-style background job queue
│   │   ├── settings_dialog.py    # Exclusion editor + preferences
│   │   └── theme_manager.py      # Light/Dark/System theme
│   ├── core/
│   │   ├── config_manager.py     # User settings persistence
│   │   ├── exclusion_manager.py  # Config-driven exclusion patterns
│   │   ├── stack_detector.py     # Tech stack detection from marker files
│   │   ├── onedrive_finder.py    # Environment-based OneDrive detection
│   │   └── transfer_engine.py    # Copy/move engine with progress & errors
│   └── utils/
│       └── resource_path.py      # PyInstaller path resolver
├── config/
│   └── default_exclusions.json   # Default exclusion patterns (extensible)
├── installer/
│   └── setup_script.iss          # Inno Setup installer script
├── build_exe.py                  # PyInstaller build automation
├── requirements.txt              # Python dependencies
├── LICENSE                       # MIT License
└── README.md                     # This file
```

## 🛠 Supported Tech Stacks

The app auto-detects and excludes build artifacts for:

| Tech Stack | Detected By | Excluded |
|---|---|---|
| JavaScript / Node.js | `package.json`, `yarn.lock` | `node_modules`, `.next`, `.nuxt`, `dist`, `.cache` |
| TypeScript | `tsconfig.json` | `node_modules`, `dist`, `build` |
| Python | `requirements.txt`, `pyproject.toml` | `venv`, `.venv`, `__pycache__`, `.tox`, `.mypy_cache` |
| Java / Kotlin | `pom.xml`, `build.gradle` | `target`, `build`, `out`, `.gradle` |
| C# / .NET | `*.csproj`, `*.sln` | `bin`, `obj`, `packages`, `.vs` |
| C / C++ | `CMakeLists.txt`, `Makefile` | `build`, `cmake-build-*`, `Debug`, `Release` |
| Rust | `Cargo.toml` | `target` |
| Go | `go.mod` | `vendor` |
| Flutter / Dart | `pubspec.yaml` | `.dart_tool`, `build`, `ios/Pods` |
| Ruby | `Gemfile` | `vendor/bundle`, `.bundle` |
| PHP | `composer.json` | `vendor` |
| Swift / iOS | `Package.swift`, `Podfile` | `DerivedData`, `Pods` |
| Android | `build.gradle`, `gradlew` | `.gradle`, `build`, `app/build` |
| Unity | `ProjectSettings/` | `Library`, `Temp`, `Obj` |
| Unreal Engine | `*.uproject` | `Binaries`, `Intermediate` |
| Terraform | `main.tf`, `*.tf` | `.terraform`, `*.tfstate` |

> **Note:** `.git` and `.vscode` are **NOT excluded** by default — these are useful folders you typically want to keep. You can add them manually if desired.

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
