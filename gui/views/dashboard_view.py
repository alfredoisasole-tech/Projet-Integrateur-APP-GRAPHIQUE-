"""
Vue Dashboard — Tableau de Bord (référence: code5.html)

Layout en grille :
- KPIs principaux (Rendement, Quais, Erreurs)
- Alertes critiques
- Table des manifestes récents
- Jauge capacité de stock
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
    FONT_HEADLINE_SM,
    FONT_BODY_MD,
    FONT_BODY_SM,
    FONT_LABEL_SM,
    FONT_LABEL_MD,
    FONT_DISPLAY,
)
from gui.components.widgets import StatCard, DataTable, StatusBadge


class DashboardView(tk.Frame):
    """Écran Tableau de Bord."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self._build_ui()

    def _build_ui(self):
        """Construit l'interface du dashboard."""
        # Scrollable content
        canvas = tk.Canvas(self, bg=SURFACE, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=SURFACE)

        self.scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        # Bind mousewheel
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        # Header
        header = tk.Frame(self.scroll_frame, bg=SURFACE)
        header.pack(fill="x", padx=24, pady=(20, 16))

        tk.Label(
            header,
            text="TABLEAU DE BORD",
            font=FONT_HEADLINE_LG,
            bg=SURFACE,
            fg=ON_SURFACE,
        ).pack(side="left")

        tk.Label(
            header,
            text="Vue temps réel des opérations",
            font=FONT_BODY_SM,
            bg=SURFACE,
            fg=ON_SURFACE_VARIANT,
        ).pack(side="left", padx=(16, 0), pady=(10, 0))

        # === RANGÉE 1 : KPIs ===
        kpi_row = tk.Frame(self.scroll_frame, bg=SURFACE)
        kpi_row.pack(fill="x", padx=24, pady=(0, 16))

        # KPI Rendement
        self.kpi_rendement = StatCard(
            kpi_row,
            title="Efficacité Globale",
            value="--%",
            subtitle="Rendement opérationnel",
        )
        self.kpi_rendement.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # KPI Quais
        self.kpi_quais = StatCard(
            kpi_row,
            title="Utilisation Quais",
            value="--/--",
            subtitle="Quais actifs sur total",
        )
        self.kpi_quais.pack(side="left", fill="both", expand=True, padx=8)

        # KPI Erreurs
        self.kpi_erreurs = StatCard(
            kpi_row,
            title="Erreurs Actives",
            value="--",
            subtitle="Incidents non résolus",
        )
        self.kpi_erreurs.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # === RANGÉE 2 : Zones ===
        zones_row = tk.Frame(self.scroll_frame, bg=SURFACE)
        zones_row.pack(fill="x", padx=24, pady=(0, 16))

        self.zone_widgets = {}
        for zone_id in ["E0", "E1", "E2", "E3"]:
            zone_card = tk.Frame(
                zones_row,
                bg=SURFACE_LOWEST,
                highlightbackground=OUTLINE_VARIANT,
                highlightthickness=1,
            )
            zone_card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 8) if zone_id != "E3" else 0,
            )

            zh = tk.Frame(zone_card, bg=SURFACE_CONTAINER_HIGH)
            zh.pack(fill="x")
            tk.Label(
                zh,
                text=f"ZONE {zone_id}",
                font=FONT_LABEL_SM,
                bg=SURFACE_CONTAINER_HIGH,
                fg=OUTLINE,
                padx=12,
                pady=6,
            ).pack(side="left")

            body = tk.Frame(zone_card, bg=SURFACE_LOWEST, padx=12, pady=8)
            body.pack(fill="x")
            pct_label = tk.Label(
                body,
                text="--%",
                font=FONT_HEADLINE_MD,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
            )
            pct_label.pack(anchor="w")
            name_label = tk.Label(
                body,
                text=zone_id,
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
            )
            name_label.pack(anchor="w")

            bar = ttk.Progressbar(
                body,
                style="Success.Horizontal.TProgressbar",
                length=100,
                mode="determinate",
                value=0,
            )
            bar.pack(fill="x", pady=(4, 0))

            self.zone_widgets[zone_id] = {
                "pct_label": pct_label,
                "bar": bar,
                "name_label": name_label,
            }

        # === RANGÉE 3 : Table + Alertes ===
        bottom_row = tk.Frame(self.scroll_frame, bg=SURFACE)
        bottom_row.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # Table manifestes récents
        columns = [
            ("ref", "Référence", 140),
            ("dest", "Destinataire", 180),
            ("statut", "Statut", 120),
            ("priorite", "Priorité", 100),
            ("date", "Date", 140),
        ]
        self.table = DataTable(
            bottom_row, columns, title="Manifestes d'Expédition Récents"
        )
        self.table.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # Panel alertes
        alerts_frame = tk.Frame(
            bottom_row,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
            width=300,
        )
        alerts_frame.pack(side="right", fill="y")
        alerts_frame.pack_propagate(False)

        ah = tk.Frame(alerts_frame, bg=SURFACE_CONTAINER_HIGH)
        ah.pack(fill="x")
        tk.Label(
            ah,
            text="ALERTES CRITIQUES",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=12,
            pady=8,
        ).pack(side="left")

        self.alerts_container = tk.Frame(alerts_frame, bg=SURFACE_LOWEST)
        self.alerts_container.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh(self):
        """Recharge les données depuis l'API."""
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        """Charge les données en arrière-plan."""
        try:
            # Dashboard data
            resp = requests.get(f"{self.api_url}/api/dashboard", timeout=5)
            if resp.ok:
                data = resp.json()
                self.after(0, lambda: self._update_kpis(data))

            # Bordereaux
            resp2 = requests.get(f"{self.api_url}/api/expedition/bordereaux", timeout=5)
            if resp2.ok:
                bordereaux = resp2.json().get("bordereaux", [])
                self.after(0, lambda: self._update_table(bordereaux))

            # Exceptions
            resp3 = requests.get(f"{self.api_url}/api/rapports/exceptions", timeout=5)
            if resp3.ok:
                exceptions = resp3.json().get("logs", [])
                self.after(0, lambda: self._update_alerts(exceptions))

        except requests.ConnectionError:
            pass

    def _update_kpis(self, data):
        """Met à jour les KPIs depuis les données API."""
        rendement = data.get("rendement", 0)
        quais_utilises = data.get("quais_utilises", 0)
        quais_total = data.get("quais_total", 0)
        erreurs = data.get("erreurs_actives", 0)
        occ = data.get("occupation_globale_pct", 0)

        # Mettre à jour les textes dans kpi_rendement
        for w in self.kpi_rendement.winfo_children():
            w.destroy()
        import tkinter as tk
        from gui.theme import (
            SURFACE_CONTAINER_HIGH,
            SURFACE_LOWEST,
            OUTLINE,
            ON_SURFACE,
            ON_SURFACE_VARIANT,
            SUCCESS,
            ERROR,
            FONT_LABEL_SM,
            FONT_HEADLINE_LG,
            FONT_BODY_SM,
            FONT_LABEL_MD,
        )

        hdr = tk.Frame(self.kpi_rendement, bg=SURFACE_CONTAINER_HIGH)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="EFFICACITÉ GLOBALE",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        body = tk.Frame(self.kpi_rendement, bg=SURFACE_LOWEST)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(
            body,
            text=f"{rendement}%",
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            body,
            text="Rendement opérationnel",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w", pady=(4, 0))

        for w in self.kpi_quais.winfo_children():
            w.destroy()
        hdr2 = tk.Frame(self.kpi_quais, bg=SURFACE_CONTAINER_HIGH)
        hdr2.pack(fill="x")
        tk.Label(
            hdr2,
            text="UTILISATION QUAIS",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        body2 = tk.Frame(self.kpi_quais, bg=SURFACE_LOWEST)
        body2.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(
            body2,
            text=f"{quais_utilises}/{quais_total}",
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            body2,
            text="Quais actifs sur total",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w", pady=(4, 0))

        for w in self.kpi_erreurs.winfo_children():
            w.destroy()
        hdr3 = tk.Frame(self.kpi_erreurs, bg=SURFACE_CONTAINER_HIGH)
        hdr3.pack(fill="x")
        tk.Label(
            hdr3,
            text="ERREURS ACTIVES",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        body3 = tk.Frame(self.kpi_erreurs, bg=SURFACE_LOWEST)
        body3.pack(fill="both", expand=True, padx=16, pady=12)
        err_color = ERROR if erreurs > 0 else SUCCESS
        tk.Label(
            body3,
            text=f"{erreurs:02d}",
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=err_color,
        ).pack(anchor="w")
        tk.Label(
            body3,
            text="Incidents non résolus",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w", pady=(4, 0))

        # Mettre à jour les cartes de zones avec les données réelles
        zones = data.get("zones", {})
        for zone_id, widgets in self.zone_widgets.items():
            zone_data = zones.get(zone_id, {})
            occ = round(zone_data.get("occupation_pct", 0))
            color = ERROR if occ > 70 else WARNING if occ > 50 else SUCCESS
            widgets["pct_label"].configure(text=f"{occ}%", fg=color)
            style = (
                "Error.Horizontal.TProgressbar"
                if occ > 85
                else (
                    "Warning.Horizontal.TProgressbar"
                    if occ > 60
                    else "Success.Horizontal.TProgressbar"
                )
            )
            widgets["bar"].configure(value=occ, style=style)
            # Mettre à jour le nom de zone depuis l'API
            nom = zone_data.get("nom", zone_id)
            widgets["name_label"].configure(text=nom)

    def _update_table(self, bordereaux):
        """Met à jour la table des manifestes."""
        rows = []
        for b in bordereaux[:8]:
            rows.append(
                (
                    b.get("id", ""),
                    b.get("destinataire_nom", ""),
                    b.get("statut", "").replace("_", " ").title(),
                    b.get("priorite", "").title(),
                    b.get("date", "")[:16],
                )
            )
        self.table.load_data(rows)

    def _update_alerts(self, exceptions):
        """Met à jour le panel alertes."""
        for w in self.alerts_container.winfo_children():
            w.destroy()

        critiques = [
            e for e in exceptions if e["statut"] in ("critique", "en_attente")
        ][:5]
        for exc in critiques:
            alert = tk.Frame(self.alerts_container, bg=SURFACE_LOWEST)
            alert.pack(fill="x", pady=(0, 8))

            StatusBadge(alert, text=exc["statut"], status=exc["statut"]).pack(
                anchor="w"
            )
            tk.Label(
                alert,
                text=(
                    exc["message"][:80] + "..."
                    if len(exc["message"]) > 80
                    else exc["message"]
                ),
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
                wraplength=260,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))
            tk.Label(
                alert,
                text=exc["timestamp"][:16],
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=OUTLINE,
            ).pack(anchor="w")

            sep = tk.Frame(alert, bg=OUTLINE_VARIANT, height=1)
            sep.pack(fill="x", pady=(6, 0))
