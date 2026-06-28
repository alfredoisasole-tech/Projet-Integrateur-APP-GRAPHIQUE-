"""
Service de rapports — Génération de rapports et KPIs.

Fonctionnalité 4 du mandat : rapports détaillés sur les performances
de l'entrepôt (stocks, espace de stockage, opérations).
"""


class RapportService:
    """Logique métier pour les rapports et les métriques de performance."""

    def __init__(self, db=None):
        if db is None:
            raise ValueError("Une instance de base de données est requise.")
        self.db = db

    def get_exceptions(self, type_filtre=None, statut_filtre=None):
        """Journal des rapports d'exception."""
        return self.db.get_rapports_exception(type_filtre, statut_filtre)

    def get_performance_kpis(self):
        """Métriques de performance globales."""
        return self.db.get_performance_kpis()

    def get_rapport_stocks(self):
        """Rapport détaillé sur l'état des stocks par zone."""
        zones = self.db.get_zones()
        rapport = []
        for zone_id, zone in zones.items():
            cellules = zone.get("cellules_detail", [])
            total_masse = sum(c["masse_actuelle"] for c in cellules)
            total_max = sum(c["masse_max"] for c in cellules)
            occupees = sum(1 for c in cellules if c["statut"] != "Libre")

            rapport.append(
                {
                    "zone_id": zone_id,
                    "nom": zone["nom"],
                    "cellules_total": len(cellules),
                    "cellules_occupees": occupees,
                    "occupation_pct": zone.get("occupation_pct", 0),
                    "masse_totale_kg": round(total_masse, 1),
                    "masse_max_kg": round(total_max, 1),
                    "utilisation_masse_pct": (
                        round(total_masse / total_max * 100, 1) if total_max else 0
                    ),
                }
            )
        return rapport

    def get_rapport_operations(self):
        """Rapport sur les opérations récentes — BUG-09 FIX : utilise self.db.transactions (vraie DB)."""
        transactions = self.db.transactions  # maintenant depuis PostgreSQL
        # Compter les types présents
        types_count = {}
        for t in transactions:
            t_type = t.get("type", "autre")
            types_count[t_type] = types_count.get(t_type, 0) + 1

        return {
            "total_transactions": len(transactions),
            "receptions": types_count.get("reception", 0),
            "stockages": types_count.get("stockage", 0),
            "preparations": types_count.get("preparation", 0),
            "expeditions": types_count.get("expedition", 0),
            "departs": types_count.get("depart", 0),
            "dernieres_transactions": sorted(
                transactions, key=lambda t: t.get("timestamp") or "", reverse=True
            )[:20],
        }

    def get_rapport_emballage(self):
        """Rapport sur le stock d'emballages — depuis la vraie base."""
        emb = (
            self.db.get_stock_emballage()
            if hasattr(self.db, "get_stock_emballage")
            else {}
        )
        neufs = emb.get("neufs", 0)
        recuperes = emb.get("recuperes", 0)
        total = neufs + recuperes
        return {
            "neufs": neufs,
            "recuperes": recuperes,
            "total": total,
            "taux_recuperation": round(recuperes / max(1, total) * 100, 1),
        }
