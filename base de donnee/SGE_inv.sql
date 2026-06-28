-- =============================================================
--  SGE_inv.sql
--  Invariants : triggers, vues, règles métier RG02-RG07
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.2.2
--  Prérequis  : SGE_cre.sql déjà exécuté
-- =============================================================

-- =============================================================
--  TRIGGER 1 : trg_masse_max
--  Vérifie que la masse cumulée dans une cellule ne dépasse pas
--  masseMaximale avant tout INSERT ou UPDATE (RG02)
-- =============================================================
CREATE OR REPLACE FUNCTION fn_masse_max()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_masse_actuelle NUMERIC := 0;
    v_masse_nouveau  NUMERIC := 0;
    v_masse_max      NUMERIC;
BEGIN
    -- Masse totale déjà stockée dans la cellule cible (lots non retirés, hors lot en cours)
    SELECT COALESCE(SUM(pm.masse * l.quantite), 0)
      INTO v_masse_actuelle
      FROM Inventaire_emplacement ie
      JOIN Lot l ON l.idLot = ie.idLot
      JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
     WHERE ie.idCellule = NEW.idCellule
       AND ie.dateRetrait IS NULL
       AND ie.idLot <> NEW.idLot;   -- exclure la ligne en cours de modification

    -- Masse du lot à déposer (si produit matériel)
    SELECT COALESCE(pm.masse * l.quantite, 0)
      INTO v_masse_nouveau
      FROM Lot l
      LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
     WHERE l.idLot = NEW.idLot;

    -- Capacité de la cellule
    SELECT masseMaximale INTO v_masse_max
      FROM Cellule WHERE idCellule = NEW.idCellule;

    IF (v_masse_actuelle + v_masse_nouveau) > v_masse_max THEN
        RAISE EXCEPTION
            'RG02 — Cellule % : capacité maximale (%.3f kg) dépassée. '
            'Masse actuelle : %.3f kg + nouveau lot : %.3f kg = %.3f kg.',
            NEW.idCellule,
            v_masse_max,
            v_masse_actuelle,
            v_masse_nouveau,
            (v_masse_actuelle + v_masse_nouveau);
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_masse_max
    BEFORE INSERT OR UPDATE ON Inventaire_emplacement
    FOR EACH ROW EXECUTE FUNCTION fn_masse_max();

COMMENT ON FUNCTION fn_masse_max() IS 'Enforce RG02 : masse cumulée ≤ masseMaximale de la cellule';

-- =============================================================
--  TRIGGER 2 : trg_statut_cellule
--  Maintient Cellule.statut synchronisé avec Inventaire_emplacement
--  (dénormalisation intentionnelle pour performance — F2)
-- =============================================================
CREATE OR REPLACE FUNCTION fn_statut_cellule()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_cellule INTEGER;
    v_nb      INTEGER;
BEGIN
    -- Déterminer la cellule concernée (INSERT/UPDATE → NEW, DELETE → OLD)
    v_cellule := COALESCE(NEW.idCellule, OLD.idCellule);

    SELECT COUNT(*) INTO v_nb
      FROM Inventaire_emplacement
     WHERE idCellule = v_cellule
       AND dateRetrait IS NULL;

    UPDATE Cellule
       SET statut = CASE WHEN v_nb > 0 THEN 'occupee' ELSE 'disponible' END
     WHERE idCellule = v_cellule;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_statut_cellule
    AFTER INSERT OR UPDATE OR DELETE ON Inventaire_emplacement
    FOR EACH ROW EXECUTE FUNCTION fn_statut_cellule();

COMMENT ON FUNCTION fn_statut_cellule()
  IS 'Synchronise Cellule.statut après chaque mouvement dans Inventaire_emplacement';

-- =============================================================
--  TRIGGER 3 : trg_ecart_reception
--  Génère un Rapport_exception lors d'un écart à la réception (RG04)
--  Déclenché : AFTER UPDATE statut → 'en_cours' sur Bon_reception
-- =============================================================
CREATE OR REPLACE FUNCTION fn_ecart_reception()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_ecart BOOLEAN := FALSE;
    v_desc  TEXT    := '';
