-- =============================================================
--  SGE_req.sql
--  Requêtes proposées — routines équivalentes à des sélections
--  Couvre les fonctionnalités F1, F2, F3, F4
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.3.2
--  Prérequis  : SGE_cre.sql, SGE_inv.sql, SGE_imm.sql
-- =============================================================

-- =============================================================
--  F1 — GESTION DES STOCKS
-- =============================================================

-- Stock temps réel complet
CREATE OR REPLACE FUNCTION sge_req_stock_temps_reel()
RETURNS TABLE (
    idProduit   INT,
    produit     TEXT,
    typeP       TEXT,
    idLot       INT,
    quantite    INT,
    origine     TEXT,
    idCellule   INT,
    zone        TEXT,
    "position"    TEXT,
    dateDepot   TIMESTAMP
) LANGUAGE sql AS $$
    SELECT idProduit, produit, typeP, idLot, quantite, origine,
           idCellule, zone, position, dateDepot
      FROM v_stock_temps_reel
     ORDER BY zone, position, produit;
$$;

-- Stock pour un produit donné
CREATE OR REPLACE FUNCTION sge_req_stock_par_produit(p_idProduit INTEGER)
RETURNS TABLE (
    idLot     INT,
    quantite  INT,
    origine   TEXT,
    idCellule INT,
    zone      TEXT,
    "position"  TEXT,
    dateDepot TIMESTAMP
) LANGUAGE sql AS $$
    SELECT idLot, quantite, origine, idCellule, zone, position, dateDepot
      FROM v_stock_temps_reel
     WHERE idProduit = p_idProduit
     ORDER BY zone, position;
$$;

-- Historique des mouvements d'un lot sur une période
CREATE OR REPLACE FUNCTION sge_req_mouvements_lot(
    p_idLot INTEGER,
    p_debut DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_fin   DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    idCellule   INT,
    zone        TEXT,
    "position"    TEXT,
    dateDepot   TIMESTAMP,
    dateRetrait TIMESTAMP,
    duree_jours NUMERIC
) LANGUAGE sql AS $$
    SELECT
        ie.idCellule,
        c.zone,
        c.position,
        ie.dateDepot,
        ie.dateRetrait,
        ROUND(EXTRACT(EPOCH FROM (
            COALESCE(ie.dateRetrait, now()) - ie.dateDepot
        )) / 86400.0, 1) AS duree_jours
      FROM Inventaire_emplacement ie
      JOIN Cellule c ON c.idCellule = ie.idCellule
     WHERE ie.idLot = p_idLot
       AND ie.dateDepot::DATE BETWEEN p_debut AND p_fin
     ORDER BY ie.dateDepot DESC;
$$;

-- Inventaire agrégé par produit
CREATE OR REPLACE FUNCTION sge_req_inventaire_produit()
RETURNS TABLE (
    idProduit        INT,
    nom              TEXT,
    typeP            TEXT,
    quantite_totale  BIGINT
) LANGUAGE sql AS $$
    SELECT
        p.idProduit,
        p.nom,
        p.typeP,
        COALESCE(SUM(l.quantite), 0) AS quantite_totale
      FROM Produit p
      LEFT JOIN Lot l ON l.idProduit = p.idProduit
     GROUP BY p.idProduit, p.nom, p.typeP
     ORDER BY p.nom;
$$;

-- Lots d'un produit (utilisé par LotRepository)
CREATE OR REPLACE FUNCTION sge_req_lots_by_produit(p_idProduit INTEGER)
RETURNS SETOF Lot LANGUAGE sql AS $$
    SELECT * FROM Lot WHERE idProduit = p_idProduit ORDER BY dateEntree;
$$;

-- =============================================================
--  F2 — OPTIMISATION DE L'ESPACE DE STOCKAGE
-- =============================================================

-- Taux d'occupation global
CREATE OR REPLACE FUNCTION sge_req_taux_occupation()
RETURNS TABLE (
    idCellule             INT,
    zone                  TEXT,
    "position"              TEXT,
    masseMaximale_kg      NUMERIC,
    masse_actuelle_kg     NUMERIC,
    capacite_residuelle_kg NUMERIC,
    taux_occupation_pct   NUMERIC,
    statut                TEXT
) LANGUAGE sql AS $$
    SELECT idCellule, zone, position, masseMaximale,
           masse_actuelle_kg, capacite_residuelle_kg,
           taux_occupation_pct, statut
      FROM v_taux_occupation
     ORDER BY taux_occupation_pct DESC;
$$;

