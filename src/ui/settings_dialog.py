"""
Settings dialog for OneDrive Smart Transfer.

A child-friendly UI for managing:
  - Exclusion patterns (checkbox toggle, add/remove, category dropdown)
  - Theme preference
  - Default action (copy/move)
  - OneDrive path override
  - Config storage path

Designed to be simple enough that even a 5-year-old can use it.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional, Callable

from src.core.exclusion_manager import ExclusionManager


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog with user-friendly exclusion pattern editor.

    Features:
      - Category dropdown to switch between tech stacks
      - Checkboxes to toggle individual patterns
      - Remove buttons for each pattern
      - Simple text input to add new patterns
      - Reset to defaults, import/export
    """

    def __init__(
        self,
        master,
        exclusion_manager: ExclusionManager,
        current_theme: str = "system",
        current_action: str = "copy",
        onedrive_path: str = "",
        config_path: str = "",
        on_theme_changed: Optional[Callable] = None,
        on_action_changed: Optional[Callable] = None,
        on_onedrive_changed: Optional[Callable] = None,
        on_config_path_changed: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._exclusion_mgr = exclusion_manager
        self._on_theme_changed = on_theme_changed
        self._on_action_changed = on_action_changed
        self._on_onedrive_changed = on_onedrive_changed
        self._on_config_path_changed = on_config_path_changed

        self.title("⚙ Settings")
        self.geometry("650x700")
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()

        # Make it appear centered
        self.after(10, self._center_window)

        self._setup_ui(current_theme, current_action, onedrive_path, config_path)

    def _center_window(self) -> None:
        """Center the dialog on the parent window."""
        self.update_idletasks()
        parent = self.master
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

    def _setup_ui(
        self,
        current_theme: str,
        current_action: str,
        onedrive_path: str,
        config_path: str,
    ) -> None:
        """Create the settings dialog UI."""
        # Main scrollable area
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)

        # ── Theme Section ──
        self._add_section_header(main_frame, "🎨 Appearance")

        theme_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(theme_frame, text="Theme:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 10))

        self._theme_var = ctk.StringVar(value=current_theme)
        for mode_value, mode_label in [("system", "🖥 System"), ("light", "☀️ Light"), ("dark", "🌙 Dark")]:
            btn = ctk.CTkRadioButton(
                theme_frame,
                text=mode_label,
                variable=self._theme_var,
                value=mode_value,
                font=ctk.CTkFont(size=12),
                command=self._on_theme_change,
            )
            btn.pack(side="left", padx=8)

        # ── Default Action Section ──
        self._add_section_header(main_frame, "📋 Default Action")

        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=(4, 12))

        self._action_var = ctk.StringVar(value=current_action)
        copy_btn = ctk.CTkRadioButton(
            action_frame, text="📄 Copy (keep originals)",
            variable=self._action_var, value="copy",
            font=ctk.CTkFont(size=12), command=self._on_action_change,
        )
        copy_btn.pack(side="left", padx=(0, 16))

        move_btn = ctk.CTkRadioButton(
            action_frame, text="📦 Move (delete originals)",
            variable=self._action_var, value="move",
            font=ctk.CTkFont(size=12), command=self._on_action_change,
        )
        move_btn.pack(side="left")

        # ── OneDrive Path Section ──
        self._add_section_header(main_frame, "☁ OneDrive Path")

        od_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        od_frame.pack(fill="x", pady=(4, 12))

        self._od_entry = ctk.CTkEntry(od_frame, font=ctk.CTkFont(size=12), height=34)
        self._od_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        if onedrive_path:
            self._od_entry.insert(0, onedrive_path)

        od_browse = ctk.CTkButton(
            od_frame, text="Browse", width=70, height=34,
            command=self._browse_onedrive,
        )
        od_browse.pack(side="right")

        # ── Config Storage Path ──
        self._add_section_header(main_frame, "💾 Config Storage Location")

        cfg_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        cfg_frame.pack(fill="x", pady=(4, 12))

        self._cfg_entry = ctk.CTkEntry(cfg_frame, font=ctk.CTkFont(size=12), height=34)
        self._cfg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        if config_path:
            self._cfg_entry.insert(0, config_path)

        cfg_browse = ctk.CTkButton(
            cfg_frame, text="Browse", width=70, height=34,
            command=self._browse_config_path,
        )
        cfg_browse.pack(side="right")

        # ── Exclusion Patterns Section ──
        self._add_section_header(main_frame, "📋 Exclusion Patterns")

        ctk.CTkLabel(
            main_frame,
            text="Toggle patterns on/off, add new ones, or remove them.\n"
                 "Changes are saved automatically.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        # Category dropdown
        categories = self._exclusion_mgr.get_categories()
        cat_names = [c["name"] for c in categories]
        self._cat_id_map = {c["name"]: c["id"] for c in categories}

        cat_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(cat_frame, text="Category:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 8))

        self._cat_dropdown = ctk.CTkComboBox(
            cat_frame,
            values=cat_names,
            font=ctk.CTkFont(size=12),
            command=self._on_category_selected,
            width=250,
            height=34,
            state="readonly",
        )
        self._cat_dropdown.pack(side="left", padx=(0, 8))
        if cat_names:
            self._cat_dropdown.set(cat_names[0])

        # Category enable toggle
        self._cat_toggle_var = ctk.BooleanVar(value=True)
        self._cat_toggle = ctk.CTkSwitch(
            cat_frame,
            text="Enabled",
            variable=self._cat_toggle_var,
            font=ctk.CTkFont(size=12),
            command=self._on_category_toggle,
        )
        self._cat_toggle.pack(side="left")

        # Patterns list (scrollable)
        self._patterns_frame = ctk.CTkScrollableFrame(
            main_frame,
            height=200,
            corner_radius=6,
        )
        self._patterns_frame.pack(fill="both", expand=True, pady=(0, 8))

        # Add pattern row
        add_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        add_frame.pack(fill="x", pady=(0, 8))

        self._add_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="Type folder or file pattern to exclude...",
            font=ctk.CTkFont(size=12),
            height=34,
        )
        self._add_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._add_entry.bind("<Return>", lambda e: self._add_pattern())

        add_btn = ctk.CTkButton(
            add_frame, text="➕ Add", width=70, height=34,
            command=self._add_pattern,
        )
        add_btn.pack(side="right")

        # Bottom buttons
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            bottom_frame, text="🔄 Reset to Defaults", width=140, height=34,
            fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"),
            text_color=("gray20", "gray90"),
            command=self._reset_defaults,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bottom_frame, text="📥 Import", width=90, height=34,
            fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"),
            text_color=("gray20", "gray90"),
            command=self._import_config,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bottom_frame, text="📤 Export", width=90, height=34,
            fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"),
            text_color=("gray20", "gray90"),
            command=self._export_config,
        ).pack(side="left")

        # Load initial category
        if categories:
            self._load_category_patterns(categories[0]["id"])

    def _add_section_header(self, parent, text: str) -> None:
        """Add a styled section header."""
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(12, 2))

        # Separator line
        separator = ctk.CTkFrame(parent, height=1, fg_color=("gray80", "gray30"))
        separator.pack(fill="x", pady=(0, 4))

    def _on_category_selected(self, selection: str) -> None:
        """Handle category dropdown change."""
        cat_id = self._cat_id_map.get(selection)
        if cat_id:
            self._load_category_patterns(cat_id)

    def _load_category_patterns(self, cat_id: str) -> None:
        """Load and display patterns for a specific category."""
        categories = self._exclusion_mgr.get_categories()
        cat = next((c for c in categories if c["id"] == cat_id), None)
        if not cat:
            return

        # Update category toggle
        self._cat_toggle_var.set(cat["enabled"])

        # Clear existing patterns
        for widget in self._patterns_frame.winfo_children():
            widget.destroy()

        # Render each pattern
        for pattern_info in cat["patterns"]:
            self._create_pattern_row(cat_id, pattern_info)

    def _create_pattern_row(self, cat_id: str, pattern_info: dict) -> None:
        """Create a single pattern row with checkbox and remove button."""
        row = ctk.CTkFrame(self._patterns_frame, fg_color="transparent", height=32)
        row.pack(fill="x", pady=2)

        # Checkbox
        var = ctk.BooleanVar(value=pattern_info["enabled"])
        checkbox = ctk.CTkCheckBox(
            row,
            text=pattern_info["name"],
            variable=var,
            font=ctk.CTkFont(size=12),
            command=lambda p=pattern_info["name"], v=var: self._toggle_pattern(cat_id, p, v.get()),
            height=24,
        )
        checkbox.pack(side="left", padx=(0, 8))

        # Default indicator
        if pattern_info["is_default"]:
            default_badge = ctk.CTkLabel(
                row,
                text="default",
                font=ctk.CTkFont(size=9),
                text_color=("gray60", "gray50"),
                anchor="w",
            )
            default_badge.pack(side="left", padx=(0, 8))

        # Remove button
        remove_btn = ctk.CTkButton(
            row,
            text="🗑",
            width=30,
            height=24,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=("#fee2e2", "#7f1d1d"),
            text_color=("#dc2626", "#ef4444"),
            command=lambda p=pattern_info["name"]: self._remove_pattern(cat_id, p),
        )
        remove_btn.pack(side="right")

    def _toggle_pattern(self, cat_id: str, pattern: str, enabled: bool) -> None:
        """Toggle a pattern on/off."""
        self._exclusion_mgr.toggle_pattern(cat_id, pattern, enabled)

    def _on_category_toggle(self) -> None:
        """Toggle entire category on/off."""
        cat_name = self._cat_dropdown.get()
        cat_id = self._cat_id_map.get(cat_name)
        if cat_id:
            self._exclusion_mgr.toggle_category(cat_id, self._cat_toggle_var.get())

    def _add_pattern(self) -> None:
        """Add a new pattern from the text input."""
        pattern = self._add_entry.get().strip()
        if not pattern:
            return

        cat_name = self._cat_dropdown.get()
        cat_id = self._cat_id_map.get(cat_name)
        if not cat_id:
            return

        if self._exclusion_mgr.add_pattern(cat_id, pattern):
            self._add_entry.delete(0, "end")
            self._load_category_patterns(cat_id)
        else:
            messagebox.showinfo("Info", f"Pattern '{pattern}' already exists.", parent=self)

    def _remove_pattern(self, cat_id: str, pattern: str) -> None:
        """Remove a pattern."""
        self._exclusion_mgr.remove_pattern(cat_id, pattern)
        self._load_category_patterns(cat_id)

    def _reset_defaults(self) -> None:
        """Reset all exclusion patterns to defaults."""
        if messagebox.askyesno("Reset", "Reset all exclusion patterns to defaults?", parent=self):
            self._exclusion_mgr.reset_to_defaults()
            cat_name = self._cat_dropdown.get()
            cat_id = self._cat_id_map.get(cat_name)
            if cat_id:
                self._load_category_patterns(cat_id)

    def _import_config(self) -> None:
        """Import exclusion config from file."""
        filepath = filedialog.askopenfilename(
            title="Import Exclusion Config",
            filetypes=[("JSON files", "*.json")],
            parent=self,
        )
        if filepath:
            if self._exclusion_mgr.import_config(filepath):
                cat_name = self._cat_dropdown.get()
                cat_id = self._cat_id_map.get(cat_name)
                if cat_id:
                    self._load_category_patterns(cat_id)
                messagebox.showinfo("Success", "Config imported successfully.", parent=self)
            else:
                messagebox.showerror("Error", "Failed to import config.", parent=self)

    def _export_config(self) -> None:
        """Export exclusion config to file."""
        filepath = filedialog.asksaveasfilename(
            title="Export Exclusion Config",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            parent=self,
        )
        if filepath:
            if self._exclusion_mgr.export_config(filepath):
                messagebox.showinfo("Success", "Config exported successfully.", parent=self)
            else:
                messagebox.showerror("Error", "Failed to export config.", parent=self)

    def _browse_onedrive(self) -> None:
        """Browse for OneDrive folder."""
        folder = filedialog.askdirectory(title="Select OneDrive Folder", parent=self)
        if folder:
            self._od_entry.delete(0, "end")
            self._od_entry.insert(0, folder)
            if self._on_onedrive_changed:
                self._on_onedrive_changed(folder)

    def _browse_config_path(self) -> None:
        """Browse for config storage folder."""
        folder = filedialog.askdirectory(title="Select Config Storage Folder", parent=self)
        if folder:
            self._cfg_entry.delete(0, "end")
            self._cfg_entry.insert(0, folder)
            if self._on_config_path_changed:
                self._on_config_path_changed(folder)

    def _on_theme_change(self) -> None:
        """Handle theme change."""
        if self._on_theme_changed:
            self._on_theme_changed(self._theme_var.get())

    def _on_action_change(self) -> None:
        """Handle default action change."""
        if self._on_action_changed:
            self._on_action_changed(self._action_var.get())
