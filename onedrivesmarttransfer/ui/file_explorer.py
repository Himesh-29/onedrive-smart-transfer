"""
Lazy-loading File Explorers with WinSCP-style layouts and VS Code style icons.

Uses ttk.Treeview for efficient rendering of thousands of files by only
loading directories when they are expanded.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk
from typing import Optional, Callable

from onedrivesmarttransfer.core.exclusion_manager import ExclusionManager
from onedrivesmarttransfer.core.stack_detector import detect_stacks, get_stack_display_names
from onedrivesmarttransfer.ui.theme_manager import theme_manager


class IconManager:
    """Generates and caches basic VS Code style material icons."""
    _instance = None

    def __init__(self):
        self.icons = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = IconManager()
        return cls._instance

    def get_icon(self, is_dir: bool, ext: str = "", excluded: bool = False) -> ImageTk.PhotoImage:
        """Get an icon for a file or folder."""
        ext = ext.lower()
        key = f"{is_dir}_{ext}_{excluded}"
        if key in self.icons:
            return self.icons[key]

        # Generate a 16x16 icon
        img = Image.new("RGBA", (18, 18), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        if is_dir:
            # Folder icon (Material yellow/blue)
            fill_color = "#4b5563" if excluded else "#dcb67a"
            draw.polygon([(1, 2), (7, 2), (9, 4), (16, 4), (16, 14), (1, 14)], fill=fill_color)
        else:
            # File icon based on extension
            color = "#9ca3af" if excluded else "#8ba4b8"
            text_color = "white"
            text = ""

            if not excluded:
                if ext in [".js", ".jsx"]: color = "#f7df1e"; text_color = "black"
                elif ext in [".ts", ".tsx"]: color = "#3178c6"
                elif ext in [".py"]: color = "#3776ab"
                elif ext in [".json"]: color = "#cb3837"
                elif ext in [".html"]: color = "#e34f26"
                elif ext in [".css"]: color = "#1572b6"
                elif ext in [".md"]: color = "#083fa1"
                elif ext in [".java", ".jar", ".class"]: color = "#b07219"
                elif ext in [".cpp", ".c", ".h", ".hpp"]: color = "#f34b7d"
                elif ext in [".rs"]: color = "#dea584"; text_color = "black"
                elif ext in [".go"]: color = "#00add8"

            # Draw a simple file outline
            draw.rectangle([(3, 1), (13, 16)], fill=color)
            draw.polygon([(13, 1), (13, 5), (17, 5)], fill="#d1d5db")  # Folded corner

            # Optional: We could draw text here if we had a tiny font, but simple colors
            # are enough to mimic the material icon look without text.

        if excluded:
            # Draw a subtle strike/overlay for excluded
            draw.line([(0, 9), (18, 9)], fill="#ef4444", width=2)

        tk_img = ImageTk.PhotoImage(img)
        self.icons[key] = tk_img
        return tk_img


def apply_treeview_style(theme_mode: str):
    """Style the ttk.Treeview to match CustomTkinter."""
    style = ttk.Style()
    
    # Use a default theme as a base that supports coloring well on Windows
    style.theme_use("clam")

    if theme_mode == "dark":
        bg_color = "#1f2940"  # matches bg_card in theme_manager
        fg_color = "#f1f5f9"
        sel_bg = "#0ea5e9"
        sel_fg = "white"
        field_bg = bg_color
    else:
        bg_color = "#ffffff"
        fg_color = "#0f172a"
        sel_bg = "#0284c7"
        sel_fg = "white"
        field_bg = bg_color

    style.configure(
        "Modern.Treeview",
        background=bg_color,
        foreground=fg_color,
        fieldbackground=field_bg,
        borderwidth=0,
        font=("Segoe UI", 10),
        rowheight=24
    )
    
    style.map(
        "Modern.Treeview",
        background=[("selected", sel_bg)],
        foreground=[("selected", sel_fg)],
    )


class LazyFileTree(ctk.CTkFrame):
    """Base lazy-loading file tree using ttk.Treeview."""

    def __init__(self, master, on_select: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._icon_mgr = IconManager.get_instance()

        self._setup_ui()

    def _setup_ui(self):
        """Create the Treeview and scrollbars."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Apply styles
        apply_treeview_style(theme_manager.get_effective_mode())

        # Treeview
        self.tree = ttk.Treeview(self, style="Modern.Treeview", show="tree")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Tags for colors
        self.tree.tag_configure("excluded", foreground="#9ca3af")
        
        # Events
        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _on_tree_select(self, event):
        """Handle item selection."""
        if self._on_select:
            selection = self.tree.selection()
            if selection:
                # Get the absolute path which is stored in the item's values
                item = self.tree.item(selection[0])
                path = item["values"][0] if item.get("values") else ""
                self._on_select(path)

    def _on_open(self, event):
        """Handle expanding a folder to lazy-load its children."""
        node_id = self.tree.focus()
        children = self.tree.get_children(node_id)
        
        # Check if the only child is the dummy node
        if len(children) == 1 and self.tree.item(children[0], "text") == "Loading...":
            self.tree.delete(children[0])
            
            # Get the path of the expanded node
            item = self.tree.item(node_id)
            path = item["values"][0]
            
            # Load actual children
            self._load_children(node_id, path)

    def _load_children(self, parent_id: str, path: str):
        """Load the immediate children of a path. Must be implemented by subclasses."""
        pass

    def _insert_node(self, parent_id: str, text: str, path: str, is_dir: bool, excluded: bool = False, ext: str = ""):
        """Insert a node into the tree."""
        icon = self._icon_mgr.get_icon(is_dir=is_dir, ext=ext, excluded=excluded)
        tags = ("excluded",) if excluded else ()
        
        node_id = self.tree.insert(
            parent_id,
            "end",
            text=f" {text}",
            image=icon,
            values=(path,),
            tags=tags
        )
        
        if is_dir and not excluded:
            # Insert dummy node to make it expandable
            self.tree.insert(node_id, "end", text="Loading...")
            
        return node_id


