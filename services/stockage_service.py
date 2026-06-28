"""
Service de stockage — Procédé de réception complet (2 phases).

Phase A : Réception immédiate
  1. Arrivée chargement → vérification bons → zone de réception
Phase B : Stockage
  1. Sélection colis → attribution emplacement → itinéraire → stockage → emballage
"""


class StockageService:
    """Logique métier pour la réception et le stockage."""

    def __init__(self, db=None):
        if db is None:
            raise ValueError("Une instance de base de données est requise.")
        self.db = db

    def recevoir_chargement(self, bon_reception_id):
        """Phase A : Réceptionner un chargement."""
        return self.db.recevoir_chargement(bon_reception_id)

    def get_colis_en_attente(self):
        """Liste des colis en zone de réception (file d'attente)."""
        return self.db.get_zone_reception()

    def selectionner_colis_prioritaire(self):
        """Sélectionne le colis de plus haute priorité (FIFO)."""
        colis = self.db.get_zone_reception()
        if not colis:
            return None
        return sorted(colis, key=lambda c: c.get("priorite", 999))[0]

    def attribuer_emplacement(self, colis_id, zone_cible=None):
        """Calcule l'emplacement optimal et l'itinéraire."""
        return self.db.attribuer_emplacement(colis_id, zone_cible)

    def confirmer_stockage(self, colis_id, cellule_id):
        """Confirme le stockage avec vérification du trigger de masse."""
        return self.db.confirmer_stockage(colis_id, cellule_id)

    def get_bons_reception(self):
        """Liste des bons de réception."""
        return self.db.get_bons_reception()

    def get_bon_reception(self, bon_id):
        """Détail d'un bon de réception."""
        return self.db.get_bon_reception(bon_id)
