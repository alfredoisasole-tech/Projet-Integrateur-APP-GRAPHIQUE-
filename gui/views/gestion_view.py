"""
Vue Gestion — CRUD Produits, Lots et Cellules.

Sous-onglets avec DataTable + formulaire CRUD pour chaque entité.
Intègre ProduitLogiciel et ProduitMateriel.
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
    FONT_BODY_MD,
    FONT_BODY_SM,
    FONT_LABEL_SM,
    FONT_LABEL_MD,
)


class GestionView(tk.Frame):
    """Écran Gestion — CRUD Produit / Lot / Cellule."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self.current_tab = "produits"
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
            text="GESTION DES DONNÉES",
            font=FONT_HEADLINE_LG,
            bg=SURFACE,
            fg=ON_SURFACE,
        ).pack(side="left")

        # Sous-onglets
        tabs = tk.Frame(self.scroll_frame, bg=SURFACE)
        tabs.pack(fill="x", padx=24, pady=(0, 12))
        self.tab_buttons = {}
        for key, label in [
            ("produits", "📦 Produits"),
            ("lots", "📋 Lots"),
            ("cellules", "🗄 Cellules"),
        ]:
            btn = tk.Label(
                tabs,
                text=label,
                font=FONT_LABEL_MD,
                bg=SURFACE,
                fg=ON_SURFACE_VARIANT,
                padx=16,
                pady=8,
                cursor="hand2",
            )
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self.tab_buttons[key] = btn

        # Formulaire
        self.form_frame = tk.Frame(
            self.scroll_frame,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
        )
        self.form_frame.pack(fill="x", padx=24, pady=(0, 20))

        # Table
        self.table_frame = tk.Frame(self.scroll_frame, bg=SURFACE)
        self.table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def _switch_tab(self, tab_key):
        self.current_tab = tab_key
        self.refresh()

    def refresh(self):
        self._update_tab_style()
        if self.current_tab == "produits":
            self._load_produits()
        elif self.current_tab == "lots":
            self._load_lots()
        elif self.current_tab == "cellules":
            self._load_cellules()

    def _update_tab_style(self):
        for k, btn in self.tab_buttons.items():
            if k == self.current_tab:
                btn.configure(bg=PRIMARY, fg="#FFFFFF")
            else:
                btn.configure(bg=SURFACE, fg=ON_SURFACE_VARIANT)

    def _clear(self):
        for w in self.form_frame.winfo_children():
            w.destroy()
        for w in self.table_frame.winfo_children():
            w.destroy()

    def _api(self, method, endpoint, json_data=None, callback=None):
        def _do():
            try:
                fn = getattr(requests, method.lower())
                kwargs = {"timeout": 5}
                if json_data is not None:
                    kwargs["json"] = json_data
                r = fn(f"{self.api_url}/api/{endpoint}", **kwargs)
                data = r.json()
                if callback:
                    self.after(0, lambda: callback(data, r.ok))
            except Exception as exc:
                err_msg = str(exc)
                if callback:
                    self.after(0, lambda: callback({"message": err_msg}, False))

        threading.Thread(target=_do, daemon=True).start()

    # ── Produits ───────────────────────────────────────────────

    def _load_produits(self):
        self._clear()
        self._build_produit_form()
        self._api("GET", "gestion/produits", callback=self._render_produit_table)

    def _build_produit_form(self):
        tk.Label(
            self.form_frame,
            text="➕ Nouveau Produit",
            font=FONT_HEADLINE_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w", padx=16, pady=(12, 8))

        row1 = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row1.pack(fill="x", padx=16, pady=(0, 4))
        self.p_nom = self._entry(row1, "Nom *", 0, 0)
        self.p_type = self._combo(
            row1, "Type *", ["materiel", "logiciel", "emballage"], 0, 2
        )
        self.p_marque = self._entry(row1, "Marque", 0, 4)
        self.p_modele = self._entry(row1, "Modèle", 0, 6)

        # Ligne matériel
        row2 = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row2.pack(fill="x", padx=16, pady=(0, 4))
        tk.Label(
            row2,
            text="Si matériel :",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).grid(row=0, column=0, sticky="w")
        self.p_long = self._entry(row2, "Long.(cm)", 0, 1)
        self.p_larg = self._entry(row2, "Larg.(cm)", 0, 3)
        self.p_haut = self._entry(row2, "Haut.(cm)", 0, 5)
        self.p_masse = self._entry(row2, "Masse(kg)", 0, 7)

        # Ligne logiciel
        row3 = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row3.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(
            row3,
            text="Si logiciel :",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).grid(row=0, column=0, sticky="w")
        self.p_version = self._entry(row3, "Version", 0, 1)
        self.p_licence = self._entry(row3, "Licence", 0, 3)

        btn = tk.Button(
            row3,
            text="Créer",
            bg=PRIMARY,
            fg="#FFFFFF",
            font=FONT_LABEL_MD,
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
            command=self._create_produit,
        )
        btn.grid(row=0, column=5, padx=(12, 0), sticky="s")

    def _create_produit(self):
        nom = self.p_nom.get().strip()
        type_p = self.p_type.get().strip()
        if not nom or not type_p:
            messagebox.showwarning("Champ manquant", "Nom et Type requis.")
            return
        data = {
            "nom": nom,
            "type_p": type_p,
            "marque": self.p_marque.get().strip() or None,
            "modele": self.p_modele.get().strip() or None,
        }
        if type_p == "materiel":
            try:
                data["longueur"] = float(self.p_long.get())
                data["largeur"] = float(self.p_larg.get())
                data["hauteur"] = float(self.p_haut.get())
                data["masse"] = float(self.p_masse.get())
            except ValueError:
                messagebox.showwarning(
                    "Champ invalide",
                    "Dimensions et masse requis pour produit matériel.",
                )
                return
        elif type_p == "logiciel":
            data["version"] = self.p_version.get().strip() or None
            data["licence"] = self.p_licence.get().strip() or None
        self._api(
            "POST",
            "gestion/produits",
            data,
            lambda d, ok: self._on_result(d, ok, "Produit créé"),
        )

    def _render_produit_table(self, data, ok):
        if not ok:
            return
        produits = data.get("produits", [])
        cols = [
            ("ID", 50),
            ("Nom", 180),
            ("Type", 80),
            ("Marque", 100),
            ("Modèle", 100),
            ("Masse", 70),
            ("Version", 80),
            ("Fournisseur", 140),
        ]
        tree = ttk.Treeview(
            self.table_frame,
            columns=[c[0] for c in cols],
            show="headings",
            height=min(18, max(5, len(produits))),
        )
        for col_name, w in cols:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=w, minwidth=w)
        for p in produits:
            masse = f"{p.get('masse', '')} kg" if p.get("masse") else ""
            tree.insert(
                "",
                "end",
                values=(
                    p.get("idproduit", ""),
                    p.get("nom", ""),
                    p.get("typep", ""),
                    p.get("marque", ""),
                    p.get("modele", ""),
                    masse,
                    p.get("version", ""),
                    p.get("fournisseur_nom", ""),
                ),
            )
        tree.pack(fill="both", expand=True)

    # ── Lots ───────────────────────────────────────────────────

    def _load_lots(self):
        self._clear()
        self._build_lot_form()
        self._api("GET", "gestion/lots", callback=self._render_lot_table)

    def _build_lot_form(self):
        tk.Label(
            self.form_frame,
            text="➕ Nouveau Lot",
            font=FONT_HEADLINE_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w", padx=16, pady=(12, 8))
        row = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.l_produit = self._entry(row, "ID Produit *", 0, 0)
        self.l_quantite = self._entry(row, "Quantité *", 0, 2)
        self.l_origine = self._combo(row, "Origine *", ["neuf", "recupere"], 0, 4)

        btn = tk.Button(
            row,
            text="Créer",
            bg=PRIMARY,
            fg="#FFFFFF",
            font=FONT_LABEL_MD,
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
            command=self._create_lot,
        )
        btn.grid(row=0, column=6, padx=(12, 0), sticky="s")

    def _create_lot(self):
        try:
            id_p = int(self.l_produit.get().strip())
            qte = int(self.l_quantite.get().strip())
        except ValueError:
            messagebox.showwarning(
                "Champ invalide", "ID Produit et Quantité doivent être numériques."
            )
            return
        data = {
            "id_produit": id_p,
            "quantite": qte,
            "origine": self.l_origine.get().strip(),
        }
        self._api(
            "POST",
            "gestion/lots",
            data,
            lambda d, ok: self._on_result(d, ok, "Lot créé"),
        )

    def _render_lot_table(self, data, ok):
        if not ok:
            return
        lots = data.get("lots", [])
        cols = [
            ("ID", 60),
            ("Produit", 200),
            ("Type", 80),
            ("Quantité", 80),
            ("Origine", 80),
            ("Date entrée", 100),
        ]
        tree = ttk.Treeview(
            self.table_frame,
            columns=[c[0] for c in cols],
            show="headings",
            height=min(18, max(5, len(lots))),
        )
        for col_name, w in cols:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=w, minwidth=w)
        for l in lots:
            tree.insert(
                "",
                "end",
                values=(
                    l.get("idlot", ""),
                    l.get("produit_nom", ""),
                    l.get("typep", ""),
                    l.get("quantite", ""),
                    l.get("origine", ""),
                    str(l.get("dateentree", "")),
                ),
            )
        tree.pack(fill="both", expand=True)

    # ── Cellules ───────────────────────────────────────────────

    def _load_cellules(self):
        self._clear()
        self._build_cellule_form()
        self._api("GET", "gestion/cellules", callback=self._render_cellule_table)

    def _build_cellule_form(self):
        tk.Label(
            self.form_frame,
            text="➕ Nouvelle Cellule",
            font=FONT_HEADLINE_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w", padx=16, pady=(12, 8))
        row = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.c_zone = self._combo(
            row, "Zone *", ["E0", "E1", "E2", "E3", "RECEP", "EXPED"], 0, 0
        )
        self.c_position = self._entry(row, "Position *", 0, 2)
        self.c_long = self._entry(row, "Long.(cm)", 0, 4)
        self.c_larg = self._entry(row, "Larg.(cm)", 0, 6)
        self.c_haut = self._entry(row, "Haut.(cm)", 0, 8)
        self.c_masse = self._entry(row, "Masse max(kg)", 0, 10)

        btn = tk.Button(
            row,
            text="Créer",
            bg=PRIMARY,
            fg="#FFFFFF",
            font=FONT_LABEL_MD,
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
            command=self._create_cellule,
        )
        btn.grid(row=0, column=12, padx=(12, 0), sticky="s")

    def _create_cellule(self):
        try:
            data = {
                "zone": self.c_zone.get().strip(),
                "position": self.c_position.get().strip(),
                "longueur": float(self.c_long.get()),
                "largeur": float(self.c_larg.get()),
                "hauteur": float(self.c_haut.get()),
                "masse_max": float(self.c_masse.get()),
            }
        except ValueError:
            messagebox.showwarning(
                "Champ invalide", "Dimensions et masse max doivent être numériques."
            )
            return
        if not data["zone"] or not data["position"]:
            messagebox.showwarning("Champ manquant", "Zone et Position requis.")
            return
        self._api(
            "POST",
            "gestion/cellules",
            data,
            lambda d, ok: self._on_result(d, ok, "Cellule créée"),
        )

    def _render_cellule_table(self, data, ok):
        if not ok:
            return
        cells = data.get("cellules", [])
        cols = [
            ("ID", 50),
            ("Zone", 60),
            ("Position", 80),
            ("Statut", 90),
            ("L(cm)", 60),
            ("l(cm)", 60),
            ("H(cm)", 60),
            ("Masse max(kg)", 100),
        ]
        tree = ttk.Treeview(
            self.table_frame,
            columns=[c[0] for c in cols],
            show="headings",
            height=min(18, max(5, len(cells))),
        )
        for col_name, w in cols:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=w, minwidth=w)
        for c in cells:
            tree.insert(
                "",
                "end",
                values=(
                    c.get("idcellule", ""),
                    c.get("zone", ""),
                    c.get("position", ""),
                    c.get("statut", ""),
                    c.get("longueur", ""),
                    c.get("largeur", ""),
                    c.get("hauteur", ""),
                    c.get("massemaximale", ""),
                ),
            )
        tree.pack(fill="both", expand=True)

    # ── Utilitaires ────────────────────────────────────────────

    def _entry(self, parent, label, row, col):
        tk.Label(
            parent,
            text=label,
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).grid(row=row, column=col, sticky="w", padx=(0, 4))
        entry = ttk.Entry(parent, width=14)
        entry.grid(row=row, column=col + 1, padx=(0, 8), sticky="ew")
        return entry

    def _combo(self, parent, label, values, row, col):
        tk.Label(
            parent,
            text=label,
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).grid(row=row, column=col, sticky="w", padx=(0, 4))
        combo = ttk.Combobox(parent, values=values, width=12, state="readonly")
        combo.grid(row=row, column=col + 1, padx=(0, 8), sticky="ew")
        if values:
            combo.current(0)
        return combo

    def _on_result(self, data, ok, success_msg):
        if ok:
            messagebox.showinfo("Succès", success_msg)
            self.refresh()
        else:
            messagebox.showerror("Erreur", data.get("message", "Erreur inconnue"))
