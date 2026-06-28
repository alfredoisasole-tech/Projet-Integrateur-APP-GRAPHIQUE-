import unittest
from unittest.mock import MagicMock
from api.server import create_api


class TestAPI(unittest.TestCase):
    def setUp(self):
        # Création d'un mock de la BD
        self.mock_db = MagicMock()

        # Le nom de la classe mockée doit être configuré pour que server.py détecte "mock"
        self.mock_db.__class__.__name__ = "MockDatabase"

        # Création de l'application Flask
        self.app = create_api(self.mock_db)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        # L'endpoint /api/health doit retourner 200 OK
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["statut"], "OK")
        self.assertEqual(data["service"], "WMS-CLAM-PRO API")
        self.assertEqual(data["db_mode"], "mock")

    def test_dashboard_endpoint(self):
        # Configuration du mock pour le dashboard
        self.mock_db.get_dashboard_data.return_value = {
            "occupation_globale_pct": 75.5,
            "total_cellules": 100,
            "zones": {},
        }

        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["statut"], "SUCCESS")
        self.assertEqual(data["occupation_globale_pct"], 75.5)
        self.mock_db.get_dashboard_data.assert_called_once()

    def test_inventaire_endpoint(self):
        self.mock_db.get_inventaire.return_value = [
            {"lot_id": "LOT-0001", "produit_nom": "Boîte", "quantite": 50}
        ]

        response = self.client.get("/api/inventaire")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["statut"], "SUCCESS")
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["inventaire"]), 1)
        self.assertEqual(data["inventaire"][0]["produit_nom"], "Boîte")


if __name__ == "__main__":
    unittest.main()
