"""
Vue Inventaire — Inventaire des Stocks (référence: code2.html)

Table d'inventaire avec filtres par catégorie/statut et statistiques.
"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import requests
import threading
from gui.theme import (
    SURFACE,
    SURFACE_LOWEST,
    SURFACE_CONTAINER_HIGH,
    ON_SURFACE,
    ON_SURFACE_VARIANT,
    PRIMARY,
    OUTLINE,
    OUTLINE_VARIANT,
    SUCCESS,
    WARNING,
    ERROR,
    FONT_HEADLINE_LG,
    FONT_BODY_MD,
    FONT_BODY_SM,
    FONT_LABEL_SM,
    FONT_LABEL_MD,
)
from gui.components.widgets import StatusBadge, DataTable, StatCard


class InventaireView(tk.Frame):
    """Écran Inventaire des Stocks."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=24, pady=(20, 16))

        tk.Label(
            header,
            text="INVENTAIRE DES STOCKS",
            font=FONT_HEADLINE_LG,
            bg=SURFACE,
            fg=ON_SURFACE,
        ).pack(side="left")

        # Badges stats
        self.total_badge = StatusBadge(header, text="Total SKU: --", status="info")
        self.total_badge.pack(side="right", padx=4)

        self.critique_badge = StatusBadge(
            header, text="Stock Critique: --", status="error"
        )
        self.critique_badge.pack(side="right", padx=4)

        # === FILTRES ===
        filters = tk.Frame(
            self,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
        )
        filters.pack(fill="x", padx=24, pady=(0, 16))

        inner = tk.Frame(filters, bg=SURFACE_LOWEST, padx=16, pady=10)
        inner.pack(fill="x")

        # Recherche
        tk.Label(
            inner, text="RECHERCHE", font=FONT_LABEL_SM, bg=SURFACE_LOWEST, fg=OUTLINE
        ).pack(side="left")

        self.search_entry = ttk.Entry(inner, width=20, font=FONT_BODY_MD)
        self.search_entry.pack(side="left", padx=(8, 16))

        # Catégorie
        tk.Label(
            inner, text="CATÉGORIE", font=FONT_LABEL_SM, bg=SURFACE_LOWEST, fg=OUTLINE
        ).pack(side="left")

        self.cat_var = tk.StringVar(value="Toutes")
        cat_combo = ttk.Combobox(
            inner,
            textvariable=self.cat_var,
            width=16,
            values=["Toutes", "Matériel", "Emballage"],
            state="readonly",
        )
        cat_combo.pack(side="left", padx=(8, 16))

        # Statut
        tk.Label(
            inner, text="STATUT", font=FONT_LABEL_SM, bg=SURFACE_LOWEST, fg=OUTLINE
        ).pack(side="left")

        self.statut_var = tk.StringVar(value="Tous")
        stat_combo = ttk.Combobox(
            inner,
            textvariable=self.statut_var,
            width=14,
            values=["Tous", "ok", "stock_faible", "rupture"],
            state="readonly",
        )
        stat_combo.pack(side="left", padx=(8, 16))

        ttk.Button(
            inner,
            text="APPLIQUER",
            style="Primary.TButton",
            command=self._apply_filters,
        ).pack(side="left")

        # === TABLE ===
        columns = [
            ("lot_id", "ID Lot", 120),
            ("produit", "Produit", 250),
            ("categorie", "Catégorie", 140),
            ("quantite", "Quantité", 80),
            ("zone", "Zone/Cellule", 100),
            ("masse", "Masse (kg)", 90),
            ("statut", "Statut", 100),
        ]
        self.table = DataTable(self, columns, title="Inventaire")
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        # === ACTIONS ===
        actions = tk.Frame(self, bg=SURFACE)
        actions.pack(fill="x", padx=24, pady=(8, 24))

        ttk.Button(
            actions,
            text="🔄 Actualiser",
            style="Secondary.TButton",
            command=self.refresh,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions,
            text="📊 Exporter",
            style="Secondary.TButton",
            command=self._exporter,
        ).pack(side="left", padx=8)

        self.sync_label = tk.Label(
            actions,
            text="Dernière synchro: --",
            font=FONT_LABEL_SM,
            bg=SURFACE,
            fg=OUTLINE,
        )
        self.sync_label.pack(side="right")

    def refresh(self):
        threading.Thread(target=self._load_data, daemon=True).start()

    def _apply_filters(self):
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        try:
            # Construire les paramètres
            params = {}
            cat = self.cat_var.get()
            if cat != "Toutes":
                params["categorie"] = cat
            statut = self.statut_var.get()
            if statut != "Tous":
                params["statut"] = statut
            search = self.search_entry.get().strip()
            if search:
                params["q"] = search

            resp = requests.get(
                f"{self.api_url}/api/inventaire", params=params, timeout=5
            )
            if resp.ok:
                data = resp.json()
                items = data.get("inventaire", [])
                self.after(0, lambda: self._update_table(items))

            resp2 = requests.get(f"{self.api_url}/api/inventaire/stats", timeout=5)
            if resp2.ok:
                stats = resp2.json()
                self.after(0, lambda: self._update_stats(stats))

        except requests.ConnectionError:
            pass

    def _update_table(self, items):
        rows = []
        for item in items:
            statut_text = item.get("statut", "ok")
            rows.append(
                (
                    item.get("lot_id", ""),
                    item.get("produit_nom", ""),
                    item.get("categorie", ""),
                    str(item.get("quantite", 0)),
                    item.get("zone_cellule", ""),
                    f"{item.get('masse_totale', 0):.1f}",
                    statut_text.replace("_", " ").upper(),
                )
            )
        self.table.load_data(rows)

        from datetime import datetime

        self.sync_label.configure(
            text=f"Dernière synchro: {datetime.now().strftime('%H:%M:%S')}"
        )

    def _update_stats(self, stats):
        self.total_badge.configure(text=f"Total SKU: {stats.get('total_sku', '--')}")
        self.critique_badge.configure(
            text=f"Stock Critique: {stats.get('stock_critique', '--')}"
        )

    def _exporter(self):
        """Exporte l'inventaire courant dans une messagebox (mode démo)."""
        items = []
        for child in self.table.tree.get_children():
            vals = self.table.tree.item(child, "values")
            items.append(vals)
        if not items:
            messagebox.showinfo(
                "Export Inventaire",
                "Aucune donnée à exporter.\nAppliquez des filtres et rechargez d'abord.",
            )
            return
        header = f"{'ID Lot':<15} {'Produit':<35} {'Qte':>6} {'Zone':<12} {'Masse':>8} {'Statut':<12}"
        lignes = [header, "-" * len(header)]
        for v in items[:30]:
            lignes.append(
                f"{str(v[0]):<15} {str(v[1]):<35} {str(v[3]):>6} {str(v[4]):<12} {str(v[5]):>8} {str(v[6]):<12}"
            )
        if len(items) > 30:
            lignes.append(f"... et {len(items)-30} entrées supplémentaires.")
        messagebox.showinfo(f"Inventaire SGE ({len(items)} lots)", "\n".join(lignes))
