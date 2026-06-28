"""Blueprint API — Administration (Organisation, Individu, Répertoire)."""

from flask import Blueprint, jsonify, request, current_app

admin_bp = Blueprint("admin", __name__)


# ── Organisations ──────────────────────────────────────────────


@admin_bp.route("/admin/organisations", methods=["GET"])
def get_organisations():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "organisations": db.get_organisations()}), 200


@admin_bp.route("/admin/organisations/<int:org_id>", methods=["GET"])
def get_organisation(org_id):
    db = current_app.config["DB"]
    org = db.get_organisation(org_id)
    if not org:
        return jsonify({"statut": "ERROR", "message": "Organisation introuvable"}), 404
    return jsonify({"statut": "SUCCESS", "organisation": org}), 200


@admin_bp.route("/admin/organisations", methods=["POST"])
def create_organisation():
    db = current_app.config["DB"]
    data = request.json or {}
    nom = data.get("nom")
    type_org = data.get("type_org")
    if not nom or not type_org:
        return jsonify({"statut": "ERROR", "message": "nom et type_org requis"}), 400
    try:
        result = db.insert_organisation(
            nom, type_org, data.get("adresse"), data.get("telephone")
        )
        return (
            jsonify(
                {"statut": "SUCCESS", "message": "Organisation créée", "result": result}
            ),
            201,
        )
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@admin_bp.route("/admin/organisations/<int:org_id>", methods=["PUT"])
def update_organisation(org_id):
    db = current_app.config["DB"]
    data = request.json or {}
    try:
        db.update_organisation(
            org_id,
            data.get("nom"),
            data.get("type_org"),
            data.get("adresse"),
            data.get("telephone"),
        )
        return jsonify({"statut": "SUCCESS", "message": "Organisation modifiée"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@admin_bp.route("/admin/organisations/<int:org_id>", methods=["DELETE"])
def delete_organisation(org_id):
    db = current_app.config["DB"]
    try:
        db.delete_organisation(org_id)
        return jsonify({"statut": "SUCCESS", "message": "Organisation supprimée"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


# ── Individus ──────────────────────────────────────────────────


@admin_bp.route("/admin/individus", methods=["GET"])
def get_individus():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "individus": db.get_individus()}), 200


@admin_bp.route("/admin/individus", methods=["POST"])
def create_individu():
    db = current_app.config["DB"]
    data = request.json or {}
    nom = data.get("nom")
    if not nom:
        return jsonify({"statut": "ERROR", "message": "nom requis"}), 400
    try:
        result = db.insert_individu(
            nom, data.get("adresse"), data.get("telephone"), data.get("email")
        )
        return (
            jsonify(
                {"statut": "SUCCESS", "message": "Individu créé", "result": result}
            ),
            201,
        )
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@admin_bp.route("/admin/individus/<int:ind_id>", methods=["PUT"])
def update_individu(ind_id):
    db = current_app.config["DB"]
    data = request.json or {}
    try:
        db.update_individu(
            ind_id,
            data.get("nom"),
            data.get("adresse"),
            data.get("telephone"),
            data.get("email"),
        )
        return jsonify({"statut": "SUCCESS", "message": "Individu modifié"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@admin_bp.route("/admin/individus/<int:ind_id>", methods=["DELETE"])
def delete_individu(ind_id):
    db = current_app.config["DB"]
    try:
        db.delete_individu(ind_id)
        return jsonify({"statut": "SUCCESS", "message": "Individu supprimé"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


# ── Répertoire ─────────────────────────────────────────────────


@admin_bp.route("/admin/repertoire", methods=["GET"])
def get_repertoire():
    db = current_app.config["DB"]
    return jsonify({"statut": "SUCCESS", "repertoire": db.get_repertoire()}), 200


@admin_bp.route("/admin/repertoire", methods=["POST"])
def create_repertoire():
    db = current_app.config["DB"]
    data = request.json or {}
    required = ["id_organisation", "id_individu", "role", "date_debut"]
    if not all(data.get(k) for k in required):
        return (
            jsonify(
                {"statut": "ERROR", "message": f"Champs requis: {', '.join(required)}"}
            ),
            400,
        )
    try:
        db.insert_repertoire(
            data["id_organisation"],
            data["id_individu"],
            data["role"],
            data["date_debut"],
            data.get("date_fin"),
        )
        return jsonify({"statut": "SUCCESS", "message": "Affectation créée"}), 201
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400


@admin_bp.route("/admin/repertoire/close", methods=["PUT"])
def close_repertoire():
    db = current_app.config["DB"]
    data = request.json or {}
    required = ["id_organisation", "id_individu", "role"]
    if not all(data.get(k) for k in required):
        return (
            jsonify(
                {"statut": "ERROR", "message": f"Champs requis: {', '.join(required)}"}
            ),
            400,
        )
    try:
        db.close_repertoire(
            data["id_organisation"],
            data["id_individu"],
            data["role"],
            data.get("date_fin"),
        )
        return jsonify({"statut": "SUCCESS", "message": "Affectation clôturée"}), 200
    except Exception as e:
        return jsonify({"statut": "ERROR", "message": str(e).split("\n")[0]}), 400
