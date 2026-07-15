"""
Main window for OneDrive Smart Transfer.

The primary application window featuring a WinSCP-style split pane:
  - Left: Lazy-loading Source File Explorer with tech stack detection
  - Right: Lazy-loading Destination Explorer for OneDrive
  - WinSCP-style transfer queue with background jobs
  - Copy/Move toggle and Start Transfer button
  - Settings gear and theme toggle in header
  - Error dialog for Retry/Skip/Skip All

Fully offline. No data sent anywhere. No file contents read.
"""

import os
import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinterdnd2 import TkinterDnD
from typing import Optional

from src.core.config_manager import ConfigManager
from src.core.exclusion_manager import ExclusionManager
from src.core.onedrive_finder import detect_onedrive_path
from src.core.transfer_engine import (
    TransferEngine,
    TransferAction,
    TransferState,
    TransferProgress,
    ErrorAction,
)
from src.ui.drop_zone import DropZone
from src.ui.file_explorer import SourceExplorer, DestinationExplorer
from src.ui.transfer_queue import TransferQueue
from src.ui.transfer_summary import TransferSummaryWidget
from src.ui.settings_dialog import SettingsDialog
from src.ui.theme_manager import theme_manager


class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    """Main application window with drag-drop, dual-pane explorer, and transfer queue."""

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        self._config = config_manager
        self._engine = TransferEngine()
        self._exclusion_mgr = ExclusionManager(
            user_overrides=self._config.exclusion_overrides
        )
        self._exclusion_mgr.set_on_change_callback(self._on_exclusions_changed)

        self._source_items: list[str] = []
        self._dest_path: str = ""
        self._current_action = TransferAction.COPY if self._config.default_action == "copy" else TransferAction.MOVE

        # Window setup
        self.title("⚡ OneDrive Smart Transfer")
        self.geometry("1000x800")
        self.minsize(800, 650)

        # Restore window geometry if saved
        saved_geometry = self._config.get("window_geometry")
        if saved_geometry:
            try:
                self.geometry(saved_geometry)
            except Exception:
                pass

        # Initialize theme
        theme_manager.initialize(self._config.theme)

        # Build UI
        self._setup_ui()

        # Start progress polling
        self._poll_progress()

        # Save geometry on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self) -> None:
        """Build the main window UI with a split pane design."""
        self.grid_rowconfigure(1, weight=1)  # Split pane area gets the weight
        self.grid_columnconfigure(0, weight=1)

        # ── 1. Header Bar ──
        header = ctk.CTkFrame(self, height=50, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)

        title_label = ctk.CTkLabel(
            header,
            text="⚡ OneDrive Smart Transfer",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title_label.pack(side="left", padx=16)

        settings_btn = ctk.CTkButton(
            header,
            text="⚙",
            width=36,
            height=36,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=self._open_settings,
        )
        settings_btn.pack(side="right", padx=(0, 12))

        self._theme_btn = ctk.CTkButton(
            header,
            text="🌙" if theme_manager.get_effective_mode() == "light" else "☀️",
            width=36,
            height=36,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="right", padx=(0, 4))

        # ── 2. Split Pane (Source / Destination) ──
        split_frame = ctk.CTkFrame(self, fg_color="transparent")
        split_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        split_frame.grid_rowconfigure(0, weight=1)
        split_frame.grid_columnconfigure(0, weight=1, uniform="pane")
        split_frame.grid_columnconfigure(1, weight=1, uniform="pane")

        # --- Left Pane: Source ---
        self.left_pane = ctk.CTkFrame(split_frame, fg_color="transparent")
        self.left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.left_pane.grid_rowconfigure(1, weight=1)
        self.left_pane.grid_columnconfigure(0, weight=1)

        source_header = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        source_header.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        ctk.CTkLabel(
            source_header,
            text="Source Preview",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        # Change Folder & Manage Exclusions buttons
        source_btns_frame = ctk.CTkFrame(source_header, fg_color="transparent")
        source_btns_frame.pack(side="right")

        self._manage_exc_btn = ctk.CTkButton(
            source_btns_frame,
            text="⚙ Exclusions",
            width=90,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            text_color=("gray20", "gray90"),
            command=self._open_settings,
        )
        self._manage_exc_btn.pack(side="right")

        self._change_folder_btn = ctk.CTkButton(
            source_btns_frame,
            text="🔄 Change Folder",
            width=100,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            text_color=("gray20", "gray90"),
            command=self._change_source_folder,
        )
        # Button is packed/unpacked dynamically

        # Drop Zone (shown when empty)
        self._drop_zone = DropZone(
            self.left_pane,
            on_files_dropped=self._on_files_dropped,
        )
        self._drop_zone.grid(row=1, column=0, sticky="nsew")

        # Source Explorer (hidden when empty)
        self._source_explorer = SourceExplorer(
            self.left_pane, 
            exclusion_manager=self._exclusion_mgr,
            corner_radius=8
        )

        # --- Right Pane: Destination ---
        self.right_pane = ctk.CTkFrame(split_frame, fg_color="transparent")
        self.right_pane.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.right_pane.grid_rowconfigure(1, weight=1)
        self.right_pane.grid_columnconfigure(0, weight=1)

        dest_header = ctk.CTkFrame(self.right_pane, fg_color="transparent")
        dest_header.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        ctk.CTkLabel(
            dest_header,
            text="Destination (OneDrive)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            dest_header,
            text="+ New Folder",
            width=80,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            text_color=("gray20", "gray90"),
            command=self._on_new_folder,
        ).pack(side="right")

        self._dest_explorer = DestinationExplorer(
            self.right_pane,
            on_path_changed=self._on_destination_changed,
            corner_radius=8
        )
        self._dest_explorer.grid(row=1, column=0, sticky="nsew")

        # Initial OneDrive Load
        onedrive_path = self._config.onedrive_path or detect_onedrive_path() or ""
        self._dest_path = self._config.last_destination or onedrive_path
        if self._dest_path:
            self._dest_explorer.load_destination(onedrive_path)

        # ── 3. Transfer Queue ──
        queue_frame = ctk.CTkFrame(self, fg_color="transparent")
        queue_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=4)
        
        self._queue_widget = TransferQueue(
            queue_frame,
            on_pause_job=self._on_pause_job,
            on_cancel_job=self._on_cancel_job,
            height=150
        )
        self._queue_widget.pack(fill="x")

        # ── 4. Transfer Summary ──
        summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        summary_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 4))
        
        self._summary_widget = TransferSummaryWidget(summary_frame, corner_radius=8)
        self._summary_widget.pack(fill="x")

        # ── 5. Action Bar ──
        action_bar = ctk.CTkFrame(self, height=60, corner_radius=0)
        action_bar.grid(row=4, column=0, sticky="ew")
        action_bar.pack_propagate(False)

        action_toggle_frame = ctk.CTkFrame(action_bar, fg_color="transparent")
        action_toggle_frame.pack(side="left", padx=16)

        self._action_var = ctk.StringVar(value=self._config.default_action)

        ctk.CTkRadioButton(
            action_toggle_frame,
            text="📄 Copy",
            variable=self._action_var,
            value="copy",
            font=ctk.CTkFont(size=13),
            command=self._on_action_changed,
        ).pack(side="left", padx=(0, 12))

        ctk.CTkRadioButton(
            action_toggle_frame,
            text="📦 Move",
            variable=self._action_var,
            value="move",
            font=ctk.CTkFont(size=13),
            command=self._on_action_changed,
        ).pack(side="left")

        self._transfer_btn = ctk.CTkButton(
            action_bar,
            text="🚀 Start Transfer",
            width=170,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_transfer,
        )
        self._transfer_btn.pack(side="right", padx=16)

    # ── Event Handlers ──

    def _on_files_dropped(self, paths: list[str]) -> None:
        """Handle files dropped onto the drop zone."""
        if not paths:
            return

        self._source_items = paths
        
        # Hide drop zone, show explorer and change button
        self._drop_zone.grid_remove()
        self._source_explorer.grid(row=1, column=0, sticky="nsew")
        self._change_folder_btn.pack(side="right", padx=(0, 8))
        
        self._source_explorer.load_sources(paths)
        self._summary_widget.calculate_stats(paths, self._source_explorer._get_root_exclusions)

    def _change_source_folder(self) -> None:
        """Change the source folder using a dialog."""
        folder = filedialog.askdirectory(
            title="Select Source Folder",
            parent=self.winfo_toplevel(),
        )
        if folder:
            paths = [os.path.normpath(folder)]
            self._on_files_dropped(paths)

    def _on_destination_changed(self, path: str) -> None:
        """Handle destination path selection in the right pane."""
        if os.path.isdir(path):
            self._dest_path = path
            self._config.last_destination = path

    def _on_new_folder(self) -> None:
        """Create a new folder in the currently selected destination."""
        if not self._dest_path or not os.path.isdir(self._dest_path):
            messagebox.showwarning("Warning", "Please select a destination folder first.", parent=self)
            return
        self._dest_explorer.create_new_folder(self._dest_path)

    def _on_action_changed(self) -> None:
        """Handle copy/move toggle change."""
        action = self._action_var.get()
        self._current_action = TransferAction.COPY if action == "copy" else TransferAction.MOVE
        self._config.default_action = action

    def _start_transfer(self) -> None:
        """Start the transfer for all source items."""
        if not self._source_items:
            messagebox.showwarning("No Source", "Please select a source folder first.", parent=self)
            return

        dest = self._dest_path
        if not dest or not os.path.isdir(dest):
            messagebox.showwarning("No Destination", "Please select a valid destination folder in the Right Pane.", parent=self)
            return

        # Start jobs
        for source_path in self._source_items:
            source_name = os.path.basename(source_path)
            
            # Re-fetch exclusions since user might have modified them
            exclusions = self._source_explorer._get_root_exclusions(source_path)
            
            job = self._engine.create_job(
                source_path=source_path,
                destination_path=dest,
                action=self._current_action,
                exclude_dirs=exclusions.get("dirs", []),
                exclude_files=exclusions.get("files", []),
            )
            self._queue_widget.add_job(job.job_id, source_name, dest)

        self._engine.start()

    def _poll_progress(self) -> None:
        """Poll the progress queue and update UI."""
        try:
            while True:
                progress: TransferProgress = self._engine.progress_queue.get_nowait()
                self._queue_widget.update_job(progress)

                if progress.state == TransferState.ERROR:
                    self._show_error_dialog(progress)

        except Exception:
            pass
            
        if self.winfo_exists():
            self.after(100, self._poll_progress)

    def _show_error_dialog(self, progress: TransferProgress) -> None:
        dialog = ErrorDialog(
            self,
            filename=progress.error_file,
            error_message=progress.error_message,
        )
        self.wait_window(dialog)
        action = dialog.result
        for job in self._engine.jobs:
            if job.job_id == progress.job_id:
                job.respond_to_error(action)
                break

    def _on_pause_job(self, job_id: str, paused: bool) -> None:
        for job in self._engine.jobs:
            if job.job_id == job_id:
                if paused: job.pause()
                else: job.resume()
                break

    def _on_cancel_job(self, job_id: str) -> None:
        for job in self._engine.jobs:
            if job.job_id == job_id:
                job.cancel()
                break

    def _on_exclusions_changed(self, user_overrides: dict) -> None:
        self._config.exclusion_overrides = user_overrides
        # Reload sources to reflect new exclusions
        if self._source_items:
            self._source_explorer.load_sources(self._source_items)
            self._summary_widget.calculate_stats(self._source_items, self._source_explorer._get_root_exclusions)

    def _toggle_theme(self) -> None:
        new_mode = theme_manager.toggle()
        self._theme_btn.configure(text="🌙" if new_mode == "light" else "☀️")
        self._config.theme = new_mode

    def _open_settings(self) -> None:
        SettingsDialog(
            self,
            exclusion_manager=self._exclusion_mgr,
            current_theme=theme_manager.current_mode,
            current_action=self._action_var.get(),
            onedrive_path=self._config.onedrive_path,
            config_path=self._config.config_path or "",
            on_theme_changed=self._on_theme_setting_changed,
            on_action_changed=self._on_action_setting_changed,
            on_onedrive_changed=self._on_onedrive_setting_changed,
        )

    def _on_theme_setting_changed(self, mode: str) -> None:
        theme_manager.set_mode(mode)
        self._theme_btn.configure(text="🌙" if theme_manager.get_effective_mode() == "light" else "☀️")
        self._config.theme = mode

    def _on_action_setting_changed(self, action: str) -> None:
        self._action_var.set(action)
        self._current_action = TransferAction.COPY if action == "copy" else TransferAction.MOVE
        self._config.default_action = action

    def _on_onedrive_setting_changed(self, path: str) -> None:
        self._config.onedrive_path = path
        self._dest_explorer.load_destination(path)

    def _on_close(self) -> None:
        try:
            self._config.set("window_geometry", self.geometry())
        except Exception:
            pass
        self._engine.stop()
        self.destroy()


