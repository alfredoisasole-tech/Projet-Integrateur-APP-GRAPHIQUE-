"""Blueprint API — Inventaire des stocks."""

from flask import Blueprint, jsonify, request, current_app

inventaire_bp = Blueprint("inventaire", __name__)


@inventaire_bp.route("/inventaire", methods=["GET"])
def get_inventaire():
    """Liste de l'inventaire avec filtres optionnels."""
    db = current_app.config["DB"]
    categorie = request.args.get("categorie")
    statut = request.args.get("statut")
    recherche = request.args.get("q")
    resultats = db.get_inventaire(categorie, statut, recherche)
    return (
        jsonify(
            {"statut": "SUCCESS", "inventaire": resultats, "total": len(resultats)}
        ),
        200,
    )


@inventaire_bp.route("/inventaire/stats", methods=["GET"])
def get_stats():
    """Statistiques globales d'inventaire."""
    db = current_app.config["DB"]
    stats = db.get_inventaire_stats()
    return jsonify({"statut": "SUCCESS", **stats}), 200


@inventaire_bp.route("/inventaire/<lot_id>", methods=["GET"])
def get_lot(lot_id):
    """Détail d'un lot spécifique."""
    db = current_app.config["DB"]
    lot = db.lots.get(lot_id)
    if not lot:
        return jsonify({"statut": "ERROR", "message": f"Lot {lot_id} introuvable"}), 404
    produit = db.produits.get(lot["produit_id"], {})
    return jsonify({"statut": "SUCCESS", "lot": lot, "produit": produit}), 200
