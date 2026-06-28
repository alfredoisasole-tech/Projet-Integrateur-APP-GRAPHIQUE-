"""
WMS-CLAM-PRO — Fenêtre principale de l'application.

Orchestre le layout global :
  - Topbar (en haut)
  - Sidebar (à gauche)
  - Zone de contenu (centre, change selon la navigation)
  - Footer (en bas)
"""

import tkinter as tk
from gui.theme import apply_theme, SURFACE
from gui.components.sidebar import Sidebar
from gui.components.topbar import Topbar
from gui.components.footer import Footer
from gui.views.dashboard_view import DashboardView
from gui.views.cartographie_view import CartographieView
from gui.views.reception_view import ReceptionView
from gui.views.expedition_view import ExpeditionView
from gui.views.inventaire_view import InventaireView
from gui.views.rapports_view import RapportsView
from gui.views.admin_view import AdminView
from gui.views.gestion_view import GestionView


class WMSApplication(tk.Tk):
    """Fenêtre principale WMS-CLAM-PRO.

    Args:
        api_base_url: URL de base de l'API Flask (ex: http://127.0.0.1:5000).
    """

    def __init__(self, api_base_url):
        super().__init__()

        self.api_url = api_base_url

        # Configuration de la fenêtre
        self.title("WMS-CLAM-PRO | SAC LOGISTICS")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        self.configure(bg=SURFACE)

        # Centrer sur l'écran
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.winfo_screenheight() // 2) - (900 // 2)
        self.geometry(f"1400x900+{x}+{y}")

        # Appliquer le thème Ttk Industrial Light
        apply_theme(self)

        # Construire le layout
        self._build_layout()

        # Afficher le dashboard par défaut
        self.show_view("dashboard")

    def _build_layout(self):
        """Construit le layout principal de l'application."""
        # Topbar
        self.topbar = Topbar(self, height=48)
        self.topbar.pack(fill="x", side="top")

        # Footer
        self.footer = Footer(self, height=32)
        self.footer.pack(fill="x", side="bottom")

        # Container central (sidebar + contenu)
        container = tk.Frame(self, bg=SURFACE)
        container.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(container, on_navigate=self.show_view, width=256)
        self.sidebar.pack(fill="y", side="left")

        # Zone de contenu
        self.content = tk.Frame(container, bg=SURFACE)
        self.content.pack(fill="both", expand=True)

        # Créer toutes les vues
        self.views = {
            "dashboard": DashboardView(self.content, self.api_url),
            "cartographie": CartographieView(self.content, self.api_url),
            "reception": ReceptionView(self.content, self.api_url),
            "expedition": ExpeditionView(self.content, self.api_url),
            "inventaire": InventaireView(self.content, self.api_url),
            "rapports": RapportsView(self.content, self.api_url),
            "gestion": GestionView(self.content, self.api_url),
            "admin": AdminView(self.content, self.api_url),
        }

        self.current_view = None

    def show_view(self, name):
        """Change la vue affichée dans la zone de contenu.

        Args:
            name: Clé de la vue (dashboard, cartographie, reception, etc.)
        """
        if name not in self.views:
            return

        # Masquer la vue courante
        if self.current_view:
            self.views[self.current_view].pack_forget()

        # Afficher la nouvelle vue
        self.views[name].pack(fill="both", expand=True)
        self.current_view = name

        # Mettre à jour la sidebar
        self.sidebar.set_active(name)

        # Rafraîchir les données
        self.views[name].refresh()
