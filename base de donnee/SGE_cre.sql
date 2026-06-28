-- =============================================================
--  SGE_cre.sql
--  Création du schéma de la base de données SGE
--  SGBD cible : PostgreSQL 16+
--  Référence  : SGE_MPS_01 | Section 4.2.1
--  Auteurs    : Équipe Dev — ICAM (UCAC/ULC)
--  Licence    : CC BY-NC-SA 4.0
-- =============================================================

-- Créer et initialiser le schéma SGE
CREATE SCHEMA IF NOT EXISTS sge;
SET search_path = sge, public;

-- Supprimer les objets existants (ordre inverse des dépendances)
DROP TABLE IF EXISTS Rapport_exception   CASCADE;
DROP TABLE IF EXISTS Bon_expedition      CASCADE;
DROP TABLE IF EXISTS Bon_reception       CASCADE;
DROP TABLE IF EXISTS Contenu_Colis       CASCADE;
DROP TABLE IF EXISTS Colis               CASCADE;
DROP TABLE IF EXISTS Inventaire_emplacement CASCADE;
DROP TABLE IF EXISTS Cellule             CASCADE;
DROP TABLE IF EXISTS Lot                 CASCADE;
DROP TABLE IF EXISTS ProduitLogiciel     CASCADE;
DROP TABLE IF EXISTS ProduitMateriel     CASCADE;
DROP TABLE IF EXISTS Produit             CASCADE;
DROP TABLE IF EXISTS Repertoire          CASCADE;
DROP TABLE IF EXISTS Individu            CASCADE;
DROP TABLE IF EXISTS Organisation        CASCADE;

-- Supprimer les domaines si existants
DROP DOMAIN IF EXISTS d_priorite     CASCADE;
DROP DOMAIN IF EXISTS d_statut_bon   CASCADE;
DROP DOMAIN IF EXISTS d_statut_colis CASCADE;

-- =============================================================
--  DOMAINES PERSONNALISÉS
-- =============================================================

-- Priorité de traitement : 1 (haute) à 5 (basse)
CREATE DOMAIN d_priorite AS SMALLINT
  CHECK (VALUE BETWEEN 1 AND 5);

-- Statut d'un bon (réception ou expédition)
CREATE DOMAIN d_statut_bon AS VARCHAR(20)
  CHECK (VALUE IN ('en_attente', 'en_cours', 'traite', 'annule'));

-- Statut d'un colis
CREATE DOMAIN d_statut_colis AS VARCHAR(30)
  CHECK (VALUE IN ('en_attente', 'en_traitement', 'traite', 'expedie'));

-- =============================================================
--  GROUPE : INTERVENANTS
-- =============================================================

-- Organisation (fournisseur, transporteur, destinataire, etc.)
CREATE TABLE Organisation (
    idOrganisation SERIAL       PRIMARY KEY,
    nom            VARCHAR(150) NOT NULL,
    adresse        TEXT,
    telephone      VARCHAR(30),
    typeOrg        VARCHAR(50)  NOT NULL
        CHECK (typeOrg IN ('fournisseur', 'transporteur', 'destinataire', 'autre'))
);

COMMENT ON TABLE Organisation IS 'Organisations impliquées dans la logistique du SGE';
COMMENT ON COLUMN Organisation.typeOrg IS 'fournisseur | transporteur | destinataire | autre';

-- Individu (membre du personnel ou tierce personne)
CREATE TABLE Individu (
    idIndividu SERIAL       PRIMARY KEY,
    nom        VARCHAR(150) NOT NULL,
    adresse    TEXT,
    telephone  VARCHAR(30),
    email      VARCHAR(100) UNIQUE
);

COMMENT ON TABLE Individu IS 'Personnes physiques impliquées dans les procédés du SGE';

-- Répertoire : table associative Individu × Organisation × Rôle
-- Modélise le fait qu'un individu peut avoir plusieurs rôles dans plusieurs organisations (RG06)
CREATE TABLE Repertoire (
    idOrganisation INTEGER     NOT NULL REFERENCES Organisation ON DELETE CASCADE,
    idIndividu     INTEGER     NOT NULL REFERENCES Individu     ON DELETE CASCADE,
    role           VARCHAR(50) NOT NULL
        CHECK (role IN ('conducteur', 'magasinier', 'acheteur',
                        'vendeur', 'agent_logistique', 'autre')),
    dateDebut      DATE        NOT NULL,
    dateFin        DATE        CHECK (dateFin > dateDebut),
    PRIMARY KEY (idOrganisation, idIndividu, role)
);

COMMENT ON TABLE Repertoire IS 'Association Individu × Organisation × Rôle (RG06)';

