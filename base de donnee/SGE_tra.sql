-- =============================================================
--  SGE_tra.sql
--  Traitements proposés — procédures de mise à jour
--  Implémente les deux procédés métier complets du SGE
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.3.3
--  Prérequis  : SGE_cre.sql, SGE_inv.sql, SGE_imm.sql
-- =============================================================

-- =============================================================
--  PROCÉDÉ RÉCEPTION — Sous-procédé A
--  Réception immédiate d'un chargement
--  Entrée : idBon (bon de réception en attente), liste de colis
--  Sortie : idColis créé, rapport d'exception si écart
-- =============================================================
CREATE OR REPLACE PROCEDURE sge_tra_reception_immediate(
    p_idBon          INTEGER,
    p_idCelluleZone  INTEGER DEFAULT NULL  -- cellule de la zone RECEP
)
LANGUAGE plpgsql AS $$
DECLARE
    v_idColis    INTEGER;
    v_bon_statut VARCHAR;
BEGIN
    -- 1. Vérifier que le bon est en statut en_attente (RG03)
    SELECT statut INTO v_bon_statut
      FROM Bon_reception WHERE idBon = p_idBon;

    IF v_bon_statut IS NULL THEN
        RAISE EXCEPTION 'Bon de réception % introuvable.', p_idBon;
    END IF;
    IF v_bon_statut <> 'en_attente' THEN
        RAISE EXCEPTION 'RG03 — Bon % n''est pas en statut en_attente (statut actuel : %).', 
            p_idBon, v_bon_statut;
    END IF;

    -- 2. Créer le colis entrant et le placer en zone de réception
    v_idColis := sge_insert_colis('entrant', p_idCelluleZone);

    -- 3. Passer le bon en cours et associer le colis
    --    Le trigger trg_ecart_reception vérifiera les écarts (RG04)
    PERFORM sge_update_statut_bon_reception(p_idBon, 'en_cours', v_idColis);

    RAISE NOTICE 'Réception immédiate — Bon % → Colis % créé en zone de réception.',
        p_idBon, v_idColis;
END;
$$;

-- =============================================================
--  PROCÉDÉ RÉCEPTION — Sous-procédé B
--  Stockage du contenu d'un colis entrant dans les cellules
-- =============================================================
CREATE OR REPLACE PROCEDURE sge_tra_stocker_contenu_colis(p_idColis INTEGER)
LANGUAGE plpgsql AS $$
DECLARE
    r              RECORD;
    v_idCellule    INTEGER;
    v_nb_lots      INTEGER := 0;
    v_idBon        INTEGER;
BEGIN
    -- Vérifier que le colis est entrant et en traitement
    IF NOT EXISTS (SELECT 1 FROM Colis
                    WHERE idColis = p_idColis
                      AND typeColis = 'entrant'
                      AND statut IN ('en_attente', 'en_traitement')) THEN
        RAISE EXCEPTION 'Colis % introuvable, non entrant ou déjà traité.', p_idColis;
    END IF;

    PERFORM sge_update_statut_colis(p_idColis, 'en_traitement');

    -- Pour chaque lot du colis
    FOR r IN
        SELECT cc.idLot, cc.quantiteColis, l.idProduit
          FROM Contenu_Colis cc
          JOIN Lot l ON l.idLot = cc.idLot
         WHERE cc.idColis = p_idColis
    LOOP
        -- Trouver la meilleure cellule disponible pour ce lot
        SELECT idCellule INTO v_idCellule
          FROM sge_req_cellules_disponibles_pour_lot(r.idLot)
         LIMIT 1;

        IF v_idCellule IS NULL THEN
            -- Insérer un rapport d'exception si aucune cellule disponible
            PERFORM sge_insert_rapport_exception(
                'ecart_stockage',
                'Aucune cellule disponible pour le lot ' || r.idLot::TEXT ||
                ' (colis ' || p_idColis::TEXT || ')'
            );
            RAISE WARNING 'Lot % : aucune cellule disponible — rapport d''exception créé.', r.idLot;
            CONTINUE;
        END IF;

        -- Stocker le lot dans la cellule (trigger trg_masse_max actif)
        PERFORM sge_stocker_lot(r.idLot, v_idCellule);
        v_nb_lots := v_nb_lots + 1;

        RAISE NOTICE 'Lot % → cellule % (%).', r.idLot, v_idCellule,
            (SELECT zone || '-' || position FROM Cellule WHERE idCellule = v_idCellule);
    END LOOP;

    -- Clôturer le colis et le bon associé
    PERFORM sge_update_statut_colis(p_idColis, 'traite');
    -- Le trigger trg_emballage_recupere crée les lots d'emballage récupéré (RG05)

    -- Passer le bon en statut traite
    SELECT idBon INTO v_idBon
      FROM Bon_reception WHERE idColis = p_idColis;
    IF v_idBon IS NOT NULL THEN
        UPDATE Bon_reception
           SET statut = 'traite', dateEffective = CURRENT_DATE
         WHERE idBon = v_idBon;
    END IF;

    -- Rafraîchir la vue matérialisée
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_inventaire_produit;

    RAISE NOTICE 'Colis % : % lot(s) stocké(s).', p_idColis, v_nb_lots;
