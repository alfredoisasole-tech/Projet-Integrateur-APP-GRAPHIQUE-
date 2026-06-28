"""
Topbar — Barre supérieure de l'application.

Affiche le titre, le menu et les indicateurs de statut.
"""

import tkinter as tk
from gui.theme import (
    SURFACE_LOWEST,
    ON_SURFACE,
    ON_SURFACE_VARIANT,
    PRIMARY,
    OUTLINE_VARIANT,
    SURFACE_CONTAINER,
    FONT_HEADLINE_SM,
    FONT_BODY_SM,
    FONT_LABEL_SM,
)


class Topbar(tk.Frame):
    """Barre supérieure fixe."""

    def __init__(self, parent, height=48):
        super().__init__(parent, bg=SURFACE_LOWEST, height=height)
        self.pack_propagate(False)

        # Bordure inférieure
        self.configure(highlightbackground=OUTLINE_VARIANT, highlightthickness=0)

        # Layout horizontal
        inner = tk.Frame(self, bg=SURFACE_LOWEST)
        inner.pack(fill="both", expand=True, padx=16)

        # Titre
        tk.Label(
            inner,
            text="WMS-CLAM-PRO",
            font=FONT_HEADLINE_SM,
            bg=SURFACE_LOWEST,
            fg=PRIMARY,
        ).pack(side="left")

        # Menu items
        menu_frame = tk.Frame(inner, bg=SURFACE_LOWEST)
        menu_frame.pack(side="left", padx=(24, 0))

        for text in ["Fichier", "Édition", "Navigation", "Aide"]:
            lbl = tk.Label(
                menu_frame,
                text=text,
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
                padx=12,
                cursor="hand2",
            )
            lbl.pack(side="left")
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg=ON_SURFACE))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(fg=ON_SURFACE_VARIANT))

        # Côté droit : recherche + indicateurs
        right = tk.Frame(inner, bg=SURFACE_LOWEST)
        right.pack(side="right")

        # Champ de recherche
        search_frame = tk.Frame(right, bg=SURFACE_CONTAINER, padx=8, pady=4)
        search_frame.pack(side="left", padx=(0, 16))

        tk.Label(
            search_frame,
            text="🔍",
            font=("Segoe UI", 10),
            bg=SURFACE_CONTAINER,
            fg=ON_SURFACE_VARIANT,
        ).pack(side="left")

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=FONT_BODY_SM,
            bg=SURFACE_CONTAINER,
            fg=ON_SURFACE,
            bd=0,
            width=20,
            insertbackground=ON_SURFACE,
        )
        search_entry.pack(side="left", padx=(4, 0))
        search_entry.insert(0, "Rechercher...")
        search_entry.bind(
            "<FocusIn>",
            lambda e: (
                search_entry.delete(0, "end")
                if search_entry.get() == "Rechercher..."
                else None
            ),
        )
        search_entry.bind(
            "<FocusOut>",
            lambda e: (
                search_entry.insert(0, "Rechercher...")
                if not search_entry.get()
                else None
            ),
        )

        # Indicateurs
        tk.Label(
            right,
            text="🔔",
            font=("Segoe UI", 14),
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
            cursor="hand2",
        ).pack(side="left", padx=4)

        tk.Label(
            right,
            text="⚙",
            font=("Segoe UI", 14),
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
            cursor="hand2",
        ).pack(side="left", padx=4)

        # Bordure basse
        border = tk.Frame(self, bg=OUTLINE_VARIANT, height=1)
        border.pack(side="bottom", fill="x")
