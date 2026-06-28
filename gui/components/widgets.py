"""
Composants réutilisables pour l'interface Tkinter.

- StatCard : Carte de statistique avec header, valeur et tendance
- DataTable : Table basée sur Treeview avec tri et style industriel
- ZoneMap : Visualisation de la cartographie des zones (Canvas)
- StatusBadge : Badge coloré pour les statuts
"""

import tkinter as tk
import tkinter.ttk as ttk
from gui.theme import (
    SURFACE_LOWEST,
    SURFACE_CONTAINER_HIGH,
    SURFACE_CONTAINER,
    ON_SURFACE,
    ON_SURFACE_VARIANT,
    PRIMARY,
    OUTLINE,
    OUTLINE_VARIANT,
    SUCCESS,
    WARNING,
    ERROR,
    SECONDARY_CONTAINER,
    FONT_DISPLAY,
    FONT_HEADLINE_LG,
    FONT_HEADLINE_MD,
    FONT_HEADLINE_SM,
    FONT_BODY_MD,
    FONT_BODY_SM,
    FONT_LABEL_SM,
    FONT_LABEL_MD,
)

# ============================================================
# STAT CARD
# ============================================================


class StatCard(tk.Frame):
    """Carte de statistique industrielle (KPI card).

    Args:
        parent: Widget parent.
        title: Titre dans le header.
        value: Valeur principale à afficher.
        subtitle: Sous-titre ou description.
        trend: Tendance (ex: "+12.4%").
        trend_positive: True si tendance positive.
        progress: Valeur de progression (0-100), None pour masquer.
    """

    def __init__(
        self,
        parent,
        title="",
        value="",
        subtitle="",
        trend="",
        trend_positive=True,
        progress=None,
        **kwargs,
    ):
        super().__init__(
            parent,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
            **kwargs,
        )

        # Header bar
        header = tk.Frame(self, bg=SURFACE_CONTAINER_HIGH)
        header.pack(fill="x")

        tk.Label(
            header,
            text=title.upper(),
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")

        # Corps
        body = tk.Frame(self, bg=SURFACE_LOWEST)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Valeur principale
        val_frame = tk.Frame(body, bg=SURFACE_LOWEST)
        val_frame.pack(anchor="w")

        tk.Label(
            val_frame,
            text=str(value),
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(side="left")

        if trend:
            trend_color = SUCCESS if trend_positive else ERROR
            tk.Label(
                val_frame,
                text=f"  {trend}",
                font=FONT_LABEL_MD,
                bg=SURFACE_LOWEST,
                fg=trend_color,
            ).pack(side="left", pady=(8, 0))

        # Sous-titre
        if subtitle:
            tk.Label(
                body,
                text=subtitle,
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
            ).pack(anchor="w", pady=(4, 0))

        # Barre de progression
        if progress is not None:
            prog_frame = tk.Frame(body, bg=SURFACE_LOWEST)
            prog_frame.pack(fill="x", pady=(8, 0))

            style_name = "Primary.Horizontal.TProgressbar"
            if progress > 90:
                style_name = "Error.Horizontal.TProgressbar"
            elif progress > 70:
                style_name = "Warning.Horizontal.TProgressbar"

            bar = ttk.Progressbar(
                prog_frame,
                style=style_name,
                length=200,
                mode="determinate",
                value=progress,
            )
            bar.pack(fill="x")

            tk.Label(
                prog_frame,
                text=f"{progress}%",
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=OUTLINE,
            ).pack(anchor="e", pady=(2, 0))


# ============================================================
# DATA TABLE
# ============================================================


class DataTable(tk.Frame):
    """Table de données haute densité basée sur Treeview.

    Args:
        parent: Widget parent.
        columns: Liste de tuples (id, label, width).
        data: Liste de tuples avec les valeurs des colonnes.
        show_header: Afficher le titre de la table.
        title: Titre de la table.
    """

    def __init__(self, parent, columns, data=None, title="", **kwargs):
        super().__init__(
            parent,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
            **kwargs,
        )

        # Titre
        if title:
            header = tk.Frame(self, bg=SURFACE_CONTAINER_HIGH)
            header.pack(fill="x")
            tk.Label(
                header,
                text=title.upper(),
                font=FONT_LABEL_SM,
                bg=SURFACE_CONTAINER_HIGH,
                fg=OUTLINE,
                padx=16,
                pady=8,
            ).pack(side="left")

        # Treeview
        col_ids = [c[0] for c in columns]
        tree_frame = tk.Frame(self, bg=SURFACE_LOWEST)
        tree_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        self.tree = ttk.Treeview(
            tree_frame, columns=col_ids, show="headings", selectmode="browse"
        )

        # Configurer les colonnes
        for col_id, label, width in columns:
            self.tree.heading(
                col_id, text=label.upper(), command=lambda c=col_id: self._sort(c)
            )
            self.tree.column(col_id, width=width, minwidth=60)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Charger les données
        if data:
            self.load_data(data)

        self._sort_reverse = {}

    def load_data(self, data):
        """Charge ou recharge les données dans la table."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in data:
            self.tree.insert("", "end", values=row)

    def _sort(self, col):
        """Tri par colonne au clic."""
        reverse = self._sort_reverse.get(col, False)
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children()]
        items.sort(reverse=reverse)
        for idx, (_, k) in enumerate(items):
            self.tree.move(k, "", idx)
        self._sort_reverse[col] = not reverse


# ============================================================
# STATUS BADGE
# ============================================================


class StatusBadge(tk.Label):
    """Badge de statut coloré (Chip rectangulaire).

    Args:
        parent: Widget parent.
        text: Texte du badge.
        status: 'ok', 'warning', 'error', 'info', 'neutral'.
    """

    STATUS_COLORS = {
        "ok": (SUCCESS, "#e8f5e9"),
        "warning": (WARNING, "#fff3e0"),
        "error": (ERROR, "#ffdad6"),
        "info": (PRIMARY, "#cfe5ff"),
        "neutral": (OUTLINE, SURFACE_CONTAINER),
        "critique": (ERROR, "#ffdad6"),
        "resolu": (PRIMARY, "#cfe5ff"),
        "en_attente": (WARNING, "#fff3e0"),
        "enregistre": (OUTLINE, SURFACE_CONTAINER),
    }

    def __init__(self, parent, text="", status="neutral", **kwargs):
        fg, bg = self.STATUS_COLORS.get(status, self.STATUS_COLORS["neutral"])
        super().__init__(
            parent,
            text=text.upper(),
            font=FONT_LABEL_SM,
            fg=fg,
            bg=bg,
            padx=8,
            pady=2,
            **kwargs,
        )


# ============================================================
# ZONE MAP
# ============================================================


class ZoneMap(tk.Frame):
    """Visualisation cartographique d'une zone d'entrepôt via Canvas.

    Args:
        parent: Widget parent.
        zone_id: Identifiant de la zone (E0-E3).
        cellules: Liste de dictionnaires cellule.
        occupation_pct: Pourcentage d'occupation.
    """

    def __init__(self, parent, zone_id="E0", cellules=None, occupation_pct=0, **kwargs):
        super().__init__(
            parent,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
            **kwargs,
        )

        # Header
        header = tk.Frame(self, bg=SURFACE_CONTAINER_HIGH)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"ZONE {zone_id}",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=12,
            pady=6,
        ).pack(side="left")

        # Badge occupation
        occ_color = (
            SUCCESS
            if occupation_pct < 60
            else WARNING if occupation_pct < 85 else ERROR
        )
        self.pct_label = tk.Label(
            header,
            text=f"{int(occupation_pct)}%",
            font=("Consolas", 10, "bold"),
            bg=SURFACE_CONTAINER_HIGH,
            fg=occ_color,
            padx=8,
        )
        self.pct_label.pack(side="right")

        # Canvas pour la grille
        self.canvas = tk.Canvas(
            self, bg=SURFACE_LOWEST, bd=0, highlightthickness=0, height=120
        )
        self.canvas.pack(fill="x", padx=8, pady=8)

        if cellules:
            self._draw_cells(cellules)

    def update_pct(self, occupation_pct):
        """Met à jour le badge de pourcentage d'occupation."""
        occ_color = (
            SUCCESS
            if occupation_pct < 60
            else WARNING if occupation_pct < 85 else ERROR
        )
        self.pct_label.config(text=f"{int(occupation_pct)}%", fg=occ_color)

    def _draw_cells(self, cellules):
        """Dessine les cellules sur le canvas."""
        cell_w = 36
        cell_h = 28
        padding = 4
        cols = 5

        for i, cell in enumerate(cellules):
            row = i // cols
            col = i % cols
            x1 = col * (cell_w + padding) + padding
            y1 = row * (cell_h + padding) + padding
            x2 = x1 + cell_w
            y2 = y1 + cell_h

            # Couleur selon statut
            if cell["statut"] == "Libre":
                fill = "#e8f5e9"
                outline_c = SUCCESS
            elif cell["statut"] == "Partiel":
                fill = "#fff3e0"
                outline_c = WARNING
            else:
                fill = "#ffdad6"
                outline_c = ERROR

            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill=fill, outline=outline_c, width=1
            )

            # Label cellule (court)
            cell_num = cell["id"].split("_")[-1]
            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=cell_num,
                font=("Consolas", 8),
                fill=ON_SURFACE_VARIANT,
            )
