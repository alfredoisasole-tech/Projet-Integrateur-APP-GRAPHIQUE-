"""
Vue Rapports — Rapports et Performance (référence: code4.html)

KPIs de performance, journal d'exceptions et actions d'export.
"""

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import requests
import threading
from datetime import datetime
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
    FONT_HEADLINE_MD,
    FONT_BODY_MD,
    FONT_BODY_SM,
    FONT_LABEL_SM,
    FONT_LABEL_MD,
)
from gui.components.widgets import StatCard, DataTable, StatusBadge


class RapportsView(tk.Frame):
    """Écran Rapports et Performance."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self._build_ui()

    def _build_ui(self):
        # Scrollable
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
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        # Header
        header = tk.Frame(self.scroll_frame, bg=SURFACE)
        header.pack(fill="x", padx=24, pady=(20, 16))

        tk.Label(
            header,
            text="RAPPORTS & PERFORMANCE",
            font=FONT_HEADLINE_LG,
            bg=SURFACE,
            fg=ON_SURFACE,
        ).pack(side="left")

        # === KPIs ===
        kpi_row = tk.Frame(self.scroll_frame, bg=SURFACE)
        kpi_row.pack(fill="x", padx=24, pady=(0, 16))

        self.kpi_occ = StatCard(
            kpi_row,
            title="Occupation Globale",
            value="--",
            subtitle="Espace utilisé",
            progress=0,
        )
        self.kpi_occ.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.kpi_rec = StatCard(
            kpi_row,
            title="Réceptions Journalières",
            value="--",
            subtitle="Unités entrantes",
            trend="",
            trend_positive=True,
        )
        self.kpi_rec.pack(side="left", fill="both", expand=True, padx=8)

        self.kpi_sort = StatCard(
            kpi_row,
            title="Sorties Journalières",
            value="--",
            subtitle="Unités sortantes",
            trend="",
            trend_positive=False,
        )
        self.kpi_sort.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # === TABLE EXCEPTIONS ===
        columns = [
            ("timestamp", "Horodatage", 140),
            ("type", "Type", 160),
            ("utilisateur", "Utilisateur", 120),
            ("message", "Description", 280),
            ("artefact", "Artéfact", 120),
            ("statut", "Statut", 100),
        ]
        self.table = DataTable(
            self.scroll_frame, columns, title="Journal des Rapports d'Exception"
        )
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 8))

        # Filtre rapide
        filter_row = tk.Frame(self.scroll_frame, bg=SURFACE)
        filter_row.pack(fill="x", padx=24, pady=(0, 8))

        tk.Label(
            filter_row,
            text="FILTRER PAR STATUT:",
            font=FONT_LABEL_SM,
            bg=SURFACE,
            fg=OUTLINE,
        ).pack(side="left")

        self.filter_var = tk.StringVar(value="Tous")
        for val, label in [
            ("Tous", "Tous"),
            ("critique", "Critique"),
            ("en_attente", "En attente"),
            ("resolu", "Résolu"),
            ("enregistre", "Enregistré"),
        ]:
            rb = ttk.Radiobutton(
                filter_row,
                text=label,
                variable=self.filter_var,
                value=val,
                command=self._apply_filter,
            )
            rb.pack(side="left", padx=(8, 0))

        # === ACTIONS ===
        actions = tk.Frame(self.scroll_frame, bg=SURFACE)
        actions.pack(fill="x", padx=24, pady=(8, 24))

        ttk.Button(
            actions,
            text="📊 Générer Fiche Stock",
            style="Secondary.TButton",
            command=self._generer_fiche_stock,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions,
            text="📥 Télécharger Journaux",
            style="Secondary.TButton",
            command=self._telecharger_journaux,
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="📋 Exporter Audit",
            style="Primary.TButton",
            command=self._exporter_audit,
        ).pack(side="right")

    def refresh(self):
        threading.Thread(target=self._load_data, daemon=True).start()

    def _apply_filter(self):
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self):
        try:
            # KPIs
            resp = requests.get(f"{self.api_url}/api/rapports/performance", timeout=5)
            if resp.ok:
                data = resp.json()
                self.after(0, lambda: self._update_kpis(data))

            # Exceptions
            params = {}
            filtre = self.filter_var.get()
            if filtre != "Tous":
                params["statut"] = filtre

            resp2 = requests.get(
                f"{self.api_url}/api/rapports/exceptions", params=params, timeout=5
            )
            if resp2.ok:
                logs = resp2.json().get("logs", [])
                self.after(0, lambda: self._update_table(logs))

        except requests.ConnectionError:
            pass

    def _update_kpis(self, data):
        """Met à jour les cartes KPI."""
        occ_pct = data.get("occupation_globale_pct", 0)
        rec_jour = data.get("receptions_jour", 0)
        rec_tend = data.get("receptions_tendance", "")
        sort_jour = data.get("sorties_jour", 0)
        sort_tend = data.get("sorties_tendance", "")

        # Reconstruire kpi_occ
        for w in self.kpi_occ.winfo_children():
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

        h1 = tk.Frame(self.kpi_occ, bg=SURFACE_CONTAINER_HIGH)
        h1.pack(fill="x")
        tk.Label(
            h1,
            text="OCCUPATION GLOBALE",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        b1 = tk.Frame(self.kpi_occ, bg=SURFACE_LOWEST)
        b1.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(
            b1,
            text=f"{occ_pct}%",
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            b1,
            text="Espace utilisé",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w", pady=(4, 0))

        for w in self.kpi_rec.winfo_children():
            w.destroy()
        h2 = tk.Frame(self.kpi_rec, bg=SURFACE_CONTAINER_HIGH)
        h2.pack(fill="x")
        tk.Label(
            h2,
            text="RÉCEPTIONS JOURNALIÈRES",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        b2 = tk.Frame(self.kpi_rec, bg=SURFACE_LOWEST)
        b2.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(
            b2,
            text=f"{rec_jour:,}",
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            b2,
            text=f"Unités entrantes  {rec_tend}",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w", pady=(4, 0))

        for w in self.kpi_sort.winfo_children():
            w.destroy()
        h3 = tk.Frame(self.kpi_sort, bg=SURFACE_CONTAINER_HIGH)
        h3.pack(fill="x")
        tk.Label(
            h3,
            text="SORTIES JOURNALIÈRES",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")
        b3 = tk.Frame(self.kpi_sort, bg=SURFACE_LOWEST)
        b3.pack(fill="both", expand=True, padx=16, pady=12)
        tk.Label(
            b3,
            text=f"{sort_jour:,}",
            font=FONT_HEADLINE_LG,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            b3,
            text=f"Unités sortantes  {sort_tend}",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w", pady=(4, 0))

    def _update_table(self, logs):
        rows = []
        for log in logs:
            rows.append(
                (
                    log.get("timestamp", "")[:16],
                    log.get("type", ""),
                    log.get("utilisateur", ""),
                    log.get("message", "")[:60],
                    log.get("artefact_lie", ""),
                    log.get("statut", "").upper(),
                )
            )
        self.table.load_data(rows)

    def _generer_fiche_stock(self):
        """Exporte un résumé du stock courant."""
        try:
            resp = requests.get(f"{self.api_url}/api/inventaire/stats", timeout=5)
            if resp.ok:
                stats = resp.json()
                texte = (
                    f"FICHE STOCK  -  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    f"{'='*40}\n"
                    f"Total SKU         : {stats.get('total_sku', '--')}\n"
                    f"Produits distincts : {stats.get('total_produits', '--')}\n"
                    f"Stock critique    : {stats.get('stock_critique', '--')} lots < 50 unités\n"
                    f"Catégories        : {', '.join(stats.get('categories', []))}\n"
                )
                messagebox.showinfo("Fiche Stock SGE", texte)
            else:
                messagebox.showerror(
                    "Erreur", "Impossible de récupérer les données de stock."
                )
        except requests.ConnectionError:
            messagebox.showerror("Connexion", "API inaccessible.")

    def _telecharger_journaux(self):
        """Affiche les journaux système (mode démo)."""
        try:
            resp = requests.get(f"{self.api_url}/api/rapports/exceptions", timeout=5)
            if resp.ok:
                logs = resp.json().get("logs", [])
                lignes = [
                    f"[{l['timestamp'][:16]}] {l['type']:<25} {l['message'][:50]}"
                    for l in logs[:20]
                ]
                messagebox.showinfo(
                    "Journal système (20 derniers)",
                    "\n".join(lignes) if lignes else "Aucun journal disponible.",
                )
            else:
                messagebox.showerror("Erreur", "Impossible d'accéder aux journaux.")
        except requests.ConnectionError:
            messagebox.showerror("Connexion", "API inaccessible.")

    def _exporter_audit(self):
        """Exporte un rapport d'audit consolidé (mode démo)."""
        try:
            resp_kpi = requests.get(
                f"{self.api_url}/api/rapports/performance", timeout=5
            )
            resp_exc = requests.get(
                f"{self.api_url}/api/rapports/exceptions", timeout=5
            )
            if resp_kpi.ok and resp_exc.ok:
                kpi = resp_kpi.json()
                nb_exc = len(resp_exc.json().get("logs", []))
                texte = (
                    f"RAPPORT D'AUDIT SGE - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    f"{'='*45}\n"
                    f"Occupation globale  : {kpi.get('occupation_globale_pct', '--')}%\n"
                    f"Réceptions / jour   : {kpi.get('receptions_jour', '--')}\n"
                    f"Sorties / jour      : {kpi.get('sorties_jour', '--')}\n"
                    f"Exceptions actives  : {nb_exc}\n"
                    f"{'='*45}\n"
                    f"[Démo] En production : export vers CSV/PDF."
                )
                messagebox.showinfo("Export Audit SGE", texte)
            else:
                messagebox.showerror("Erreur", "Données inaccessibles.")
        except requests.ConnectionError:
            messagebox.showerror("Connexion", "API inaccessible.")
