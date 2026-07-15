"""
Theme manager for OneDrive Smart Transfer.

Manages Light / Dark / System theme modes using customtkinter's built-in
system detection. Falls back to Light mode if detection fails.
"""

import customtkinter as ctk


# Color palette for the application
COLORS = {
    "dark": {
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_card": "#1f2940",
        "accent": "#0ea5e9",
        "accent_hover": "#38bdf8",
        "accent_gradient_start": "#06b6d4",
        "accent_gradient_end": "#3b82f6",
        "text_primary": "#f1f5f9",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "excluded": "#ef4444",
        "included": "#22c55e",
        "border": "#334155",
        "border_accent": "#0ea5e9",
        "drop_zone_bg": "#1e293b",
        "drop_zone_border": "#475569",
        "drop_zone_hover": "#0ea5e9",
        "progress_bg": "#1e293b",
        "progress_fill": "#0ea5e9",
        "button_primary": "#0ea5e9",
        "button_primary_hover": "#38bdf8",
        "button_secondary": "#334155",
        "button_secondary_hover": "#475569",
    },
    "light": {
        "bg_primary": "#f8fafc",
        "bg_secondary": "#f1f5f9",
        "bg_card": "#ffffff",
        "accent": "#0284c7",
        "accent_hover": "#0369a1",
        "accent_gradient_start": "#0891b2",
        "accent_gradient_end": "#2563eb",
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "text_muted": "#94a3b8",
        "success": "#16a34a",
        "warning": "#d97706",
        "error": "#dc2626",
        "excluded": "#dc2626",
        "included": "#16a34a",
        "border": "#e2e8f0",
        "border_accent": "#0284c7",
        "drop_zone_bg": "#f1f5f9",
        "drop_zone_border": "#cbd5e1",
        "drop_zone_hover": "#0284c7",
        "progress_bg": "#e2e8f0",
        "progress_fill": "#0284c7",
        "button_primary": "#0284c7",
        "button_primary_hover": "#0369a1",
        "button_secondary": "#e2e8f0",
        "button_secondary_hover": "#cbd5e1",
    },
}


class ThemeManager:
    """Manages application theme (Light/Dark/System)."""

    def __init__(self):
        self._current_mode = "system"
        self._on_change_callbacks = []

    def initialize(self, mode: str = "system") -> None:
        """Initialize the theme.

        Args:
            mode: "system", "light", or "dark".
        """
        self._current_mode = mode
        self._apply_mode(mode)

    def _apply_mode(self, mode: str) -> None:
        """Apply the theme mode to customtkinter.

        Args:
            mode: "system", "light", or "dark".
        """
        try:
            if mode == "system":
                # customtkinter uses darkdetect internally for system detection
                ctk.set_appearance_mode("system")
            elif mode == "dark":
                ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode("light")
        except Exception:
            # If system detection fails, fall back to light
            ctk.set_appearance_mode("light")

    def toggle(self) -> str:
        """Toggle between light and dark mode.

        Returns:
            The new mode ("light" or "dark").
        """
        current = self.get_effective_mode()
        new_mode = "light" if current == "dark" else "dark"
        self._current_mode = new_mode
        self._apply_mode(new_mode)
        for callback in self._on_change_callbacks:
            callback(new_mode)
        return new_mode

    def set_mode(self, mode: str) -> None:
        """Set the theme mode explicitly.

        Args:
            mode: "system", "light", or "dark".
        """
        self._current_mode = mode
        self._apply_mode(mode)
        for callback in self._on_change_callbacks:
            callback(mode)

    def get_effective_mode(self) -> str:
        """Get the currently active mode (resolves 'system' to actual mode).

        Returns:
            "light" or "dark".
        """
        if self._current_mode == "system":
            try:
                import darkdetect
                return "dark" if darkdetect.isDark() else "light"
            except Exception:
                return "light"
        return self._current_mode

    @property
    def current_mode(self) -> str:
        """Get the configured mode (may be 'system')."""
        return self._current_mode

    def get_colors(self) -> dict:
        """Get the color palette for the current theme.

        Returns:
            Dictionary of color values.
        """
        effective = self.get_effective_mode()
        return COLORS.get(effective, COLORS["light"])

    def on_change(self, callback) -> None:
        """Register a callback for theme changes.

        Args:
            callback: Function that receives the new mode string.
        """
        self._on_change_callbacks.append(callback)


# Global theme manager instance
theme_manager = ThemeManager()
