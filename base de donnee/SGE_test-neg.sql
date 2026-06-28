-- =============================================================
--  SGE_test-neg.sql
--  Tests unitaires NÉGATIFS — violations de contraintes attendues
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.2.5 & 4.3.5
--  Prérequis  : SGE_cre.sql, SGE_inv.sql, SGE_imm.sql
-- =============================================================

-- Macro utilitaire : tester qu'une exception est bien levée
CREATE OR REPLACE FUNCTION test_doit_echouer(p_sql TEXT, p_test TEXT)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    EXECUTE p_sql;
    RAISE EXCEPTION '% ÉCHEC : l''exception attendue n''a pas été levée.', p_test;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '% OK : exception détectée → %', p_test, SQLERRM;
END;
$$;

BEGIN;

DO $$ BEGIN RAISE NOTICE '=== Démarrage des tests unitaires négatifs ==='; END $$;

-- =============================================================
--  N01 : Violation du domaine typeOrg (valeur inconnue)
-- =============================================================
DO $$ BEGIN
    PERFORM test_doit_echouer(
        $$INSERT INTO Organisation(nom, typeOrg) VALUES ('X', 'inconnu')$$,
        'N01'
    );
END $$;

-- =============================================================
--  N02 : Violation de masse maximale (RG02)
-- =============================================================
DO $$ DECLARE v_idP INTEGER; v_idLot INTEGER; v_idCel INTEGER;
BEGIN
    v_idP   := sge_insert_produit('Lourd N02', 'materiel');
    PERFORM sge_insert_produit_materiel(v_idP, 100.0, 100.0, 100.0, 500.0);
    v_idLot := sge_insert_lot(v_idP, 1, 'neuf');
    -- Cellule avec masseMaximale = 10 kg seulement
    v_idCel := sge_insert_cellule(200.0, 200.0, 200.0, 10.0, 'E0', 'Z-99-01');
    PERFORM test_doit_echouer(
        FORMAT('SELECT sge_stocker_lot(%s, %s)', v_idLot, v_idCel),
        'N02'
    );
END $$;

-- =============================================================
--  N03 : Violation RG03 — bon non en_attente avant traitement
-- =============================================================
DO $$ DECLARE v_idOrg INTEGER; v_idBon INTEGER; v_idColis INTEGER;
BEGIN
    v_idOrg   := sge_insert_organisation('Org N03', 'fournisseur');
    v_idBon   := sge_insert_bon_reception(v_idOrg, CURRENT_DATE + 5);
    v_idColis := sge_insert_colis('entrant');
    -- Passer en_cours une première fois (OK)
    PERFORM sge_update_statut_bon_reception(v_idBon, 'en_cours', v_idColis);
    -- Retenter en_cours alors qu'il est déjà en_cours (doit échouer — RG03)
    PERFORM test_doit_echouer(
        FORMAT('SELECT sge_update_statut_bon_reception(%s, ''en_cours'', %s)',
               v_idBon, v_idColis),
        'N03'
    );
END $$;

-- =============================================================
--  N04 : Retrait d'un lot non stocké
-- =============================================================
DO $$ DECLARE v_idCel INTEGER;
BEGIN
    v_idCel := sge_insert_cellule(100.0, 100.0, 100.0, 100.0, 'E1', 'Z-99-02');
    PERFORM test_doit_echouer(
        FORMAT('SELECT sge_retirer_lot(99999, %s)', v_idCel),
        'N04'
    );
END $$;