BEGIN
    IF NEW.statut = 'en_cours' AND OLD.statut = 'en_attente'
       AND NEW.idColis IS NOT NULL THEN

        -- Vérifier si le colis contient tous les lots attendus (simplification)
        -- En pratique : comparer Contenu_Colis avec les lignes du bon (table à enrichir)
        SELECT EXISTS (
            SELECT 1 FROM Contenu_Colis cc
             WHERE cc.idColis = NEW.idColis
               AND cc.quantiteColis <> (
                   SELECT COALESCE(l.quantite, 0) FROM Lot l
                    WHERE l.idLot = cc.idLot)
        ) INTO v_ecart;

        IF v_ecart THEN
            v_desc := 'Écart de quantité détecté sur le bon de réception n° ' || NEW.idBon::TEXT;
            INSERT INTO Rapport_exception (typeRapport, description, idBonReception)
            VALUES ('ecart_reception', v_desc, NEW.idBon);
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_ecart_reception
    AFTER UPDATE ON Bon_reception
    FOR EACH ROW EXECUTE FUNCTION fn_ecart_reception();

-- =============================================================
--  TRIGGER 4 : trg_ecart_expedition
--  Génère un Rapport_exception si un produit est indisponible (RG04)
-- =============================================================
CREATE OR REPLACE FUNCTION fn_ecart_expedition()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_desc TEXT;
BEGIN
    IF NEW.statut = 'en_cours' AND OLD.statut = 'en_attente'
       AND NEW.idColis IS NOT NULL THEN

        -- Vérifier la disponibilité de chaque lot du colis
        IF EXISTS (
            SELECT 1 FROM Contenu_Colis cc
             WHERE cc.idColis = NEW.idColis
               AND NOT EXISTS (
                   SELECT 1 FROM Inventaire_emplacement ie
                    WHERE ie.idLot = cc.idLot
                      AND ie.dateRetrait IS NULL)
        ) THEN
            v_desc := 'Produit(s) indisponible(s) pour le bon d''expédition n° '
                      || NEW.idBon::TEXT;
            INSERT INTO Rapport_exception (typeRapport, description, idBonExpedition)
            VALUES ('ecart_expedition', v_desc, NEW.idBon);
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_ecart_expedition
    AFTER UPDATE ON Bon_expedition
    FOR EACH ROW EXECUTE FUNCTION fn_ecart_expedition();

-- =============================================================
--  TRIGGER 5 : trg_emballage_recupere
--  Crée automatiquement des lots d'emballage récupéré
--  lors du traitement d'un colis entrant (RG05)
-- =============================================================
CREATE OR REPLACE FUNCTION fn_emballage_recupere()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.statut = 'traite' AND OLD.statut <> 'traite'
       AND NEW.typeColis = 'entrant' THEN

        -- Créer un lot d'emballage récupéré pour chaque produit d'emballage du colis
        INSERT INTO Lot (idProduit, quantite, origine, dateEntree)
        SELECT l.idProduit,                    -- idProduit (correctif BUG-05)
               cc.quantiteColis,
               'recupere',
               CURRENT_DATE
          FROM Contenu_Colis cc
          JOIN Lot l ON l.idLot = cc.idLot
          JOIN Produit p ON p.idProduit = l.idProduit
         WHERE cc.idColis = NEW.idColis
           AND p.typeP = 'emballage';

    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_emballage_recupere
    AFTER UPDATE ON Colis
    FOR EACH ROW EXECUTE FUNCTION fn_emballage_recupere();

-- =============================================================
--  VUE 1 : v_stock_temps_reel  (F1 — gestion des stocks)
-- =============================================================
CREATE OR REPLACE VIEW v_stock_temps_reel AS
    SELECT
        p.idProduit,
        p.nom         AS produit,
        p.typeP,
        l.idLot,
        l.quantite,
        l.origine,
        l.dateEntree,
        c.idCellule,
        c.zone,
        c.position,
        c.statut      AS statut_cellule,
        ie.dateDepot
    FROM Inventaire_emplacement ie
    JOIN Lot     l ON l.idLot     = ie.idLot
    JOIN Produit p ON p.idProduit = l.idProduit
    JOIN Cellule c ON c.idCellule = ie.idCellule
   WHERE ie.dateRetrait IS NULL;