class ErrorDialog(ctk.CTkToplevel):
    """Windows-style error dialog with Retry / Skip / Skip All buttons."""
    def __init__(self, master, filename: str, error_message: str, **kwargs):
        super().__init__(master, **kwargs)
        self.title("⚠ Error Transferring File")
        self.geometry("450x220")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result = ErrorAction.SKIP
        self.after(10, self._center)
        self._setup_ui(filename, error_message)

    def _center(self) -> None:
        if not self.winfo_exists():
            return
        self.update_idletasks()
        parent = self.master
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _setup_ui(self, filename: str, error_message: str) -> None:
        ctk.CTkLabel(self, text="⚠️ Error Transferring File", font=ctk.CTkFont(size=16, weight="bold"), text_color=("#dc2626", "#ef4444")).pack(pady=(20, 10))
        ctk.CTkLabel(self, text=f"File: {filename}", font=ctk.CTkFont(size=12), wraplength=400).pack(pady=(0, 4))
        ctk.CTkLabel(self, text=f"Error: {error_message}", font=ctk.CTkFont(size=12), text_color=("gray40", "gray70"), wraplength=400).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))
        ctk.CTkButton(btn_frame, text="🔄 Retry", width=100, height=36, command=lambda: self._respond(ErrorAction.RETRY)).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="⏭ Skip", width=100, height=36, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), text_color=("gray20", "gray90"), command=lambda: self._respond(ErrorAction.SKIP)).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="⏭⏭ Skip All", width=100, height=36, fg_color=("#fee2e2", "#7f1d1d"), hover_color=("#fecaca", "#991b1b"), text_color=("#991b1b", "#fca5a5"), command=lambda: self._respond(ErrorAction.SKIP_ALL)).pack(side="left", padx=6)

    def _respond(self, action: ErrorAction) -> None:
        self.result = action
        self.destroy()
