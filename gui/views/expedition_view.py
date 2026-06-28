"""
Vue Expédition — Expédition / Picking (référence: code1.html)

Gestion du processus d'expédition avec pick list et emballage éco-logistique.
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
    FONT_HEADLINE_MD,
    FONT_HEADLINE_SM,
    FONT_BODY_MD,
    FONT_BODY_SM,
    FONT_LABEL_SM,
    FONT_LABEL_MD,
)
from gui.components.widgets import StatusBadge, DataTable


class ExpeditionView(tk.Frame):
    """Écran Expédition / Picking."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self.current_bon = None
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=24, pady=(20, 16))

        tk.Label(
            header,
            text="EXPÉDITION / PICKING",
            font=FONT_HEADLINE_LG,
            bg=SURFACE,
            fg=ON_SURFACE,
        ).pack(side="left")

        self.statut_label = StatusBadge(header, text="En attente", status="neutral")
        self.statut_label.pack(side="right")

        # === BARRE DE CRITÈRE ===
        criteria = tk.Frame(
            self,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
        )
        criteria.pack(fill="x", padx=24, pady=(0, 16))

        inner = tk.Frame(criteria, bg=SURFACE_LOWEST, padx=16, pady=12)
        inner.pack(fill="x")

        tk.Label(
            inner,
            text="ID BORDEREAU",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
        ).pack(side="left")

        self.bon_entry = ttk.Entry(inner, width=25, font=FONT_BODY_MD)
        self.bon_entry.pack(side="left", padx=(12, 8))
        self.bon_entry.insert(0, "EXP-2024-001")

        ttk.Button(
            inner, text="CHARGER", style="Primary.TButton", command=self._load_bon
        ).pack(side="left", padx=4)

        # Infos rapides
        self.info_frame = tk.Frame(inner, bg=SURFACE_LOWEST)
        self.info_frame.pack(side="right")

        self.volume_label = tk.Label(
            self.info_frame,
            text="Volume: --",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
        )
        self.volume_label.pack(side="left", padx=8)

        self.priorite_badge = StatusBadge(self.info_frame, text="--", status="neutral")
        self.priorite_badge.pack(side="left")

        # === ACTIONS (Packé en bas en premier pour toujours être visible) ===
        actions = tk.Frame(self, bg=SURFACE)
        actions.pack(side="bottom", fill="x", padx=24, pady=(16, 24))

        ttk.Button(
            actions,
            text="📋 Feuille de Route",
            style="Secondary.TButton",
            command=self._feuille_de_route,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions,
            text="🚚 Confirmer Départ",
            style="Secondary.TButton",
            command=self._confirmer_depart,
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="✓ Confirmer Sortie",
            style="Primary.TButton",
            command=self._valider_expedition,
        ).pack(side="right")

        # === CONTENU PRINCIPAL ===
        main = tk.Frame(self, bg=SURFACE)
        main.pack(side="top", fill="both", expand=True, padx=24)

        # Table pick list (gauche)
        columns = [
            ("id", "ID Produit", 120),
            ("nom", "Produit", 220),
            ("qte", "Qté", 60),
            ("zone", "Zone/Cellule", 100),
            ("chemin", "Chemin Optimal", 140),
            ("statut", "Statut", 100),
        ]
        self.table = DataTable(main, columns, title="Vue Arborescente de Picking")
        self.table.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # Sidebar droite
        right = tk.Frame(
            main,
            bg=SURFACE_LOWEST,
            width=280,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
        )
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # Itinéraire section
        rh = tk.Frame(right, bg=SURFACE_CONTAINER_HIGH)
        rh.pack(fill="x")
        tk.Label(
            rh,
            text="APERÇU ITINÉRAIRE",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=12,
            pady=8,
        ).pack(side="left")

        self.itin_frame = tk.Frame(right, bg=SURFACE_LOWEST, padx=12, pady=8)
        self.itin_frame.pack(fill="x")

        tk.Label(
            self.itin_frame,
            text="Chargez un bordereau",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack()

        # Emballage section
        tk.Frame(right, bg=OUTLINE_VARIANT, height=1).pack(fill="x", padx=12, pady=4)

        emb_h = tk.Frame(right, bg=SURFACE_CONTAINER_HIGH)
        emb_h.pack(fill="x")
        tk.Label(
            emb_h,
            text="RECOMMANDATION EMBALLAGE",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=12,
            pady=8,
        ).pack(side="left")

        self.emballage_frame = tk.Frame(right, bg=SURFACE_LOWEST, padx=12, pady=8)
        self.emballage_frame.pack(fill="x")

        self.emb_label = tk.Label(
            self.emballage_frame,
            text="--",
            font=FONT_BODY_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        )
        self.emb_label.pack(anchor="w")

        # Stock emballage
        self.stock_frame = tk.Frame(right, bg=SURFACE_LOWEST, padx=12)
        self.stock_frame.pack(fill="x", pady=8)

        self.stock_neuf_label = tk.Label(
            self.stock_frame,
            text="Neufs: --",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
        )
        self.stock_neuf_label.pack(anchor="w")

        self.stock_recup_label = tk.Label(
            self.stock_frame,
            text="Récupérés: --",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=SUCCESS,
        )
        self.stock_recup_label.pack(anchor="w")

    def refresh(self):
        threading.Thread(target=self._load_emballage, daemon=True).start()

    def _load_bon(self):
        bon_id = self.bon_entry.get().strip()
        if not bon_id:
            return
        threading.Thread(target=self._fetch_bon, args=(bon_id,), daemon=True).start()

    def _fetch_bon(self, bon_id):
        try:
            resp = requests.get(
                f"{self.api_url}/api/expedition/bordereau/{bon_id}", timeout=5
            )
            if resp.ok:
                bon = resp.json().get("bordereau", {})
                self.after(0, lambda: self._display_bon(bon))

            resp2 = requests.get(
                f"{self.api_url}/api/expedition/pick-list/{bon_id}", timeout=5
            )
            if resp2.ok:
                items = resp2.json().get("pick_list", [])
                self.after(0, lambda: self._display_pick_list(items))

            resp3 = requests.get(
                f"{self.api_url}/api/expedition/itineraire/{bon_id}", timeout=5
            )
            if resp3.ok:
                itin = resp3.json()
                self.after(0, lambda: self._display_itineraire(itin))
        except requests.ConnectionError:
            self.after(0, lambda: self.statut_label.configure(text="ERREUR CONNEXION"))

    def _display_bon(self, bon):
        self.current_bon = bon
        self.statut_label.configure(
            text=bon.get("statut", "").replace("_", " ").upper()
        )
        self.volume_label.configure(text=f"Volume: {bon.get('volume_estime', '--')} m³")

        priorite = bon.get("priorite", "normale")
        p_status = (
            "error"
            if priorite == "haute"
            else "warning" if priorite == "normale" else "neutral"
        )
        self.priorite_badge.configure(text=priorite.upper())
        self.emb_label.configure(text=bon.get("emballage_recommande", "Standard"))

    def _display_pick_list(self, items):
        rows = []
        for item in items:
            rows.append(
                (
                    item.get("produit_id", ""),
                    item.get("produit_nom", ""),
                    str(item.get("quantite", 0)),
                    item.get("zone_cellule", ""),
                    item.get("chemin_optimal", ""),
                    item.get("statut", "").replace("_", " ").title(),
                )
            )
        self.table.load_data(rows)

    def _display_itineraire(self, data):
        for w in self.itin_frame.winfo_children():
            w.destroy()

        zones = data.get("zones", [])
        for z in zones:
            row = tk.Frame(self.itin_frame, bg=SURFACE_LOWEST)
            row.pack(fill="x", pady=2)
            tk.Label(
                row,
                text=f"→ {z['cellule']}",
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=PRIMARY,
            ).pack(side="left")
            tk.Label(
                row,
                text=z["chemin"],
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
            ).pack(side="right")

        tk.Frame(self.itin_frame, bg=OUTLINE_VARIANT, height=1).pack(fill="x", pady=4)
        tk.Label(
            self.itin_frame,
            text=f"Distance: {data.get('longueur_totale_m', 0)}m  |  Temps: ~{data.get('temps_estime_min', 0)} min",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
        ).pack(anchor="w")

    def _load_emballage(self):
        try:
            resp = requests.get(f"{self.api_url}/api/rapports/emballage", timeout=5)
            if resp.ok:
                data = resp.json()
                self.after(0, lambda: self._update_emballage(data))
        except requests.ConnectionError:
            pass

    def _update_emballage(self, data):
        self.stock_neuf_label.configure(text=f"Neufs: {data.get('neufs', '--')}")
        self.stock_recup_label.configure(
            text=f"Récupérés: {data.get('recuperes', '--')} (priorité éco)"
        )

    def _valider_expedition(self):
        if not self.current_bon:
            messagebox.showwarning(
                "Attention", "Veuillez charger un bordereau au préalable."
            )
            return
        bon_id = self.current_bon.get("id")
        threading.Thread(target=self._do_valider, args=(bon_id,), daemon=True).start()

    def _do_valider(self, bon_id):
        try:
            resp = requests.post(
                f"{self.api_url}/api/expedition/valider",
                json={"bon_expedition_id": bon_id},
                timeout=5,
            )
            result = resp.json()
            statut = result.get("statut", "ERROR")
            msg = result.get("message", "")
            emb = result.get("emballage_utilise", "")
            if statut == "SUCCESS":
                self.after(
                    0, lambda: self.statut_label.configure(text=f"PRÊT À EXPÉDIER")
                )
                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Succès",
                        f"{msg}\n\nEmballage recommandé et sélectionné : {emb}",
                    ),
                )
                self.after(0, self._load_emballage)
            else:
                self.after(0, lambda: self.statut_label.configure(text="ERREUR"))
                self.after(0, lambda: messagebox.showerror("Erreur", msg))
        except requests.ConnectionError:
            self.after(
                0, lambda: messagebox.showerror("Erreur", "Connexion API impossible")
            )

    def _confirmer_depart(self):
        if not self.current_bon:
            messagebox.showwarning(
                "Attention", "Veuillez charger un bordereau au préalable."
            )
            return
        bon_id = self.current_bon.get("id")
        threading.Thread(target=self._do_depart, args=(bon_id,), daemon=True).start()

    def _do_depart(self, bon_id):
        try:
            resp = requests.post(
                f"{self.api_url}/api/expedition/confirmer-depart",
                json={"bon_expedition_id": bon_id},
                timeout=5,
            )
            result = resp.json()
            statut = result.get("statut", "ERROR")
            msg = result.get("message", "")
            if statut == "SUCCESS":
                self.after(0, lambda: self.statut_label.configure(text="EXPÉDIÉ"))
                self.after(0, lambda: messagebox.showinfo("Succès", msg))
            else:
                self.after(0, lambda: messagebox.showerror("Erreur", msg))
        except requests.ConnectionError:
            self.after(
                0, lambda: messagebox.showerror("Erreur", "Connexion API impossible")
            )

    def _feuille_de_route(self):
        """Génère une feuille de route textuelle pour l'expédition."""
        if not self.current_bon:
            messagebox.showwarning(
                "Attention", "Chargez d'abord un bordereau d'expédition."
            )
            return
        bon = self.current_bon
        rows = []
        for item in self.table.tree.get_children():
            vals = self.table.tree.item(item, "values")
            rows.append(
                f"  {vals[1]:<30} Qte:{vals[2]:>5}  Zone:{vals[3]:<12} Chemin:{vals[4]}"
            )
        texte = (
            f"FEUILLE DE ROUTE D'EXPÉDITION\n"
            f"{'='*50}\n"
            f"Bordereau  : {bon.get('id', '--')}\n"
            f"Destinataire: {bon.get('destinataire_nom', '--')}\n"
            f"Transporteur: {bon.get('transporteur_nom', '--')}\n"
            f"Statut      : {bon.get('statut', '--').upper()}\n"
            f"{'='*50}\n"
            f"PRODUITS A COLLECTER :\n"
            + (
                "\n".join(rows)
                if rows
                else "  (Charger le bordereau pour voir la liste)"
            )
            + f"\n{'='*50}\n"
            f"[Démo] En production : impression PDF."
        )
        messagebox.showinfo("Feuille de Route", texte)