COMMENT ON VIEW v_stock_temps_reel IS 'F1 — Stock actuel : lots non retirés avec localisation';

-- =============================================================
--  VUE 2 : v_taux_occupation  (F2 — optimisation espace)
-- =============================================================
CREATE OR REPLACE VIEW v_taux_occupation AS
    SELECT
        c.idCellule,
        c.zone,
        c.position,
        c.masseMaximale,
        COALESCE(SUM(pm.masse * l.quantite), 0)         AS masse_actuelle_kg,
        c.masseMaximale
            - COALESCE(SUM(pm.masse * l.quantite), 0)   AS capacite_residuelle_kg,
        ROUND(
            100.0 * COALESCE(SUM(pm.masse * l.quantite), 0)
            / c.masseMaximale,
        1)                                               AS taux_occupation_pct,
        c.statut
    FROM Cellule c
    LEFT JOIN Inventaire_emplacement ie
        ON ie.idCellule = c.idCellule AND ie.dateRetrait IS NULL
    LEFT JOIN Lot l             ON l.idLot     = ie.idLot
    LEFT JOIN ProduitMateriel pm ON pm.idProduit = l.idProduit
   GROUP BY c.idCellule, c.zone, c.position, c.masseMaximale, c.statut;

COMMENT ON VIEW v_taux_occupation IS 'F2 — Taux d''occupation par cellule';

-- =============================================================
--  VUE 3 : v_cellules_disponibles  (F2 — choix emplacement)
-- =============================================================
CREATE OR REPLACE VIEW v_cellules_disponibles AS
    SELECT idCellule, zone, position,
           masseMaximale, capacite_residuelle_kg, taux_occupation_pct
      FROM v_taux_occupation
     WHERE statut IN ('disponible', 'occupee')
       AND capacite_residuelle_kg > 0
     ORDER BY zone, capacite_residuelle_kg DESC;

-- =============================================================
--  VUE 4 : v_bons_reception_attente  (F3 — planification)
-- =============================================================
CREATE OR REPLACE VIEW v_bons_reception_attente AS
    SELECT
        br.idBon,
        o.nom         AS fournisseur,
        br.dateAttendue,
        br.priorite,
        br.statut,
        br.idColis
    FROM Bon_reception br
    JOIN Organisation o ON o.idOrganisation = br.idFournisseur
   WHERE br.statut = 'en_attente'
   ORDER BY br.priorite ASC, br.dateAttendue ASC;

-- =============================================================
--  VUE 5 : v_bons_expedition_attente  (F3 — planification)
-- =============================================================
CREATE OR REPLACE VIEW v_bons_expedition_attente AS
    SELECT
        be.idBon,
        o.nom         AS destinataire,
        be.dateAttendue,
        be.priorite,
        be.statut,
        be.idColis
    FROM Bon_expedition be
    JOIN Organisation o ON o.idOrganisation = be.idDestinataire
   WHERE be.statut = 'en_attente'
   ORDER BY be.priorite ASC, be.dateAttendue ASC;

-- =============================================================
--  VUE 6 : v_rapports_exception  (F4 — rapports)
-- =============================================================
CREATE OR REPLACE VIEW v_rapports_exception AS
    SELECT
        re.idRapport,
        re.typeRapport,
        re.description,
        re.dateRapport,
        re.idBonReception,
        re.idBonExpedition,
        i.nom AS agent
    FROM Rapport_exception re
    LEFT JOIN Individu i ON i.idIndividu = re.idIndividu
   ORDER BY re.dateRapport DESC;

-- =============================================================
--  VUE MATÉRIALISÉE : mv_inventaire_produit  (F1/F4)
-- =============================================================
CREATE MATERIALIZED VIEW mv_inventaire_produit AS
    SELECT
        p.idProduit,
        p.nom,
        p.typeP,
        SUM(l.quantite) AS quantite_totale
    FROM Lot l
    JOIN Produit p ON p.idProduit = l.idProduit
   GROUP BY p.idProduit, p.nom, p.typeP
  WITH DATA;

CREATE UNIQUE INDEX ON mv_inventaire_produit(idProduit);

COMMENT ON MATERIALIZED VIEW mv_inventaire_produit
  IS 'F1/F4 — Quantité totale en stock par produit (rafraîchir après chaque lot)';
