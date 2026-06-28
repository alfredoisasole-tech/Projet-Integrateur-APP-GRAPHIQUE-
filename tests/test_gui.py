import unittest
import tkinter as tk
from gui.components.widgets import StatusBadge, StatCard


class TestGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialise Tkinter en mode invisible pour éviter l'ouverture de fenêtres
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_status_badge(self):
        # Vérifie que le badge de statut s'instancie correctement et met en majuscules
        badge = StatusBadge(self.root, text="en attente", status="en_attente")
        self.assertIsNotNone(badge)
        self.assertEqual(badge.cget("text"), "EN ATTENTE")
        # bg_color depend du theme, on verifie juste qu'il n'y a pas d'erreur
        self.assertTrue(badge.cget("bg") != "")

    def test_stat_card(self):
        # Vérifie que la carte statistique se crée correctement avec progression
        card = StatCard(
            self.root, title="Revenus", value="1000", trend="+10%", progress=80
        )
        self.assertIsNotNone(card)
        self.assertTrue(card.winfo_exists())


if __name__ == "__main__":
    unittest.main()
