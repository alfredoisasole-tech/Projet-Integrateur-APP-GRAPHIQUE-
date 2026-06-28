import unittest
from db.sge_database import SGEDatabase


class TestValidation(unittest.TestCase):
    def test_extract_id_valide(self):
        # Vérifie que la fonction utilitaire d'extraction d'ID fonctionne
        # avec différents formats attendus dans WMS-CLAM-PRO

        # Test format classique
        self.assertEqual(SGEDatabase._extract_id("REC-0012"), 12)
        self.assertEqual(SGEDatabase._extract_id("EXP-0150"), 150)

        # Test format numérique pur
        self.assertEqual(SGEDatabase._extract_id("42"), 42)
        self.assertEqual(SGEDatabase._extract_id(42), 42)

    def test_extract_id_invalide(self):
        # Doit retourner None pour les formats invalides
        self.assertIsNone(SGEDatabase._extract_id("INVALID"))
        self.assertIsNone(SGEDatabase._extract_id(None))
        self.assertIsNone(SGEDatabase._extract_id("REC-ABC"))

    def test_priorite_label(self):
        # Vérification de la conversion du niveau de priorité
        self.assertEqual(SGEDatabase._priorite_label(1), "haute")
        self.assertEqual(SGEDatabase._priorite_label(2), "normale")
        self.assertEqual(SGEDatabase._priorite_label(3), "normale")
        self.assertEqual(SGEDatabase._priorite_label(4), "basse")
        self.assertEqual(SGEDatabase._priorite_label(99), "normale")


if __name__ == "__main__":
    unittest.main()
