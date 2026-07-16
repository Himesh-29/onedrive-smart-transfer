"""
Build script for creating a distributable OneDrive Smart Transfer package.

Uses PyInstaller to package the application into a standalone Windows
directory bundle. The output can then be wrapped with Inno Setup for
a professional installer.

Usage:
    python build_exe.py
"""

import os
import sys
import subprocess


def build():
    """Build the application with PyInstaller."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    venv_scripts = os.path.join(project_root, "venv", "Scripts")
    pyinstaller_exe = os.path.join(venv_scripts, "pyinstaller.exe")

    if not os.path.isfile(pyinstaller_exe):
        # Fall back to PATH
        pyinstaller_exe = "pyinstaller"

    # Find customtkinter and tkinterdnd2 install locations
    venv_python = os.path.join(venv_scripts, "python.exe")
    if not os.path.isfile(venv_python):
        venv_python = sys.executable

    cmd = [
        pyinstaller_exe,
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--collect-all", "customtkinter",
        "--collect-all", "tkinterdnd2",
        "--collect-all", "darkdetect",
        "--add-data", f"{os.path.join(project_root, 'config')};config",
        "--add-data", f"{os.path.join(project_root, 'assets')};assets",
        "--name", "OneDriveSmartTransfer",
        "--clean",
        os.path.join(project_root, "onedrivesmarttransfer", "app.py"),
    ]

    # Add icon if it exists
    icon_path = os.path.join(project_root, "assets", "icon.ico")
    if os.path.isfile(icon_path):
        cmd.extend(["--icon", icon_path])

    print("=" * 60)
    print("Building OneDrive Smart Transfer")
    print("=" * 60)
    print(f"\nCommand:\n  {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        dist_dir = os.path.join(project_root, "dist", "OneDriveSmartTransfer")
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"\nOutput directory: {dist_dir}")
        print(f"\nRun the app:  {os.path.join(dist_dir, 'OneDriveSmartTransfer.exe')}")
        print("\nTo create an installer, use the Inno Setup script:")
        print(f"  {os.path.join(project_root, 'installer', 'setup_script.iss')}")
    else:
        print("\nBUILD FAILED! Check the output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    build()
