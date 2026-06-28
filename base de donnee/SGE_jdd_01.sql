-- =============================================================
--  SGE_jdd_01.sql
--  Jeu de données complet — Scénarios 1 à 5
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.2.3
--  Prérequis  : SGE_cre.sql, SGE_inv.sql exécutés
-- =============================================================

BEGIN;

-- =============================================================
--  SCÉNARIO 1 : Initialisation — Organisations, Individus,
--               Produits, Cellules
-- =============================================================

-- ── Organisations ─────────────────────────────────────────────
INSERT INTO Organisation(idOrganisation, nom, adresse, telephone, typeOrg) VALUES
(1, 'PackSol Cameroun',     'Av. de l''Indépendance, Yaoundé',  '+237222001001', 'fournisseur'),
(2, 'LogiTrans SA',         'Zone industrielle, Douala',          '+237233002002', 'transporteur'),
(3, 'DistribuCentre SARL',  'Bp 1234 Bafoussam',                  '+237244003003', 'destinataire'),
(4, 'FourniTech Sarl',      'Rue du Commerce, Bertoua',           '+237255004004', 'fournisseur'),
(5, 'SAC (interne)',        'Siège social SAC, Yaoundé',          '+237222005005', 'autre');

-- ── Individus ─────────────────────────────────────────────────
INSERT INTO Individu(idIndividu, nom, telephone, email) VALUES
(1, 'Marie Ngono',     '+237677100001', 'marie.ngono@sac.cm'),
(2, 'Paul Bello',      '+237677100002', 'paul.bello@sac.cm'),
(3, 'Alice Fouda',     '+237677100003', 'alice.fouda@sac.cm'),
(4, 'Thierry Manga',   '+237677100004', 'thierry.manga@sac.cm'),
(5, 'Robert Etoa',     '+237677100005', 'robert.etoa@sac.cm');

-- ── Répertoire ────────────────────────────────────────────────
INSERT INTO Repertoire(idOrganisation, idIndividu, role, dateDebut) VALUES
(5, 1, 'magasinier',       '2023-01-15'),
(5, 2, 'magasinier',       '2023-01-15'),
(5, 3, 'agent_logistique', '2023-03-01'),
(5, 4, 'conducteur',       '2023-06-01'),
(2, 4, 'conducteur',       '2022-09-01'),
(5, 5, 'autre',            '2024-01-01');

-- ── Produits matériels ────────────────────────────────────────
INSERT INTO Produit(idProduit, nom, description, marque, modele, typeP, idFournisseur) VALUES
(1,  'Boîte carton 60x40x40',    'Boîte standard grande',       'SAC Pack', 'BC-644', 'materiel',  1),
(2,  'Boîte carton 40x30x30',    'Boîte standard moyenne',      'SAC Pack', 'BC-433', 'materiel',  1),
(3,  'Boîte carton 20x15x15',    'Boîte standard petite',       'SAC Pack', 'BC-215', 'materiel',  1),
(4,  'Palette bois 120x80',      'Palette européenne standard',  'PaletPro','PAL-EUR', 'materiel',  1),
(5,  'Caisse plastique 60x40',   'Caisse rigide empilable',     'PlastiCo','CPL-640', 'materiel',  4),
(6,  'Produit électronique A',   'Écran 24 pouces',             'TechBrand','ECR-24', 'materiel',  4),
(7,  'Produit électronique B',   'Clavier sans fil',            'TechBrand','CLV-WL', 'materiel',  4),
(8,  'Produit textile C',        'Lot de 10 chemises',          'ModeSAC',  'CHM-10', 'materiel',  4),
(9,  'Produit alimentaire D',    'Huile de palme 5L',           'AgriSAC',  'HLP-5L', 'materiel',  4),
(10, 'Produit ménager E',        'Détergent 10kg',              'CleanPro', 'DET-10', 'materiel',  4);

INSERT INTO Produit(idProduit, nom, typeP, idFournisseur) VALUES
(11, 'Ruban adhésif 50m',    'emballage', 1),
(12, 'Papier bulle 50x100',  'emballage', 1);

