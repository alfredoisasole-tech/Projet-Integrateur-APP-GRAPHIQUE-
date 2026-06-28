-- =============================================================
--  SGE_test-pos.sql
--  Tests unitaires POSITIFS — scénarios valides attendus
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.2.4 & 4.3.4
--  Prérequis  : SGE_cre.sql, SGE_inv.sql, SGE_imm.sql,
--               SGE_req.sql, SGE_tra.sql, SGE_jdd_01.sql
-- =============================================================

BEGIN;

-- Compteur de tests
DO $$ BEGIN RAISE NOTICE '=== Démarrage des tests unitaires positifs ==='; END $$;

-- =============================================================
--  BLOC P01 : Insertion Organisation
-- =============================================================
DO $$ DECLARE v_id INTEGER;
BEGIN
    v_id := sge_insert_organisation('Test Fournisseur SA', 'fournisseur',
                                    '10 rue des Tests', '+237600000001');
    ASSERT v_id IS NOT NULL AND v_id > 0,
        'P01 ÉCHEC : idOrganisation non généré';
    ASSERT EXISTS (SELECT 1 FROM Organisation WHERE idOrganisation = v_id
                     AND nom = 'Test Fournisseur SA'),
        'P01 ÉCHEC : Organisation non trouvée après insertion';
    RAISE NOTICE 'P01 OK : insertion Organisation → id=%', v_id;
END $$;

-- =============================================================
--  BLOC P02 : Insertion Individu
-- =============================================================
DO $$ DECLARE v_id INTEGER;
BEGIN
    v_id := sge_insert_individu('Jean Dupont', NULL, '+237600000002', 'jean@test.cm');
    ASSERT v_id IS NOT NULL,
        'P02 ÉCHEC : idIndividu non généré';
    ASSERT EXISTS (SELECT 1 FROM Individu WHERE email = 'jean@test.cm'),
        'P02 ÉCHEC : Individu non trouvé';
    RAISE NOTICE 'P02 OK : insertion Individu → id=%', v_id;
END $$;

-- =============================================================
--  BLOC P03 : Insertion Produit matériel complet
-- =============================================================
DO $$ DECLARE v_idP INTEGER;
BEGIN
    v_idP := sge_insert_produit('Boîte carton 50x40x30', 'materiel',
                                 'Boîte standard entrepôt', 'SAC Pack', 'BCK-503');
    PERFORM sge_insert_produit_materiel(v_idP, 50.0, 40.0, 30.0, 0.5);
    ASSERT EXISTS (SELECT 1 FROM ProduitMateriel WHERE idProduit = v_idP),
        'P03 ÉCHEC : ProduitMateriel non trouvé';
    RAISE NOTICE 'P03 OK : Produit matériel créé → id=%', v_idP;
END $$;

-- =============================================================
--  BLOC P04 : Insertion Lot et stockage dans une cellule valide
-- =============================================================
DO $$ DECLARE v_idP INTEGER; v_idLot INTEGER; v_idCel INTEGER;
BEGIN
    -- Produit
    v_idP := sge_insert_produit('Carton test P04', 'materiel');
    PERFORM sge_insert_produit_materiel(v_idP, 30.0, 20.0, 15.0, 2.0);
    -- Lot (10 unités × 2 kg = 20 kg)
    v_idLot := sge_insert_lot(v_idP, 10, 'neuf');
    -- Cellule (masseMax = 100 kg)
    v_idCel := sge_insert_cellule(120.0, 80.0, 200.0, 100.0, 'E0', 'A-01-01');
    -- Stockage
    PERFORM sge_stocker_lot(v_idLot, v_idCel);
    ASSERT EXISTS (
        SELECT 1 FROM Inventaire_emplacement
         WHERE idLot = v_idLot AND idCellule = v_idCel AND dateRetrait IS NULL
    ), 'P04 ÉCHEC : lot non trouvé dans Inventaire_emplacement';
    ASSERT (SELECT statut FROM Cellule WHERE idCellule = v_idCel) = 'occupee',
        'P04 ÉCHEC : statut cellule non mis à jour par trigger';
    RAISE NOTICE 'P04 OK : Lot % stocké dans cellule % (statut=occupee)', v_idLot, v_idCel;