END;
$$;

-- =============================================================
--  PROCÉDÉ EXPÉDITION — Sous-procédé A
--  Préparation d'un colis d'expédition
-- =============================================================
CREATE OR REPLACE PROCEDURE sge_tra_preparer_expedition(
    p_idBon         INTEGER,
    p_idCelluleZone INTEGER DEFAULT NULL  -- cellule zone EXPED
)
LANGUAGE plpgsql AS $$
DECLARE
    r              RECORD;
    v_idColis      INTEGER;
    v_bon_statut   VARCHAR;
    v_tout_dispo   BOOLEAN := TRUE;
    v_manquants    TEXT    := '';
BEGIN
    -- 1. Vérifier statut bon (RG03)
    SELECT statut INTO v_bon_statut
      FROM Bon_expedition WHERE idBon = p_idBon;

    IF v_bon_statut IS NULL THEN
        RAISE EXCEPTION 'Bon d''expédition % introuvable.', p_idBon;
    END IF;
    IF v_bon_statut <> 'en_attente' THEN
        RAISE EXCEPTION 'RG03 — Bon % non en statut en_attente.', p_idBon;
    END IF;

    -- 2. Créer le colis sortant
    v_idColis := sge_insert_colis('sortant', p_idCelluleZone);

    -- 3. Vérifier disponibilité de tous les lots requis (RG04)
    FOR r IN
        SELECT cc.idLot, cc.quantiteColis, p.nom AS produit
          FROM Contenu_Colis cc
          JOIN Lot l ON l.idLot = cc.idLot
          JOIN Produit p ON p.idProduit = l.idProduit
         WHERE cc.idColis = v_idColis   -- à remplacer par table de lignes bon
    LOOP
        IF NOT EXISTS (SELECT 1 FROM Inventaire_emplacement ie
                        WHERE ie.idLot = r.idLot AND ie.dateRetrait IS NULL) THEN
            v_tout_dispo := FALSE;
            v_manquants := v_manquants || ' [Lot ' || r.idLot::TEXT
                           || ' — ' || r.produit || ']';
        END IF;
    END LOOP;

    IF NOT v_tout_dispo THEN
        PERFORM sge_insert_rapport_exception(
            'ecart_expedition',
            'Produits indisponibles pour bon ' || p_idBon::TEXT || ' :' || v_manquants
        );
        -- Passer le bon en annule si produits manquants
        UPDATE Bon_expedition SET statut = 'annule' WHERE idBon = p_idBon;
        RAISE EXCEPTION 'Expédition annulée — produits manquants : %.', v_manquants;
    END IF;

    -- 4. Passer le bon en cours
    PERFORM sge_update_statut_bon_expedition(p_idBon, 'en_cours', v_idColis);

    -- 5. Déstockage selon itinéraire optimal
    FOR r IN
        SELECT * FROM sge_req_itineraire_destockage(v_idColis)
    LOOP
        PERFORM sge_retirer_lot(r.idLot, r.idCellule);
        RAISE NOTICE 'Étape % — Lot % retiré de cellule % (%).', 
            r.etape, r.idLot, r.idCellule, r.zone || '-' || r.position;
    END LOOP;

    -- 6. Placer le colis en zone d'expédition
    PERFORM sge_update_statut_colis(v_idColis, 'en_attente');

    RAISE NOTICE 'Expédition préparée — Bon % → Colis % en zone EXPED.', 
        p_idBon, v_idColis;
