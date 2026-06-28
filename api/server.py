"""
Serveur Flask API — Point d'entrée du backend.

Lance Flask dans un thread daemon pour que l'interface Tkinter
puisse communiquer via HTTP sur localhost.
"""

import threading
import logging
from flask import Flask
from flask_cors import CORS

# Réduire les logs Flask en mode thread
log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)


def create_api(db):
    """Crée l'application Flask avec la DB injectée.

    Args:
        db: Instance de SGEDatabase (PostgreSQL).

    Returns:
        Flask: Application Flask configurée.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "sge-sac-wms-2024"
    CORS(app)

    # Stocker la DB dans le contexte Flask
    app.config["DB"] = db
    # Détecter le mode de DB (mock vs real)
    try:
        mode = "real" if db.__class__.__name__ == "SGEDatabase" else "mock"
    except Exception:
        mode = "unknown"
    app.config["DB_MODE"] = mode

    # Enregistrer les blueprints
    from api.dashboard_api import dashboard_bp
    from api.reception_api import reception_bp
    from api.expedition_api import expedition_bp
    from api.inventaire_api import inventaire_bp
    from api.rapports_api import rapports_bp
    from api.admin_api import admin_bp
    from api.gestion_api import gestion_bp

    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(reception_bp, url_prefix="/api")
    app.register_blueprint(expedition_bp, url_prefix="/api")
    app.register_blueprint(inventaire_bp, url_prefix="/api")
    app.register_blueprint(rapports_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(gestion_bp, url_prefix="/api")

    # Route santé
    @app.route("/api/health")
    def health():
        db = app.config.get("DB")
        mode = app.config.get("DB_MODE", "unknown")
        info = {
            "statut": "OK",
            "service": "WMS-CLAM-PRO API",
            "version": "2.4.1",
            "db_mode": mode,
        }

        # Tenter de récupérer quelques métriques DB pour confirmer le lien
        try:
            if mode == "mock":
                info["produits"] = len(getattr(db, "produits", []))
                info["cellules"] = len(getattr(db, "cellules", []))
                info["lots"] = len(getattr(db, "lots", []))
            elif mode == "real":
                # SGEDatabase: tenter des comptages simples via méthodes internes
                try:
                    p = db._query("SELECT COUNT(*) AS c FROM Produit", fetchone=True)
                    info["produits"] = int(p.get("c", 0)) if p else None
                except Exception:
                    info["produits"] = None
                try:
                    c = db._query("SELECT COUNT(*) AS c FROM Cellule", fetchone=True)
                    info["cellules"] = int(c.get("c", 0)) if c else None
                except Exception:
                    info["cellules"] = None
                try:
                    l = db._query("SELECT COUNT(*) AS c FROM Lot", fetchone=True)
                    info["lots"] = int(l.get("c", 0)) if l else None
                except Exception:
                    info["lots"] = None
            else:
                info["produits"] = None
                info["cellules"] = None
                info["lots"] = None
        except Exception:
            info["produits"] = None
            info["cellules"] = None
            info["lots"] = None

        from flask import jsonify

        return jsonify(info), 200

    return app


def run_api_server(db, host="127.0.0.1", port=5000):
    """Lance le serveur Flask dans un thread daemon.

    Le thread daemon se termine automatiquement quand le thread
    principal (Tkinter) se ferme.

    Args:
        db: Instance de SGEDatabase.
        host: Adresse d'écoute.
        port: Port d'écoute.

    Returns:
        threading.Thread: Le thread du serveur.
    """
    app = create_api(db)
    thread = threading.Thread(
        target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
        daemon=True,
        name="flask-api-server",
    )
    thread.start()
    return thread
