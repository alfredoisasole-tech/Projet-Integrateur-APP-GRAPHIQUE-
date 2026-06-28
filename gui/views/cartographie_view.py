"""
Vue Cartographie — Cartographie Opérationnelle (référence: code.html)

Affiche la grille des 4 zones (E0-E3) avec leurs cellules colorées.
"""

import tkinter as tk
import tkinter.ttk as ttk
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
    SUCCESS,
    WARNING,
    ERROR,
    OUTLINE_VARIANT,
    FONT_HEADLINE_LG,
    FONT_HEADLINE_MD,
    FONT_BODY_MD,
    FONT_BODY_SM,
    FONT_LABEL_SM,
    FONT_LABEL_MD,
)
from gui.components.widgets import ZoneMap, StatCard, StatusBadge


class CartographieView(tk.Frame):
    """Écran Cartographie Opérationnelle."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self._build_ui()

    def _build_ui(self):
        """Construit l'interface de cartographie."""
        # Header
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=24, pady=(20, 16))

        tk.Label(
            header,
            text="CARTOGRAPHIE OPÉRATIONNELLE",
            font=FONT_HEADLINE_LG,
            bg=SURFACE,
            fg=ON_SURFACE,
        ).pack(side="left")

        # Badges
        badge_frame = tk.Frame(header, bg=SURFACE)
        badge_frame.pack(side="right")
        StatusBadge(badge_frame, text="Disponibilité: Nominale", status="ok").pack(
            side="left", padx=4
        )
        StatusBadge(badge_frame, text="Débit: Normal", status="info").pack(
            side="left", padx=4
        )

        # Layout principal : grille zones + sidebar
        main = tk.Frame(self, bg=SURFACE)
        main.pack(fill="both", expand=True, padx=24)

        # === GRILLE DES ZONES (gauche) ===
        zones_frame = tk.Frame(main, bg=SURFACE)
        zones_frame.pack(side="left", fill="both", expand=True)

        # 2x2 grid
        self.zone_maps = {}
        grid_top = tk.Frame(zones_frame, bg=SURFACE)
        grid_top.pack(fill="both", expand=True, pady=(0, 8))

        grid_bottom = tk.Frame(zones_frame, bg=SURFACE)
        grid_bottom.pack(fill="both", expand=True)

        # Zones seront remplies au refresh
        for zone_id, parent_frame in [
            ("E0", grid_top),
            ("E1", grid_top),
            ("E2", grid_bottom),
            ("E3", grid_bottom),
        ]:
            zm = ZoneMap(parent_frame, zone_id=zone_id, cellules=[], occupation_pct=0)
            zm.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 8) if zone_id in ("E0", "E2") else 0,
            )
            self.zone_maps[zone_id] = zm

        # Stats sous la grille
        stats_row = tk.Frame(zones_frame, bg=SURFACE)
        stats_row.pack(fill="x", pady=(16, 0))

        self.perf_card = StatCard(
            stats_row,
            title="Cellules Occupées",
            value="--",
            subtitle="Cellules de stockage utilisées",
        )
        self.perf_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.eco_card = StatCard(
            stats_row,
            title="Emballages Récupérés",
            value="--",
            subtitle="Emballages recyclés disponibles",
        )
        self.eco_card.pack(side="left", fill="both", expand=True)

        # === SIDEBAR DROITE ===
        sidebar = tk.Frame(
            main,
            bg=SURFACE_LOWEST,
            width=280,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
        )
        sidebar.pack(side="right", fill="y", padx=(16, 0))
        sidebar.pack_propagate(False)

        # Header sidebar
        sh = tk.Frame(sidebar, bg=SURFACE_CONTAINER_HIGH)
        sh.pack(fill="x")
        tk.Label(
            sh,
            text="STATUT GLOBAL",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=12,
            pady=8,
        ).pack(side="left")

        # Indicateurs
        self.indicator_widgets = {}
        indicators = [
            ("Emballage", "-", "ok"),
            ("Densité", "--%", "info"),
            ("Latence Sys.", "< 50ms", "ok"),
            ("Quais Actifs", "--/--", "info"),
        ]
        for label, value, status in indicators:
            row = tk.Frame(sidebar, bg=SURFACE_LOWEST)
            row.pack(fill="x", padx=12, pady=4)
            tk.Label(
                row, text=label, font=FONT_LABEL_SM, bg=SURFACE_LOWEST, fg=OUTLINE
            ).pack(side="left")
            badge = StatusBadge(row, text=value, status=status)
            badge.pack(side="right")
            self.indicator_widgets[label] = badge

        # Séparateur
        tk.Frame(sidebar, bg=OUTLINE_VARIANT, height=1).pack(fill="x", padx=12, pady=8)

        # Journaux système
        tk.Label(
            sidebar,
            text="JOURNAUX SYSTÈME",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
            padx=12,
        ).pack(anchor="w")

        self.log_container = tk.Frame(sidebar, bg=SURFACE_LOWEST)
        self.log_container.pack(fill="both", expand=True, padx=12, pady=8)

        # Légende
        legend = tk.Frame(sidebar, bg=SURFACE_LOWEST)
        legend.pack(fill="x", padx=12, pady=(0, 12))
        for label, color in [
            ("Libre", SUCCESS),
            ("Partiel", WARNING),
            ("Occupé", ERROR),
        ]:
            lf = tk.Frame(legend, bg=SURFACE_LOWEST)
            lf.pack(side="left", padx=(0, 12))
            tk.Canvas(lf, width=10, height=10, bg=color, highlightthickness=0).pack(
                side="left", padx=(0, 4)
            )
            tk.Label(
                lf, text=label, font=FONT_LABEL_SM, bg=SURFACE_LOWEST, fg=OUTLINE
            ).pack(side="left")

    def refresh(self):
        """Recharge les données depuis l'API."""
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        try:
            resp = requests.get(f"{self.api_url}/api/dashboard/zones", timeout=5)
            if resp.ok:
                zones = resp.json().get("zones", {})
                self.after(0, lambda: self._update_zones(zones))

            resp2 = requests.get(f"{self.api_url}/api/rapports/exceptions", timeout=5)
            if resp2.ok:
                logs = resp2.json().get("logs", [])[:5]
                self.after(0, lambda: self._update_logs(logs))

            # Mettre à jour la sidebar avec les données réelles
            resp3 = requests.get(f"{self.api_url}/api/dashboard", timeout=5)
            if resp3.ok:
                data = resp3.json()
                self.after(0, lambda: self._update_sidebar(data))
        except requests.ConnectionError:
            pass

    def _update_zones(self, zones):
        for zone_id, zone_data in zones.items():
            if zone_id in self.zone_maps:
                zm = self.zone_maps[zone_id]
                cellules = zone_data.get("cellules_detail", [])
                occ = zone_data.get("occupation_pct", 0)
                zm.canvas.delete("all")
                zm._draw_cells(cellules)
                zm.update_pct(occ)

    def _update_logs(self, logs):
        for w in self.log_container.winfo_children():
            w.destroy()
        for log in logs:
            lf = tk.Frame(self.log_container, bg=SURFACE_LOWEST)
            lf.pack(fill="x", pady=2)
            tk.Label(
                lf,
                text=log["timestamp"][:16],
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=OUTLINE,
            ).pack(anchor="w")
            tk.Label(
                lf,
                text=log["message"][:60],
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
                wraplength=240,
                justify="left",
            ).pack(anchor="w")

    def _update_sidebar(self, data):
        """Met à jour les indicateurs de la sidebar."""
        occ = data.get("occupation_globale_pct", 0)
        quais_u = data.get("quais_utilises", 0)
        quais_t = data.get("quais_total", 0)
        emb = data.get("emballages", {})
        recup = emb.get("recuperes", 0)
        neufs = emb.get("neufs", 0)

        if "Densité" in self.indicator_widgets:
            status = "warning" if occ > 70 else "ok"
            self.indicator_widgets["Densité"].configure(
                text=f"{occ:.0f}%", bg="#fff3e0" if occ > 70 else "#e8f5e9"
            )
        if "Quais Actifs" in self.indicator_widgets:
            self.indicator_widgets["Quais Actifs"].configure(
                text=f"{quais_u}/{quais_t}"
            )
        if "Emballage" in self.indicator_widgets:
            total = neufs + recup
            self.indicator_widgets["Emballage"].configure(text=f"{total} dispo")

        # Mise à jour des stat cards
        cellules_occ = data.get("cellules_occupees", 0)
        cellules_tot = data.get("total_cellules", 0)
        for w in self.perf_card.winfo_children():
            w.destroy()
        from gui.theme import (
            SURFACE_CONTAINER_HIGH,
            SURFACE_LOWEST,
            OUTLINE,
            ON_SURFACE,
            ON_SURFACE_VARIANT,
            FONT_LABEL_SM,
            FONT_HEADLINE_LG,
            FONT_BODY_SM,
        )

        hdr = tk.Frame(self.perf_card, bg=SURFACE_CONTAINER_HIGH)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="CELLULES OCCUPÉES",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        body = tk.Frame(self.perf_card, bg=SURFACE_LOWEST)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(
            body,
            text=f"{cellules_occ}/{cellules_tot}",
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            body,
            text="Cellules de stockage utilisées",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w")

        for w in self.eco_card.winfo_children():
            w.destroy()
        hdr2 = tk.Frame(self.eco_card, bg=SURFACE_CONTAINER_HIGH)
        hdr2.pack(fill="x")
        tk.Label(
            hdr2,
            text="EMBALLAGES RÉCUPÉRÉS",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        body2 = tk.Frame(self.eco_card, bg=SURFACE_LOWEST)
        body2.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(
            body2,
            text=str(recup),
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            body2,
            text="Emballages recyclés disponibles",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w")
