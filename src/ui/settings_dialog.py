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
    """Settings dialog with user-friendly exclusion pattern editor and general settings.

    Features:
      - Tabbed layout (General & Exclusions)
      - Category dropdown to switch between tech stacks
      - Checkboxes to toggle individual patterns
      - Remove buttons for each pattern
      - Simple text input to add new patterns
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
        self.minsize(600, 600)
        self.transient(master)
        
        # Hide window immediately to prevent flashing before centering
        self.withdraw()

        self._setup_ui(current_theme, current_action, onedrive_path, config_path)
        
        # Center the window and show it
        self.after(50, self._center_window)

    def _center_window(self) -> None:
        """Center the dialog on the parent window and make it visible."""
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
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def _setup_ui(
        self,
        current_theme: str,
        current_action: str,
        onedrive_path: str,
        config_path: str,
    ) -> None:
        """Create the settings dialog UI with a modern Tabview."""
        # Main Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tabview.add("General")
        self.tabview.add("Exclusions")
        
        self._setup_general_tab(self.tabview.tab("General"), current_theme, current_action, onedrive_path, config_path)
        self._setup_exclusions_tab(self.tabview.tab("Exclusions"))

    def _setup_general_tab(self, parent, current_theme, current_action, onedrive_path, config_path):
        """Build the General settings tab."""
        # ── Theme Section ──
        theme_frame = self._create_card(parent, "🎨 Appearance")
        
        self._theme_var = ctk.StringVar(value=current_theme)
        for mode_value, mode_label in [("system", "🖥 System"), ("light", "☀️ Light"), ("dark", "🌙 Dark")]:
            btn = ctk.CTkRadioButton(
                theme_frame,
                text=mode_label,
                variable=self._theme_var,
                value=mode_value,
                font=ctk.CTkFont(size=13),
                command=self._on_theme_change,
            )
            btn.pack(side="left", padx=15, pady=10)

        # ── Default Action Section ──
        action_frame = self._create_card(parent, "📋 Default Action")
        
        self._action_var = ctk.StringVar(value=current_action)
        for action_value, action_label in [("copy", "📄 Copy (keep originals)"), ("move", "📦 Move (delete originals)")]:
            btn = ctk.CTkRadioButton(
                action_frame, 
                text=action_label,
                variable=self._action_var, 
                value=action_value,
                font=ctk.CTkFont(size=13), 
                command=self._on_action_change,
            )
            btn.pack(side="left", padx=15, pady=10)

        # ── Paths Section ──
        paths_frame = self._create_card(parent, "📂 Directories")
        
        # OneDrive Path
        od_container = ctk.CTkFrame(paths_frame, fg_color="transparent")
        od_container.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(od_container, text="OneDrive:", width=80, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self._od_entry = ctk.CTkEntry(od_container, font=ctk.CTkFont(size=12), height=34)
        self._od_entry.pack(side="left", fill="x", expand=True, padx=10)
        if onedrive_path: self._od_entry.insert(0, onedrive_path)
        ctk.CTkButton(od_container, text="Browse", width=70, height=34, command=self._browse_onedrive).pack(side="right")

        # Config Path
        cfg_container = ctk.CTkFrame(paths_frame, fg_color="transparent")
        cfg_container.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(cfg_container, text="Config:", width=80, anchor="w", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self._cfg_entry = ctk.CTkEntry(cfg_container, font=ctk.CTkFont(size=12), height=34)
        self._cfg_entry.pack(side="left", fill="x", expand=True, padx=10)
        if config_path: self._cfg_entry.insert(0, config_path)
        ctk.CTkButton(cfg_container, text="Browse", width=70, height=34, command=self._browse_config_path).pack(side="right")

    def _setup_exclusions_tab(self, parent):
        """Build the Exclusions tab."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="Manage items to exclude during transfers.",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60")
        ).pack(side="left")
        
        # Action Buttons (Reset, Import, Export)
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.pack(side="right")
        
        for btn_text, cmd in [("📥 Import", self._import_config), ("📤 Export", self._export_config), ("🔄 Reset", self._reset_defaults)]:
            ctk.CTkButton(
                actions_frame, text=btn_text, width=80, height=28,
                fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"),
                text_color=("gray20", "gray90"), command=cmd
            ).pack(side="left", padx=4)

        # Card container for Category and Patterns
        card = self._create_card(parent, "")
        
        # Category Selector
        cat_frame = ctk.CTkFrame(card, fg_color="transparent")
        cat_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(cat_frame, text="Tech Stack:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 10))

        categories = self._exclusion_mgr.get_categories()
        cat_names = [c["name"] for c in categories]
        self._cat_id_map = {c["name"]: c["id"] for c in categories}

        self._cat_dropdown = ctk.CTkComboBox(
            cat_frame, values=cat_names, font=ctk.CTkFont(size=13),
            command=self._on_category_selected, width=220, height=34, state="readonly"
        )
        self._cat_dropdown.pack(side="left", padx=(0, 15))
        if cat_names:
            self._cat_dropdown.set(cat_names[0])

        self._cat_toggle_var = ctk.BooleanVar(value=True)
        self._cat_toggle = ctk.CTkSwitch(
            cat_frame, text="Enable this Stack", variable=self._cat_toggle_var,
            font=ctk.CTkFont(size=13), command=self._on_category_toggle,
        )
        self._cat_toggle.pack(side="left")

        # Patterns List Scrollable Frame
        self._patterns_frame = ctk.CTkScrollableFrame(card, height=250, corner_radius=6, fg_color=("gray90", "gray15"))
        self._patterns_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Add Pattern Entry
        add_frame = ctk.CTkFrame(card, fg_color="transparent")
        add_frame.pack(fill="x", padx=15, pady=10)

        self._add_entry = ctk.CTkEntry(
            add_frame, placeholder_text="Type folder or file pattern to exclude (e.g., node_modules)...",
            font=ctk.CTkFont(size=13), height=36
        )
        self._add_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._add_entry.bind("<Return>", lambda e: self._add_pattern())

        ctk.CTkButton(
            add_frame, text="➕ Add Pattern", width=120, height=36,
            font=ctk.CTkFont(size=13, weight="bold"), command=self._add_pattern
        ).pack(side="right")

        # Initial Load
        if categories:
            self._load_category_patterns(categories[0]["id"])

    def _create_card(self, parent, title: str):
        """Helper to create a visually appealing section card."""
        card = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray95", "gray10"))
        card.pack(fill="x", padx=10, pady=10)
        
        if title:
            header_frame = ctk.CTkFrame(card, corner_radius=8, fg_color=("gray85", "gray17"))
            header_frame.pack(fill="x", padx=2, pady=2)
            ctk.CTkLabel(
                header_frame, text=title, font=ctk.CTkFont(size=14, weight="bold")
            ).pack(side="left", padx=15, pady=8)
            
        return card

    # ── Category & Pattern Handlers ──

    def _on_category_selected(self, selection: str) -> None:
        cat_id = self._cat_id_map.get(selection)
        if cat_id: self._load_category_patterns(cat_id)

    def _load_category_patterns(self, cat_id: str) -> None:
        categories = self._exclusion_mgr.get_categories()
        cat = next((c for c in categories if c["id"] == cat_id), None)
        if not cat: return

        self._cat_toggle_var.set(cat["enabled"])

        for widget in self._patterns_frame.winfo_children():
            widget.destroy()

        for pattern_info in cat["patterns"]:
            self._create_pattern_row(cat_id, pattern_info)

    def _create_pattern_row(self, cat_id: str, pattern_info: dict) -> None:
        row = ctk.CTkFrame(self._patterns_frame, fg_color="transparent", height=40)
        row.pack(fill="x", pady=4, padx=5)

        var = ctk.BooleanVar(value=pattern_info["enabled"])
        checkbox = ctk.CTkCheckBox(
            row, text=pattern_info["name"], variable=var,
            font=ctk.CTkFont(size=13),
            command=lambda p=pattern_info["name"], v=var: self._toggle_pattern(cat_id, p, v.get()),
        )
        checkbox.pack(side="left", padx=(5, 10), pady=8)

        if pattern_info["is_default"]:
            ctk.CTkLabel(
                row, text="default", font=ctk.CTkFont(size=10),
                text_color=("gray50", "gray50"), fg_color=("gray85", "gray25"),
                corner_radius=4, padx=6
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            row, text="✕", width=28, height=28, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent", hover_color=("#fee2e2", "#7f1d1d"), text_color=("#dc2626", "#ef4444"),
            command=lambda p=pattern_info["name"]: self._remove_pattern(cat_id, p),
        ).pack(side="right", padx=5)

    def _toggle_pattern(self, cat_id: str, pattern: str, enabled: bool) -> None:
        self._exclusion_mgr.toggle_pattern(cat_id, pattern, enabled)

    def _on_category_toggle(self) -> None:
        cat_id = self._cat_id_map.get(self._cat_dropdown.get())
        if cat_id: self._exclusion_mgr.toggle_category(cat_id, self._cat_toggle_var.get())

    def _add_pattern(self) -> None:
        pattern = self._add_entry.get().strip()
        if not pattern: return

        cat_id = self._cat_id_map.get(self._cat_dropdown.get())
        if not cat_id: return

        if self._exclusion_mgr.add_pattern(cat_id, pattern):
            self._add_entry.delete(0, "end")
            self._load_category_patterns(cat_id)
        else:
            messagebox.showinfo("Info", f"Pattern '{pattern}' already exists.", parent=self)

    def _remove_pattern(self, cat_id: str, pattern: str) -> None:
        self._exclusion_mgr.remove_pattern(cat_id, pattern)
        self._load_category_patterns(cat_id)

    # ── General Actions ──

    def _reset_defaults(self) -> None:
        if messagebox.askyesno("Reset", "Reset all exclusion patterns to defaults?", parent=self):
            self._exclusion_mgr.reset_to_defaults()
            cat_id = self._cat_id_map.get(self._cat_dropdown.get())
            if cat_id: self._load_category_patterns(cat_id)

    def _import_config(self) -> None:
        filepath = filedialog.askopenfilename(title="Import Config", filetypes=[("JSON files", "*.json")], parent=self)
        if filepath and self._exclusion_mgr.import_config(filepath):
            cat_id = self._cat_id_map.get(self._cat_dropdown.get())
            if cat_id: self._load_category_patterns(cat_id)
            messagebox.showinfo("Success", "Config imported successfully.", parent=self)

    def _export_config(self) -> None:
        filepath = filedialog.asksaveasfilename(title="Export Config", defaultextension=".json", filetypes=[("JSON files", "*.json")], parent=self)
        if filepath and self._exclusion_mgr.export_config(filepath):
            messagebox.showinfo("Success", "Config exported successfully.", parent=self)

    def _browse_onedrive(self) -> None:
        folder = filedialog.askdirectory(title="Select OneDrive Folder", parent=self)
        if folder:
            self._od_entry.delete(0, "end")
            self._od_entry.insert(0, folder)
            if self._on_onedrive_changed: self._on_onedrive_changed(folder)

    def _browse_config_path(self) -> None:
        folder = filedialog.askdirectory(title="Select Config Folder", parent=self)
        if folder:
            self._cfg_entry.delete(0, "end")
            self._cfg_entry.insert(0, folder)
            if self._on_config_path_changed: self._on_config_path_changed(folder)

    def _on_theme_change(self) -> None:
        if self._on_theme_changed: self._on_theme_changed(self._theme_var.get())

    def _on_action_change(self) -> None:
        if self._on_action_changed: self._on_action_changed(self._action_var.get())
