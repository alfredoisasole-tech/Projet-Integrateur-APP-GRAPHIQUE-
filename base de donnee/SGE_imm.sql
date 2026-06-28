-- =============================================================
--  SGE_imm.sql
--  Interface Machine-Machine (IMM) — opérations CRUD de base
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.3.1
--  Prérequis  : SGE_cre.sql, SGE_inv.sql
-- =============================================================

-- =============================================================
--  CRUD — Organisation
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_organisation(
    p_nom       VARCHAR,
    p_typeOrg   VARCHAR,
    p_adresse   TEXT    DEFAULT NULL,
    p_telephone VARCHAR DEFAULT NULL
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Organisation(nom, typeOrg, adresse, telephone)
    VALUES (p_nom, p_typeOrg, p_adresse, p_telephone)
    RETURNING idOrganisation INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_organisation(
    p_id        INTEGER,
    p_nom       VARCHAR DEFAULT NULL,
    p_typeOrg   VARCHAR DEFAULT NULL,
    p_adresse   TEXT    DEFAULT NULL,
    p_telephone VARCHAR DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Organisation SET
        nom       = COALESCE(p_nom,       nom),
        typeOrg   = COALESCE(p_typeOrg,   typeOrg),
        adresse   = COALESCE(p_adresse,   adresse),
        telephone = COALESCE(p_telephone, telephone)
    WHERE idOrganisation = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Organisation % introuvable.', p_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION sge_delete_organisation(p_id INTEGER)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM Organisation WHERE idOrganisation = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Organisation % introuvable.', p_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION sge_get_organisation(p_id INTEGER)
RETURNS SETOF Organisation LANGUAGE sql AS $$
    SELECT * FROM Organisation WHERE idOrganisation = p_id;
$$;

-- =============================================================
--  CRUD — Individu
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_individu(
    p_nom       VARCHAR,
    p_adresse   TEXT    DEFAULT NULL,
    p_telephone VARCHAR DEFAULT NULL,
    p_email     VARCHAR DEFAULT NULL
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Individu(nom, adresse, telephone, email)
    VALUES (p_nom, p_adresse, p_telephone, p_email)
    RETURNING idIndividu INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_individu(
    p_id        INTEGER,
    p_nom       VARCHAR DEFAULT NULL,
    p_adresse   TEXT    DEFAULT NULL,
    p_telephone VARCHAR DEFAULT NULL,
    p_email     VARCHAR DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Individu SET
        nom       = COALESCE(p_nom,       nom),
        adresse   = COALESCE(p_adresse,   adresse),
        telephone = COALESCE(p_telephone, telephone),
        email     = COALESCE(p_email,     email)
    WHERE idIndividu = p_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Individu % introuvable.', p_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION sge_delete_individu(p_id INTEGER)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM Individu WHERE idIndividu = p_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Individu % introuvable.', p_id; END IF;
END;
$$;

-- =============================================================
--  CRUD — Répertoire
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_repertoire(
    p_idOrg   INTEGER,
    p_idInd   INTEGER,
    p_role    VARCHAR,
    p_debut   DATE,
    p_fin     DATE DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO Repertoire(idOrganisation, idIndividu, role, dateDebut, dateFin)
    VALUES (p_idOrg, p_idInd, p_role, p_debut, p_fin);
END;
$$;

CREATE OR REPLACE FUNCTION sge_close_repertoire(
    p_idOrg INTEGER,
    p_idInd INTEGER,
    p_role  VARCHAR,
    p_fin   DATE DEFAULT CURRENT_DATE
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Repertoire SET dateFin = p_fin
    WHERE idOrganisation = p_idOrg
      AND idIndividu     = p_idInd
      AND role           = p_role
      AND dateFin IS NULL;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Entrée Répertoire (org=%, ind=%, role=%) introuvable ou déjà clôturée.',
            p_idOrg, p_idInd, p_role;
    END IF;
END;
$$;

-- =============================================================
--  CRUD — Produit
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_produit(
    p_nom           VARCHAR,
    p_typeP         VARCHAR,
    p_description   TEXT    DEFAULT NULL,
    p_marque        VARCHAR DEFAULT NULL,
    p_modele        VARCHAR DEFAULT NULL,
    p_idFournisseur INTEGER DEFAULT NULL
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Produit(nom, typeP, description, marque, modele, idFournisseur)
    VALUES (p_nom, p_typeP, p_description, p_marque, p_modele, p_idFournisseur)
    RETURNING idProduit INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_insert_produit_materiel(
    p_idProduit INTEGER,
    p_longueur  NUMERIC,
    p_largeur   NUMERIC,
    p_hauteur   NUMERIC,
    p_masse     NUMERIC
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO ProduitMateriel(idProduit, longueur, largeur, hauteur, masse)
    VALUES (p_idProduit, p_longueur, p_largeur, p_hauteur, p_masse);
END;
$$;

CREATE OR REPLACE FUNCTION sge_insert_produit_logiciel(
    p_idProduit     INTEGER,
    p_version       VARCHAR DEFAULT NULL,
    p_licence       VARCHAR DEFAULT NULL,
    p_supportExpire DATE    DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO ProduitLogiciel(idProduit, version, licence, supportExpire)
    VALUES (p_idProduit, p_version, p_licence, p_supportExpire);
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_produit(
    p_id          INTEGER,
    p_nom         VARCHAR DEFAULT NULL,
    p_description TEXT    DEFAULT NULL,
    p_marque      VARCHAR DEFAULT NULL,
    p_modele      VARCHAR DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Produit SET
        nom         = COALESCE(p_nom,         nom),
        description = COALESCE(p_description, description),
        marque      = COALESCE(p_marque,      marque),
        modele      = COALESCE(p_modele,      modele)
    WHERE idProduit = p_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Produit % introuvable.', p_id; END IF;
END;
$$;

CREATE OR REPLACE FUNCTION sge_delete_produit(p_id INTEGER)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM Produit WHERE idProduit = p_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Produit % introuvable.', p_id; END IF;
END;
$$;

-- =============================================================
--  CRUD — Lot
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_lot(
    p_idProduit INTEGER,
    p_quantite  INTEGER,
    p_origine   VARCHAR,
    p_dateEntree DATE DEFAULT CURRENT_DATE
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Lot(idProduit, quantite, origine, dateEntree)
    VALUES (p_idProduit, p_quantite, p_origine, p_dateEntree)
    RETURNING idLot INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_lot_quantite(
    p_idLot    INTEGER,
    p_quantite INTEGER
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    IF p_quantite < 0 THEN
        RAISE EXCEPTION 'La quantité ne peut pas être négative.';
    END IF;
    UPDATE Lot SET quantite = p_quantite WHERE idLot = p_idLot;
    IF NOT FOUND THEN RAISE EXCEPTION 'Lot % introuvable.', p_idLot; END IF;
END;
$$;

CREATE OR REPLACE FUNCTION sge_delete_lot(p_id INTEGER)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM Lot WHERE idLot = p_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Lot % introuvable.', p_id; END IF;
END;
$$;

-- =============================================================
--  CRUD — Cellule
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_cellule(
    p_longueur      NUMERIC,
    p_largeur       NUMERIC,
    p_hauteur       NUMERIC,
    p_masseMax      NUMERIC,
    p_zone          VARCHAR,
    p_position      VARCHAR
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Cellule(longueur, largeur, hauteur, masseMaximale, zone, position)
    VALUES (p_longueur, p_largeur, p_hauteur, p_masseMax, p_zone, p_position)
    RETURNING idCellule INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_cellule_statut(
    p_id     INTEGER,
    p_statut VARCHAR
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Cellule SET statut = p_statut WHERE idCellule = p_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'Cellule % introuvable.', p_id; END IF;
END;
$$;

-- =============================================================
--  CRUD — Inventaire_emplacement
-- =============================================================

CREATE OR REPLACE FUNCTION sge_stocker_lot(
    p_idLot     INTEGER,
    p_idCellule INTEGER
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    -- Vérifier que la cellule existe (la capacité est gérée par le trigger trg_masse_max)
    IF NOT EXISTS (SELECT 1 FROM Cellule
                    WHERE idCellule = p_idCellule) THEN
        RAISE EXCEPTION 'Cellule % introuvable ou invalide.', p_idCellule;
    END IF;

    INSERT INTO Inventaire_emplacement(idCellule, idLot, dateDepot)
    VALUES (p_idCellule, p_idLot, now());
    -- Le trigger trg_masse_max vérifie la capacité (RG02)
    -- Le trigger trg_statut_cellule met à jour Cellule.statut
END;
$$;

CREATE OR REPLACE FUNCTION sge_retirer_lot(
    p_idLot     INTEGER,
    p_idCellule INTEGER
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Inventaire_emplacement
       SET dateRetrait = now()
     WHERE idLot     = p_idLot
       AND idCellule = p_idCellule
       AND dateRetrait IS NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Lot % non trouvé dans cellule % ou déjà retiré.',
            p_idLot, p_idCellule;
    END IF;
    -- Le trigger trg_statut_cellule se charge de la mise à jour du statut
END;
$$;

-- =============================================================
--  CRUD — Colis
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_colis(
    p_type          VARCHAR,
    p_idCelluleZone INTEGER DEFAULT NULL
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Colis(typeColis, idCelluleZone)
    VALUES (p_type, p_idCelluleZone)
    RETURNING idColis INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_add_lot_to_colis(
    p_idColis       INTEGER,
    p_idLot         INTEGER,
    p_quantiteColis INTEGER
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO Contenu_Colis(idColis, idLot, quantiteColis)
    VALUES (p_idColis, p_idLot, p_quantiteColis)
    ON CONFLICT (idColis, idLot)
    DO UPDATE SET quantiteColis = EXCLUDED.quantiteColis;
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_statut_colis(
    p_idColis INTEGER,
    p_statut  VARCHAR
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Colis SET statut = p_statut WHERE idColis = p_idColis;
    IF NOT FOUND THEN RAISE EXCEPTION 'Colis % introuvable.', p_idColis; END IF;
END;
$$;

-- =============================================================
--  CRUD — Bons de réception
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_bon_reception(
    p_idFournisseur INTEGER,
    p_dateAttendue  DATE,
    p_priorite      SMALLINT DEFAULT 3
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Bon_reception(idFournisseur, dateAttendue, priorite)
    VALUES (p_idFournisseur, p_dateAttendue, p_priorite)
    RETURNING idBon INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_statut_bon_reception(
    p_idBon  INTEGER,
    p_statut VARCHAR,
    p_idColis INTEGER DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    -- Vérifier statut en_attente avant traitement (RG03)
    IF p_statut = 'en_cours' AND NOT EXISTS (
        SELECT 1 FROM Bon_reception
         WHERE idBon = p_idBon AND statut = 'en_attente')
    THEN
        RAISE EXCEPTION 'RG03 — Bon de réception % n''est pas en statut en_attente.', p_idBon;
    END IF;

    UPDATE Bon_reception SET
        statut        = p_statut,
        idColis       = COALESCE(p_idColis, idColis),
        dateEffective = CASE WHEN p_statut = 'traite' THEN CURRENT_DATE ELSE dateEffective END
    WHERE idBon = p_idBon;

    IF NOT FOUND THEN RAISE EXCEPTION 'Bon réception % introuvable.', p_idBon; END IF;
END;
$$;

-- =============================================================
--  CRUD — Bons d'expédition
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_bon_expedition(
    p_idDestinataire INTEGER,
    p_dateAttendue   DATE,
    p_priorite       SMALLINT DEFAULT 3,
    p_idTransporteur INTEGER  DEFAULT NULL
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Bon_expedition(idDestinataire, idTransporteur, dateAttendue, priorite)
    VALUES (p_idDestinataire, p_idTransporteur, p_dateAttendue, p_priorite)
    RETURNING idBon INTO v_id;
    RETURN v_id;
END;
$$;

CREATE OR REPLACE FUNCTION sge_update_statut_bon_expedition(
    p_idBon          INTEGER,
    p_statut         VARCHAR,
    p_idColis        INTEGER DEFAULT NULL,
    p_idTransporteur INTEGER DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    IF p_statut = 'en_cours' AND NOT EXISTS (
        SELECT 1 FROM Bon_expedition
         WHERE idBon = p_idBon AND statut = 'en_attente')
    THEN
        RAISE EXCEPTION 'RG03 — Bon d''expédition % n''est pas en statut en_attente.', p_idBon;
    END IF;

    UPDATE Bon_expedition SET
        statut          = p_statut,
        idColis         = COALESCE(p_idColis,        idColis),
        idTransporteur  = COALESCE(p_idTransporteur, idTransporteur),
        dateEffective   = CASE WHEN p_statut = 'expedie' THEN CURRENT_DATE ELSE dateEffective END
    WHERE idBon = p_idBon;

    IF NOT FOUND THEN RAISE EXCEPTION 'Bon expédition % introuvable.', p_idBon; END IF;
END;
$$;

-- =============================================================
--  CRUD — Rapport d'exception
-- =============================================================

CREATE OR REPLACE FUNCTION sge_insert_rapport_exception(
    p_type          VARCHAR,
    p_description   TEXT,
    p_idBonRec      INTEGER DEFAULT NULL,
    p_idBonExp      INTEGER DEFAULT NULL,
    p_idIndividu    INTEGER DEFAULT NULL
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE v_id INTEGER;
BEGIN
    INSERT INTO Rapport_exception(typeRapport, description,
                                  idBonReception, idBonExpedition, idIndividu)
    VALUES (p_type, p_description, p_idBonRec, p_idBonExp, p_idIndividu)
    RETURNING idRapport INTO v_id;
    RETURN v_id;
END;
$$;
