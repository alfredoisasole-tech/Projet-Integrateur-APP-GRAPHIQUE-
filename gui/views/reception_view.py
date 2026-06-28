"""
Vue Réception — Réception de marchandise (référence: code3.html)

Procédé complet en 2 phases :
- Chargement d'un bon de réception
- Calcul d'itinéraire et validation du stockage
"""

import json
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
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
    FONT_DISPLAY,
)
from gui.components.widgets import StatusBadge


class ReceptionView(tk.Frame):
    """Écran Réception de marchandise."""

    def __init__(self, parent, api_url):
        super().__init__(parent, bg=SURFACE)
        self.api_url = api_url
        self.current_bon = None
        self.current_itineraire = None
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=24, pady=(20, 16))

        tk.Label(
            header, text="RÉCEPTION", font=FONT_HEADLINE_LG, bg=SURFACE, fg=ON_SURFACE
        ).pack(side="left")

        self.statut_label = StatusBadge(header, text="En attente", status="neutral")
        self.statut_label.pack(side="right")
        # Label pour afficher l'ID du colis après réception
        self.colis_id_label = tk.Label(
            header, text="", font=FONT_LABEL_SM, bg=SURFACE, fg=ON_SURFACE_VARIANT
        )
        self.colis_id_label.pack(side="right", padx=(0, 12))

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
            text="ID BON DE RÉCEPTION",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
        ).pack(side="left")

        self.bon_entry = ttk.Entry(inner, width=25, font=FONT_BODY_MD)
        self.bon_entry.pack(side="left", padx=(12, 8))
        self.bon_entry.insert(0, "REC-2024-001")

        ttk.Button(
            inner, text="CHARGER", style="Primary.TButton", command=self._load_bon
        ).pack(side="left", padx=4)

        ttk.Button(
            inner, text="RECEVOIR", style="Secondary.TButton", command=self._recevoir
        ).pack(side="left", padx=4)

        # === ACTIONS (Packé en bas en premier pour toujours être visible) ===
        actions = tk.Frame(self, bg=SURFACE)
        actions.pack(side="bottom", fill="x", padx=24, pady=(16, 24))

        ttk.Button(
            actions,
            text="⚠ Signaler Anomalie",
            style="Danger.TButton",
            command=self._signaler_anomalie,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            actions,
            text="🗺️ Calculer Itinéraire",
            style="Secondary.TButton",
            command=self._calculer_itineraire,
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="✓ Valider Stockage",
            style="Primary.TButton",
            command=self._valider_stockage,
        ).pack(side="right")

        # === CONTENU PRINCIPAL ===
        main = tk.Frame(self, bg=SURFACE)
        main.pack(side="top", fill="both", expand=True, padx=24)

        # Panneau gauche : Détails du bon
        left = tk.Frame(
            main,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        lh = tk.Frame(left, bg=SURFACE_CONTAINER_HIGH)
        lh.pack(fill="x")
        tk.Label(
            lh,
            text="DÉTAILS DU BON",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")

        self.details_frame = tk.Frame(left, bg=SURFACE_LOWEST, padx=16, pady=12)
        self.details_frame.pack(fill="both", expand=True)

        # Placeholder
        tk.Label(
            self.details_frame,
            text="Chargez un bon de réception\npour voir les détails",
            font=FONT_BODY_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
            justify="center",
        ).pack(expand=True)

        # Panneau droit : Itinéraire
        right = tk.Frame(
            main,
            bg=SURFACE_LOWEST,
            highlightbackground=OUTLINE_VARIANT,
            highlightthickness=1,
        )
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        rh = tk.Frame(right, bg=SURFACE_CONTAINER_HIGH)
        rh.pack(fill="x")
        tk.Label(
            rh,
            text="RÉSULTAT DU CALCUL D'ITINÉRAIRE",
            font=FONT_LABEL_SM,
            bg=SURFACE_CONTAINER_HIGH,
            fg=OUTLINE,
            padx=16,
            pady=8,
        ).pack(side="left")

        self.itineraire_frame = tk.Frame(right, bg=SURFACE_LOWEST, padx=16, pady=12)
        self.itineraire_frame.pack(fill="both", expand=True)

        tk.Label(
            self.itineraire_frame,
            text="Aucun itinéraire calculé",
            font=FONT_BODY_MD,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
            justify="center",
        ).pack(expand=True)

    def refresh(self):
        """Actualise la vue."""
        pass

    def _parse_api_response(self, resp):
        """Parse la réponse API en gérant les erreurs HTTP et JSON."""
        if not resp.ok:
            try:
                data = resp.json()
                message = data.get("message") if isinstance(data, dict) else None
            except (ValueError, json.JSONDecodeError):
                message = resp.text or f"Erreur HTTP {resp.status_code}"
            raise RuntimeError(message or f"Erreur HTTP {resp.status_code}")

        try:
            return resp.json()
        except (ValueError, json.JSONDecodeError):
            raise RuntimeError("Réponse API invalide")

    def _load_bon(self):
        """Charge un bon de réception depuis l'API."""
        bon_id = self.bon_entry.get().strip()
        if not bon_id:
            return
        threading.Thread(target=self._fetch_bon, args=(bon_id,), daemon=True).start()

    def _fetch_bon(self, bon_id):
        try:
            resp = requests.get(f"{self.api_url}/api/reception/bon/{bon_id}", timeout=5)
            data = self._parse_api_response(resp)
            bon = data.get("bon", {})
            self.after(0, lambda: self._display_bon(bon))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_error("Connexion API impossible"))
        except Exception as e:
            err = str(e)
            self.after(0, lambda: self._show_error(err))

    def _display_bon(self, bon):
        """Affiche les détails du bon."""
        self.current_bon = bon

        for w in self.details_frame.winfo_children():
            w.destroy()

        # Statut
        self.statut_label.configure(
            text=bon.get("statut", "").replace("_", " ").upper()
        )

        # Fournisseur
        fields = [
            ("Fournisseur", bon.get("fournisseur_nom", "")),
            ("Date", bon.get("date", "")[:16]),
            ("Masse Totale", f"{bon.get('masse_totale', 0)} kg"),
            ("Volume Estimé", f"{bon.get('volume_estime', 0)} m³"),
            ("Palettes", str(bon.get("nb_palettes", 0))),
        ]

        for label, value in fields:
            row = tk.Frame(self.details_frame, bg=SURFACE_LOWEST)
            row.pack(fill="x", pady=4)
            tk.Label(
                row,
                text=label.upper(),
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=OUTLINE,
                width=16,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                row, text=value, font=FONT_BODY_MD, bg=SURFACE_LOWEST, fg=ON_SURFACE
            ).pack(side="left")

        # Séparateur
        tk.Frame(self.details_frame, bg=OUTLINE_VARIANT, height=1).pack(
            fill="x", pady=12
        )

        # Items du bon
        tk.Label(
            self.details_frame,
            text="PRODUITS",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
        ).pack(anchor="w")

        for item in bon.get("items", []):
            item_frame = tk.Frame(self.details_frame, bg=SURFACE_LOWEST)
            item_frame.pack(fill="x", pady=4)

            tk.Label(
                item_frame,
                text=f"📦 {item['produit_nom']}",
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE,
            ).pack(anchor="w")
            tk.Label(
                item_frame,
                text=f"   Qté: {item['quantite']}  |  Masse: {item['masse_totale']} kg",
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE_VARIANT,
            ).pack(anchor="w")

        # Afficher l'ID du colis si déjà créé / associé
        colis_id = bon.get("colis_id")
        if colis_id:
            self._display_colis_id(colis_id)
        else:
            self._display_colis_id(None)

    def _recevoir(self):
        """Phase A : Réceptionner le chargement."""
        bon_id = self.bon_entry.get().strip()
        if not bon_id:
            return
        threading.Thread(target=self._do_recevoir, args=(bon_id,), daemon=True).start()

    def _do_recevoir(self, bon_id):
        try:
            resp = requests.post(
                f"{self.api_url}/api/reception/recevoir",
                json={"bon_reception_id": bon_id},
                timeout=5,
            )
            result = self._parse_api_response(resp)
            # Mettre à jour statut et afficher colis_id si présent
            self.after(0, lambda: self._show_result(result))
            colis_id = result.get("colis_id") if isinstance(result, dict) else None
            if colis_id:
                self.after(0, lambda: self._display_colis_id(colis_id))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_error("Connexion API impossible"))
        except Exception as e:
            err = str(e)
            self.after(0, lambda: self._show_error(err))

    def _calculer_itineraire(self):
        """Calcule l'itinéraire de stockage."""
        threading.Thread(target=self._do_itineraire, daemon=True).start()

    def _do_itineraire(self):
        try:
            resp = requests.get(
                f"{self.api_url}/api/reception/zone-reception", timeout=5
            )
            data = self._parse_api_response(resp)
            colis = data.get("colis", [])
            if not colis:
                self.after(
                    0, lambda: self._show_error("Aucun colis en zone de réception")
                )
                return

            colis_id = colis[0]["id"]
            resp2 = requests.post(
                f"{self.api_url}/api/reception/attribuer-emplacement",
                json={"colis_id": colis_id},
                timeout=5,
            )
            result = self._parse_api_response(resp2)
            self.after(0, lambda: self._display_itineraire(result))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_error("Connexion API impossible"))
        except Exception as e:
            err = str(e)
            self.after(0, lambda: self._show_error(err))

    def _display_itineraire(self, result):
        """Affiche l'itinéraire calculé."""
        self.current_itineraire = result

        for w in self.itineraire_frame.winfo_children():
            w.destroy()

        if result.get("statut") != "SUCCESS":
            tk.Label(
                self.itineraire_frame,
                text=result.get("message", "Erreur"),
                font=FONT_BODY_MD,
                bg=SURFACE_LOWEST,
                fg=ERROR,
            ).pack(expand=True)
            return

        cellule = result.get("cellule_cible", {})
        itineraire = result.get("itineraire", [])

        # Cellule cible (grand)
        target_frame = tk.Frame(self.itineraire_frame, bg=SURFACE_LOWEST)
        target_frame.pack(fill="x", pady=(0, 12))

        zone_id = cellule.get("zone_id", "E?")
        cell_id = cellule.get("id", "?")
        tk.Label(
            target_frame,
            text=f"ZONE {zone_id}",
            font=FONT_HEADLINE_MD,
            bg=SURFACE_LOWEST,
            fg=PRIMARY,
        ).pack(anchor="w")
        tk.Label(
            target_frame,
            text=cell_id,
            font=FONT_DISPLAY,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE,
        ).pack(anchor="w")
        tk.Label(
            target_frame,
            text=f"Capacité: {cellule.get('masse_max', 0) - cellule.get('masse_actuelle', 0):.0f} kg restants",
            font=FONT_BODY_SM,
            bg=SURFACE_LOWEST,
            fg=ON_SURFACE_VARIANT,
        ).pack(anchor="w")

        # Séparateur
        tk.Frame(self.itineraire_frame, bg=OUTLINE_VARIANT, height=1).pack(
            fill="x", pady=8
        )

        # Étapes
        tk.Label(
            self.itineraire_frame,
            text="ITINÉRAIRE",
            font=FONT_LABEL_SM,
            bg=SURFACE_LOWEST,
            fg=OUTLINE,
        ).pack(anchor="w", pady=(0, 4))

        for step in itineraire:
            step_frame = tk.Frame(self.itineraire_frame, bg=SURFACE_LOWEST)
            step_frame.pack(fill="x", pady=3)

            tk.Label(
                step_frame,
                text=f"Étape {step['etape']}",
                font=FONT_LABEL_SM,
                bg=SURFACE_LOWEST,
                fg=PRIMARY,
                width=8,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                step_frame,
                text=step["direction"],
                font=FONT_BODY_SM,
                bg=SURFACE_LOWEST,
                fg=ON_SURFACE,
            ).pack(side="left", padx=(4, 8))
            StatusBadge(step_frame, text=step["info"], status="info").pack(side="right")

    def _valider_stockage(self):
        """Phase B : Valider le stockage."""
        if not self.current_itineraire:
            self._show_error("Calculez d'abord l'itinéraire")
            return

        result = self.current_itineraire
        colis = result.get("colis", {})
        cellule = result.get("cellule_cible", {})

        threading.Thread(
            target=self._do_stockage,
            args=(colis.get("id"), cellule.get("id")),
            daemon=True,
        ).start()

    def _do_stockage(self, colis_id, cellule_id):
        try:
            resp = requests.post(
                f"{self.api_url}/api/reception/stocker",
                json={"colis_id": colis_id, "cellule_cible": cellule_id},
                timeout=5,
            )
            result = self._parse_api_response(resp)
            self.after(0, lambda: self._show_result(result, is_stockage=True))
        except requests.ConnectionError:
            self.after(0, lambda: self._show_error("Connexion API impossible"))
        except Exception as e:
            err = str(e)
            self.after(0, lambda: self._show_error(err))

    def _show_result(self, result, is_stockage=False):
        """Affiche un résultat d'opération."""
        statut = result.get("statut", "ERROR")
        message = result.get("message", "")
        color = (
            SUCCESS
            if statut == "SUCCESS"
            else WARNING if statut == "EXCEPTION_TRIGGER" else ERROR
        )

        if statut == "SUCCESS":
            self.statut_label.configure(text="SUCCESS", bg="#e8f5e9", fg=SUCCESS)
            messagebox.showinfo("Succès", message or "Opération effectuée avec succès.")
            if is_stockage:
                self.current_itineraire = None
                for w in self.itineraire_frame.winfo_children():
                    w.destroy()
                tk.Label(
                    self.itineraire_frame,
                    text="Stockage validé avec succès.",
                    font=FONT_BODY_MD,
                    bg=SURFACE_LOWEST,
                    fg=SUCCESS,
                    justify="center",
                ).pack(expand=True)
                self.colis_id_label.configure(text="")
        else:
            self.statut_label.configure(text="ERREUR", bg="#ffdad6", fg=ERROR)
            messagebox.showerror("Erreur / Exception", message)

    def _display_colis_id(self, colis_id):
        """Affiche l'ID du colis dans l'en-tête."""
        if colis_id:
            self.colis_id_label.configure(text=f"Colis: #{colis_id}")
        else:
            self.colis_id_label.configure(text="")

    def _show_error(self, msg):
        self.statut_label.configure(text="ERREUR", bg="#ffdad6", fg=ERROR)
        messagebox.showerror("Erreur", msg)

    def _signaler_anomalie(self):
        """Ouvre une fenêtre de saisie pour signaler une anomalie."""
        bon_id = self.bon_entry.get().strip() or "N/A"
        desc = simpledialog.askstring(
            "Signaler une Anomalie",
            f"Bon : {bon_id}\n\nDécrivez l'anomalie observée :",
            parent=self,
        )
        if desc and desc.strip():
            threading.Thread(
                target=self._do_signaler, args=(bon_id, desc.strip()), daemon=True
            ).start()

    def _do_signaler(self, bon_id, description):
        try:
            resp = requests.post(
                f"{self.api_url}/api/rapports/signaler",
                json={
                    "bon_id": bon_id,
                    "description": description,
                    "type": "ecart_reception",
                },
                timeout=5,
            )
            if resp.ok:
                self.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Anomalie enregistrée", "Rapport d'exception créé avec succès."
                    ),
                )
            else:
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        "Erreur API", resp.json().get("message", "Erreur inconnue")
                    ),
                )
        except requests.ConnectionError:
            self.after(
                0, lambda: messagebox.showerror("Connexion", "API inaccessible.")
            )