-- =============================================================
--  GROUPE : PRODUITS
-- =============================================================

-- Produit générique (discriminé par typeP)
CREATE TABLE Produit (
    idProduit     SERIAL       PRIMARY KEY,
    nom           VARCHAR(200) NOT NULL,
    description   TEXT,
    marque        VARCHAR(100),
    modele        VARCHAR(100),
    typeP         VARCHAR(20)  NOT NULL
        CHECK (typeP IN ('materiel', 'logiciel', 'emballage')),
    idFournisseur INTEGER      REFERENCES Organisation
);

COMMENT ON TABLE Produit IS 'Catalogue général des produits (materiel | logiciel | emballage)';
COMMENT ON COLUMN Produit.typeP IS 'Discriminant de spécialisation : materiel | logiciel | emballage';

-- Spécialisation : produit matériel (dimensions physiques)
CREATE TABLE ProduitMateriel (
    idProduit INTEGER        PRIMARY KEY REFERENCES Produit ON DELETE CASCADE,
    longueur  NUMERIC(10, 2) NOT NULL CHECK (longueur > 0),  -- cm
    largeur   NUMERIC(10, 2) NOT NULL CHECK (largeur  > 0),  -- cm
    hauteur   NUMERIC(10, 2) NOT NULL CHECK (hauteur  > 0),  -- cm
    masse     NUMERIC(10, 3) NOT NULL CHECK (masse    > 0)   -- kg
);

COMMENT ON TABLE ProduitMateriel IS 'Attributs physiques des produits matériels (RG02 : masse)';

-- Spécialisation : produit logiciel
CREATE TABLE ProduitLogiciel (
    idProduit     INTEGER      PRIMARY KEY REFERENCES Produit ON DELETE CASCADE,
    version       VARCHAR(50),
    licence       VARCHAR(100),
    supportExpire DATE
);

COMMENT ON TABLE ProduitLogiciel IS 'Attributs spécifiques aux produits logiciels';

-- Lot : regroupement quantifié d'un produit
-- L'attribut origine permet de tracer l'emballage récupéré (RG05)
CREATE TABLE Lot (
    idLot      SERIAL     PRIMARY KEY,
    idProduit  INTEGER    NOT NULL REFERENCES Produit,
    quantite   INTEGER    NOT NULL CHECK (quantite >= 0),
    origine    VARCHAR(20) NOT NULL
        CHECK (origine IN ('neuf', 'recupere')),
    dateEntree DATE       NOT NULL DEFAULT CURRENT_DATE
);

COMMENT ON TABLE Lot IS 'Lot de produits (quantité + origine). Emballage récupéré → origine=recupere (RG05)';

-- =============================================================
--  GROUPE : ENTREPÔT
-- =============================================================

-- Cellule d'entreposage (identifiée par zone + position)
CREATE TABLE Cellule (
    idCellule     SERIAL        PRIMARY KEY,
    longueur      NUMERIC(10, 2) NOT NULL CHECK (longueur > 0),      -- cm
    largeur       NUMERIC(10, 2) NOT NULL CHECK (largeur  > 0),      -- cm
    hauteur       NUMERIC(10, 2) NOT NULL CHECK (hauteur  > 0),      -- cm
    masseMaximale NUMERIC(10, 3) NOT NULL CHECK (masseMaximale > 0), -- kg (RG02)
    zone          VARCHAR(10)   NOT NULL
        CHECK (zone IN ('E0', 'E1', 'E2', 'E3', 'RECEP', 'EXPED', 'EMBAL')),
    position      VARCHAR(50)   NOT NULL,   -- ex. A-03-02
    statut        VARCHAR(20)   NOT NULL DEFAULT 'disponible'
        CHECK (statut IN ('disponible', 'occupee', 'reservee'))
);

COMMENT ON TABLE Cellule IS 'Cellule physique de l''entrepôt. statut maintenu par trigger (dénormalisation intentionnelle)';
COMMENT ON COLUMN Cellule.masseMaximale IS 'Capacité de charge max en kg — contrainte RG02';

-- Inventaire des emplacements (historique complet des mouvements — RG07)
-- Clé primaire composite : une cellule + un lot à un instant donné
CREATE TABLE Inventaire_emplacement (
    idCellule   INTEGER   NOT NULL REFERENCES Cellule ON DELETE RESTRICT,
    idLot       INTEGER   NOT NULL REFERENCES Lot     ON DELETE RESTRICT,
    dateDepot   TIMESTAMP NOT NULL DEFAULT now(),
    dateRetrait TIMESTAMP CHECK (dateRetrait >= dateDepot),
    PRIMARY KEY (idCellule, idLot, dateDepot)
);