-- Taux d'occupation par zone
CREATE OR REPLACE FUNCTION sge_req_taux_occupation_par_zone()
RETURNS TABLE (
    zone                 TEXT,
    nb_cellules          BIGINT,
    masse_totale_kg      NUMERIC,
    capacite_totale_kg   NUMERIC,
    taux_moyen_pct       NUMERIC
) LANGUAGE sql AS $$
    SELECT
        zone,
        COUNT(*)                                   AS nb_cellules,
        SUM(masse_actuelle_kg)                     AS masse_totale_kg,
        SUM(masseMaximale)                         AS capacite_totale_kg,
        ROUND(100.0 * SUM(masse_actuelle_kg)
              / NULLIF(SUM(masseMaximale), 0), 1)  AS taux_moyen_pct
      FROM v_taux_occupation
     GROUP BY zone
     ORDER BY taux_moyen_pct DESC;
$$;

-- Cellules disponibles pour un lot donné (proposition d'emplacement)
CREATE OR REPLACE FUNCTION sge_req_cellules_disponibles_pour_lot(p_idLot INTEGER)
RETURNS TABLE (
    idCellule             INT,
    zone                  TEXT,
    "position"              TEXT,
    capacite_residuelle_kg NUMERIC,
    taux_occupation_pct   NUMERIC
) LANGUAGE plpgsql AS $$
DECLARE
    v_masse_lot NUMERIC;
BEGIN
    -- Masse du lot à stocker
    SELECT COALESCE(pm.masse * l.quantite, 0)
      INTO v_masse_lot
      FROM Lot l
      LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
     WHERE l.idLot = p_idLot;

    RETURN QUERY
    SELECT
        vo.idCellule,
                vo.zone::text AS zone,
                vo.position::text AS "position",
        vo.capacite_residuelle_kg,
        vo.taux_occupation_pct
      FROM v_taux_occupation vo
     WHERE vo.statut IN ('disponible', 'occupee')
       AND vo.zone IN ('E0', 'E1', 'E2', 'E3')
       AND vo.capacite_residuelle_kg >= COALESCE(v_masse_lot, 0)
     ORDER BY vo.taux_occupation_pct DESC,  -- privilégier les cellules déjà utilisées
              vo.capacite_residuelle_kg ASC;
END;
$$;

-- Calcul d'un itinéraire optimal pour déstockage (liste ordonnée de cellules)
CREATE OR REPLACE FUNCTION sge_req_itineraire_destockage(p_idColis INTEGER)
RETURNS TABLE (
    etape     INT,
    idLot     INT,
    idCellule INT,
    zone      TEXT,
    "position"  TEXT,
    quantite  INT
) LANGUAGE sql AS $$
    SELECT
        ROW_NUMBER() OVER (ORDER BY c.zone, c.position) AS etape,
        cc.idLot,
        ie.idCellule,
        c.zone,
        c.position,
        cc.quantiteColis AS quantite
      FROM Contenu_Colis cc
      JOIN Inventaire_emplacement ie ON ie.idLot = cc.idLot AND ie.dateRetrait IS NULL
      JOIN Cellule c ON c.idCellule = ie.idCellule
     WHERE cc.idColis = p_idColis
     ORDER BY c.zone, c.position;
$$;

-- =============================================================
--  F3 — PLANIFICATION DES OPÉRATIONS
-- =============================================================

-- Bons de réception en attente (triés par priorité)
CREATE OR REPLACE FUNCTION sge_req_bons_reception_attente()
RETURNS TABLE (
    idBon        INT,
    fournisseur  TEXT,
    dateAttendue DATE,
    priorite     SMALLINT,
    statut       TEXT,
    idColis      INT
) LANGUAGE sql AS $$
    SELECT idBon, fournisseur, dateAttendue, priorite, statut, idColis
      FROM v_bons_reception_attente;
$$;

-- Bons d'expédition en attente (triés par priorité)
CREATE OR REPLACE FUNCTION sge_req_bons_expedition_attente()
RETURNS TABLE (
    idBon        INT,
    destinataire TEXT,
    dateAttendue DATE,
    priorite     SMALLINT,
    statut       TEXT,
    idColis      INT
) LANGUAGE sql AS $$
    SELECT idBon, destinataire, dateAttendue, priorite, statut, idColis
      FROM v_bons_expedition_attente;
$$;

-- Vérification de disponibilité d'un colis pour expédition
CREATE OR REPLACE FUNCTION sge_req_verifier_disponibilite_colis(p_idColis INTEGER)
RETURNS TABLE (
    idLot        INT,
    produit      TEXT,
    quantite_bon INT,
    disponible   BOOLEAN,
    idCellule    INT,
    zone         TEXT
) LANGUAGE sql AS $$
    SELECT
        cc.idLot,
        p.nom AS produit,
        cc.quantiteColis AS quantite_bon,
        EXISTS (
            SELECT 1 FROM Inventaire_emplacement ie
             WHERE ie.idLot = cc.idLot AND ie.dateRetrait IS NULL
        ) AS disponible,
        ie2.idCellule,
        c.zone
      FROM Contenu_Colis cc
      JOIN Lot l ON l.idLot = cc.idLot
      JOIN Produit p ON p.idProduit = l.idProduit
      LEFT JOIN Inventaire_emplacement ie2
             ON ie2.idLot = cc.idLot AND ie2.dateRetrait IS NULL
      LEFT JOIN Cellule c ON c.idCellule = ie2.idCellule
     WHERE cc.idColis = p_idColis
     ORDER BY disponible ASC, p.nom;
$$;

-- Stock emballage disponible
CREATE OR REPLACE FUNCTION sge_req_stock_emballage()
RETURNS TABLE (
    idProduit       INT,
    nom             TEXT,
    quantite_neuf   BIGINT,
    quantite_recup  BIGINT,
    quantite_totale BIGINT
) LANGUAGE sql AS $$
    SELECT
        p.idProduit,
        p.nom,
        COALESCE(SUM(l.quantite) FILTER (WHERE l.origine = 'neuf'),      0) AS quantite_neuf,
        COALESCE(SUM(l.quantite) FILTER (WHERE l.origine = 'recupere'),  0) AS quantite_recup,
        COALESCE(SUM(l.quantite), 0) AS quantite_totale
      FROM Produit p
      JOIN Lot l ON l.idProduit = p.idProduit
     WHERE p.typeP = 'emballage'
     GROUP BY p.idProduit, p.nom
     ORDER BY p.nom;
$$;

-- =============================================================
--  F4 — PRODUCTION DE RAPPORTS
-- =============================================================

-- Rapports d'exception sur une période
CREATE OR REPLACE FUNCTION sge_req_rapports_exception(
    p_debut DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_fin   DATE DEFAULT CURRENT_DATE,
    p_type  VARCHAR DEFAULT NULL
) RETURNS TABLE (
    idRapport       INT,
    typeRapport     TEXT,
    description     TEXT,
    dateRapport     TIMESTAMP,
    idBonReception  INT,
    idBonExpedition INT,
    agent           TEXT
) LANGUAGE sql AS $$
    SELECT idRapport, typeRapport, description, dateRapport,
           idBonReception, idBonExpedition, agent
      FROM v_rapports_exception
     WHERE dateRapport::DATE BETWEEN p_debut AND p_fin
       AND (p_type IS NULL OR typeRapport = p_type)
     ORDER BY dateRapport DESC;
$$;

-- Performance des réceptions sur une période
CREATE OR REPLACE FUNCTION sge_req_perf_reception(
    p_debut DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_fin   DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    statut          TEXT,
    nb              BIGINT,
    pct             NUMERIC
) LANGUAGE sql AS $$
    SELECT
        statut,
        COUNT(*)           AS nb,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
      FROM Bon_reception
     WHERE dateAttendue BETWEEN p_debut AND p_fin
     GROUP BY statut
     ORDER BY nb DESC;
$$;

-- Performance des expéditions sur une période
CREATE OR REPLACE FUNCTION sge_req_perf_expedition(
    p_debut DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_fin   DATE DEFAULT CURRENT_DATE
) RETURNS TABLE (
    statut TEXT,
    nb     BIGINT,
    pct    NUMERIC
) LANGUAGE sql AS $$
    SELECT
        statut,
        COUNT(*) AS nb,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
      FROM Bon_expedition
     WHERE dateAttendue BETWEEN p_debut AND p_fin
     GROUP BY statut
     ORDER BY nb DESC;
$$;

-- Rapport synthétique stock par zone
CREATE OR REPLACE FUNCTION sge_req_rapport_stock_par_zone()
RETURNS TABLE (
    zone            TEXT,
    nb_lots         BIGINT,
    nb_produits     BIGINT,
    masse_totale_kg NUMERIC
) LANGUAGE sql AS $$
    SELECT
        s.zone,
        COUNT(DISTINCT s.idLot)     AS nb_lots,
        COUNT(DISTINCT s.idProduit) AS nb_produits,
        COALESCE(SUM(pm.masse * s.quantite), 0) AS masse_totale_kg
      FROM v_stock_temps_reel s
      LEFT JOIN ProduitMateriel pm ON pm.idProduit = s.idProduit
     GROUP BY s.zone
     ORDER BY s.zone;
$$;