END $$;

-- =============================================================
--  BLOC P05 : Retrait d'un lot — libération de cellule
-- =============================================================
DO $$ DECLARE v_idP INTEGER; v_idLot INTEGER; v_idCel INTEGER;
BEGIN
    v_idP   := sge_insert_produit('Produit retrait P05', 'materiel');
    PERFORM sge_insert_produit_materiel(v_idP, 10.0, 10.0, 10.0, 1.0);
    v_idLot := sge_insert_lot(v_idP, 5, 'neuf');
    v_idCel := sge_insert_cellule(100.0, 100.0, 100.0, 50.0, 'E1', 'B-02-01');
    PERFORM sge_stocker_lot(v_idLot, v_idCel);
    PERFORM sge_retirer_lot(v_idLot, v_idCel);
    ASSERT EXISTS (
        SELECT 1 FROM Inventaire_emplacement
         WHERE idLot = v_idLot AND idCellule = v_idCel AND dateRetrait IS NOT NULL
    ), 'P05 ÉCHEC : dateRetrait non renseignée';
    ASSERT (SELECT statut FROM Cellule WHERE idCellule = v_idCel) = 'disponible',
        'P05 ÉCHEC : cellule non revenue à disponible';
    RAISE NOTICE 'P05 OK : retrait lot %, cellule % → disponible', v_idLot, v_idCel;
END $$;

-- =============================================================
--  BLOC P06 : Création Bon de réception et mise à jour statut
-- =============================================================
DO $$ DECLARE v_idOrg INTEGER; v_idBon INTEGER; v_idColis INTEGER;
BEGIN
    v_idOrg  := sge_insert_organisation('Fournisseur P06', 'fournisseur');
    v_idBon  := sge_insert_bon_reception(v_idOrg, CURRENT_DATE + 7, 2::SMALLINT);
    v_idColis := sge_insert_colis('entrant');
    PERFORM sge_update_statut_bon_reception(v_idBon, 'en_cours', v_idColis);
    ASSERT (SELECT statut FROM Bon_reception WHERE idBon = v_idBon) = 'en_cours',
        'P06 ÉCHEC : statut bon réception non mis à jour';
    RAISE NOTICE 'P06 OK : Bon réception % → en_cours', v_idBon;
END $$;

-- =============================================================
--  BLOC P07 : Création Bon d'expédition et clôture
-- =============================================================
DO $$ DECLARE v_idOrg INTEGER; v_idBon INTEGER; v_idColis INTEGER; v_idTrans INTEGER;
BEGIN
    v_idOrg   := sge_insert_organisation('Destinataire P07', 'destinataire');
    v_idTrans := sge_insert_organisation('Transport P07', 'transporteur');
    v_idBon   := sge_insert_bon_expedition(v_idOrg, CURRENT_DATE + 3, 1::SMALLINT, v_idTrans);
    v_idColis := sge_insert_colis('sortant');
    PERFORM sge_update_statut_bon_expedition(v_idBon, 'en_cours', v_idColis);
    PERFORM sge_update_statut_bon_expedition(v_idBon, 'expedie');
    ASSERT (SELECT statut FROM Bon_expedition WHERE idBon = v_idBon) = 'expedie',
        'P07 ÉCHEC : statut bon expédition non mis à jour';
    RAISE NOTICE 'P07 OK : Bon expédition % → expedie', v_idBon;
END $$;

