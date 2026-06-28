"""
Sidebar — Barre latérale de navigation.

Reproduit la sidebar des maquettes HTML avec :
- Logo SAC LOGISTICS + Nœud Terminal A-1
- 6 boutons de navigation
- Indicateur de page active
"""

import tkinter as tk
import tkinter.ttk as ttk
from gui.theme import (
    SURFACE_LOWEST,
    SECONDARY_CONTAINER,
    PRIMARY,
    ON_SURFACE,
    ON_SURFACE_VARIANT,
    OUTLINE_VARIANT,
    FONT_HEADLINE_SM,
    FONT_BODY_SM,
    FONT_LABEL_SM,
)


class Sidebar(tk.Frame):
    """Barre latérale de navigation fixe."""

    NAV_ITEMS = [
        ("dashboard", "📊", "Tableau de Bord"),
        ("cartographie", "🗺️", "Cartographie"),
        ("reception", "📥", "Réception"),
        ("expedition", "📤", "Expédition"),
        ("inventaire", "📦", "Inventaire"),
        ("rapports", "📋", "Rapports"),
        ("gestion", "🔧", "Gestion"),
        ("admin", "⚙️", "Administration"),
    ]

    def __init__(self, parent, on_navigate=None, width=256):
        super().__init__(parent, bg=SURFACE_LOWEST, width=width)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.buttons = {}
        self.active_view = None

        self._build_header()
        self._build_separator()
        self._build_nav_buttons()
        self._build_footer()

    def _build_header(self):
        """Logo et titre."""
        header = tk.Frame(self, bg=SURFACE_LOWEST)
        header.pack(fill="x", padx=20, pady=(20, 8))

        # Icône industrielle
        tk.Label(
            header, text="⚙", font=("Segoe UI", 28), bg=SURFACE_LOWEST, fg=PRIMARY
        ).pack(anchor="w")

        tk.Label(
            header,
            text="SAC LOGISTICS",
            font=FONT_HEADLINE_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            header,
            text="Nœud Terminal A-1",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w")

    def _build_separator(self):
        """Ligne de séparation."""
        sep = tk.Frame(self, bg=OUTLINE_VARIANT, height=1)
        sep.pack(fill="x", padx=16, pady=12)

    def _build_nav_buttons(self):
        """Boutons de navigation."""
        nav_frame = tk.Frame(self, bg=SURFACE_LOWEST)
        nav_frame.pack(fill="x", padx=12)

        for key, icon, label in self.NAV_ITEMS:
            btn_frame = tk.Frame(nav_frame, bg=SURFACE_LOWEST, cursor="hand2")
            btn_frame.pack(fill="x", pady=2)

            btn_label = tk.Label(
                btn_frame,
                text=f"  {icon}  {label}",
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
                anchor="w",
                padx=12,
                pady=10,
                cursor="hand2",
            )
            btn_label.pack(fill="x")

            # Stocker les références
            self.buttons[key] = (btn_frame, btn_label)

            # Bind click
            for widget in (btn_frame, btn_label):
                widget.bind("<Button-1>", lambda e, k=key: self._on_click(k))
                widget.bind("<Enter>", lambda e, k=key: self._on_hover(k, True))
                widget.bind("<Leave>", lambda e, k=key: self._on_hover(k, False))

    def _build_footer(self):
        """Informations en bas de la sidebar."""
        spacer = tk.Frame(self, bg=SURFACE_LOWEST)
        spacer.pack(fill="both", expand=True)

        footer = tk.Frame(self, bg=SURFACE_LOWEST)
        footer.pack(fill="x", padx=20, pady=(0, 16))

        sep = tk.Frame(footer, bg=OUTLINE_VARIANT, height=1)
        sep.pack(fill="x", pady=(0, 12))

        tk.Label(
            footer,
            text="WMS v2.4.1",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w")

        tk.Label(
            footer, text="admin_sys", font=FONT_LABEL_SM, bg=SURFACE_LOWEST, fg=PRIMARY
        ).pack(anchor="w")

    def _on_click(self, key):
        """Gère le clic sur un bouton de navigation."""
        self.set_active(key)
        if self.on_navigate:
            self.on_navigate(key)

    def _on_hover(self, key, entering):
        """Effet de survol."""
        if key == self.active_view:
            return
        frame, label = self.buttons[key]
        if entering:
            frame.configure(bg="#f2f4f7")
            label.configure(bg="#f2f4f7")
        else:
            frame.configure(bg=SURFACE_LOWEST)
            label.configure(bg=SURFACE_LOWEST)

    def set_active(self, key):
        """Met à jour l'indicateur de page active."""
        self.active_view = key
        for k, (frame, label) in self.buttons.items():
            if k == key:
                frame.configure(bg=SECONDARY_CONTAINER)
                label.configure(
                    bg=SECONDARY_CONTAINER,
                    fg=ON_SURFACE,
                    font=("Segoe UI", 12, "bold"),
                )
            else:
                frame.configure(bg=SURFACE_LOWEST)
                label.configure(
                    bg=SURFACE_LOWEST,
                    fg=ON_SURFACE_VARIANT,
                    font=FONT_BODY_SM,
                )
