import unittest
from unittest.mock import MagicMock
from services.stockage_service import StockageService
from services.expedition_service import ExpeditionService
from services.rapport_service import RapportService


class TestStockageService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.service = StockageService(self.mock_db)

    def test_selectionner_colis_prioritaire(self):
        # Mock de get_zone_reception qui retourne une liste de colis avec des priorités
        self.mock_db.get_zone_reception.return_value = [
            {"id": "1", "priorite": 2},
            {"id": "2", "priorite": 1},
            {"id": "3", "priorite": 3},
        ]

        colis = self.service.selectionner_colis_prioritaire()

        # Le colis avec la priorité la plus basse (valeur 1, la plus haute en logique FIFO/Urgence)
        # selon le code lambda c: c.get("priorite", 999) doit être retourné
        self.assertEqual(colis["id"], "2")
        self.mock_db.get_zone_reception.assert_called_once()

    def test_selectionner_colis_prioritaire_vide(self):
        self.mock_db.get_zone_reception.return_value = []
        colis = self.service.selectionner_colis_prioritaire()
        self.assertIsNone(colis)

    def test_attribuer_emplacement(self):
        self.mock_db.attribuer_emplacement.return_value = {
            "statut": "SUCCESS",
            "cellule_cible": {"id": "E0_A-01-01"},
        }
        result = self.service.attribuer_emplacement(123)
        self.assertEqual(result["statut"], "SUCCESS")
        self.assertEqual(result["cellule_cible"]["id"], "E0_A-01-01")


class TestRapportService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.service = RapportService(self.mock_db)

    def test_get_rapport_emballage(self):
        self.mock_db.get_stock_emballage.return_value = {
            "neufs": 100,
            "recuperes": 50,
            "detail": [],
        }

        rapport = self.service.get_rapport_emballage()
        self.assertEqual(rapport["total"], 150)
        self.assertEqual(rapport["taux_recuperation"], 33.3)  # 50 / 150 = 33.3%

    def test_get_rapport_operations(self):
        # On simule l'attribut transactions de la DB
        self.mock_db.transactions = [
            {"type": "reception"},
            {"type": "reception"},
            {"type": "stockage"},
        ]

        rapport = self.service.get_rapport_operations()

        self.assertEqual(rapport["total_transactions"], 3)
        self.assertEqual(rapport["receptions"], 2)
        self.assertEqual(rapport["stockages"], 1)


if __name__ == "__main__":
    unittest.main()
