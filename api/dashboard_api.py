"""Blueprint API — Dashboard & Cartographie."""

from flask import Blueprint, jsonify, current_app

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    """Retourne les données résumées du tableau de bord."""
    db = current_app.config["DB"]
    data = db.get_dashboard_data()
    return jsonify({"statut": "SUCCESS", **data}), 200


@dashboard_bp.route("/dashboard/zones", methods=["GET"])
def get_zones():
    """Retourne toutes les zones avec leurs cellules."""
    db = current_app.config["DB"]
    zones = db.get_zones()
    return jsonify({"statut": "SUCCESS", "zones": zones}), 200


@dashboard_bp.route("/dashboard/zone/<zone_id>", methods=["GET"])
def get_zone(zone_id):
    """Retourne le détail d'une zone spécifique."""
    db = current_app.config["DB"]
    zone = db.get_zone(zone_id)
    if not zone:
        return (
            jsonify({"statut": "ERROR", "message": f"Zone {zone_id} introuvable"}),
            404,
        )
    return jsonify({"statut": "SUCCESS", "zone": zone}), 200
