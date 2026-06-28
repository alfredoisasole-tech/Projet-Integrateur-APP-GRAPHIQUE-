"""
Service d'expédition — Procédé d'expédition complet (2 phases).

Phase A : Préparation
  1. Sélection bon → vérification dispo → itinéraire picking → emballage → zone expédition
Phase B : Expédition
  1. Arrivée transporteur → vérification → départ

Logique éco-logistique (section 2.2 du mandat) :
  → Le matériel d'emballage récupéré est PRIORITAIRE sur le matériel neuf.
"""


class ExpeditionService:
    """Logique métier pour l'expédition et le picking."""

    def __init__(self, db=None):
        if db is None:
            raise ValueError("Une instance de base de données est requise.")
        self.db = db

    def get_bons_expedition(self):
        """Liste des bons d'expédition."""
        return self.db.get_bons_expedition()

    def get_bon_expedition(self, bon_id):
        """Détail d'un bon d'expédition."""
        return self.db.get_bon_expedition(bon_id)

    def preparer_expedition(self, bon_id):
        """Phase A : Prépare une expédition complète."""
        return self.db.preparer_expedition(bon_id)

    def get_pick_list(self, bon_id):
        """Retourne la liste de picking pour un bon."""
        bon = self.db.get_bon_expedition(bon_id)
        if not bon:
            return []
        return [
            {
                "produit_id": item["produit_id"],
                "produit_nom": item["produit_nom"],
                "quantite": item["quantite"],
                "zone_cellule": item.get("zone_cellule", "N/A"),
                "chemin_optimal": item.get("chemin", "N/A"),
                "statut": (
                    "en_attente"
                    if bon["statut"] in ("planifie", "en_preparation")
                    else "pret"
                ),
            }
            for item in bon["items"]
        ]

    def calculer_itineraire_picking(self, bon_id):
        """Calcule le chemin optimal pour le picking."""
        bon = self.db.get_bon_expedition(bon_id)
        if not bon:
            return None

        # Agréger les zones à visiter
        zones_a_visiter = []
        for item in bon["items"]:
            chemin = item.get("chemin", "DIRECT")
            zones_a_visiter.append(
                {
                    "produit": item["produit_nom"],
                    "cellule": item.get("zone_cellule", "N/A"),
                    "chemin": chemin,
                }
            )

        nb_zones = max(1, len(zones_a_visiter))
        return {
            "bon_id": bon_id,
            "zones": zones_a_visiter,
            "longueur_totale_m": nb_zones * nb_zones * 15,
            "temps_estime_min": nb_zones * 5,
            "depart": "Zone Réception",
            "sortie": "Zone Expédition",
        }

    def valider_expedition(self, bon_id):
        """Phase B : Valide l'expédition avec logique éco-emballage."""
        return self.db.valider_expedition(bon_id)

    def confirmer_depart(self, bon_id):
        """Confirme le départ avec le transporteur."""
        return self.db.confirmer_depart(bon_id)

    def get_zone_expedition(self):
        """Colis en zone d'expédition (attente départ)."""
        return self.db.get_zone_expedition()

    def get_recommandation_emballage(self, bon_id):
        """Recommandation de type d'emballage selon poids/volume."""
        bon = self.db.get_bon_expedition(bon_id)
        if not bon:
            return "Standard"
        return bon.get("emballage_recommande", "Euro-Palette Standard")

    def get_stock_emballages(self):
        """État du stock d'emballages depuis la base."""
        if hasattr(self.db, "get_stock_emballage"):
            return self.db.get_stock_emballage()
        return {"neufs": 0, "recuperes": 0}
