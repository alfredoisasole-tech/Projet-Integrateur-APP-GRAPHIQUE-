"""Blueprint API — Gestion (Produit, Lot, Cellule) + Requêtes avancées."""

from flask import Blueprint, jsonify, request, current_app

gestion_bp = Blueprint("gestion", __name__)


# ── Requêtes avancées (Phase 1) ────────────────────────────────


@gestion_bp.route("/rapports/perf-reception", methods=["GET"])
def perf_reception():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "performance": db.get_perf_reception()}), 200


@gestion_bp.route("/rapports/perf-expedition", methods=["GET"])
def perf_expedition():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "performance": db.get_perf_expedition()}), 200


@gestion_bp.route("/rapports/stock-par-zone", methods=["GET"])
def stock_par_zone():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "zones": db.get_rapport_stock_par_zone()}), 200


@gestion_bp.route("/inventaire/produit/<int:produit_id>", methods=["GET"])
def stock_produit(produit_id):
    db = current_app.config["DB"]
    return (
        jsonify({"statut": "SUCCESS", "stock": db.get_stock_par_produit(produit_id)}),
        200,
    )


@gestion_bp.route("/inventaire/lot/<int:lot_id>/mouvements", methods=["GET"])
def mouvements_lot(lot_id):
    db = current_app.config["DB"]
    return (
        jsonify({"statut": "SUCCESS", "mouvements": db.get_mouvements_lot(lot_id)}),
        200,
    )


@gestion_bp.route("/inventaire/produits-agrege", methods=["GET"])
def inventaire_agrege():
    db = current_app.config["DB"]
    return (
        jsonify({"statut": "SUCCESS", "inventaire": db.get_inventaire_produit()}),
        200,
    )


# ── Produits (Phase 3) ─────────────────────────────────────────


@gestion_bp.route("/gestion/produits", methods=["GET"])
def get_produits():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "produits": db.get_produits_complet()}), 200


