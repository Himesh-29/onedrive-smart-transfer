import os
import threading
import customtkinter as ctk
from typing import Dict, List

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

class TransferSummaryWidget(ctk.CTkFrame):
    """Displays stats about the files to be transferred before starting."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self._current_task_id = 0
        self._setup_ui()
        
    def _setup_ui(self):
        self.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.status_label = ctk.CTkLabel(
            self, 
            text="Drop folders to see transfer summary",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=("gray50", "gray50")
        )
        self.status_label.grid(row=0, column=0, columnspan=3, pady=8)
        
        # We will pack these when stats are ready
        self.total_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.transfer_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=("#16a34a", "#4ade80"))
        self.saved_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))

    def calculate_stats(self, source_paths: List[str], get_exclusions_func):
        """Start background calculation of stats.
        get_exclusions_func takes a path and returns dict with 'dirs' and 'files'.
        """
        if not source_paths:
            self.status_label.configure(text="Drop folders to see transfer summary")
            self.status_label.grid(row=0, column=0, columnspan=3, pady=8)
            self.total_label.grid_remove()
            self.transfer_label.grid_remove()
            self.saved_label.grid_remove()
            return
            
        self.status_label.configure(text="Calculating transfer stats... ⏳")
        self.status_label.grid(row=0, column=0, columnspan=3, pady=8)
        self.total_label.grid_remove()
        self.transfer_label.grid_remove()
        self.saved_label.grid_remove()
        
        self._current_task_id += 1
        task_id = self._current_task_id
        
        threading.Thread(target=self._scan_thread, args=(task_id, source_paths, get_exclusions_func), daemon=True).start()
        
    def _scan_thread(self, task_id: int, source_paths: List[str], get_exclusions_func):
        total_files = 0
        total_size = 0
        transfer_files = 0
        transfer_size = 0
        
        try:
            for root_path in source_paths:
                if task_id != self._current_task_id:
                    return
                if not os.path.isdir(root_path):
                    if os.path.isfile(root_path):
                        # Edge case if user somehow drops a file
                        size = os.path.getsize(root_path)
                        total_files += 1
                        total_size += size
                        transfer_files += 1
                        transfer_size += size
                    continue
                
                exclusions = get_exclusions_func(root_path)
                exclude_dirs = set(exclusions.get("dirs", []))
                exclude_files = set(exclusions.get("files", []))
                
                for dirpath, dirnames, filenames in os.walk(root_path):
                    if task_id != self._current_task_id:
                        return
                        
                    # Filter directories in-place for os.walk to skip excluded dirs completely
                    original_dirnames = list(dirnames)
                    dirnames.clear()
                    for d in original_dirnames:
                        if d not in exclude_dirs:
                            dirnames.append(d)
                            
                    # Tally all files in this directory (including those we will skip for transfer)
                    # Wait, if we filter dirnames above, os.walk won't even visit the excluded directories!
                    # So we won't count the files inside node_modules towards "total_files" and "total_size".
                    # Is that what we want? The user asked: "how many files are in the source folder vs how many would be moved"
                    # Yes, they probably want to see the massive amount of files in node_modules vs what is actually moved.
                    # This means we CANNOT skip them in os.walk if we want to tally the TRUE total size.
                    # We must walk everything, but track if the current path is excluded.
                    break
        except Exception:
            pass
            
        # Proper full walk to get true totals vs transfer totals
        total_files = 0
        total_size = 0
        transfer_files = 0
        transfer_size = 0
        
        try:
            for root_path in source_paths:
                if task_id != self._current_task_id: return
                
                exclusions = get_exclusions_func(root_path)
                exclude_dirs = set(exclusions.get("dirs", []))
                exclude_files = set(exclusions.get("files", []))
                
                for dirpath, dirnames, filenames in os.walk(root_path):
                    if task_id != self._current_task_id: return
                    
                    # Check if current directory path contains an excluded directory
                    # A robust way is to check the path parts relative to root
                    rel_path = os.path.relpath(dirpath, root_path)
                    parts = [] if rel_path == '.' else rel_path.split(os.sep)
                    
                    is_dir_excluded = any(part in exclude_dirs for part in parts)
                    
                    for f in filenames:
                        if task_id != self._current_task_id: return
                        
                        f_path = os.path.join(dirpath, f)
                        try:
                            # Use lstat to avoid following symlinks into loops
                            stat = os.lstat(f_path)
                            size = stat.st_size
                            
                            total_files += 1
                            total_size += size
                            
                            if not is_dir_excluded and f not in exclude_files:
                                transfer_files += 1
                                transfer_size += size
                        except OSError:
                            pass
        except Exception:
            pass
            
        if task_id == self._current_task_id:
            # Update UI on main thread
            if self.winfo_exists():
                self.after(0, lambda: self._update_ui_with_stats(total_files, total_size, transfer_files, transfer_size))

    def _update_ui_with_stats(self, total_files: int, total_size: int, transfer_files: int, transfer_size: int):
        self.status_label.grid_remove()
        
        saved_size = total_size - transfer_size
        pct = (saved_size / total_size * 100) if total_size > 0 else 0
        transfer_pct = (transfer_size / total_size * 100) if total_size > 0 else 100
        
        self.total_label.configure(text=f"📂 Source: {total_files:,} files ({format_size(total_size)})")
        self.transfer_label.configure(text=f"✨ Transferring: {transfer_files:,} files ({format_size(transfer_size)})")
        self.saved_label.configure(text=f"📉 Space Saved: {format_size(saved_size)} ({pct:.1f}%)")
        
        self.total_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.transfer_label.grid(row=0, column=1, padx=8, pady=8)
        self.saved_label.grid(row=0, column=2, padx=8, pady=8, sticky="e")