-- Dimensions physiques
INSERT INTO ProduitMateriel(idProduit, longueur, largeur, hauteur, masse) VALUES
(1,  60.0, 40.0, 40.0,  0.50),
(2,  40.0, 30.0, 30.0,  0.30),
(3,  20.0, 15.0, 15.0,  0.15),
(4, 120.0, 80.0, 15.0, 22.00),
(5,  60.0, 40.0, 35.0,  3.00),
(6,  58.0, 40.0, 12.0,  5.80),
(7,  40.0, 20.0,  5.0,  0.90),
(8,  35.0, 25.0, 20.0,  2.50),
(9,  25.0, 20.0, 30.0,  5.20),
(10, 30.0, 25.0, 25.0, 10.00),
(11,  5.0,  5.0, 15.0,  0.08),
(12, 50.0,100.0,  5.0,  0.50);

-- ── Cellules — 20 cellules réparties dans E0-E3, RECEP, EXPED, EMBAL ──
INSERT INTO Cellule(idCellule, longueur, largeur, hauteur, masseMaximale, zone, position) VALUES
-- Zone E0 (6 cellules)
(1,  130.0, 90.0, 210.0, 500.0, 'E0', 'A-01-01'),
(2,  130.0, 90.0, 210.0, 500.0, 'E0', 'A-01-02'),
(3,  130.0, 90.0, 210.0, 500.0, 'E0', 'A-02-01'),
(4,  130.0, 90.0, 210.0, 300.0, 'E0', 'A-02-02'),
(5,  130.0, 90.0, 210.0, 300.0, 'E0', 'A-03-01'),
(6,   80.0, 60.0, 150.0, 150.0, 'E0', 'A-03-02'),
-- Zone E1 (4 cellules)
(7,  130.0, 90.0, 210.0, 500.0, 'E1', 'B-01-01'),
(8,  130.0, 90.0, 210.0, 500.0, 'E1', 'B-01-02'),
(9,  130.0, 90.0, 210.0, 200.0, 'E1', 'B-02-01'),
(10,  80.0, 60.0, 150.0, 150.0, 'E1', 'B-02-02'),
-- Zone E2 (4 cellules)
(11, 130.0, 90.0, 210.0, 500.0, 'E2', 'C-01-01'),
(12, 130.0, 90.0, 210.0, 500.0, 'E2', 'C-01-02'),
(13, 130.0, 90.0, 210.0, 300.0, 'E2', 'C-02-01'),
(14,  80.0, 60.0, 150.0, 150.0, 'E2', 'C-02-02'),
-- Zone E3 (2 cellules)
(15, 130.0, 90.0, 210.0, 500.0, 'E3', 'D-01-01'),
(16, 130.0, 90.0, 210.0, 500.0, 'E3', 'D-01-02'),
-- Zones fonctionnelles
(17, 300.0,200.0, 250.0, 2000.0,'RECEP', 'ZR-01'),
(18, 300.0,200.0, 250.0, 2000.0,'EXPED', 'ZE-01'),
(19, 200.0,150.0, 200.0, 1000.0,'EMBAL', 'ZM-01'),
(20, 100.0, 80.0, 150.0,  500.0,'EMBAL', 'ZM-02');

-- ── Lots initiaux ─────────────────────────────────────────────
INSERT INTO Lot(idLot, idProduit, quantite, origine, dateEntree) VALUES
(1,  1, 50, 'neuf', '2024-01-10'),
(2,  2, 80, 'neuf', '2024-01-10'),
(3,  3,120, 'neuf', '2024-01-10'),
(4,  4, 10, 'neuf', '2024-01-12'),
(5,  5, 20, 'neuf', '2024-01-12'),
(6,  6, 15, 'neuf', '2024-01-15'),
(7,  7, 30, 'neuf', '2024-01-15'),
(8,  8, 25, 'neuf', '2024-01-18'),
(9,  9, 40, 'neuf', '2024-01-20'),
(10,10, 12, 'neuf', '2024-01-20'),
-- Emballage
(11,11,200, 'neuf', '2024-01-05'),
(12,12, 50, 'neuf', '2024-01-05'),
-- Emballage récupéré
(13,11, 30, 'recupere', '2024-01-22'),
(14,12, 10, 'recupere', '2024-01-22');

