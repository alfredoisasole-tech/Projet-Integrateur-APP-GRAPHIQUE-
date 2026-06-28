"""Blueprint API — Rapports & Exceptions."""

from flask import Blueprint, jsonify, request, current_app
from services.rapport_service import RapportService

rapports_bp = Blueprint("rapports", __name__)


@rapports_bp.route("/rapports/exceptions", methods=["GET"])
def get_exceptions():
    """Journal des rapports d'exception."""
    db = current_app.config["DB"]
    type_f = request.args.get("type")
    statut_f = request.args.get("statut")
    logs = db.get_rapports_exception(type_f, statut_f)
    return jsonify({"statut": "SUCCESS", "logs": logs, "total": len(logs)}), 200


@rapports_bp.route("/rapports/performance", methods=["GET"])
def get_performance():
    """Métriques de performance."""
    db = current_app.config["DB"]
    kpis = db.get_performance_kpis()
    return jsonify({"statut": "SUCCESS", **kpis}), 200


@rapports_bp.route("/rapports/stocks", methods=["GET"])
def get_rapport_stocks():
    """Rapport détaillé des stocks par zone."""
    service = RapportService(current_app.config.get("DB"))
    rapport = service.get_rapport_stocks()
    return jsonify({"statut": "SUCCESS", "rapport": rapport}), 200


@rapports_bp.route("/rapports/operations", methods=["GET"])
def get_rapport_operations():
    """Rapport sur les opérations récentes."""
    service = RapportService(current_app.config.get("DB"))
    rapport = service.get_rapport_operations()
    return jsonify({"statut": "SUCCESS", **rapport}), 200


@rapports_bp.route("/rapports/emballage", methods=["GET"])
def get_rapport_emballage():
    """Rapport sur le stock d'emballages."""
    service = RapportService(current_app.config.get("DB"))
    rapport = service.get_rapport_emballage()
    return jsonify({"statut": "SUCCESS", **rapport}), 200


@rapports_bp.route("/rapports/signaler", methods=["POST"])
def signaler_anomalie():
    """Signalement manuel d'une anomalie depuis l'interface."""
    db = current_app.config["DB"]
    data = request.json or {}
    bon_id = data.get("bon_id", "N/A")
    description = data.get("description", "")
    type_rapport = data.get("type", "autre")

    if not description.strip():
        return jsonify({"statut": "ERROR", "message": "Description requise"}), 400

    # Types valides
    types_valides = {
        "ecart_reception",
        "ecart_stockage",
        "ecart_expedition",
        "ecart_chargement",
        "masse_depassee",
        "autre",
    }
    if type_rapport not in types_valides:
        type_rapport = "autre"

    db._ajouter_exception(
        type_rapport,
        f"[SIGNALEMENT MANUEL | BON:{bon_id}] {description}",
        bon_id,
        "operateur_gui",
    )
    return (
        jsonify(
            {
                "statut": "SUCCESS",
                "message": f"Rapport d'exception créé — type: {type_rapport}",
            }
        ),
        201,
    )