class SourceExplorer(LazyFileTree):
    """File explorer for source folders with exclusion checking and stack detection."""

    def __init__(self, master, exclusion_manager: ExclusionManager, **kwargs):
        super().__init__(master, **kwargs)
        self._exclusion_mgr = exclusion_manager
        
        # Store detection results per root path
        self._root_stacks = {}
        self._root_exclusions = {}

    def load_sources(self, source_paths: list[str]):
        """Load root source directories into the tree."""
        # Clear existing
        self.tree.delete(*self.tree.get_children())
        self._root_stacks.clear()
        self._root_exclusions.clear()

        for path in source_paths:
            path = os.path.normpath(path)
            if not os.path.exists(path):
                continue
                
            name = os.path.basename(path) or path
            is_dir = os.path.isdir(path)
            
            if is_dir:
                # Detect stacks and exclusions for this root
                stacks = detect_stacks(path)
                self._root_stacks[path] = stacks
                self._root_exclusions[path] = self._exclusion_mgr.get_active_exclusions(stacks)
                
            self._insert_node("", name, path, is_dir=is_dir)

    def _get_root_exclusions(self, path: str) -> dict:
        """Find the exclusion rules applicable to a path by finding its root."""
        for root, exclusions in self._root_exclusions.items():
            if path.startswith(root):
                return exclusions
        return {"dirs": [], "files": []}

    def _load_children(self, parent_id: str, parent_path: str):
        """Load directory contents and apply exclusions."""
        try:
            items = os.listdir(parent_path)
        except PermissionError:
            return

        exclusions = self._get_root_exclusions(parent_path)
        exclude_dirs = exclusions.get("dirs", [])
        exclude_files = exclusions.get("files", [])

        # Separate dirs and files for sorting (dirs first)
        dirs = []
        files = []

        for name in items:
            full_path = os.path.join(parent_path, name)
            if os.path.isdir(full_path):
                dirs.append(name)
            else:
                files.append(name)

        dirs.sort(key=str.lower)
        files.sort(key=str.lower)

        for d in dirs:
            full_path = os.path.join(parent_path, d)
            excluded = d in exclude_dirs
            self._insert_node(parent_id, d, full_path, is_dir=True, excluded=excluded)

        for f in files:
            full_path = os.path.join(parent_path, f)
            excluded = f in exclude_files
            ext = os.path.splitext(f)[1]
            self._insert_node(parent_id, f, full_path, is_dir=False, excluded=excluded, ext=ext)


class DestinationExplorer(LazyFileTree):
    """File explorer for the destination (OneDrive) directory."""

    def __init__(self, master, on_path_changed: Callable, **kwargs):
        super().__init__(master, on_select=on_path_changed, **kwargs)

    def load_destination(self, path: str):
        """Load the root OneDrive folder."""
        self.tree.delete(*self.tree.get_children())
        
        path = os.path.normpath(path)
        if not os.path.exists(path):
            return

        name = os.path.basename(path) or path
        
        root_id = self._insert_node("", name, path, is_dir=True)
        # Delete the dummy Loading... node
        children = self.tree.get_children(root_id)
        if len(children) == 1 and self.tree.item(children[0], "text") == "Loading...":
            self.tree.delete(children[0])
            
        # Auto-expand the root node
        self.tree.item(root_id, open=True)
        self._load_children(root_id, path)
        
        # Select root
        self.tree.selection_set(root_id)

    def _load_children(self, parent_id: str, parent_path: str):
        """Load directory contents (only folders for destination, or all files?).
        For destinations, usually we want to see folders, but seeing files is fine too.
        Let's show everything to be consistent."""
        try:
            items = os.listdir(parent_path)
        except PermissionError:
            return

        dirs = []
        files = []

        for name in items:
            full_path = os.path.join(parent_path, name)
            if os.path.isdir(full_path):
                dirs.append(name)
            else:
                files.append(name)

        dirs.sort(key=str.lower)
        files.sort(key=str.lower)

        for d in dirs:
            full_path = os.path.join(parent_path, d)
            self._insert_node(parent_id, d, full_path, is_dir=True)

        for f in files:
            full_path = os.path.join(parent_path, f)
            ext = os.path.splitext(f)[1]
            self._insert_node(parent_id, f, full_path, is_dir=False, ext=ext)

    def create_new_folder(self, parent_path: str):
        """Create a new subfolder in the selected directory."""
        if not parent_path or not os.path.isdir(parent_path):
            messagebox.showwarning("Warning", "Please select a valid destination folder first.")
            return

        dialog = ctk.CTkInputDialog(text="Enter new folder name:", title="Create New Folder")
        folder_name = dialog.get_input()
        
        if folder_name:
            folder_name = folder_name.strip()
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                folder_name = folder_name.replace(char, "_")

            new_path = os.path.join(parent_path, folder_name)
            try:
                os.makedirs(new_path, exist_ok=True)
                # Reload the destination to show the new folder
                # We could insert it manually, but reloading is simpler if we just reload the parent
                # For a full implementation, we'd find the node_id for parent_path and reload it
                # For now, just reload the root
                root_item = self.tree.get_children()[0]
                root_path = self.tree.item(root_item)["values"][0]
                self.load_destination(root_path)
                messagebox.showinfo("Success", f"Created folder: {folder_name}")
            except OSError as e:
                messagebox.showerror("Error", f"Could not create folder:\n{e}")
