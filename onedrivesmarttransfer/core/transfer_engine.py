"""
Transfer engine for OneDrive Smart Transfer.

Handles the actual file copy/move operations with:
  - Background threading (never blocks the UI)
  - Progress reporting via queue
  - Windows-style error handling (Retry / Skip / Skip All)
  - Exclusion filtering
  - Transfer statistics (speed, ETA, file counts)

No file contents are sent anywhere — all operations are local filesystem only.
"""

import os
import shutil
import time
import threading
import queue as queue_module
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable

from onedrivesmarttransfer.core.exclusion_manager import should_exclude_dir, should_exclude_file


class TransferAction(Enum):
    """The type of transfer operation."""
    COPY = "copy"
    MOVE = "move"


class TransferState(Enum):
    """Current state of a transfer job."""
    QUEUED = "queued"
    SCANNING = "scanning"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class ErrorAction(Enum):
    """User's response to a file transfer error."""
    RETRY = "retry"
    SKIP = "skip"
    SKIP_ALL = "skip_all"


@dataclass
class TransferProgress:
    """Progress information for a transfer job."""
    job_id: str
    state: TransferState
    total_files: int = 0
    transferred_files: int = 0
    total_bytes: int = 0
    transferred_bytes: int = 0
    current_file: str = ""
    speed_bytes_per_sec: float = 0.0
    eta_seconds: float = 0.0
    skipped_files: list = field(default_factory=list)
    error_file: str = ""
    error_message: str = ""
    source_name: str = ""
    destination: str = ""


@dataclass
class FileEntry:
    """A file to be transferred."""
    source_path: str
    relative_path: str
    size: int
    is_excluded: bool = False
    exclude_reason: str = ""


class TransferJob:
    """Represents a single transfer job (one source to one destination)."""

    def __init__(
        self,
        job_id: str,
        source_path: str,
        destination_path: str,
        action: TransferAction,
        exclude_dirs: set,
        exclude_files: set,
    ):
        self.job_id = job_id
        self.source_path = source_path
        self.destination_path = destination_path
        self.action = action
        self.exclude_dirs = exclude_dirs
        self.exclude_files = exclude_files
        self.state = TransferState.QUEUED
        self.files: list[FileEntry] = []
        self.skipped_files: list[dict] = []
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        self._skip_all_errors = False
        self._error_response_queue: queue_module.Queue = queue_module.Queue()

    def cancel(self) -> None:
        """Cancel this transfer job."""
        self._cancel_event.set()
        self._pause_event.set()  # Unblock if paused

    def pause(self) -> None:
        """Pause this transfer job."""
        self._pause_event.clear()
        self.state = TransferState.PAUSED

    def resume(self) -> None:
        """Resume this transfer job."""
        self._pause_event.set()
        self.state = TransferState.IN_PROGRESS

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def respond_to_error(self, action: ErrorAction) -> None:
        """Provide the user's response to an error prompt.

        Args:
            action: The user's chosen action (retry, skip, skip_all).
        """
        if action == ErrorAction.SKIP_ALL:
            self._skip_all_errors = True
        self._error_response_queue.put(action)


def scan_directory(
    source_path: str,
    exclude_dirs: set[str],
    exclude_files: set[str],
) -> list[FileEntry]:
    """Scan a directory and build the list of files, marking exclusions.

    Only file/directory NAMES are checked — no file contents are read.

    Args:
        source_path: Root directory to scan.
        exclude_dirs: Set of directory name patterns to exclude.
        exclude_files: Set of file name patterns to exclude.

    Returns:
        List of FileEntry objects with exclusion status.
    """
    entries = []

    if os.path.isfile(source_path):
        # Single file — check if excluded
        filename = os.path.basename(source_path)
        excluded = should_exclude_file(filename, exclude_files)
        try:
            size = os.path.getsize(source_path)
        except OSError:
            size = 0
        entries.append(FileEntry(
            source_path=source_path,
            relative_path=filename,
            size=size,
            is_excluded=excluded,
            exclude_reason="Matched file pattern" if excluded else "",
        ))
        return entries

    base_name = os.path.basename(source_path)

    for root, dirs, files in os.walk(source_path):
        # Calculate relative path from the source
        rel_root = os.path.relpath(root, os.path.dirname(source_path))

        # Filter directories in-place to prevent os.walk from descending
        excluded_dir_names = []
        for d in dirs[:]:
            if should_exclude_dir(d, exclude_dirs):
                excluded_dir_names.append(d)
                dirs.remove(d)
                # Add an entry for the excluded directory so it shows in preview
                dir_rel_path = os.path.join(rel_root, d)
                try:
                    dir_size = _get_dir_size_fast(os.path.join(root, d))
                except OSError:
                    dir_size = 0
                entries.append(FileEntry(
                    source_path=os.path.join(root, d),
                    relative_path=dir_rel_path,
                    size=dir_size,
                    is_excluded=True,
                    exclude_reason=f"Excluded directory: {d}",
                ))

        # Process files
        for f in files:
            file_path = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f)
            excluded = should_exclude_file(f, exclude_files)
            try:
                size = os.path.getsize(file_path)
            except OSError:
                size = 0

            entries.append(FileEntry(
                source_path=file_path,
                relative_path=rel_path,
                size=size,
                is_excluded=excluded,
                exclude_reason=f"Matched file pattern: {f}" if excluded else "",
            ))

    return entries