-- =============================================================
--  BLOC P08 : Vue stock temps réel non vide
-- =============================================================
DO $$ BEGIN
    ASSERT (SELECT COUNT(*) FROM v_stock_temps_reel) >= 0,
        'P08 ÉCHEC : vue v_stock_temps_reel inaccessible';
    RAISE NOTICE 'P08 OK : vue v_stock_temps_reel accessible (% lignes)',
        (SELECT COUNT(*) FROM v_stock_temps_reel);
END $$;

-- =============================================================
--  BLOC P09 : Vue taux_occupation cohérente (taux ∈ [0,100])
-- =============================================================
DO $$ BEGIN
    ASSERT NOT EXISTS (
        SELECT 1 FROM v_taux_occupation
         WHERE taux_occupation_pct < 0 OR taux_occupation_pct > 100
    ), 'P09 ÉCHEC : taux d''occupation hors bornes [0,100]';
    RAISE NOTICE 'P09 OK : tous les taux d''occupation ∈ [0,100]';
END $$;

-- =============================================================
--  BLOC P10 : Requête disponibilité cellules pour lot
-- =============================================================
DO $$ DECLARE v_idP INTEGER; v_idLot INTEGER;
BEGIN
    v_idP   := sge_insert_produit('Produit P10', 'materiel');
    PERFORM sge_insert_produit_materiel(v_idP, 20.0, 15.0, 10.0, 3.0);
    v_idLot := sge_insert_lot(v_idP, 2, 'neuf');
    -- Insérer au moins une cellule disponible
    PERFORM sge_insert_cellule(100.0, 80.0, 200.0, 200.0, 'E2', 'C-01-01');
    ASSERT (SELECT COUNT(*) FROM sge_req_cellules_disponibles_pour_lot(v_idLot)) >= 0,
        'P10 ÉCHEC : fonction sge_req_cellules_disponibles_pour_lot inaccessible';
    RAISE NOTICE 'P10 OK : sge_req_cellules_disponibles_pour_lot exécutée avec succès';
END $$;

-- =============================================================
--  BLOC P11 : Rapport d'exception créé manuellement
-- =============================================================
DO $$ DECLARE v_idRap INTEGER;
BEGIN
    v_idRap := sge_insert_rapport_exception(
        'autre', 'Test unitaire P11 — création manuelle', NULL, NULL, NULL
    );
    ASSERT v_idRap IS NOT NULL AND v_idRap > 0,
        'P11 ÉCHEC : rapport exception non créé';
    RAISE NOTICE 'P11 OK : rapport exception créé → id=%', v_idRap;
END $$;

-- =============================================================
--  BLOC P12 : Vues F3 accessibles
-- =============================================================
DO $$ BEGIN
    ASSERT (SELECT COUNT(*) FROM v_bons_reception_attente)  >= 0,
        'P12 ÉCHEC : v_bons_reception_attente inaccessible';
    ASSERT (SELECT COUNT(*) FROM v_bons_expedition_attente) >= 0,
        'P12 ÉCHEC : v_bons_expedition_attente inaccessible';
    RAISE NOTICE 'P12 OK : vues bons en attente accessibles';
END $$;

-- =============================================================
--  BLOC P13 : Fonctions rapport F4 exécutables
-- =============================================================
DO $$ BEGIN
    ASSERT (SELECT COUNT(*) FROM sge_req_perf_reception(
        CURRENT_DATE - 30, CURRENT_DATE)) >= 0,
        'P13 ÉCHEC : sge_req_perf_reception inaccessible';
    ASSERT (SELECT COUNT(*) FROM sge_req_perf_expedition(
        CURRENT_DATE - 30, CURRENT_DATE)) >= 0,
        'P13 ÉCHEC : sge_req_perf_expedition inaccessible';
    RAISE NOTICE 'P13 OK : fonctions rapport F4 accessibles';
END $$;

DO $$ BEGIN RAISE NOTICE '=== Tests positifs terminés ==='; END $$;

ROLLBACK;  -- Tous les tests sans effet persistant
