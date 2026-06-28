"""Blueprint API — Expédition (Procédé complet en 2 phases)."""

from flask import Blueprint, jsonify, request, current_app
from services.expedition_service import ExpeditionService

expedition_bp = Blueprint("expedition", __name__)


@expedition_bp.route("/expedition/bordereaux", methods=["GET"])
def get_bordereaux():
    """Liste des bons d'expédition."""
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "bordereaux": db.get_bons_expedition()}), 200


@expedition_bp.route("/expedition/bordereau/<bon_id>", methods=["GET"])
def get_bordereau(bon_id):
    """Détail d'un bon d'expédition."""
    db = current_app.config["DB"]
    bon = db.get_bon_expedition(bon_id)
    if not bon:
        return jsonify({"statut": "ERROR", "message": "Bordereau introuvable"}), 404
    return jsonify({"statut": "SUCCESS", "bordereau": bon}), 200


@expedition_bp.route("/expedition/preparer", methods=["POST"])
def preparer():
    """Phase A : Préparer une expédition."""
    db = current_app.config["DB"]
    data = request.json or {}
    bon_id = data.get("bon_expedition_id")
    if not bon_id:
        return jsonify({"statut": "ERROR", "message": "bon_expedition_id requis"}), 400
    result = db.preparer_expedition(bon_id)
    code = 200 if result["statut"] == "SUCCESS" else 400
    return jsonify(result), code


@expedition_bp.route("/expedition/pick-list/<bon_id>", methods=["GET"])
def pick_list(bon_id):
    """Liste de picking pour un bon d'expédition."""
    service = ExpeditionService(current_app.config.get("DB"))
    items = service.get_pick_list(bon_id)
    return jsonify({"statut": "SUCCESS", "pick_list": items}), 200


@expedition_bp.route("/expedition/itineraire/<bon_id>", methods=["GET"])
def itineraire(bon_id):
    """Calcul du chemin optimal de picking."""
    service = ExpeditionService(current_app.config.get("DB"))
    result = service.calculer_itineraire_picking(bon_id)
    if not result:
        return jsonify({"statut": "ERROR", "message": "Bordereau introuvable"}), 404
    return jsonify({"statut": "SUCCESS", **result}), 200


@expedition_bp.route("/expedition/valider", methods=["POST"])
def valider():
    """Phase B : Valider l'expédition (emballage éco-logistique)."""
    db = current_app.config["DB"]
    data = request.json or {}
    bon_id = data.get("bon_expedition_id")
    if not bon_id:
        return jsonify({"statut": "ERROR", "message": "bon_expedition_id requis"}), 400
    result = db.valider_expedition(bon_id)
    code = 200 if result["statut"] == "SUCCESS" else 400
    return jsonify(result), code


@expedition_bp.route("/expedition/zone-expedition", methods=["GET"])
def zone_expedition():
    """Colis en zone d'expédition."""
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "colis": db.get_zone_expedition()}), 200


@expedition_bp.route("/expedition/confirmer-depart", methods=["POST"])
def confirmer_depart():
    """Confirme le départ avec le transporteur."""
    db = current_app.config["DB"]
    data = request.json or {}
    bon_id = data.get("bon_expedition_id")
    if not bon_id:
        return jsonify({"statut": "ERROR", "message": "bon_expedition_id requis"}), 400
    result = db.confirmer_depart(bon_id)
    code = 200 if result["statut"] == "SUCCESS" else 400
    return jsonify(result), code