def _get_dir_size_fast(path: str) -> int:
    """Quickly estimate directory size without reading file contents.

    Args:
        path: Directory path.

    Returns:
        Total size in bytes (approximate — may fail on permission issues).
    """
    total = 0
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
    except OSError:
        pass
    return total


class TransferEngine:
    """Manages the transfer queue and executes jobs in background threads.

    All file operations are local-only. No network calls are made.
    """

    def __init__(self):
        self._jobs: list[TransferJob] = []
        self._progress_queue: queue_module.Queue = queue_module.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._job_counter = 0

    @property
    def progress_queue(self) -> queue_module.Queue:
        """Queue for receiving progress updates in the main thread."""
        return self._progress_queue

    @property
    def jobs(self) -> list[TransferJob]:
        """Get the list of all transfer jobs."""
        return self._jobs

    def create_job(
        self,
        source_path: str,
        destination_path: str,
        action: TransferAction,
        exclude_dirs: set,
        exclude_files: set,
    ) -> TransferJob:
        """Create a new transfer job and add it to the queue.

        Args:
            source_path: Source file or directory.
            destination_path: Destination directory.
            action: Copy or move.
            exclude_dirs: Directory name patterns to exclude.
            exclude_files: File name patterns to exclude.

        Returns:
            The created TransferJob.
        """
        self._job_counter += 1
        job = TransferJob(
            job_id=f"job-{self._job_counter}",
            source_path=source_path,
            destination_path=destination_path,
            action=action,
            exclude_dirs=exclude_dirs,
            exclude_files=exclude_files,
        )
        self._jobs.append(job)
        return job

    def start(self) -> None:
        """Start processing the job queue in a background thread."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        """Stop the transfer engine and cancel all pending jobs."""
        self._running = False
        for job in self._jobs:
            if job.state in (TransferState.QUEUED, TransferState.IN_PROGRESS):
                job.cancel()

    def remove_completed_jobs(self) -> None:
        """Remove all completed/cancelled jobs from the queue."""
        self._jobs = [
            j for j in self._jobs
            if j.state not in (TransferState.COMPLETED, TransferState.CANCELLED)
        ]

    def _process_queue(self) -> None:
        """Worker thread: process jobs one at a time."""
        while self._running:
            # Find next queued job
            next_job = None
            for job in self._jobs:
                if job.state == TransferState.QUEUED:
                    next_job = job
                    break

            if next_job is None:
                self._running = False
                break

            self._execute_job(next_job)

    def _execute_job(self, job: TransferJob) -> None:
        """Execute a single transfer job.

        Args:
            job: The job to execute.
        """
        source_name = os.path.basename(job.source_path)

        # Phase 1: Scan
        job.state = TransferState.SCANNING
        self._emit_progress(job, source_name=source_name)

        job.files = scan_directory(job.source_path, job.exclude_dirs, job.exclude_files)
        included_files = [f for f in job.files if not f.is_excluded]

        total_files = len(included_files)
        total_bytes = sum(f.size for f in included_files)

        # Phase 2: Transfer
        job.state = TransferState.IN_PROGRESS
        transferred_files = 0
        transferred_bytes = 0
        start_time = time.time()

        for file_entry in included_files:
            if job.is_cancelled:
                job.state = TransferState.CANCELLED
                self._emit_progress(job, source_name=source_name)
                return

            # Respect pause
            job._pause_event.wait()
            if job.is_cancelled:
                job.state = TransferState.CANCELLED
                self._emit_progress(job, source_name=source_name)
                return

            # Calculate destination path
            dest_path = os.path.join(job.destination_path, file_entry.relative_path)
            dest_dir = os.path.dirname(dest_path)

            # Attempt file transfer with error handling
            success = False
            while not success:
                try:
                    os.makedirs(dest_dir, exist_ok=True)

                    if job.action == TransferAction.COPY:
                        shutil.copy2(file_entry.source_path, dest_path)
                    else:
                        shutil.move(file_entry.source_path, dest_path)

                    success = True
                    transferred_files += 1
                    transferred_bytes += file_entry.size

                except OSError as e:
                    if job._skip_all_errors:
                        job.skipped_files.append({
                            "file": file_entry.relative_path,
                            "error": str(e),
                        })
                        break  # Skip this file

                    # Emit error progress and wait for user response
                    elapsed = time.time() - start_time
                    speed = transferred_bytes / elapsed if elapsed > 0 else 0
                    remaining_bytes = total_bytes - transferred_bytes
                    eta = remaining_bytes / speed if speed > 0 else 0

                    error_progress = TransferProgress(
                        job_id=job.job_id,
                        state=TransferState.ERROR,
                        total_files=total_files,
                        transferred_files=transferred_files,
                        total_bytes=total_bytes,
                        transferred_bytes=transferred_bytes,
                        current_file=file_entry.relative_path,
                        speed_bytes_per_sec=speed,
                        eta_seconds=eta,
                        skipped_files=list(job.skipped_files),
                        error_file=file_entry.relative_path,
                        error_message=str(e),
                        source_name=source_name,
                        destination=job.destination_path,
                    )
                    self._progress_queue.put(error_progress)

                    # Wait for user response
                    try:
                        response = job._error_response_queue.get(timeout=300)
                    except queue_module.Empty:
                        response = ErrorAction.SKIP

                    if response == ErrorAction.RETRY:
                        continue  # Retry the same file
                    elif response == ErrorAction.SKIP:
                        job.skipped_files.append({
                            "file": file_entry.relative_path,
                            "error": str(e),
                        })
                        break  # Skip this file
                    elif response == ErrorAction.SKIP_ALL:
                        job.skipped_files.append({
                            "file": file_entry.relative_path,
                            "error": str(e),
                        })
                        break  # Skip this file (flag already set)

            # Emit progress update
            elapsed = time.time() - start_time
            speed = transferred_bytes / elapsed if elapsed > 0 else 0
            remaining_bytes = total_bytes - transferred_bytes
            eta = remaining_bytes / speed if speed > 0 else 0

            progress = TransferProgress(
                job_id=job.job_id,
                state=TransferState.IN_PROGRESS if not job.is_cancelled else TransferState.CANCELLED,
                total_files=total_files,
                transferred_files=transferred_files,
                total_bytes=total_bytes,
                transferred_bytes=transferred_bytes,
                current_file=file_entry.relative_path,
                speed_bytes_per_sec=speed,
                eta_seconds=eta,
                skipped_files=list(job.skipped_files),
                source_name=source_name,
                destination=job.destination_path,
            )
            self._progress_queue.put(progress)

        # Phase 3: Complete
        if not job.is_cancelled:
            job.state = TransferState.COMPLETED
            self._emit_progress(job, source_name=source_name, total_files=total_files,
                              transferred_files=transferred_files, total_bytes=total_bytes,
                              transferred_bytes=transferred_bytes)

    def _emit_progress(self, job: TransferJob, **kwargs) -> None:
        """Emit a progress update to the queue.

        Args:
            job: The current job.
            **kwargs: Additional progress fields.
        """
        progress = TransferProgress(
            job_id=job.job_id,
            state=job.state,
            skipped_files=list(job.skipped_files),
            source_name=kwargs.get("source_name", ""),
            destination=job.destination_path,
            total_files=kwargs.get("total_files", 0),
            transferred_files=kwargs.get("transferred_files", 0),
            total_bytes=kwargs.get("total_bytes", 0),
            transferred_bytes=kwargs.get("transferred_bytes", 0),
        )
        self._progress_queue.put(progress)
