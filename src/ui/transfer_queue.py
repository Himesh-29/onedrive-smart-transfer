"""
Transfer queue widget for OneDrive Smart Transfer (WinSCP-style).

Shows a list of active and queued transfer jobs, each with:
  - Source → Destination label
  - Individual progress bar
  - File counter
  - Speed and ETA
  - Pause/Cancel controls
"""

import customtkinter as ctk
from typing import Optional, Callable

from src.core.transfer_engine import TransferProgress, TransferState, ErrorAction

def format_size(size_bytes: int) -> str:
    """Format a byte count into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class TransferJobWidget(ctk.CTkFrame):
    """A single transfer job row in the queue.

    Shows progress, file counter, speed, ETA, and control buttons.
    """

    def __init__(
        self,
        master,
        job_id: str,
        source_name: str,
        destination: str,
        on_pause: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.job_id = job_id
        self._on_pause = on_pause
        self._on_cancel = on_cancel
        self._is_paused = False

        self.configure(corner_radius=8, border_width=1, border_color=("gray80", "gray30"))

        self._setup_ui(source_name, destination)

    def _setup_ui(self, source_name: str, destination: str) -> None:
        """Create the job widget UI."""
        # Top row: source → destination + controls
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 4))

        # Source → Destination
        dest_basename = destination.split("\\")[-1] if "\\" in destination else destination.split("/")[-1]
        route_label = ctk.CTkLabel(
            top_row,
            text=f"📁 {source_name} → {dest_basename}",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        route_label.pack(side="left", fill="x", expand=True)

        # Status badge
        self._status_badge = ctk.CTkLabel(
            top_row,
            text="⏳ Queued",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=("gray75", "gray35"),
            text_color=("gray30", "gray80"),
            corner_radius=4,
            height=20,
            width=80,
        )
        self._status_badge.pack(side="right", padx=(8, 0))

        # Progress bar row
        progress_row = ctk.CTkFrame(self, fg_color="transparent")
        progress_row.pack(fill="x", padx=10, pady=(0, 2))

        self._progress_bar = ctk.CTkProgressBar(
            progress_row,
            height=12,
            corner_radius=6,
        )
        self._progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._progress_bar.set(0)

        self._percent_label = ctk.CTkLabel(
            progress_row,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=40,
        )
        self._percent_label.pack(side="right")

        # Details row: current file, speed, ETA
        details_row = ctk.CTkFrame(self, fg_color="transparent")
        details_row.pack(fill="x", padx=10, pady=(0, 4))

        self._file_label = ctk.CTkLabel(
            details_row,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        self._file_label.pack(side="left", fill="x", expand=True)

        self._speed_label = ctk.CTkLabel(
            details_row,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="e",
        )
        self._speed_label.pack(side="right")

        # Stats row: file count
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=10, pady=(0, 4))

        self._count_label = ctk.CTkLabel(
            stats_row,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        self._count_label.pack(side="left")

        self._action_label = ctk.CTkLabel(
            stats_row,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="e",
        )
        self._action_label.pack(side="right")

        # Control buttons row
        controls_row = ctk.CTkFrame(self, fg_color="transparent")
        controls_row.pack(fill="x", padx=10, pady=(0, 8))

        self._pause_btn = ctk.CTkButton(
            controls_row,
            text="⏸ Pause",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=("gray75", "gray35"),
            hover_color=("gray65", "gray45"),
            text_color=("gray20", "gray90"),
            command=self._toggle_pause,
        )
        self._pause_btn.pack(side="left", padx=(0, 6))

        self._cancel_btn = ctk.CTkButton(
            controls_row,
            text="✕ Cancel",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=("#fee2e2", "#7f1d1d"),
            hover_color=("#fecaca", "#991b1b"),
            text_color=("#991b1b", "#fca5a5"),
            command=self._do_cancel,
        )
        self._cancel_btn.pack(side="left")

    def _toggle_pause(self) -> None:
        """Toggle pause/resume."""
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_btn.configure(text="▶ Resume")
        else:
            self._pause_btn.configure(text="⏸ Pause")
        if self._on_pause:
            self._on_pause(self.job_id, self._is_paused)

    def _do_cancel(self) -> None:
        """Cancel this job."""
        if self._on_cancel:
            self._on_cancel(self.job_id)

    def update_progress(self, progress: TransferProgress) -> None:
        """Update the widget with new progress data.

        Args:
            progress: TransferProgress from the engine.
        """
        state = progress.state

        # Progress bar
        if progress.total_files > 0:
            fraction = progress.transferred_files / progress.total_files
            self._progress_bar.set(fraction)
            self._percent_label.configure(text=f"{int(fraction * 100)}%")

        # File counter
        if progress.total_files > 0:
            self._count_label.configure(
                text=f"{progress.transferred_files}/{progress.total_files} files  •  "
                     f"{format_size(progress.transferred_bytes)}/{format_size(progress.total_bytes)}"
            )

        # Current file
        if progress.current_file:
            self._file_label.configure(text=f"Current: {progress.current_file}")

        # Speed and ETA
        if progress.speed_bytes_per_sec > 0:
            speed_str = f"{format_size(int(progress.speed_bytes_per_sec))}/s"
            eta_str = self._format_eta(progress.eta_seconds)
            self._speed_label.configure(text=f"Speed: {speed_str}  •  ETA: {eta_str}")

        # Status badge
        if state == TransferState.SCANNING:
            self._status_badge.configure(
                text="🔍 Scanning",
                fg_color=("#dbeafe", "#1e3a5f"),
                text_color=("#1d4ed8", "#93c5fd"),
            )
        elif state == TransferState.IN_PROGRESS:
            self._status_badge.configure(
                text="🚀 Copying" if progress.source_name else "🚀 Running",
                fg_color=("#dcfce7", "#14532d"),
                text_color=("#16a34a", "#86efac"),
            )
        elif state == TransferState.PAUSED:
            self._status_badge.configure(
                text="⏸ Paused",
                fg_color=("#fef3c7", "#78350f"),
                text_color=("#d97706", "#fcd34d"),
            )
        elif state == TransferState.COMPLETED:
            self._progress_bar.set(1.0)
            self._percent_label.configure(text="100%")
            self._status_badge.configure(
                text="✅ Done",
                fg_color=("#dcfce7", "#14532d"),
                text_color=("#16a34a", "#86efac"),
            )
            self._pause_btn.configure(state="disabled")
            self._cancel_btn.configure(state="disabled")
            if progress.skipped_files:
                self._file_label.configure(
                    text=f"⚠ {len(progress.skipped_files)} file(s) skipped",
                    text_color=("#d97706", "#f59e0b"),
                )
        elif state == TransferState.CANCELLED:
            self._status_badge.configure(
                text="✕ Cancelled",
                fg_color=("#fee2e2", "#7f1d1d"),
                text_color=("#dc2626", "#fca5a5"),
            )
            self._pause_btn.configure(state="disabled")
            self._cancel_btn.configure(state="disabled")
        elif state == TransferState.ERROR:
            self._status_badge.configure(
                text="⚠ Error",
                fg_color=("#fee2e2", "#7f1d1d"),
                text_color=("#dc2626", "#fca5a5"),
            )

    def _format_eta(self, seconds: float) -> str:
        """Format ETA seconds into a readable string."""
        if seconds <= 0 or seconds > 86400:
            return "--"
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m"


class TransferQueue(ctk.CTkFrame):
    """WinSCP-style transfer queue showing all active and pending jobs.

    Features:
      - Individual job widgets with progress
      - Scrollable list
      - Pause/Cancel per job
    """

    def __init__(
        self,
        master,
        on_pause_job: Optional[Callable] = None,
        on_cancel_job: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._on_pause_job = on_pause_job
        self._on_cancel_job = on_cancel_job
        self._job_widgets: dict[str, TransferJobWidget] = {}

        self.configure(corner_radius=8)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create the queue UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        self._title_label = ctk.CTkLabel(
            header,
            text="Transfer Queue",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self._title_label.pack(side="left")

        self._count_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
        )
        self._count_label.pack(side="right")

        # Scrollable job list
        self._jobs_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=6,
            height=150,
        )
        self._jobs_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Empty state
        self._empty_label = ctk.CTkLabel(
            self._jobs_frame,
            text="No active transfers",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
        )
        self._empty_label.pack(pady=20)

    def add_job(self, job_id: str, source_name: str, destination: str) -> None:
        """Add a new job to the queue display.

        Args:
            job_id: Unique job identifier.
            source_name: Name of the source.
            destination: Destination path.
        """
        # Remove empty state label
        if self._empty_label and self._empty_label.winfo_exists():
            self._empty_label.destroy()

        widget = TransferJobWidget(
            self._jobs_frame,
            job_id=job_id,
            source_name=source_name,
            destination=destination,
            on_pause=self._on_pause_job,
            on_cancel=self._on_cancel_job,
        )
        widget.pack(fill="x", pady=4, padx=2)
        self._job_widgets[job_id] = widget
        self._update_count()

    def update_job(self, progress: TransferProgress) -> None:
        """Update a job's progress display.

        Args:
            progress: TransferProgress from the engine.
        """
        if progress.job_id in self._job_widgets:
            self._job_widgets[progress.job_id].update_progress(progress)

    def remove_job(self, job_id: str) -> None:
        """Remove a job from the queue display.

        Args:
            job_id: The job to remove.
        """
        if job_id in self._job_widgets:
            self._job_widgets[job_id].destroy()
            del self._job_widgets[job_id]
            self._update_count()

    def _update_count(self) -> None:
        """Update the job count label."""
        count = len(self._job_widgets)
        if count > 0:
            self._count_label.configure(text=f"{count} job(s)")
        else:
            self._count_label.configure(text="")
            self._empty_label = ctk.CTkLabel(
                self._jobs_frame,
                text="No active transfers",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray60"),
            )
            self._empty_label.pack(pady=20)