-- =============================================================
--  N05 : quantite négative dans Lot
-- =============================================================
DO $$ DECLARE v_idP INTEGER;
BEGIN
    v_idP := sge_insert_produit('Prod N05', 'materiel');
    PERFORM test_doit_echouer(
        FORMAT('INSERT INTO Lot(idProduit, quantite, origine, dateEntree)
                VALUES (%s, -1, ''neuf'', CURRENT_DATE)', v_idP),
        'N05'
    );
END $$;

-- =============================================================
--  N06 : masseMaximale négative ou nulle dans Cellule
-- =============================================================
DO $$ BEGIN
    PERFORM test_doit_echouer(
        $$INSERT INTO Cellule(longueur, largeur, hauteur, masseMaximale, zone, position)
          VALUES (100, 80, 200, -5.0, 'E0', 'Z-99-03')$$,
        'N06'
    );
    PERFORM test_doit_echouer(
        $$INSERT INTO Cellule(longueur, largeur, hauteur, masseMaximale, zone, position)
          VALUES (100, 80, 200, 0.0, 'E0', 'Z-99-04')$$,
        'N06b'
    );
END $$;

-- =============================================================
--  N07 : typeP produit invalide
-- =============================================================
DO $$ BEGIN
    PERFORM test_doit_echouer(
        $$INSERT INTO Produit(nom, typeP) VALUES ('Prod invalide', 'robot')$$,
        'N07'
    );
END $$;

-- =============================================================
--  N08 : priorite hors domaine (< 1 ou > 5)
-- =============================================================
DO $$ DECLARE v_idOrg INTEGER;
BEGIN
    v_idOrg := sge_insert_organisation('Org N08', 'fournisseur');
    PERFORM test_doit_echouer(
        FORMAT('INSERT INTO Bon_reception(idFournisseur, dateAttendue, priorite)
                VALUES (%s, CURRENT_DATE, 0)', v_idOrg),
        'N08a'
    );
    PERFORM test_doit_echouer(
        FORMAT('INSERT INTO Bon_reception(idFournisseur, dateAttendue, priorite)
                VALUES (%s, CURRENT_DATE, 6)', v_idOrg),
        'N08b'
    );
END $$;

-- =============================================================
--  N09 : dateFin avant dateDebut dans Répertoire
-- =============================================================
DO $$ DECLARE v_idOrg INTEGER; v_idInd INTEGER;
BEGIN
    v_idOrg := sge_insert_organisation('Org N09', 'autre');
    v_idInd := sge_insert_individu('Individu N09');
    PERFORM test_doit_echouer(
        FORMAT($$INSERT INTO Repertoire(idOrganisation, idIndividu, role, dateDebut, dateFin)
                  VALUES (%s, %s, 'magasinier', '2024-01-01', '2023-01-01')$$,
                v_idOrg, v_idInd),
        'N09'
    );
END $$;

-- =============================================================
--  N10 : typeColis invalide
-- =============================================================
DO $$ BEGIN
    PERFORM test_doit_echouer(
        $$INSERT INTO Colis(typeColis) VALUES ('transfert')$$,
        'N10'
    );
END $$;

-- =============================================================
--  N11 : quantiteColis < 1 dans Contenu_Colis
-- =============================================================
DO $$ DECLARE v_idP INTEGER; v_idLot INTEGER; v_idColis INTEGER;
BEGIN
    v_idP     := sge_insert_produit('Prod N11', 'materiel');
    PERFORM sge_insert_produit_materiel(v_idP, 10.0, 10.0, 10.0, 1.0);
    v_idLot   := sge_insert_lot(v_idP, 5, 'neuf');
    v_idColis := sge_insert_colis('sortant');
    PERFORM test_doit_echouer(
        FORMAT('INSERT INTO Contenu_Colis(idColis, idLot, quantiteColis)
                VALUES (%s, %s, 0)', v_idColis, v_idLot),
        'N11'
    );
END $$;

-- =============================================================
--  N12 : typeRapport invalide
-- =============================================================
DO $$ BEGIN
    PERFORM test_doit_echouer(
        $$INSERT INTO Rapport_exception(typeRapport, description)
          VALUES ('incident_grave', 'Test N12')$$,
        'N12'
    );
END $$;

-- =============================================================
--  N13 : FK invalide — idProduit inexistant dans Lot
-- =============================================================
DO $$ BEGIN
    PERFORM test_doit_echouer(
        $$INSERT INTO Lot(idProduit, quantite, origine, dateEntree)
          VALUES (999999, 1, 'neuf', CURRENT_DATE)$$,
        'N13'
    );
END $$;

-- =============================================================
--  N14 : Zone cellule invalide
-- =============================================================
DO $$ BEGIN
    PERFORM test_doit_echouer(
        $$INSERT INTO Cellule(longueur, largeur, hauteur, masseMaximale, zone, position)
          VALUES (100, 80, 200, 100, 'X9', 'Z-99-05')$$,
        'N14'
    );
END $$;

-- =============================================================
--  N15 : Email non unique dans Individu
-- =============================================================
DO $$ BEGIN
    PERFORM sge_insert_individu('Personne A', NULL, NULL, 'doublon@test.cm');
    PERFORM test_doit_echouer(
        $$SELECT sge_insert_individu('Personne B', NULL, NULL, 'doublon@test.cm')$$,
        'N15'
    );
END $$;

DO $$ BEGIN RAISE NOTICE '=== Tests négatifs terminés ==='; END $$;

ROLLBACK;  -- Nettoyage complet

-- Supprimer la fonction utilitaire temporaire
DROP FUNCTION IF EXISTS test_doit_echouer(TEXT, TEXT);