@gestion_bp.route("/gestion/produits", methods=["POST"])
def create_produit():
    db = current_app.config["DB"]
    data = request.json or {}
    nom = data.get("nom")
    type_p = data.get("type_p")
    if not nom or not type_p:
        return jsonify({"statut": "ERROR", "message": "nom et type_p requis"}), 400
    try:
        result = db.insert_produit(
            nom,
            type_p,
            data.get("description"),
            data.get("marque"),
            data.get("modele"),
            data.get("id_fournisseur"),
        )
        # Ajouter les attributs de spécialisation
        if result and type_p == "materiel":
            id_p = list(result.values())[0] if isinstance(result, dict) else None
            if id_p and all(
                data.get(k) for k in ["longueur", "largeur", "hauteur", "masse"]
            ):
                db.insert_produit_materiel(
                    id_p,
                    data["longueur"],
                    data["largeur"],
                    data["hauteur"],
                    data["masse"],
                )
        elif result and type_p == "logiciel":
            id_p = list(result.values())[0] if isinstance(result, dict) else None
            if id_p:
                db.insert_produit_logiciel(
                    id_p,
                    data.get("version"),
                    data.get("licence"),
                    data.get("support_expire"),
                )
        return (
            jsonify({"statut": "SUCCESS", "message": "Produit créé", "result": result}),
            201,
        )
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@gestion_bp.route("/gestion/produits/<int:prod_id>", methods=["PUT"])
def update_produit(prod_id):
    db = current_app.config["DB"]
    data = request.json or {}
    try:
        db.update_produit(
            prod_id,
            data.get("nom"),
            data.get("description"),
            data.get("marque"),
            data.get("modele"),
        )
        return jsonify({"statut": "SUCCESS", "message": "Produit modifié"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@gestion_bp.route("/gestion/produits/<int:prod_id>", methods=["DELETE"])
def delete_produit(prod_id):
    db = current_app.config["DB"]
    try:
        db.delete_produit(prod_id)
        return jsonify({"statut": "SUCCESS", "message": "Produit supprimé"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


# ── Lots (Phase 3) ─────────────────────────────────────────────


@gestion_bp.route("/gestion/lots", methods=["GET"])
def get_lots():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "lots": db.get_lots_complet()}), 200


@gestion_bp.route("/gestion/lots", methods=["POST"])
def create_lot():
    db = current_app.config["DB"]
    data = request.json or {}
    required = ["id_produit", "quantite", "origine"]
    if not all(data.get(k) for k in required):
        return (
            jsonify(
                {"statut": "ERROR", "message": f"Champs requis: {', '.join(required)}"}
            ),
            400,
        )
    try:
        result = db.insert_lot(
            data["id_produit"],
            data["quantite"],
            data["origine"],
            data.get("date_entree"),
        )
        return (
            jsonify({"statut": "SUCCESS", "message": "Lot créé", "result": result}),
            201,
        )
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@gestion_bp.route("/gestion/lots/<int:lot_id>/quantite", methods=["PUT"])
def update_lot_qte(lot_id):
    db = current_app.config["DB"]
    data = request.json or {}
    quantite = data.get("quantite")
    if quantite is None:
        return jsonify({"statut": "ERROR", "message": "quantite requis"}), 400
    try:
        db.update_lot_quantite(lot_id, quantite)
        return jsonify({"statut": "SUCCESS", "message": "Quantité modifiée"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@gestion_bp.route("/gestion/lots/<int:lot_id>", methods=["DELETE"])
def delete_lot(lot_id):
    db = current_app.config["DB"]
    try:
        db.delete_lot(lot_id)
        return jsonify({"statut": "SUCCESS", "message": "Lot supprimé"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


# ── Cellules (Phase 3) ─────────────────────────────────────────


@gestion_bp.route("/gestion/cellules", methods=["GET"])
def get_cellules():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "cellules": db.get_cellules_complet()}), 200


@gestion_bp.route("/gestion/cellules", methods=["POST"])
def create_cellule():
    db = current_app.config["DB"]
    data = request.json or {}
    required = ["longueur", "largeur", "hauteur", "masse_max", "zone", "position"]
    if not all(data.get(k) for k in required):
        return (
            jsonify(
                {"statut": "ERROR", "message": f"Champs requis: {', '.join(required)}"}
            ),
            400,
        )
    try:
        result = db.insert_cellule(
            data["longueur"],
            data["largeur"],
            data["hauteur"],
            data["masse_max"],
            data["zone"],
            data["position"],
        )
        return (
            jsonify(
                {"statut": "SUCCESS", "message": "Cellule créée", "result": result}
            ),
            201,
        )
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@gestion_bp.route("/gestion/cellules/<int:cell_id>/statut", methods=["PUT"])
def update_cellule(cell_id):
    db = current_app.config["DB"]
    data = request.json or {}
    statut = data.get("statut")
    if not statut:
        return jsonify({"statut": "ERROR", "message": "statut requis"}), 400
    try:
        db.update_cellule_statut(cell_id, statut)
        return jsonify({"statut": "SUCCESS", "message": "Statut cellule modifié"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


# ── Bons (Phase 4) ─────────────────────────────────────────────


@gestion_bp.route("/reception/bons", methods=["POST"])
def create_bon_reception():
    db = current_app.config["DB"]
    data = request.json or {}
    required = ["id_fournisseur", "date_attendue"]
    if not all(data.get(k) for k in required):
        return (
            jsonify(
                {"statut": "ERROR", "message": f"Champs requis: {', '.join(required)}"}
            ),
            400,
        )
    try:
        result = db.insert_bon_reception(
            data["id_fournisseur"], data["date_attendue"], data.get("priorite", 3)
        )
        return (
            jsonify(
                {
                    "statut": "SUCCESS",
                    "message": "Bon de réception créé",
                    "result": result,
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@gestion_bp.route("/expedition/bordereaux", methods=["POST"])
def create_bon_expedition():
    db = current_app.config["DB"]
    data = request.json or {}
    required = ["id_destinataire", "date_attendue"]
    if not all(data.get(k) for k in required):
        return (
            jsonify(
                {"statut": "ERROR", "message": f"Champs requis: {', '.join(required)}"}
            ),
            400,
        )
    try:
        result = db.insert_bon_expedition(
            data["id_destinataire"],
            data["date_attendue"],
            data.get("priorite", 3),
            data.get("id_transporteur"),
        )
        return (
            jsonify(
                {
                    "statut": "SUCCESS",
                    "message": "Bon d'expédition créé",
                    "result": result,
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400