END;
$$;

-- =============================================================
--  PROCÉDÉ EXPÉDITION — Sous-procédé B
--  Prise en charge par le transporteur et chargement
-- =============================================================
CREATE OR REPLACE PROCEDURE sge_tra_confirmer_expedition(
    p_idBon          INTEGER,
    p_idTransporteur INTEGER
)
LANGUAGE plpgsql AS $$
DECLARE
    v_idColis INTEGER;
BEGIN
    -- Récupérer le colis associé au bon
    SELECT idColis INTO v_idColis
      FROM Bon_expedition WHERE idBon = p_idBon;

    IF v_idColis IS NULL THEN
        RAISE EXCEPTION 'Bon % : aucun colis associé — vérifier la préparation.', p_idBon;
    END IF;

    -- Vérification finale + chargement
    PERFORM sge_update_statut_colis(v_idColis, 'expedie');

    -- Clôturer le bon (statut 'traite' — d_statut_bon n'autorise pas 'expedie')
    PERFORM sge_update_statut_bon_expedition(p_idBon, 'traite',
                                              v_idColis, p_idTransporteur);

    RAISE NOTICE 'Expédition confirmée — Bon % / Colis % / Transporteur %.', 
        p_idBon, v_idColis, p_idTransporteur;
END;
$$;

-- =============================================================
--  TRAITEMENT UTILITAIRE : réapprovisionnement manuel d'un lot
-- =============================================================
CREATE OR REPLACE PROCEDURE sge_tra_reapprovisionner_lot(
    p_idProduit INTEGER,
    p_quantite  INTEGER,
    p_idCellule INTEGER,
    p_origine   VARCHAR DEFAULT 'neuf'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_idLot INTEGER;
BEGIN
    -- Créer le lot
    v_idLot := sge_insert_lot(p_idProduit, p_quantite, p_origine);

    -- Le stocker immédiatement
    PERFORM sge_stocker_lot(v_idLot, p_idCellule);

    -- Rafraîchir inventaire
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_inventaire_produit;

    RAISE NOTICE 'Réapprovisionnement : lot % (produit %, qté %, cellule %) créé.',
        v_idLot, p_idProduit, p_quantite, p_idCellule;
END;
$$;

-- =============================================================
--  TRAITEMENT UTILITAIRE : transfert de lot entre cellules
-- =============================================================
CREATE OR REPLACE PROCEDURE sge_tra_transferer_lot(
    p_idLot          INTEGER,
    p_idCelluleSource INTEGER,
    p_idCelluleCible  INTEGER
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Retirer de la source
    PERFORM sge_retirer_lot(p_idLot, p_idCelluleSource);

    -- Stocker dans la cible (trigger masse_max actif)
    PERFORM sge_stocker_lot(p_idLot, p_idCelluleCible);

    RAISE NOTICE 'Lot % transféré : cellule % → cellule %.', 
        p_idLot, p_idCelluleSource, p_idCelluleCible;
END;
$$;

-- =============================================================
--  TRAITEMENT UTILITAIRE : rafraîchissement vue matérialisée
-- =============================================================
CREATE OR REPLACE PROCEDURE sge_tra_refresh_inventaire()
LANGUAGE plpgsql AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_inventaire_produit;
    RAISE NOTICE 'Vue matérialisée mv_inventaire_produit rafraîchie.';
END;
$$;
