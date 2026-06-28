"""
Footer — Barre de statut en bas de l'application.

Affiche la version, le statut de connexion, l'utilisateur et la latence API.
"""

import tkinter as tk
from datetime import datetime
from gui.theme import (
    INVERSE_SURFACE,
    INVERSE_ON_SURFACE,
    SUCCESS,
    PRIMARY,
    FONT_LABEL_SM,
)


class Footer(tk.Frame):
    """Barre de statut en bas."""

    def __init__(self, parent, height=32):
        super().__init__(parent, bg=INVERSE_SURFACE, height=height)
        self.pack_propagate(False)

        inner = tk.Frame(self, bg=INVERSE_SURFACE)
        inner.pack(fill="both", expand=True, padx=16)

        # Gauche : version + statut
        left = tk.Frame(inner, bg=INVERSE_SURFACE)
        left.pack(side="left")

        tk.Label(
            left,
            text="WMS v2.4.1",
            font=FONT_LABEL_SM,
            bg=INVERSE_SURFACE,
            fg=INVERSE_ON_SURFACE,
        ).pack(side="left")

        tk.Label(
            left, text="  ●", font=("Segoe UI", 10), bg=INVERSE_SURFACE, fg=SUCCESS
        ).pack(side="left")

        tk.Label(
            left, text=" Connecté", font=FONT_LABEL_SM, bg=INVERSE_SURFACE, fg=SUCCESS
        ).pack(side="left")

        # Centre : utilisateur
        center = tk.Frame(inner, bg=INVERSE_SURFACE)
        center.pack(side="left", expand=True)

        tk.Label(
            center,
            text="Utilisateur: admin_sys  |  Terminal: A-1",
            font=FONT_LABEL_SM,
            bg=INVERSE_SURFACE,
            fg=INVERSE_ON_SURFACE,
        ).pack()

        # Droite : latence + horloge
        right = tk.Frame(inner, bg=INVERSE_SURFACE)
        right.pack(side="right")

        self.latency_label = tk.Label(
            right,
            text="Latence API: --ms",
            font=FONT_LABEL_SM,
            bg=INVERSE_SURFACE,
            fg=INVERSE_ON_SURFACE,
        )
        self.latency_label.pack(side="left", padx=(0, 16))

        self.clock_label = tk.Label(
            right, text="", font=FONT_LABEL_SM, bg=INVERSE_SURFACE, fg=PRIMARY
        )
        self.clock_label.pack(side="left")

        self._update_clock()

    def _update_clock(self):
        """Met à jour l'horloge chaque seconde."""
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=now)
        self.after(1000, self._update_clock)

    def set_latency(self, ms):
        """Met à jour la latence affichée."""
        color = SUCCESS if ms < 50 else "#f57c00" if ms < 200 else "#ba1a1a"
        self.latency_label.configure(text=f"Latence API: {ms}ms", fg=color)
