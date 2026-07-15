"""
Drag-and-drop zone widget for OneDrive Smart Transfer.

A visually prominent area where users can drag files/folders from
Windows File Explorer. Features animated borders and hover effects.
"""

import os
import customtkinter as ctk
from tkinterdnd2 import DND_FILES
from typing import Callable, Optional


class DropZone(ctk.CTkFrame):
    """A drag-and-drop zone that accepts files from Windows Explorer.

    Features:
      - Animated dashed border
      - Hover glow effect when dragging over
      - Click to browse fallback
      - Displays list of dropped items
    """

    def __init__(
        self,
        master,
        on_files_dropped: Optional[Callable[[list[str]], None]] = None,
        **kwargs,
    ):
        """Initialize the drop zone.

        Args:
            master: Parent widget.
            on_files_dropped: Callback when files are dropped. Receives a list of paths.
        """
        super().__init__(master, **kwargs)
        self._on_files_dropped = on_files_dropped
        self._dropped_items: list[str] = []
        self._is_hovering = False
        self._animation_step = 0

        self._setup_ui()
        self._setup_dnd()

    def _setup_ui(self) -> None:
        """Create the drop zone UI."""
        self.configure(corner_radius=12)

        # Main drop area
        self._drop_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            border_width=2,
            border_color=("gray70", "gray30"),
        )
        self._drop_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Icon and text
        self._icon_label = ctk.CTkLabel(
            self._drop_frame,
            text="📂",
            font=ctk.CTkFont(size=40),
        )
        self._icon_label.pack(pady=(20, 5))

        self._text_label = ctk.CTkLabel(
            self._drop_frame,
            text="Drag & Drop Folders Here",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self._text_label.pack(pady=(0, 2))

        self._subtext_label = ctk.CTkLabel(
            self._drop_frame,
            text="or click to browse",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
        )
        self._subtext_label.pack(pady=(0, 20))

        # Bind click to browse
        for widget in [self._drop_frame, self._icon_label, self._text_label, self._subtext_label]:
            widget.bind("<Button-1>", self._on_click_browse)

    def _setup_dnd(self) -> None:
        """Set up drag-and-drop handlers."""
        try:
            self._drop_frame.drop_target_register(DND_FILES)
            self._drop_frame.dnd_bind("<<DropEnter>>", self._on_drag_enter)
            self._drop_frame.dnd_bind("<<DropLeave>>", self._on_drag_leave)
            self._drop_frame.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            # If DnD registration fails (e.g., tkdnd not available),
            # the click-to-browse fallback still works
            pass

    def _on_drag_enter(self, event=None) -> None:
        """Handle drag hover enter — show visual feedback."""
        self._is_hovering = True
        self._drop_frame.configure(
            border_color=("#0284c7", "#0ea5e9"),
            border_width=3,
        )
        self._icon_label.configure(text="⬇️")
        self._text_label.configure(text="Drop Here!", text_color=("#0284c7", "#0ea5e9"))

    def _on_drag_leave(self, event=None) -> None:
        """Handle drag hover leave — reset visual feedback."""
        self._is_hovering = False
        self._drop_frame.configure(
            border_color=("gray70", "gray30"),
            border_width=2,
        )
        self._icon_label.configure(text="📂")
        self._text_label.configure(
            text="Drag & Drop Folders Here",
            text_color=("gray10", "gray90"),
        )

    def _on_drop(self, event) -> None:
        """Handle files being dropped onto the zone."""
        self._on_drag_leave()

        # Parse the dropped file paths
        try:
            files = self.tk.splitlist(event.data)
        except Exception:
            files = event.data.split()

        # Filter to existing paths
        valid_paths = []
        for f in files:
            # Remove braces that tkdnd may add around paths with spaces
            f = f.strip("{}")
            if os.path.exists(f):
                valid_paths.append(os.path.normpath(f))

        if valid_paths:
            # Add to existing items (avoid duplicates)
            for path in valid_paths:
                if path not in self._dropped_items:
                    self._dropped_items.append(path)

            if self._on_files_dropped:
                self._on_files_dropped(list(self._dropped_items))

    def _on_click_browse(self, event=None) -> None:
        """Open a folder dialog as an alternative to drag-and-drop."""
        from tkinter import filedialog

        folder = filedialog.askdirectory(
            title="Select a Folder",
            parent=self.winfo_toplevel(),
        )

        if folder:
            norm_path = os.path.normpath(folder)
            if norm_path not in self._dropped_items:
                self._dropped_items.append(norm_path)

            if self._on_files_dropped:
                self._on_files_dropped(list(self._dropped_items))

    def get_items(self) -> list[str]:
        """Get the list of dropped/selected items.

        Returns:
            List of file/folder paths.
        """
        return list(self._dropped_items)

    def clear_items(self) -> None:
        """Clear all dropped items."""
        self._dropped_items.clear()
        if self._on_files_dropped:
            self._on_files_dropped([])

    def remove_item(self, path: str) -> None:
        """Remove a specific item from the list.

        Args:
            path: The path to remove.
        """
        if path in self._dropped_items:
            self._dropped_items.remove(path)
            if self._on_files_dropped:
                self._on_files_dropped(list(self._dropped_items))