COMMENT ON TABLE Inventaire_emplacement
  IS 'Historique des mouvements lot↔cellule (RG07). dateRetrait IS NULL = en place actuellement';

-- Colis (entrant ou sortant)
CREATE TABLE Colis (
    idColis       SERIAL          PRIMARY KEY,
    typeColis     VARCHAR(20)     NOT NULL
        CHECK (typeColis IN ('entrant', 'sortant')),
    dateColis     TIMESTAMP       NOT NULL DEFAULT now(),
    statut        d_statut_colis  NOT NULL DEFAULT 'en_attente',
    idCelluleZone INTEGER         REFERENCES Cellule  -- zone RECEP ou EXPED
);

COMMENT ON TABLE Colis IS 'Colis physique. idCelluleZone = zone de réception ou d''expédition';

-- Contenu d'un colis : association Colis × Lot avec quantité
CREATE TABLE Contenu_Colis (
    idColis       INTEGER NOT NULL REFERENCES Colis ON DELETE CASCADE,
    idLot         INTEGER NOT NULL REFERENCES Lot,
    quantiteColis INTEGER NOT NULL CHECK (quantiteColis >= 1),
    PRIMARY KEY (idColis, idLot)
);

COMMENT ON TABLE Contenu_Colis IS 'Détail des lots contenus dans un colis';

-- =============================================================
--  GROUPE : ARTÉFACTS
-- =============================================================

-- Bon de réception
CREATE TABLE Bon_reception (
    idBon          SERIAL       PRIMARY KEY,
    idFournisseur  INTEGER      NOT NULL REFERENCES Organisation,
    dateAttendue   DATE         NOT NULL,
    dateEffective  DATE,
    statut         d_statut_bon NOT NULL DEFAULT 'en_attente',
    priorite       d_priorite   NOT NULL DEFAULT 3,
    idColis        INTEGER      REFERENCES Colis
);

COMMENT ON TABLE Bon_reception IS 'Bon de réception (RG03 : statut en_attente avant traitement)';
COMMENT ON COLUMN Bon_reception.priorite IS '1=haute priorité, 5=basse priorité';

-- Bon d'expédition
CREATE TABLE Bon_expedition (
    idBon           SERIAL       PRIMARY KEY,
    idDestinataire  INTEGER      NOT NULL REFERENCES Organisation,
    idTransporteur  INTEGER      REFERENCES Organisation,
    dateAttendue    DATE         NOT NULL,
    dateEffective   DATE,
    statut          d_statut_bon NOT NULL DEFAULT 'en_attente',
    priorite        d_priorite   NOT NULL DEFAULT 3,
    idColis         INTEGER      REFERENCES Colis
);

COMMENT ON TABLE Bon_expedition IS 'Bon d''expédition (RG03 : statut en_attente avant traitement)';

-- Rapport d'exception (inséré automatiquement par trigger — RG04)
CREATE TABLE Rapport_exception (
    idRapport       SERIAL      PRIMARY KEY,
    typeRapport     VARCHAR(50) NOT NULL
        CHECK (typeRapport IN ('ecart_reception', 'ecart_stockage',
                               'ecart_expedition', 'ecart_chargement',
                               'masse_depassee', 'autre')),
    description     TEXT        NOT NULL,
    dateRapport     TIMESTAMP   NOT NULL DEFAULT now(),
    idBonReception  INTEGER     REFERENCES Bon_reception,
    idBonExpedition INTEGER     REFERENCES Bon_expedition,
    idIndividu      INTEGER     REFERENCES Individu
);

COMMENT ON TABLE Rapport_exception
  IS 'Rapport d''exception produit automatiquement à chaque écart détecté (RG04)';

-- =============================================================
--  INDEX (performances requêtes F1-F4)
-- =============================================================

CREATE INDEX idx_lot_produit    ON Lot(idProduit);
CREATE INDEX idx_inv_cellule    ON Inventaire_emplacement(idCellule);
CREATE INDEX idx_inv_lot        ON Inventaire_emplacement(idLot);
CREATE INDEX idx_inv_retrait    ON Inventaire_emplacement(dateRetrait);
CREATE INDEX idx_cel_zone       ON Cellule(zone);
CREATE INDEX idx_cel_statut     ON Cellule(statut);
CREATE INDEX idx_br_statut      ON Bon_reception(statut, priorite);
CREATE INDEX idx_be_statut      ON Bon_expedition(statut, priorite);
CREATE INDEX idx_rapport_type   ON Rapport_exception(typeRapport, dateRapport);
