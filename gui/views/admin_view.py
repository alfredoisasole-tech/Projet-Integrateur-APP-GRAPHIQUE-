"""
Vue Administration — Gestion des Organisations, Individus et Répertoire.

Sous-onglets avec DataTable + formulaire CRUD pour chaque entité.
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
from gui.components.widgets import DataTable


class AdminView(tk.Frame):
    """Écran Administration — CRUD Organisation / Individu / Répertoire."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self.current_tab = "organisations"
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
            text="ADMINISTRATION",
            font=FONT_HEADLINE_LG,
            bg=SURFACE,
            fg=ON_SURFACE,
        ).pack(side="left")

        # Sous-onglets
        tabs = tk.Frame(self.scroll_frame, bg=SURFACE)
        tabs.pack(fill="x", padx=24, pady=(0, 12))
        self.tab_buttons = {}
        for key, label in [
            ("organisations", "🏢 Organisations"),
            ("individus", "👤 Individus"),
            ("repertoire", "📋 Répertoire"),
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

        # Container contenu
        self.content_frame = tk.Frame(self.scroll_frame, bg=SURFACE)
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

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
        # Update tab button styles
        for k, btn in self.tab_buttons.items():
            if k == tab_key:
                btn.configure(bg=PRIMARY, fg="#FFFFFF")
            else:
                btn.configure(bg=SURFACE, fg=ON_SURFACE_VARIANT)
        self.refresh()

    def refresh(self):
        self._switch_tab_style()
        if self.current_tab == "organisations":
            self._load_organisations()
        elif self.current_tab == "individus":
            self._load_individus()
        elif self.current_tab == "repertoire":
            self._load_repertoire()

    def _switch_tab_style(self):
        for k, btn in self.tab_buttons.items():
            if k == self.current_tab:
                btn.configure(bg=PRIMARY, fg="#FFFFFF")
            else:
                btn.configure(bg=SURFACE, fg=ON_SURFACE_VARIANT)

    def _clear_content(self):
        for w in self.form_frame.winfo_children():
            w.destroy()
        for w in self.table_frame.winfo_children():
            w.destroy()

    def _api_call(self, method, endpoint, json_data=None, callback=None):
        def _do():
            try:
                if method == "GET":
                    r = requests.get(f"{self.api_url}/api/{endpoint}", timeout=5)
                elif method == "POST":
                    r = requests.post(
                        f"{self.api_url}/api/{endpoint}", json=json_data, timeout=5
                    )
                elif method == "PUT":
                    r = requests.put(
                        f"{self.api_url}/api/{endpoint}", json=json_data, timeout=5
                    )
                elif method == "DELETE":
                    r = requests.delete(f"{self.api_url}/api/{endpoint}", timeout=5)
                else:
                    return
                data = r.json()
                if callback:
                    self.after(0, lambda: callback(data, r.ok))
            except Exception as exc:
                err_msg = str(exc)
                if callback:
                    self.after(0, lambda: callback({"message": err_msg}, False))

        threading.Thread(target=_do, daemon=True).start()

    # ── Organisations ──────────────────────────────────────────

    def _load_organisations(self):
        self._clear_content()
        self._build_org_form()
        self._api_call("GET", "admin/organisations", callback=self._render_org_table)

    def _build_org_form(self):
        tk.Label(
            self.form_frame,
            text="➕ Nouvelle Organisation",
            font=FONT_HEADLINE_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w", padx=16, pady=(12, 8))
        row = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.org_nom = self._entry(row, "Nom *", 0, 0)
        self.org_type = self._combo(
            row,
            "Type *",
            ["fournisseur", "transporteur", "destinataire", "autre"],
            0,
            2,
        )
        self.org_adresse = self._entry(row, "Adresse", 0, 4)
        self.org_tel = self._entry(row, "Téléphone", 0, 6)

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
            command=self._create_organisation,
        )
        btn.grid(row=0, column=8, padx=(12, 0), sticky="s")

    def _create_organisation(self):
        nom = self.org_nom.get().strip()
        type_org = self.org_type.get().strip()
        if not nom or not type_org:
            messagebox.showwarning("Champ manquant", "Nom et Type sont requis.")
            return
        data = {
            "nom": nom,
            "type_org": type_org,
            "adresse": self.org_adresse.get().strip() or None,
            "telephone": self.org_tel.get().strip() or None,
        }
        self._api_call(
            "POST",
            "admin/organisations",
            data,
            lambda d, ok: self._on_crud_result(d, ok, "Organisation créée"),
        )

    def _delete_org(self, org_id):
        if messagebox.askyesno("Confirmer", f"Supprimer l'organisation #{org_id} ?"):
            self._api_call(
                "DELETE",
                f"admin/organisations/{org_id}",
                callback=lambda d, ok: self._on_crud_result(
                    d, ok, "Organisation supprimée"
                ),
            )

    def _render_org_table(self, data, ok):
        if not ok:
            return
        orgs = data.get("organisations", [])
        if not orgs:
            tk.Label(
                self.table_frame,
                text="Aucune organisation",
                font=FONT_BODY_MD,
                bg=SURFACE,
                fg=ON_SURFACE_VARIANT,
            ).pack(pady=20)
            return

        cols = [
            ("ID", 60),
            ("Nom", 200),
            ("Type", 120),
            ("Adresse", 250),
            ("Téléphone", 120),
            ("", 80),
        ]
        tree = ttk.Treeview(
            self.table_frame,
            columns=[c[0] for c in cols],
            show="headings",
            height=min(15, len(orgs)),
        )
        for col_name, w in cols:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=w, minwidth=w)
        for o in orgs:
            oid = o.get("idorganisation", "?")
            tree.insert(
                "",
                "end",
                values=(
                    oid,
                    o.get("nom", ""),
                    o.get("typeorg", ""),
                    o.get("adresse", ""),
                    o.get("telephone", ""),
                    "🗑",
                ),
            )
        tree.pack(fill="both", expand=True)
        tree.bind("<Double-1>", lambda e: self._on_tree_dblclick(tree, "org"))

    # ── Individus ──────────────────────────────────────────────

    def _load_individus(self):
        self._clear_content()
        self._build_ind_form()
        self._api_call("GET", "admin/individus", callback=self._render_ind_table)

    def _build_ind_form(self):
        tk.Label(
            self.form_frame,
            text="➕ Nouvel Individu",
            font=FONT_HEADLINE_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w", padx=16, pady=(12, 8))
        row = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.ind_nom = self._entry(row, "Nom *", 0, 0)
        self.ind_email = self._entry(row, "Email", 0, 2)
        self.ind_tel = self._entry(row, "Téléphone", 0, 4)
        self.ind_adresse = self._entry(row, "Adresse", 0, 6)

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
            command=self._create_individu,
        )
        btn.grid(row=0, column=8, padx=(12, 0), sticky="s")

    def _create_individu(self):
        nom = self.ind_nom.get().strip()
        if not nom:
            messagebox.showwarning("Champ manquant", "Nom requis.")
            return
        data = {
            "nom": nom,
            "email": self.ind_email.get().strip() or None,
            "telephone": self.ind_tel.get().strip() or None,
            "adresse": self.ind_adresse.get().strip() or None,
        }
        self._api_call(
            "POST",
            "admin/individus",
            data,
            lambda d, ok: self._on_crud_result(d, ok, "Individu créé"),
        )

    def _render_ind_table(self, data, ok):
        if not ok:
            return
        inds = data.get("individus", [])
        if not inds:
            tk.Label(
                self.table_frame,
                text="Aucun individu",
                font=FONT_BODY_MD,
                bg=SURFACE,
                fg=ON_SURFACE_VARIANT,
            ).pack(pady=20)
            return
        cols = [
            ("ID", 60),
            ("Nom", 200),
            ("Email", 180),
            ("Téléphone", 120),
            ("Adresse", 250),
        ]
        tree = ttk.Treeview(
            self.table_frame,
            columns=[c[0] for c in cols],
            show="headings",
            height=min(15, len(inds)),
        )
        for col_name, w in cols:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=w, minwidth=w)
        for i in inds:
            tree.insert(
                "",
                "end",
                values=(
                    i.get("idindividu", "?"),
                    i.get("nom", ""),
                    i.get("email", ""),
                    i.get("telephone", ""),
                    i.get("adresse", ""),
                ),
            )
        tree.pack(fill="both", expand=True)

    # ── Répertoire ─────────────────────────────────────────────

    def _load_repertoire(self):
        self._clear_content()
        self._build_rep_form()
        self._api_call("GET", "admin/repertoire", callback=self._render_rep_table)

    def _build_rep_form(self):
        tk.Label(
            self.form_frame,
            text="➕ Nouvelle Affectation",
            font=FONT_HEADLINE_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w", padx=16, pady=(12, 8))
        row = tk.Frame(self.form_frame, bg=SURFACE_LOWEST)
        row.pack(fill="x", padx=16, pady=(0, 12))

        self.rep_org_id = self._entry(row, "ID Org *", 0, 0)
        self.rep_ind_id = self._entry(row, "ID Individu *", 0, 2)
        self.rep_role = self._combo(
            row,
            "Rôle *",
            [
                "conducteur",
                "magasinier",
                "acheteur",
                "vendeur",
                "agent_logistique",
                "autre",
            ],
            0,
            4,
        )
        self.rep_debut = self._entry(row, "Date début * (YYYY-MM-DD)", 0, 6)

        btn = tk.Button(
            row,
            text="Assigner",
            bg=PRIMARY,
            fg="#FFFFFF",
            font=FONT_LABEL_MD,
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
            command=self._create_repertoire,
        )
        btn.grid(row=0, column=8, padx=(12, 0), sticky="s")

    def _create_repertoire(self):
        org = self.rep_org_id.get().strip()
        ind = self.rep_ind_id.get().strip()
        role = self.rep_role.get().strip()
        debut = self.rep_debut.get().strip()
        if not all([org, ind, role, debut]):
            messagebox.showwarning("Champ manquant", "Tous les champs * sont requis.")
            return
        data = {
            "id_organisation": int(org),
            "id_individu": int(ind),
            "role": role,
            "date_debut": debut,
        }
        self._api_call(
            "POST",
            "admin/repertoire",
            data,
            lambda d, ok: self._on_crud_result(d, ok, "Affectation créée"),
        )

    def _render_rep_table(self, data, ok):
        if not ok:
            return
        reps = data.get("repertoire", [])
        if not reps:
            tk.Label(
                self.table_frame,
                text="Aucune affectation",
                font=FONT_BODY_MD,
                bg=SURFACE,
                fg=ON_SURFACE_VARIANT,
            ).pack(pady=20)
            return
        cols = [
            ("Organisation", 180),
            ("Individu", 180),
            ("Rôle", 140),
            ("Début", 100),
            ("Fin", 100),
        ]
        tree = ttk.Treeview(
            self.table_frame,
            columns=[c[0] for c in cols],
            show="headings",
            height=min(15, len(reps)),
        )
        for col_name, w in cols:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=w, minwidth=w)
        for r in reps:
            tree.insert(
                "",
                "end",
                values=(
                    r.get("organisation", ""),
                    r.get("individu", ""),
                    r.get("role", ""),
                    str(r.get("datedebut", "")),
                    str(r.get("datefin", "") or "—"),
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
        entry = ttk.Entry(parent, width=18)
        entry.grid(row=row, column=col + 1, padx=(0, 12), sticky="ew")
        return entry

    def _combo(self, parent, label, values, row, col):
        tk.Label(
            parent,
            text=label,
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).grid(row=row, column=col, sticky="w", padx=(0, 4))
        combo = ttk.Combobox(parent, values=values, width=16, state="readonly")
        combo.grid(row=row, column=col + 1, padx=(0, 12), sticky="ew")
        if values:
            combo.current(0)
        return combo

    def _on_crud_result(self, data, ok, success_msg):
        if ok:
            messagebox.showinfo("Succès", success_msg)
            self.refresh()
        else:
            messagebox.showerror("Erreur", data.get("message", "Erreur inconnue"))

    def _on_tree_dblclick(self, tree, entity):
        item = tree.focus()
        if not item:
            return
        values = tree.item(item, "values")
        if entity == "org" and values:
            self._delete_org(values[0])
