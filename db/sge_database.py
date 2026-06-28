"""
SGE — SGEDatabase : couche d'accès PostgreSQL

Accès PostgreSQL pour le SGE WMS-CLAM-PRO.
Utilise les vues et fonctions SQL définies dans :
  - SGE_req.sql (requêtes F1-F4)
  - SGE_imm.sql (CRUD)
  - SGE_inv.sql (triggers actifs côté DB)
"""

from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from db.connection import get_conn, release_conn


class SGEDatabase:
    """Base de données PostgreSQL pour le SGE de la SAC.

    Interface PostgreSQL complète pour le SGE.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _query(self, sql, params=None, fetchone=False):
        """Exécute une requête SELECT et retourne les résultats."""
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetchone:
                    row = cur.fetchone()
                    return dict(row) if row else None
                return [dict(r) for r in cur.fetchall()]
        finally:
            release_conn(conn)

    def _execute(self, sql, params=None):
        """Exécute un INSERT/UPDATE/DELETE et commit."""
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                conn.commit()
                try:
                    return dict(cur.fetchone()) if cur.description else None
                except Exception:
                    return None
        except psycopg2.errors.RaiseException:
            conn.rollback()
            raise
        except psycopg2.Error:
            conn.rollback()
            raise
        finally:
            release_conn(conn)

    def _call_func(self, func_name, params=None):
        """Appelle une fonction PostgreSQL et retourne les lignes."""
        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if params is not None:
                    params = params if isinstance(params, (list, tuple)) else (params,)
                    placeholders = ", ".join(["%s"] * len(params))
                    cur.execute(f"SELECT * FROM {func_name}({placeholders})", params)
                else:
                    cur.execute(f"SELECT * FROM {func_name}()")
                return [dict(r) for r in cur.fetchall()]
        finally:
            release_conn(conn)

    # ----------------------------------------------------------
    # DASHBOARD & CARTOGRAPHIE
    # ----------------------------------------------------------

    def get_dashboard_data(self):
        """Retourne les données résumées du tableau de bord."""
        zones_data = self._call_func("sge_req_taux_occupation_par_zone")
        total_cellules = sum(z["nb_cellules"] for z in zones_data)
        masse_totale = sum(float(z.get("masse_totale_kg") or 0) for z in zones_data)
        capacite_totale = sum(
            float(z.get("capacite_totale_kg") or 0) for z in zones_data
        )
        occupation_pct = (
            round(masse_totale / capacite_totale * 100, 1) if capacite_totale else 0
        )

        erreurs_actives = len(
            self._query(
                "SELECT 1 FROM Rapport_exception WHERE typeRapport IN ('ecart_reception','ecart_stockage','masse_depassee')"
            )
        )
        nb_bons_rec = len(
            self._query("SELECT 1 FROM Bon_reception WHERE statut = 'en_attente'")
        )
        nb_bons_exp = len(
            self._query("SELECT 1 FROM Bon_expedition WHERE statut = 'en_attente'")
        )

        zones = {}
        for z in zones_data:
            zone_id = z["zone"]
            cellules_detail = self._query(
                "SELECT * FROM v_taux_occupation WHERE zone = %s ORDER BY position",
                (zone_id,),
            )
            zones[zone_id] = {
                "id": zone_id,
                "nom": zone_id,
                "nb_cellules": int(z["nb_cellules"]),
                "occupation_pct": float(z.get("taux_moyen_pct") or 0),
                "cellules": [str(c["idcellule"]) for c in cellules_detail],
                "cellules_detail": [
                    {
                        "id": f"{zone_id}_{c['position']}",
                        "zone_id": zone_id,
                        "position": c["position"],
                        "masse_max": float(c["massemaximale"]),
                        "masse_actuelle": float(c["masse_actuelle_kg"]),
                        "statut": (
                            "Libre"
                            if c["statut"] == "disponible"
                            else (
                                "Occupé"
                                if float(c.get("taux_occupation_pct") or 0) > 80
                                else "Partiel"
                            )
                        ),
                    }
                    for c in cellules_detail
                ],
            }

        return {
            "zones": zones,
            "emballages": self._get_emballages_dict(),
            "occupation_globale_pct": occupation_pct,
            "total_cellules": total_cellules,
            "cellules_occupees": len(
                self._query("SELECT 1 FROM Cellule WHERE statut = 'occupee'")
            ),
            "receptions_jour": nb_bons_rec,
            "sorties_jour": nb_bons_exp,
            "erreurs_actives": erreurs_actives,
            "rendement": round(
                len(self._query("SELECT 1 FROM Bon_reception WHERE statut = 'traite'"))
                / max(1, len(self._query("SELECT 1 FROM Bon_reception")))
                * 100,
                1,
            ),
            "quais_utilises": len(self._query("""SELECT 1 FROM Colis c
                   JOIN Cellule cel ON cel.idCellule = c.idCelluleZone
                   WHERE c.statut IN ('en_attente', 'en_traitement')
                     AND cel.zone IN ('RECEP', 'EXPED')""")),
            "quais_total": len(
                self._query("SELECT 1 FROM Cellule WHERE zone IN ('RECEP', 'EXPED')")
            ),
            "colis_zone_reception": len(
                self._query(
                    "SELECT 1 FROM Colis WHERE typeColis = 'entrant' AND statut IN ('en_attente','en_traitement')"
                )
            ),
            "colis_zone_expedition": len(
                self._query(
                    "SELECT 1 FROM Colis WHERE typeColis = 'sortant' AND statut IN ('en_attente','en_traitement')"
                )
            ),
        }

    def get_zones(self):
        """Retourne toutes les zones avec leurs cellules."""
        return self.get_dashboard_data()["zones"]

    def get_zone(self, zone_id):
        """Retourne le détail d'une zone spécifique."""
        return self.get_zones().get(zone_id)

    # ----------------------------------------------------------
    # RÉCEPTION (Procédé complet en 2 phases)
    # ----------------------------------------------------------

    def get_bons_reception(self):
        """Retourne tous les bons de réception."""
        rows = self._query("""
            SELECT br.idBon AS id, o.nom AS fournisseur_nom,
                   br.dateAttendue AS date, br.statut, br.priorite
            FROM Bon_reception br
            JOIN Organisation o ON o.idOrganisation = br.idFournisseur
            ORDER BY br.priorite ASC, br.dateAttendue ASC
        """)
        result = []
        for r in rows:
            result.append(
                {
                    "id": f"REC-{r['id']:04d}",
                    "fournisseur_nom": r["fournisseur_nom"],
                    "date": str(r["date"]),
                    "statut": r["statut"],
                    "priorite": self._priorite_label(r["priorite"]),
                }
            )
        return result

    def get_bon_reception(self, bon_id):
        """Retourne un bon de réception spécifique."""
        num = self._extract_id(bon_id)
        if num is None:
            return None
        bon = self._query(
            """
            SELECT br.idBon, o.nom AS fournisseur_nom,
                   br.dateAttendue, br.statut, br.priorite,
                   br.idColis,
                   br.dateEffective
            FROM Bon_reception br
            JOIN Organisation o ON o.idOrganisation = br.idFournisseur
            WHERE br.idBon = %s
        """,
            (num,),
            fetchone=True,
        )
        if not bon:
            return None

        # BUG-02 FIX : utiliser les lots réellement liés au colis du bon (via Contenu_Colis)
        # Si le bon a déjà un colis associé, on utilise Contenu_Colis ; sinon on prend
        # les lots disponibles du fournisseur comme aperçu avant réception.
        colis_id = bon.get("idcolis")
        if colis_id:
            items = self._query(
                """
                SELECT p.idProduit AS produit_id, p.nom AS produit_nom,
                       cc.quantiteColis AS quantite,
                       COALESCE(pm.masse * cc.quantiteColis, 0) AS masse_totale,
                       COALESCE(pm.longueur * pm.largeur * pm.hauteur * cc.quantiteColis / 1e6, 0) AS volume_m3
                FROM Contenu_Colis cc
                JOIN Lot l ON l.idLot = cc.idLot
                JOIN Produit p ON p.idProduit = l.idProduit
                LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
                WHERE cc.idColis = %s
            """,
                (colis_id,),
            )
        else:
            items = self._query(
                """
                SELECT p.idProduit AS produit_id, p.nom AS produit_nom,
                       l.quantite,
                       COALESCE(pm.masse * l.quantite, 0) AS masse_totale,
                       COALESCE(pm.longueur * pm.largeur * pm.hauteur * l.quantite / 1e6, 0) AS volume_m3
                FROM Lot l
                JOIN Produit p ON p.idProduit = l.idProduit
                LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
                WHERE l.idProduit IN (
                    SELECT idProduit FROM Produit
                    WHERE idFournisseur = (SELECT idFournisseur FROM Bon_reception WHERE idBon = %s)
                )
                ORDER BY l.dateEntree DESC
            """,
                (num,),
            )

        masse_totale = sum(float(i.get("masse_totale", 0)) for i in items)
        # BUG-12 FIX : volume depuis les dimensions réelles, pas masse * 0.008
        volume_total = sum(float(i.get("volume_m3", 0)) for i in items)
        return {
            "id": bon_id,
            "fournisseur_nom": bon["fournisseur_nom"],
            "date": str(bon["dateattendue"]),
            "statut": bon["statut"],
            "priorite": self._priorite_label(bon["priorite"]),
            "colis_id": str(bon["idcolis"]) if bon.get("idcolis") else None,
            "masse_totale": round(masse_totale, 1),
            "volume_estime": round(volume_total, 3),
            "nb_palettes": max(1, len(items) // 3),
            "items": [
                {
                    "produit_id": str(i["produit_id"]),
                    "produit_nom": i["produit_nom"],
                    "quantite": i["quantite"],
                    "masse_totale": float(i["masse_totale"]),
                }
                for i in items
            ],
        }

    def recevoir_chargement(self, bon_id):
        """Phase A : Réception immédiate."""
        num = self._extract_id(bon_id)
        if num is None:
            return {"statut": "ERROR", "message": f"Bon {bon_id} introuvable"}

        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT statut, idColis FROM Bon_reception WHERE idBon = %s", (num,)
                )
                row = cur.fetchone()
                if not row:
                    return {"statut": "ERROR", "message": f"Bon {bon_id} introuvable"}
                if row["statut"] == "en_cours":
                    colis_id = row.get("idcolis")
                    if colis_id:
                        return {
                            "statut": "SUCCESS",
                            "message": f"Bon {bon_id} déjà en cours. Reprise sur colis #{colis_id} en zone de réception.",
                            "colis_id": str(colis_id),
                            "colis_en_attente": len(self.get_zone_reception()),
                        }
                    return {
                        "statut": "ERROR",
                        "message": f"Bon {bon_id} déjà en cours sans colis associé",
                    }
                if row["statut"] != "en_attente":
                    return {
                        "statut": "ERROR",
                        "message": f"Bon {bon_id} déjà traité (statut: {row['statut']})",
                    }

                cur.execute("CALL sge_tra_reception_immediate(%s, %s)", (num, None))

                cur.execute(
                    "SELECT idColis FROM Bon_reception WHERE idBon = %s", (num,)
                )
                colis_id = cur.fetchone()["idcolis"]

                # Peupler Contenu_Colis : répartir les lots du fournisseur
                # entre les bons en attente (round-robin)
                cur.execute(
                    """
                    SELECT l.idLot, l.quantite
                      FROM Lot l
                      JOIN Produit p ON p.idProduit = l.idProduit
                     WHERE p.idFournisseur = (
                               SELECT idFournisseur FROM Bon_reception WHERE idBon = %s
                           )
                       AND p.typeP = 'materiel'
                       AND l.idLot NOT IN (SELECT cc2.idLot FROM Contenu_Colis cc2)
                     ORDER BY l.idLot
                """,
                    (num,),
                )
                available_lots = cur.fetchall()

                # Compter les bons en attente/en_cours de ce fournisseur
                cur.execute(
                    """
                    SELECT idBon FROM Bon_reception
                     WHERE idFournisseur = (SELECT idFournisseur FROM Bon_reception WHERE idBon = %s)
                       AND statut IN ('en_attente', 'en_cours')
                     ORDER BY idBon
                """,
                    (num,),
                )
                pending_bons = [row["idbon"] for row in cur.fetchall()]
                try:
                    bon_index = pending_bons.index(num)
                except ValueError:
                    bon_index = 0
                nb_bons = max(1, len(pending_bons))

                # Round-robin : chaque bon reçoit un sous-ensemble de lots
                for i, lot in enumerate(available_lots):
                    if i % nb_bons == bon_index:
                        cur.execute(
                            "SELECT sge_add_lot_to_colis(%s, %s, %s)",
                            (colis_id, lot["idlot"], lot["quantite"]),
                        )

                conn.commit()

            return {
                "statut": "SUCCESS",
                "message": f"Chargement réceptionné - colis #{colis_id} en zone de réception",
                "colis_id": str(colis_id),
                "colis_en_attente": len(self.get_zone_reception()),
                "exceptions": [],
            }
        except psycopg2.errors.RaiseException as e:
            if conn:
                conn.rollback()
            return {"statut": "EXCEPTION_TRIGGER", "message": str(e).split("\n")[0]}
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            return {"statut": "ERROR", "message": str(e).split("\n")[0]}
        finally:
            if conn:
                release_conn(conn)

    def get_zone_reception(self):
        """Retourne les colis en attente dans la zone de réception."""
        rows = self._query("""
            SELECT c.idColis AS id, c.dateColis AS date_arrivee, c.statut,
                   cell.position AS position_recep
            FROM Colis c
            LEFT JOIN Cellule cell ON cell.idCellule = c.idCelluleZone
            WHERE c.typeColis = 'entrant'
              AND c.statut IN ('en_attente', 'en_traitement')
            ORDER BY c.dateColis ASC
        """)
        result = []
        for i, r in enumerate(rows):
            result.append(
                {
                    "id": str(r["id"]),
                    "date_arrivee": str(r["date_arrivee"]),
                    "statut": r["statut"],
                    "priorite": i + 1,
                }
            )
        return result

    def attribuer_emplacement(self, colis_id, zone_cible=None):
        """Phase B : Attribue un emplacement optimal pour un colis."""
        try:
            colis_num = int(colis_id)
        except (TypeError, ValueError):
            return {"statut": "ERROR", "message": f"Colis {colis_id} invalide"}

        colis = self._query(
            "SELECT * FROM Colis WHERE idColis = %s AND statut IN ('en_attente','en_traitement')",
            (colis_num,),
            fetchone=True,
        )
        if not colis:
            return {
                "statut": "ERROR",
                "message": f"Colis {colis_id} non trouvé en zone de réception",
            }

        lots = self._query(
            "SELECT cc.idLot FROM Contenu_Colis cc WHERE cc.idColis = %s", (colis_num,)
        )
        if not lots:
            return {
                "statut": "ERROR",
                "message": f"Colis {colis_id} ne contient aucun lot",
            }

        # Calculer la masse TOTALE de tous les lots du colis
        masse_totale_colis = self._query(
            """
            SELECT COALESCE(SUM(pm.masse * l.quantite), 0) AS masse_totale
              FROM Contenu_Colis cc
              JOIN Lot l ON l.idLot = cc.idLot
              LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
             WHERE cc.idColis = %s
        """,
            (colis_num,),
            fetchone=True,
        )
        masse_kg = (
            float(masse_totale_colis["masse_totale"]) if masse_totale_colis else 0
        )

        # Trouver les cellules avec assez de capacité résiduelle pour la masse totale
        cellules = self._query(
            """
            SELECT vo.idCellule AS idcellule, vo.zone, vo.position,
                   vo.capacite_residuelle_kg, vo.taux_occupation_pct,
                   vo.statut
              FROM v_taux_occupation vo
             WHERE vo.statut IN ('disponible', 'occupee')
               AND vo.zone IN ('E0', 'E1', 'E2', 'E3')
               AND vo.capacite_residuelle_kg >= %s
             ORDER BY vo.taux_occupation_pct DESC,
                      vo.capacite_residuelle_kg ASC
        """,
            (masse_kg,),
        )

        if not cellules:
            # Pas de cellule unique assez grande → mode multi-cellules
            cellules = self._query("""
                SELECT vo.idCellule AS idcellule, vo.zone, vo.position,
                       vo.capacite_residuelle_kg, vo.taux_occupation_pct,
                       vo.statut
                  FROM v_taux_occupation vo
                 WHERE vo.statut IN ('disponible', 'occupee')
                   AND vo.zone IN ('E0', 'E1', 'E2', 'E3')
                   AND vo.capacite_residuelle_kg > 0
                 ORDER BY vo.capacite_residuelle_kg DESC
            """)
            if not cellules:
                return {
                    "statut": "ERROR",
                    "message": "Aucune cellule disponible dans l'entrepôt",
                }

        # Préférer une cellule réellement disponible (statut = 'disponible')
        target = None
        for c in cellules:
            if c.get("statut") == "disponible":
                target = c
                break

        # Si aucune cellule libre, fallback sur la première proposée
        if target is None:
            target = cellules[0]

        cellule_cible = {
            "id": f"{target['zone']}_{target['position']}",
            "zone_id": target["zone"],
            "position": target["position"],
            "masse_max": float(target.get("capacite_residuelle_kg", 500)),
            "masse_actuelle": 0,
        }

        itineraire = [
            {
                "etape": 1,
                "direction": "Sortie Zone RECEP, Tourner vers zone " + target["zone"],
                "info": "QUAI-A",
            },
            {
                "etape": 2,
                "direction": f"Naviguer vers {target['zone']}-{target['position']}",
                "info": f"TRANSIT-{target['zone']}",
            },
            {
                "etape": 3,
                "direction": f"Accéder cellule {target['position']}",
                "info": f"{target['zone']}_{target['position']}",
            },
            {
                "etape": 4,
                "direction": "Valider Échange RFID",
                "info": "VERROUILLAGE SÉCURISÉ",
            },
        ]

        return {
            "statut": "SUCCESS",
            "colis": {"id": str(colis_num)},
            "cellule_cible": cellule_cible,
            "itineraire": itineraire,
        }

    def _resolve_cellule_id(self, cellule_id, cur):
        if "_" in str(cellule_id):
            parts = str(cellule_id).split("_", 1)
            position = parts[1] if len(parts) > 1 else cellule_id
            cur.execute(
                "SELECT idCellule FROM Cellule WHERE position = %s LIMIT 1",
                (position,),
            )
            cell_row = cur.fetchone()
            return cell_row["idcellule"] if cell_row else None
        try:
            return int(cellule_id)
        except (ValueError, TypeError):
            return None

    def _assign_lot_to_best_cell(self, lot_id, cell_num, cur):
        cur.execute(
            """
            UPDATE Inventaire_emplacement
               SET dateRetrait = CURRENT_TIMESTAMP
             WHERE idLot = %s AND dateRetrait IS NULL
        """,
            (lot_id,),
        )
        cur.execute(
            """
            SELECT vo.idCellule, vo.zone, vo.position, vo.capacite_residuelle_kg
              FROM v_taux_occupation vo
             WHERE vo.statut IN ('disponible', 'occupee')
               AND vo.zone IN ('E0', 'E1', 'E2', 'E3')
               AND vo.capacite_residuelle_kg >= (
                   SELECT COALESCE(pm.masse * l.quantite, 0)
                     FROM Lot l
                     LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
                    WHERE l.idLot = %s
               )
             ORDER BY CASE WHEN vo.idCellule = %s THEN 0 ELSE 1 END,
                      vo.capacite_residuelle_kg ASC
             LIMIT 1
        """,
            (lot_id, cell_num),
        )
        best = cur.fetchone()
        if best:
            target_cell = best["idcellule"]
            cur.execute("SELECT sge_stocker_lot(%s, %s)", (lot_id, target_cell))
            return best
        return None

    def confirmer_stockage(self, colis_id, cellule_id):
        """Confirme le stockage d'un colis dans une cellule."""
        try:
            colis_num = int(colis_id)
        except (TypeError, ValueError):
            return {"statut": "ERROR", "message": f"Colis {colis_id} invalide"}

        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cell_num = self._resolve_cellule_id(cellule_id, cur)
                if cell_num is None:
                    return {"statut": "ERROR", "message": f"Cellule {cellule_id} introuvable"}

                cur.execute(
                    "SELECT cc.idLot FROM Contenu_Colis cc WHERE cc.idColis = %s",
                    (colis_num,),
                )
                lots = cur.fetchall()

                if not lots:
                    return {
                        "statut": "ERROR",
                        "message": f"Colis {colis_num} ne contient aucun lot dans Contenu_Colis. Ajoutez d'abord des lots au colis.",
                    }

                lots_stockes = []
                cells_used = set()
                for lot_row in lots:
                    best = self._assign_lot_to_best_cell(lot_row["idlot"], cell_num, cur)
                    if best:
                        lots_stockes.append(lot_row["idlot"])
                        cells_used.add(f"{best['zone']}_{best['position']}")

                cur.execute("SELECT sge_update_statut_colis(%s, %s)", (colis_num, "traite"))

                cur.execute("SELECT idBon FROM Bon_reception WHERE idColis = %s", (colis_num,))
                bon_row = cur.fetchone()
                if bon_row:
                    cur.execute(
                        "UPDATE Bon_reception SET statut = 'traite', dateEffective = CURRENT_DATE WHERE idBon = %s",
                        (bon_row["idbon"],),
                    )

                conn.commit()

            cell_summary = ", ".join(sorted(cells_used)) if cells_used else cellule_id
            return {
                "statut": "SUCCESS",
                "message": f"{len(lots_stockes)} lot(s) stocké(s) dans {len(cells_used)} cellule(s) ({cell_summary}). Emballage récupéré.",
                "lots_stockes": lots_stockes,
            }

        except psycopg2.errors.RaiseException as e:
            if conn:
                conn.rollback()
            msg = str(e).split("\n")[0]
            return {
                "statut": "EXCEPTION_TRIGGER",
                "message": f"Erreur [SGE_inv.sql] : {msg}",
            }
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            return {"statut": "ERROR", "message": str(e).split("\n")[0]}
        finally:
            if conn:
                release_conn(conn)

    # ----------------------------------------------------------
    # EXPÉDITION (Procédé complet en 2 phases)
    # ----------------------------------------------------------

    def get_bons_expedition(self):
        """Retourne tous les bons d'expédition."""
        rows = self._query("""
            SELECT be.idBon AS id, o.nom AS destinataire_nom,
                   t.nom AS transporteur_nom,
                   be.dateAttendue AS date, be.statut, be.priorite
            FROM Bon_expedition be
            JOIN Organisation o ON o.idOrganisation = be.idDestinataire
            LEFT JOIN Organisation t ON t.idOrganisation = be.idTransporteur
            ORDER BY be.priorite ASC, be.dateAttendue ASC
        """)
        result = []
        for r in rows:
            result.append(
                {
                    "id": f"EXP-{r['id']:04d}",
                    "destinataire_nom": r["destinataire_nom"],
                    "transporteur_nom": r.get("transporteur_nom", "N/A"),
                    "date": str(r["date"]),
                    "statut": r["statut"],
                    "priorite": self._priorite_label(r["priorite"]),
                }
            )
        return result

    def get_bon_expedition(self, bon_id):
        """Retourne un bon d'expédition spécifique."""
        num = self._extract_id(bon_id)
        if num is None:
            return None
        bon = self._query(
            """
            SELECT be.idBon, o.nom AS destinataire_nom,
                   t.nom AS transporteur_nom,
                   be.dateAttendue, be.statut, be.priorite
            FROM Bon_expedition be
            JOIN Organisation o ON o.idOrganisation = be.idDestinataire
            LEFT JOIN Organisation t ON t.idOrganisation = be.idTransporteur
            WHERE be.idBon = %s
        """,
            (num,),
            fetchone=True,
        )
        if not bon:
            return None

        # BUG-01 FIX : utiliser les lots réellement liés au colis du bon
        # via Contenu_Colis, puis localiser dans Inventaire_emplacement.
        # Si aucun colis n'est encore associé au bon, on affiche le stock disponible
        # comme aperçu de ce qui peut être expédié.
        bon_colis_id = self._query(
            "SELECT idColis FROM Bon_expedition WHERE idBon = %s", (num,), fetchone=True
        )
        colis_exp = (
            bon_colis_id["idcolis"]
            if bon_colis_id and bon_colis_id.get("idcolis")
            else None
        )

        if colis_exp:
            items = self._query(
                """
                SELECT l.idProduit AS produit_id, p.nom AS produit_nom,
                       cc.quantiteColis AS quantite,
                       c.zone, c.position,
                       c.zone || '-' || c.position AS zone_cellule,
                       COALESCE(pm.longueur * pm.largeur * pm.hauteur * cc.quantiteColis / 1e6, 0) AS volume_m3
                FROM Contenu_Colis cc
                JOIN Lot l ON l.idLot = cc.idLot
                JOIN Produit p ON p.idProduit = l.idProduit
                LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
                LEFT JOIN Inventaire_emplacement ie
                       ON ie.idLot = cc.idLot AND ie.dateRetrait IS NULL
                LEFT JOIN Cellule c ON c.idCellule = ie.idCellule
                WHERE cc.idColis = %s
                ORDER BY c.zone, c.position
            """,
                (colis_exp,),
            )
        else:
            # Aucun colis préparé → aperçu du stock disponible
            items = self._query("""
                SELECT s.idProduit AS produit_id, s.produit AS produit_nom,
                       s.quantite,
                       s.zone, s.position,
                       s.zone || '-' || s.position AS zone_cellule,
                       COALESCE(pm.longueur * pm.largeur * pm.hauteur * s.quantite / 1e6, 0) AS volume_m3
                FROM v_stock_temps_reel s
                LEFT JOIN ProduitMateriel pm ON pm.idProduit = s.idProduit
                WHERE s.typeP = 'materiel'
                ORDER BY s.zone, s.position
                LIMIT 10
            """)

        # BUG-12 FIX : volume calculé depuis dimensions réelles
        volume_total = sum(float(i.get("volume_m3", 0)) for i in items)
        # Recommandation emballage dynamique selon volume
        if volume_total > 2.0:
            emballage_rec = "Euro-Palette Double"
        elif volume_total > 0.5:
            emballage_rec = "Euro-Palette Standard"
        else:
            emballage_rec = "Caisse Carton"

        return {
            "id": bon_id,
            "destinataire_nom": bon["destinataire_nom"],
            "transporteur_nom": bon.get("transporteur_nom", "N/A"),
            "date": str(bon["dateattendue"]),
            "statut": bon["statut"],
            "priorite": self._priorite_label(bon["priorite"]),
            "volume_estime": round(volume_total, 3),
            "emballage_recommande": emballage_rec,
            "items": [
                {
                    "produit_id": str(i["produit_id"]),
                    "produit_nom": i["produit_nom"],
                    "quantite": i["quantite"],
                    "zone_cellule": i.get("zone_cellule") or "Non localisé",
                    "chemin": (
                        f"COULOIR-{i.get('zone', 'X')}-DIRECT"
                        if i.get("zone")
                        else "N/A"
                    ),
                }
                for i in items
            ],
        }

    def preparer_expedition(self, bon_id):
        """Phase A : Prépare une expédition."""
        num = self._extract_id(bon_id)
        if num is None:
            return {"statut": "ERROR", "message": f"Bon {bon_id} introuvable"}

        bon = self.get_bon_expedition(bon_id)
        if not bon:
            return {"statut": "ERROR", "message": f"Bon {bon_id} introuvable"}

        # Ne modifie pas le statut en base de données pour permettre à
        # valider_expedition d'utiliser la procédure sge_tra_preparer_expedition.
        pick_list = [
            {
                "produit_id": item["produit_id"],
                "produit_nom": item["produit_nom"],
                "quantite": item["quantite"],
                "zone_cellule": item.get("zone_cellule", "N/A"),
                "chemin": item.get("chemin", "N/A"),
                "statut": (
                    "en_attente"
                    if bon["statut"] in ("planifie", "en_preparation")
                    else "pret"
                ),
            }
            for item in bon.get("items", [])
        ]

        return {
            "statut": "SUCCESS",
            "bon": bon,
            "pick_list": pick_list,
            "indisponibles": [],
            "emballage_recommande": bon.get("emballage_recommande", "Standard"),
        }

    def valider_expedition(self, bon_id):
        """Phase B : Valide l'expédition avec emballage éco-logistique."""
        num = self._extract_id(bon_id)
        if num is None:
            return {"statut": "ERROR", "message": f"Bon {bon_id} introuvable"}

        emb = self._get_emballages_dict()
        if emb["recuperes"] > 0:
            type_emballage = "Carton Récupéré (Priorité Éco-Logistique respectée)"
        elif emb["neufs"] > 0:
            type_emballage = "Carton Neuf (Stock récupéré épuisé)"
        else:
            return {
                "statut": "ERROR",
                "message": "Rupture de stock sur tous les emballages !",
            }

        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Appelle la procédure pour effectuer le déstockage et créer le colis
                cur.execute("CALL sge_tra_preparer_expedition(%s, NULL)", (num,))

                cur.execute(
                    "SELECT idColis FROM Bon_expedition WHERE idBon = %s", (num,)
                )
                colis_row = cur.fetchone()
                colis_id = colis_row["idcolis"] if colis_row else None

                conn.commit()

            return {
                "statut": "SUCCESS",
                "message": "Expédition validée et prête à partir.",
                "emballage_utilise": type_emballage,
                "colis": {"id": str(colis_id)},
            }
        except psycopg2.errors.RaiseException as e:
            if conn:
                conn.rollback()
            return {"statut": "EXCEPTION_TRIGGER", "message": str(e).split("\n")[0]}
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            return {"statut": "ERROR", "message": str(e).split("\n")[0]}
        finally:
            if conn:
                release_conn(conn)

    def get_zone_expedition(self):
        """Retourne les colis en zone d'expédition."""
        rows = self._query("""
            SELECT c.idColis AS id, c.dateColis, c.statut
            FROM Colis c
            WHERE c.typeColis = 'sortant'
              AND c.statut IN ('en_attente', 'en_traitement')
        """)
        return [{"id": str(r["id"]), "statut": r["statut"]} for r in rows]

    def confirmer_depart(self, bon_id):
        """Confirme le départ avec le transporteur."""
        num = self._extract_id(bon_id)
        if num is None:
            return {"statut": "ERROR", "message": f"Bon {bon_id} introuvable"}

        conn = get_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT idTransporteur FROM Bon_expedition WHERE idBon = %s", (num,)
                )
                row = cur.fetchone()
                id_transporteur = row.get("idtransporteur") if row else 3
                if id_transporteur is None:
                    id_transporteur = 3

                cur.execute(
                    "CALL sge_tra_confirmer_expedition(%s, %s)", (num, id_transporteur)
                )
                conn.commit()
            return {
                "statut": "SUCCESS",
                "message": f"Expédition {bon_id} confirmée - départ effectué.",
            }
        except psycopg2.errors.RaiseException as e:
            if conn:
                conn.rollback()
            return {"statut": "ERROR", "message": str(e).split("\n")[0]}
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            return {"statut": "ERROR", "message": str(e).split("\n")[0]}
        finally:
            if conn:
                release_conn(conn)

    # ----------------------------------------------------------
    # INVENTAIRE
    # ----------------------------------------------------------

    def get_inventaire(self, categorie=None, statut=None, recherche=None):
        """Retourne l'inventaire filtré."""
        rows = self._call_func("sge_req_stock_temps_reel")
        resultats = []
        # Pré-charger les masses unitaires des produits matériels
        _masses = {}
        for m in self._query("SELECT idProduit, masse FROM ProduitMateriel"):
            _masses[m["idproduit"]] = float(m["masse"])
        for r in rows:
            qte = int(r.get("quantite", 0))
            if qte == 0:
                lot_statut = "rupture"
            elif qte < 50:
                lot_statut = "stock_faible"
            else:
                lot_statut = "ok"

            cat = r.get("typep", "materiel")
            cat_label = {
                "materiel": "Matériel",
                "logiciel": "Logiciel",
                "emballage": "Emballage",
            }.get(cat, cat)

            if categorie and cat_label.lower() != categorie.lower():
                continue
            if statut and lot_statut != statut:
                continue
            if recherche:
                s = recherche.lower()
                if (
                    s not in str(r.get("idlot", "")).lower()
                    and s not in str(r.get("produit", "")).lower()
                ):
                    continue

            resultats.append(
                {
                    "lot_id": f"LOT-{r.get('idlot', 0):04d}",
                    "produit_id": str(r.get("idproduit", "")),
                    "produit_nom": r.get("produit", "Inconnu"),
                    "categorie": cat_label,
                    "quantite": qte,
                    "zone_cellule": f"{r.get('zone', '?')}/{r.get('position', '?')}",
                    "masse_totale": round(
                        _masses.get(int(r.get("idproduit", 0)), 0) * qte, 1
                    ),
                    "statut": lot_statut,
                }
            )
        return resultats

    def get_inventaire_stats(self):
        """Retourne les statistiques d'inventaire."""
        total_sku = self._query("SELECT COUNT(*) AS cnt FROM Lot", fetchone=True)
        critique = self._query(
            "SELECT COUNT(*) AS cnt FROM Lot WHERE quantite < 50", fetchone=True
        )
        total_prod = self._query("SELECT COUNT(*) AS cnt FROM Produit", fetchone=True)
        cats = self._query("SELECT DISTINCT typeP FROM Produit")
        return {
            "total_sku": total_sku["cnt"] if total_sku else 0,
            "stock_critique": critique["cnt"] if critique else 0,
            "total_produits": total_prod["cnt"] if total_prod else 0,
            "categories": [c["typep"] for c in cats],
        }

    # ----------------------------------------------------------
    # RAPPORTS & EXCEPTIONS
    # ----------------------------------------------------------

    def get_rapports_exception(self, type_filtre=None, statut_filtre=None):
        """Retourne les rapports d'exception via la vue v_rapports_exception."""
        rows = self._query("""
            SELECT idRapport AS id, typeRapport AS type,
                   description AS message, dateRapport AS timestamp,
                   COALESCE(agent, 'SYSTEM') AS utilisateur,
                   COALESCE('BON-' || COALESCE(idBonReception::TEXT, idBonExpedition::TEXT), 'N/A') AS artefact_lie
            FROM v_rapports_exception
        """)

        result = []
        for r in rows:
            msg = r.get("message", "").lower()
            if (
                "refus" in msg
                or "rupture" in msg
                or "masse" in msg
                or "depassee" in msg
            ):
                s = "critique"
            elif "ecart" in msg or "manquant" in msg:
                s = "en_attente"
            else:
                s = "enregistre"

            if type_filtre and r.get("type", "") != type_filtre:
                continue
            if statut_filtre and s != statut_filtre:
                continue

            result.append(
                {
                    "id": f"EXC-{r['id']:03d}",
                    "type": r.get("type", "autre"),
                    "message": r.get("message", ""),
                    "timestamp": str(r.get("timestamp", "")),
                    "utilisateur": r.get("utilisateur", "SYSTEM"),
                    "statut": s,
                    "artefact_lie": r.get("artefact_lie", "N/A"),
                    "source": r.get("artefact_lie", "N/A"),
                }
            )
        return result

    def get_performance_kpis(self):
        """Retourne les métriques de performance."""
        zones = self._call_func("sge_req_taux_occupation_par_zone")
        masse_total = sum(float(z.get("masse_totale_kg", 0) or 0) for z in zones)
        cap_total = sum(float(z.get("capacite_totale_kg", 0) or 0) for z in zones)
        occ_pct = round(masse_total / cap_total * 100, 1) if cap_total else 0

        rec = self._query(
            "SELECT COUNT(*) AS cnt FROM Bon_reception WHERE statut = 'en_attente'",
            fetchone=True,
        )
        exp = self._query(
            "SELECT COUNT(*) AS cnt FROM Bon_expedition WHERE statut = 'en_attente'",
            fetchone=True,
        )

        return {
            "occupation_globale_pct": occ_pct,
            "occupation_kg": f"{masse_total:.0f} / {cap_total:.0f} kg",
            "receptions_jour": rec["cnt"] if rec else 0,
            "receptions_tendance": f"+{rec['cnt']}%" if rec else "+0%",
            "sorties_jour": exp["cnt"] if exp else 0,
            "sorties_tendance": f"-{exp['cnt']}%" if exp else "-0%",
            "cible_efficacite": 950,
            "fenetre_critique": "14:00 - 16:00",
        }

    def get_stock_emballage(self):
        """Retourne les quantités d'emballages neufs et récupérés depuis la vraie DB (BUG-09 FIX)."""
        rows = self._call_func("sge_req_stock_emballage")
        neufs = sum(int(r.get("quantite_neuf") or 0) for r in rows)
        recuperes = sum(int(r.get("quantite_recup") or 0) for r in rows)
        return {"neufs": neufs, "recuperes": recuperes, "detail": rows}

    # ----------------------------------------------------------
    # MÉTHODES UTILITAIRES PRIVÉES
    # ----------------------------------------------------------

    def _ajouter_exception(self, type_exc, message, source, utilisateur):
        """Ajoute un rapport d'exception."""
        ind_id = None
        if utilisateur and utilisateur != "SYSTEM":
            ind = self._query(
                "SELECT idIndividu FROM Individu WHERE nom ILIKE %s LIMIT 1",
                (f"%{utilisateur}%",),
                fetchone=True,
            )
            if ind:
                ind_id = ind["idindividu"]

        types_map = {
            "SURCHARGE_CELLULE": "masse_depassee",
            "AUCUN_EMPLACEMENT": "ecart_stockage",
            "RUPTURE_STOCK": "ecart_expedition",
            "RUPTURE_EMBALLAGE": "ecart_chargement",
            "ecart_reception": "ecart_reception",
            "ecart_stockage": "ecart_stockage",
            "ecart_expedition": "ecart_expedition",
            "ecart_chargement": "ecart_chargement",
            "masse_depassee": "masse_depassee",
        }
        pg_type = types_map.get(type_exc, "autre")

        try:
            self._execute(
                "SELECT sge_insert_rapport_exception(%s, %s, NULL, NULL, %s)",
                (pg_type, message, ind_id),
            )
        except psycopg2.Error:
            pass

    def _get_emballages_dict(self):
        """Retourne le stock d'emballages sous forme dict compatible."""
        rows = self._call_func("sge_req_stock_emballage")
        neufs = sum(int(r.get("quantite_neuf", 0)) for r in rows)
        recup = sum(int(r.get("quantite_recup", 0)) for r in rows)
        return {"neufs": neufs, "recuperes": recup}

    @property
    def emballages(self):
        """Propriété pour accéder au stock d'emballages."""
        return self._get_emballages_dict()

    @property
    def cellules(self):
        """Propriété compatible — retourne les cellules depuis PostgreSQL."""
        rows = self._query("SELECT * FROM v_taux_occupation ORDER BY zone, position")
        result = {}
        for r in rows:
            cell_id = f"{r['zone']}_{r['position']}"
            result[cell_id] = {
                "id": cell_id,
                "zone_id": r["zone"],
                "position": r["position"],
                "masse_max": float(r["massemaximale"]),
                "masse_actuelle": float(r["masse_actuelle_kg"]),
                "statut": (
                    "Libre"
                    if r["statut"] == "disponible"
                    else (
                        "Occupé"
                        if float(r.get("taux_occupation_pct", 0) or 0) > 80
                        else "Partiel"
                    )
                ),
                "lot_id": None,
                "produit_nom": None,
            }
        return result

    @property
    def lots(self):
        """Propriété compatible — retourne les lots depuis PostgreSQL."""
        rows = self._query("""
            SELECT l.idLot, l.idProduit AS produit_id, l.quantite, l.origine, l.dateEntree
            FROM Lot l ORDER BY l.idLot
        """)
        result = {}
        for r in rows:
            lot_id = f"LOT-{r['idlot']:04d}"
            result[lot_id] = {
                "produit_id": str(r["produit_id"]),
                "quantite": r["quantite"],
                "origine": r["origine"],
                "date_creation": str(r["dateentree"]),
            }
        return result

    @property
    def produits(self):
        """Propriété compatible — retourne les produits depuis PostgreSQL."""
        rows = self._query("""
            SELECT p.idProduit, p.nom, p.typeP, p.marque, p.modele,
                   COALESCE(pm.masse, 0) AS masse_unitaire
            FROM Produit p
            LEFT JOIN ProduitMateriel pm ON pm.idProduit = p.idProduit
        """)
        result = {}
        for r in rows:
            result[str(r["idproduit"])] = {
                "nom": r["nom"],
                "categorie": r["typep"],
                "marque": r.get("marque", ""),
                "modele": r.get("modele", ""),
                "masse_unitaire": float(r["masse_unitaire"]),
            }
        return result

    @property
    def transactions(self):
        """BUG-09 FIX : construit la liste des transactions depuis les vraies tables."""
        rows = self._query("""
            SELECT 'reception' AS type,
                   br.idBon::TEXT AS reference,
                   o.nom AS tiers,
                   br.dateEffective::TEXT AS timestamp,
                   br.statut
            FROM Bon_reception br
            JOIN Organisation o ON o.idOrganisation = br.idFournisseur
            WHERE br.statut IN ('traite', 'en_cours')

            UNION ALL

            SELECT 'expedition' AS type,
                   be.idBon::TEXT AS reference,
                   o.nom AS tiers,
                   be.dateEffective::TEXT AS timestamp,
                   be.statut
            FROM Bon_expedition be
            JOIN Organisation o ON o.idOrganisation = be.idDestinataire
            WHERE be.statut IN ('expedie', 'en_cours')

            UNION ALL

            SELECT 'stockage' AS type,
                   ie.idLot::TEXT AS reference,
                   c.zone || '-' || c.position AS tiers,
                   ie.dateDepot::TEXT AS timestamp,
                   CASE WHEN ie.dateRetrait IS NULL THEN 'en_place' ELSE 'retire' END AS statut
            FROM Inventaire_emplacement ie
            JOIN Cellule c ON c.idCellule = ie.idCellule
            ORDER BY timestamp DESC NULLS LAST
            LIMIT 50
        """)
        return [
            {
                "type": r["type"],
                "reference": r["reference"],
                "tiers": r["tiers"],
                "timestamp": r["timestamp"] or "",
                "statut": r["statut"],
            }
            for r in rows
        ]

    @staticmethod
    def _priorite_label(p):
        """Convertit une priorité numérique en label."""
        return {1: "haute", 2: "normale", 3: "normale", 4: "basse", 5: "basse"}.get(
            p, "normale"
        )

    @staticmethod
    def _extract_id(bon_id):
        """Extrait le numérique d'un ID comme REC-2024-001 ou EXP-0001."""
        if bon_id is None:
            return None
        s = str(bon_id)
        parts = s.replace("-", " ").split()
        for part in reversed(parts):
            try:
                return int(part)
            except ValueError:
                continue
        try:
            return int(s)
        except ValueError:
            return None

    # ----------------------------------------------------------
    # REQUÊTES AVANCÉES (Phase 1 — sge_req_*)
    # ----------------------------------------------------------

    def get_stock_par_produit(self, produit_id):
        """Stock détaillé pour un produit via sge_req_stock_par_produit."""
        return self._call_func("sge_req_stock_par_produit", (int(produit_id),))

    def get_mouvements_lot(self, lot_id, debut=None, fin=None):
        """Historique des mouvements d'un lot via sge_req_mouvements_lot."""
        params = [int(lot_id)]
        if debut:
            params.append(debut)
        if fin:
            params.append(fin)
        return self._call_func("sge_req_mouvements_lot", params)

    def get_inventaire_produit(self):
        """Inventaire agrégé par produit via sge_req_inventaire_produit."""
        return self._call_func("sge_req_inventaire_produit")

    def get_cellules_disponibles(self):
        """Cellules disponibles via la vue v_cellules_disponibles."""
        return self._query("SELECT * FROM v_cellules_disponibles")

    def get_vue_bons_reception_attente(self):
        """Bons de réception en attente via la vue v_bons_reception_attente."""
        return self._query("SELECT * FROM v_bons_reception_attente")

    def get_vue_bons_expedition_attente(self):
        """Bons d'expédition en attente via la vue v_bons_expedition_attente."""
        return self._query("SELECT * FROM v_bons_expedition_attente")

    def get_inventaire_produit_materialise(self):
        """Inventaire agrégé par produit via la vue matérialisée mv_inventaire_produit."""
        return self._query("SELECT * FROM mv_inventaire_produit ORDER BY nom")

    def get_lots_by_produit(self, produit_id):
        """Lots d'un produit via sge_req_lots_by_produit."""
        return self._call_func("sge_req_lots_by_produit", (int(produit_id),))

    def get_cellules_disponibles_pour_lot(self, lot_id):
        """Cellules avec capacité suffisante via sge_req_cellules_disponibles_pour_lot."""
        return self._call_func("sge_req_cellules_disponibles_pour_lot", (int(lot_id),))

    def get_itineraire_destockage(self, colis_id):
        """Itinéraire de déstockage via sge_req_itineraire_destockage."""
        return self._call_func("sge_req_itineraire_destockage", (int(colis_id),))

    def get_bons_reception_attente(self):
        """Bons de réception en attente via sge_req_bons_reception_attente."""
        return self._call_func("sge_req_bons_reception_attente")

    def get_bons_expedition_attente(self):
        """Bons d'expédition en attente via sge_req_bons_expedition_attente."""
        return self._call_func("sge_req_bons_expedition_attente")

    def verifier_disponibilite_colis(self, colis_id):
        """Vérifie la disponibilité d'un colis via sge_req_verifier_disponibilite_colis."""
        return self._call_func("sge_req_verifier_disponibilite_colis", (int(colis_id),))

    def get_rapports_exception_periode(self, debut=None, fin=None, type_exc=None):
        """Rapports d'exception sur une période via sge_req_rapports_exception."""
        params = []
        if debut:
            params.append(debut)
        if fin:
            params.append(fin)
        if type_exc:
            params.append(type_exc)
        return self._call_func("sge_req_rapports_exception", params if params else None)

    def get_perf_reception(self, debut=None, fin=None):
        """Performance réception via sge_req_perf_reception."""
        params = []
        if debut:
            params.append(debut)
        if fin:
            params.append(fin)
        return self._call_func("sge_req_perf_reception", params if params else None)

    def get_perf_expedition(self, debut=None, fin=None):
        """Performance expédition via sge_req_perf_expedition."""
        params = []
        if debut:
            params.append(debut)
        if fin:
            params.append(fin)
        return self._call_func("sge_req_perf_expedition", params if params else None)

    def get_rapport_stock_par_zone(self):
        """Rapport stock par zone via sge_req_rapport_stock_par_zone."""
        return self._call_func("sge_req_rapport_stock_par_zone")

    # ----------------------------------------------------------
    # CRUD ADMIN — Organisation (Phase 2)
    # ----------------------------------------------------------

    def get_organisations(self):
        """Liste toutes les organisations."""
        return self._query("SELECT * FROM Organisation ORDER BY idOrganisation")

    def get_organisation(self, org_id):
        """Détail d'une organisation via sge_get_organisation."""
        rows = self._call_func("sge_get_organisation", (int(org_id),))
        return rows[0] if rows else None

    def insert_organisation(self, nom, type_org, adresse=None, telephone=None):
        """Crée une organisation via sge_insert_organisation."""
        result = self._execute(
            "SELECT sge_insert_organisation(%s, %s, %s, %s)",
            (nom, type_org, adresse, telephone),
        )
        return result

    def update_organisation(
        self, org_id, nom=None, type_org=None, adresse=None, telephone=None
    ):
        """Modifie une organisation via sge_update_organisation."""
        self._execute(
            "SELECT sge_update_organisation(%s, %s, %s, %s, %s)",
            (int(org_id), nom, type_org, adresse, telephone),
        )

    def delete_organisation(self, org_id):
        """Supprime une organisation via sge_delete_organisation."""
        self._execute("SELECT sge_delete_organisation(%s)", (int(org_id),))

    # ----------------------------------------------------------
    # CRUD ADMIN — Individu (Phase 2)
    # ----------------------------------------------------------

    def get_individus(self):
        """Liste tous les individus."""
        return self._query("SELECT * FROM Individu ORDER BY idIndividu")

    def insert_individu(self, nom, adresse=None, telephone=None, email=None):
        """Crée un individu via sge_insert_individu."""
        return self._execute(
            "SELECT sge_insert_individu(%s, %s, %s, %s)",
            (nom, adresse, telephone, email),
        )

    def update_individu(
        self, ind_id, nom=None, adresse=None, telephone=None, email=None
    ):
        """Modifie un individu via sge_update_individu."""
        self._execute(
            "SELECT sge_update_individu(%s, %s, %s, %s, %s)",
            (int(ind_id), nom, adresse, telephone, email),
        )

    def delete_individu(self, ind_id):
        """Supprime un individu via sge_delete_individu."""
        self._execute("SELECT sge_delete_individu(%s)", (int(ind_id),))

    # ----------------------------------------------------------
    # CRUD ADMIN — Répertoire (Phase 2)
    # ----------------------------------------------------------

    def get_repertoire(self):
        """Liste les affectations du répertoire (table Repertoire)."""
        return self._query("""
            SELECT r.idOrganisation, o.nom AS organisation,
                   r.idIndividu, i.nom AS individu,
                   r.role, r.dateDebut, r.dateFin
            FROM Repertoire r
            JOIN Organisation o ON o.idOrganisation = r.idOrganisation
            JOIN Individu i ON i.idIndividu = r.idIndividu
            ORDER BY r.dateDebut DESC
        """)

    def insert_repertoire(self, id_org, id_ind, role, date_debut, date_fin=None):
        """Crée une affectation via sge_insert_repertoire."""
        self._execute(
            "SELECT sge_insert_repertoire(%s, %s, %s, %s, %s)",
            (int(id_org), int(id_ind), role, date_debut, date_fin),
        )

    def close_repertoire(self, id_org, id_ind, role, date_fin=None):
        """Clôture une affectation via sge_close_repertoire."""
        params = [int(id_org), int(id_ind), role]
        if date_fin:
            params.append(date_fin)
        self._execute(
            f"SELECT sge_close_repertoire({', '.join(['%s'] * len(params))})", params
        )

    # ----------------------------------------------------------
    # CRUD GESTION — Produit (Phase 3)
    # ----------------------------------------------------------

    def get_produits_complet(self):
        """Liste tous les produits avec détails matériel/logiciel."""
        return self._query("""
            SELECT p.*, pm.longueur, pm.largeur, pm.hauteur, pm.masse,
                   pl.version, pl.licence, pl.supportExpire,
                   o.nom AS fournisseur_nom
            FROM Produit p
            LEFT JOIN ProduitMateriel pm ON pm.idProduit = p.idProduit
            LEFT JOIN ProduitLogiciel pl ON pl.idProduit = p.idProduit
            LEFT JOIN Organisation o ON o.idOrganisation = p.idFournisseur
            ORDER BY p.idProduit
        """)

    def insert_produit(
        self,
        nom,
        type_p,
        description=None,
        marque=None,
        modele=None,
        id_fournisseur=None,
    ):
        """Crée un produit via sge_insert_produit. Retourne l'ID."""
        result = self._execute(
            "SELECT sge_insert_produit(%s, %s, %s, %s, %s, %s)",
            (nom, type_p, description, marque, modele, id_fournisseur),
        )
        return result

    def insert_produit_materiel(self, id_produit, longueur, largeur, hauteur, masse):
        """Ajoute les attributs matériels via sge_insert_produit_materiel."""
        self._execute(
            "SELECT sge_insert_produit_materiel(%s, %s, %s, %s, %s)",
            (int(id_produit), longueur, largeur, hauteur, masse),
        )

    def insert_produit_logiciel(
        self, id_produit, version=None, licence=None, support_expire=None
    ):
        """Ajoute les attributs logiciels via sge_insert_produit_logiciel."""
        self._execute(
            "SELECT sge_insert_produit_logiciel(%s, %s, %s, %s)",
            (int(id_produit), version, licence, support_expire),
        )

    def update_produit(
        self, id_produit, nom=None, description=None, marque=None, modele=None
    ):
        """Modifie un produit via sge_update_produit."""
        self._execute(
            "SELECT sge_update_produit(%s, %s, %s, %s, %s)",
            (int(id_produit), nom, description, marque, modele),
        )

    def delete_produit(self, id_produit):
        """Supprime un produit via sge_delete_produit."""
        self._execute("SELECT sge_delete_produit(%s)", (int(id_produit),))

    # ----------------------------------------------------------
    # CRUD GESTION — Lot (Phase 3)
    # ----------------------------------------------------------

    def get_lots_complet(self):
        """Liste tous les lots avec produit associé."""
        return self._query("""
            SELECT l.*, p.nom AS produit_nom, p.typeP
            FROM Lot l
            JOIN Produit p ON p.idProduit = l.idProduit
            ORDER BY l.idLot
        """)

    def insert_lot(self, id_produit, quantite, origine, date_entree=None):
        """Crée un lot via sge_insert_lot."""
        params = [int(id_produit), int(quantite), origine]
        if date_entree:
            params.append(date_entree)
        result = self._execute(
            f"SELECT sge_insert_lot({', '.join(['%s'] * len(params))})", params
        )
        return result

    def update_lot_quantite(self, id_lot, quantite):
        """Modifie la quantité d'un lot via sge_update_lot_quantite."""
        self._execute(
            "SELECT sge_update_lot_quantite(%s, %s)", (int(id_lot), int(quantite))
        )

    def delete_lot(self, id_lot):
        """Supprime un lot via sge_delete_lot."""
        self._execute("SELECT sge_delete_lot(%s)", (int(id_lot),))

    def retirer_lot(self, id_lot, id_cellule):
        """Retire un lot d'une cellule via sge_retirer_lot."""
        self._execute("SELECT sge_retirer_lot(%s, %s)", (int(id_lot), int(id_cellule)))

    # ----------------------------------------------------------
    # CRUD GESTION — Cellule (Phase 3)
    # ----------------------------------------------------------

    def get_cellules_complet(self):
        """Liste toutes les cellules."""
        return self._query("SELECT * FROM Cellule ORDER BY zone, position")

    def insert_cellule(self, longueur, largeur, hauteur, masse_max, zone, position):
        """Crée une cellule via sge_insert_cellule."""
        return self._execute(
            "SELECT sge_insert_cellule(%s, %s, %s, %s, %s, %s)",
            (longueur, largeur, hauteur, masse_max, zone, position),
        )

    def update_cellule_statut(self, id_cellule, statut):
        """Change le statut d'une cellule via sge_update_cellule_statut."""
        self._execute(
            "SELECT sge_update_cellule_statut(%s, %s)", (int(id_cellule), statut)
        )

    # ----------------------------------------------------------
    # CRUD — Bons (Phase 4)
    # ----------------------------------------------------------

    def insert_bon_reception(self, id_fournisseur, date_attendue, priorite=3):
        """Crée un bon de réception via sge_insert_bon_reception."""
        return self._execute(
            "SELECT sge_insert_bon_reception(%s, %s::DATE, %s::SMALLINT)",
            (int(id_fournisseur), str(date_attendue), int(priorite)),
        )

    def insert_bon_expedition(
        self, id_destinataire, date_attendue, priorite=3, id_transporteur=None
    ):
        """Crée un bon d'expédition via sge_insert_bon_expedition."""
        return self._execute(
            "SELECT sge_insert_bon_expedition(%s, %s::DATE, %s::SMALLINT, %s)",
            (
                int(id_destinataire),
                str(date_attendue),
                int(priorite),
                int(id_transporteur) if id_transporteur else None,
            ),
        )

    # ----------------------------------------------------------
    # Wrappers CRUD restants (utilisés indirectement par sge_tra_*)
    # ----------------------------------------------------------

    def insert_colis(self, type_colis, id_cellule_zone=None):
        """Crée un colis via sge_insert_colis."""
        return self._execute(
            "SELECT sge_insert_colis(%s, %s)", (type_colis, id_cellule_zone)
        )

    def update_statut_bon_reception(self, id_bon, statut, id_colis=None):
        """Met à jour le statut d'un bon de réception via sge_update_statut_bon_reception."""
        self._execute(
            "SELECT sge_update_statut_bon_reception(%s, %s, %s)",
            (int(id_bon), statut, id_colis),
        )

    def update_statut_bon_expedition(
        self, id_bon, statut, id_colis=None, id_transporteur=None
    ):
        """Met à jour le statut d'un bon d'expédition via sge_update_statut_bon_expedition."""
        self._execute(
            "SELECT sge_update_statut_bon_expedition(%s, %s, %s, %s)",
            (int(id_bon), statut, id_colis, id_transporteur),
        )
