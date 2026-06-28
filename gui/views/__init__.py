# gui.views — Les 6 écrans de l'application
from gui.views.dashboard_view import DashboardView
from gui.views.cartographie_view import CartographieView
from gui.views.reception_view import ReceptionView
from gui.views.expedition_view import ExpeditionView
from gui.views.inventaire_view import InventaireView
from gui.views.rapports_view import RapportsView

__all__ = [
    "DashboardView",
    "CartographieView",
    "ReceptionView",
    "ExpeditionView",
    "InventaireView",
    "RapportsView",
]
