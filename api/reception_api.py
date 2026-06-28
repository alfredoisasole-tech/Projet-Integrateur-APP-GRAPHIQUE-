"""Blueprint API — Réception (Procédé complet en 2 phases)."""

from flask import Blueprint, jsonify, request, current_app

reception_bp = Blueprint("reception", __name__)


@reception_bp.route("/reception/bons", methods=["GET"])
def get_bons():
    """Liste des bons de réception."""
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "bons": db.get_bons_reception()}), 200


@reception_bp.route("/reception/bon/<bon_id>", methods=["GET"])
def get_bon(bon_id):
    """Détail d'un bon de réception."""
    db = current_app.config["DB"]
    bon = db.get_bon_reception(bon_id)
    if not bon:
        return jsonify({"statut": "ERROR", "message": "Bon introuvable"}), 404
    return jsonify({"statut": "SUCCESS", "bon": bon}), 200


@reception_bp.route("/reception/recevoir", methods=["POST"])
def recevoir():
    """Phase A : Réception immédiate d'un chargement."""
    db = current_app.config["DB"]
    data = request.json or {}
    bon_id = data.get("bon_reception_id")
    if not bon_id:
        return jsonify({"statut": "ERROR", "message": "bon_reception_id requis"}), 400
    result = db.recevoir_chargement(bon_id)
    code = 200 if result["statut"] == "SUCCESS" else 400
    return jsonify(result), code


@reception_bp.route("/reception/zone-reception", methods=["GET"])
def zone_reception():
    """Colis en attente dans la zone de réception."""
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "colis": db.get_zone_reception()}), 200


@reception_bp.route("/reception/attribuer-emplacement", methods=["POST"])
def attribuer_emplacement():
    """Attribution d'un emplacement optimal pour un colis."""
    db = current_app.config["DB"]
    data = request.json or {}
    colis_id = data.get("colis_id")
    zone_cible = data.get("zone_cible")
    if not colis_id:
        return jsonify({"statut": "ERROR", "message": "colis_id requis"}), 400
    result = db.attribuer_emplacement(colis_id, zone_cible)
    code = 200 if result["statut"] == "SUCCESS" else 400
    return jsonify(result), code


@reception_bp.route("/reception/stocker", methods=["POST"])
def stocker():
    """Phase B : Confirmation du stockage dans une cellule."""
    db = current_app.config["DB"]
    data = request.json or {}
    colis_id = data.get("colis_id")
    cellule_id = data.get("cellule_cible") or data.get("cellule_id")
    if not colis_id or not cellule_id:
        return (
            jsonify({"statut": "ERROR", "message": "colis_id et cellule_cible requis"}),
            400,
        )
    result = db.confirmer_stockage(colis_id, cellule_id)
    code = 200 if result["statut"] == "SUCCESS" else 400
    return jsonify(result), code