-- ── Inventaire initial ────────────────────────────────────────
INSERT INTO Inventaire_emplacement(idCellule, idLot, dateDepot) VALUES
(1,  1, '2024-01-10 09:00:00'),
(1,  2, '2024-01-10 09:30:00'),
(2,  3, '2024-01-10 10:00:00'),
(3,  4, '2024-01-12 08:00:00'),
(4,  5, '2024-01-12 08:30:00'),
(7,  6, '2024-01-15 14:00:00'),
(7,  7, '2024-01-15 14:30:00'),
(8,  8, '2024-01-18 11:00:00'),
(11, 9, '2024-01-20 10:00:00'),
(12,10, '2024-01-20 10:30:00'),
(19,11, '2024-01-05 08:00:00'),
(19,12, '2024-01-05 08:00:00'),
(20,13, '2024-01-22 16:00:00'),
(20,14, '2024-01-22 16:00:00');

-- =============================================================
--  SCÉNARIO 2 : Bons de réception en attente
-- =============================================================
INSERT INTO Bon_reception(idBon, idFournisseur, dateAttendue, statut, priorite) VALUES
(1, 1, '2024-02-01', 'en_attente', 1),
(2, 4, '2024-02-03', 'en_attente', 2),
(3, 1, '2024-02-10', 'en_attente', 3);

-- =============================================================
--  SCÉNARIO 3 : Bons d'expédition en attente
-- =============================================================
INSERT INTO Bon_expedition(idBon, idDestinataire, idTransporteur, dateAttendue, statut, priorite) VALUES
(1, 3, 2, '2024-02-02', 'en_attente', 1),
(2, 3, 2, '2024-02-05', 'en_attente', 2);

-- =============================================================
--  SCÉNARIO 4 : Historique mouvements (lot retiré puis re-stocké)
-- =============================================================
-- Lot 9 retiré de cellule 11 le 2024-01-25
UPDATE Inventaire_emplacement
   SET dateRetrait = '2024-01-25 09:00:00'
 WHERE idCellule = 11 AND idLot = 9;

-- Re-stocké en cellule 13
INSERT INTO Inventaire_emplacement(idCellule, idLot, dateDepot)
VALUES (13, 9, '2024-01-25 09:30:00');

-- =============================================================
--  SCÉNARIO 5 : Rapports d'exception existants
-- =============================================================
INSERT INTO Rapport_exception(typeRapport, description, dateRapport, idIndividu) VALUES
('ecart_reception',
 'Colis JDD-001 : 5 unités boîte 60x40x40 manquantes sur les 50 attendues',
 '2024-01-10 10:15:00', 1),
('ecart_stockage',
 'Lot 4 (palettes) : cellule A-02-01 refusée — masse trop proche du seuil',
 '2024-01-12 09:00:00', 2);

-- Rafraîchir la vue matérialisée si elle existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_matviews
        WHERE matviewname = 'mv_inventaire_produit'
    ) THEN
        EXECUTE 'REFRESH MATERIALIZED VIEW mv_inventaire_produit';
    END IF;
END $$;

COMMIT;

-- ── Vérifications post-chargement ─────────────────────────────
DO $$
DECLARE
    nb_org  INTEGER; nb_ind INTEGER; nb_prod INTEGER;
    nb_lot  INTEGER; nb_cel INTEGER; nb_inv  INTEGER;
BEGIN
    SELECT COUNT(*) INTO nb_org  FROM Organisation;
    SELECT COUNT(*) INTO nb_ind  FROM Individu;
    SELECT COUNT(*) INTO nb_prod FROM Produit;
    SELECT COUNT(*) INTO nb_lot  FROM Lot;
    SELECT COUNT(*) INTO nb_cel  FROM Cellule;
    SELECT COUNT(*) INTO nb_inv  FROM Inventaire_emplacement;
    RAISE NOTICE '=== Jeu de données JDD_01 chargé ===';
    RAISE NOTICE '  Organisations : %', nb_org;
    RAISE NOTICE '  Individus     : %', nb_ind;
    RAISE NOTICE '  Produits      : %', nb_prod;
    RAISE NOTICE '  Lots          : %', nb_lot;
    RAISE NOTICE '  Cellules      : %', nb_cel;
    RAISE NOTICE '  Inventaire    : % lignes', nb_inv;
    ASSERT nb_org  = 5,  'Erreur : nombre d''organisations incorrect';
    ASSERT nb_cel  = 20, 'Erreur : nombre de cellules incorrect';
    ASSERT nb_prod = 12, 'Erreur : nombre de produits incorrect';
    RAISE NOTICE '=== Vérifications OK ===';
END $$;
