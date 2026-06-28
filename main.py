"""
WMS-CLAM-PRO — Système de Gestion d'Entrepôt
Société Amazones et Centaures (SAC)

Point d'entrée principal de l'application.
Lance le backend Flask API en arrière-plan, puis l'interface Tkinter.

Usage:
    python main.py
"""

import sys
import time
import os

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests
import socket
from config import Config
from db import get_database
from api.server import run_api_server
from gui.app import WMSApplication


def wait_for_api(url, timeout=30):
    """Attend que l'API Flask soit prête.

    Args:
        url: URL de santé de l'API.
        timeout: Temps max d'attente en secondes.
    """
    host = Config.FLASK_HOST
    port = Config.FLASK_PORT
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                try:
                    resp = requests.get(f"{url}/api/health", timeout=1)
                    if resp.status_code == 200:
                        print(f"[OK] API prête ({resp.json().get('service', 'WMS')})")
                        return True
                    print(
                        f"[WARN] API socket ouverte mais /api/health HTTP {resp.status_code}"
                    )
                except requests.RequestException:
                    pass
        except OSError:
            pass
        time.sleep(0.2)
    print("[ERREUR] L'API n'a pas démarré dans le temps imparti.")
    return False


def main():
    """Point d'entrée principal."""
    print("=" * 50)
    print("  WMS-CLAM-PRO — SAC LOGISTICS")
    print("  Système de Gestion d'Entrepôt")
    print("=" * 50)

    # 1. Initialiser la base de données (mock ou réelle selon config)
    print("[1/3] Initialisation de la base de données...")
    db = get_database()
    try:
        prod_count = len(db.produits)
    except Exception:
        prod_count = "?"
    try:
        cells_count = len(db.cellules)
    except Exception:
        cells_count = "?"
    try:
        lots_count = len(db.lots)
    except Exception:
        lots_count = "?"
    print(
        f"      > {prod_count} produits, {cells_count} cellules, {lots_count} lots charges"
    )

    # 2. Lancer Flask API en arrière-plan
    print(f"[2/3] Lancement du serveur API sur {Config.API_BASE_URL} ...")
    run_api_server(db, host=Config.FLASK_HOST, port=Config.FLASK_PORT)

    if not wait_for_api(Config.API_BASE_URL, timeout=30):
        print("[ERREUR] Impossible de démarrer le serveur API.")
        sys.exit(1)

    # 3. Lancer l'interface Tkinter
    print("[3/3] Lancement de l'interface graphique...")
    print(f"      > Fenetre: {Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
    print()

    app = WMSApplication(api_base_url=Config.API_BASE_URL)

    # Gestion propre de la fermeture
    def on_close():
        print("\n[INFO] Fermeture de WMS-CLAM-PRO...")
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
