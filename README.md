# WMS-CLAM-PRO — Système de Gestion d'Entrepôt

**Société Amazones et Centaures (SAC)**

Application de gestion d'entrepôt (Warehouse Management System) développée en
Python. Elle combine une interface graphique Tkinter avec une API REST Flask et
une base de données PostgreSQL.

---

## Table des matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration de la base de données](#configuration-de-la-base-de-données)
4. [Lancement de l'application](#lancement-de-lapplication)
5. [Réinitialisation de la base de données](#réinitialisation-de-la-base-de-données)
6. [Structure du projet](#structure-du-projet)

---

## Prérequis

Avant d'installer le projet, assurez-vous d'avoir les logiciels suivants
installés sur votre machine :

| Logiciel       | Version minimale | Téléchargement                                        |
| -------------- | ---------------- | ----------------------------------------------------- |
| **Python**     | 3.10+            | [python.org](https://www.python.org/downloads/)       |
| **PostgreSQL** | 14+              | [postgresql.org](https://www.postgresql.org/download/) |
| **Git**        | 2.30+            | [git-scm.com](https://git-scm.com/downloads)          |

> **Note :** Lors de l'installation de Python sur Windows, cochez la case
> **« Add Python to PATH »** pour pouvoir l'utiliser depuis le terminal.

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/alfredoisasole-tech/Projet-Integrateur-APP-GRAPHIQUE-.git
cd Projet-Integrateur-APP-GRAPHIQUE-
```

### 2. Créer un environnement virtuel Python

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

Les dépendances principales sont :
- **Flask** — Serveur API REST
- **flask-cors** — Gestion des requêtes Cross-Origin
- **requests** — Client HTTP (communication GUI ↔ API)
- **psycopg2-binary** — Pilote PostgreSQL pour Python

---

## Configuration de la base de données

### 1. Créer l'utilisateur et la base de données PostgreSQL

Ouvrez un terminal PostgreSQL (`psql`) en tant que superutilisateur
(`postgres`) et exécutez :

```sql
-- Créer l'utilisateur
CREATE USER sge_user WITH PASSWORD 'sge_pass';

-- Créer la base de données
CREATE DATABASE sge_db OWNER sge_user;

-- Donner les droits nécessaires
GRANT ALL PRIVILEGES ON DATABASE sge_db TO sge_user;

-- Se connecter à la base
\c sge_db

-- Permettre la création de schémas
GRANT CREATE ON SCHEMA public TO sge_user;
```

> **Important :** Les identifiants ci-dessus correspondent aux valeurs par
> défaut dans le fichier `config.py`. Si vous souhaitez utiliser d'autres
> identifiants, modifiez la section `DATABASE` dans `config.py` :
>
> ```python
> DATABASE = {
>     "host": "localhost",
>     "port": 5432,
>     "dbname": "sge_db",
>     "user": "sge_user",
>     "password": "sge_pass",
>     "schema": "sge",
>     "options": "-c search_path=sge,public",
> }
> ```

### 2. Initialiser le schéma et les données

```bash
python db/setup_db.py
```

Ce script exécute dans l'ordre les fichiers SQL situés dans le dossier
`base de donnee/` :

| Fichier          | Rôle                                      |
| ---------------- | ----------------------------------------- |
| `SGE_cre.sql`    | Création du schéma et des tables          |
| `SGE_inv.sql`    | Invariants et contraintes                 |
| `SGE_imm.sql`    | Données de référence (immutables)         |
| `SGE_req.sql`    | Requêtes et vues SQL                      |
| `SGE_tra.sql`    | Triggers et procédures stockées           |
| `SGE_jdd_01.sql` | Jeu de données de démonstration           |

---

## Lancement de l'application

Une fois la base de données configurée, lancez l'application avec :

```bash
python main.py
```

L'application effectue les étapes suivantes au démarrage :

1. **Connexion à PostgreSQL** — Chargement des données depuis la base `sge_db`.
2. **Démarrage de l'API Flask** — Serveur REST lancé sur `http://127.0.0.1:5001`.
3. **Ouverture de l'interface graphique** — Fenêtre Tkinter WMS-CLAM-PRO.

> **Note :** Le serveur PostgreSQL doit être démarré **avant** de lancer
> l'application. Sur Windows, il est souvent configuré pour démarrer
> automatiquement en tant que service.

---

## Réinitialisation de la base de données

Si vous souhaitez remettre la base de données à son état initial (supprimer
toutes les données et recharger le jeu de démonstration) :

```bash
python reset_db.py
```

Ce script :
1. Supprime le schéma `sge` en cascade (toutes les tables, vues, triggers).
2. Recrée le schéma vide.
3. Recharge tous les fichiers SQL dans l'ordre.
4. Resynchronise les séquences auto-incrémentées.

---

## Structure du projet

```
Projet-Integrateur-APP-GRAPHIQUE-/
│
├── api/                        # API REST Flask
│   ├── server.py               # Configuration et démarrage du serveur
│   ├── dashboard_api.py        # Endpoints du tableau de bord
│   ├── reception_api.py        # Endpoints de réception
│   ├── expedition_api.py       # Endpoints d'expédition
│   ├── inventaire_api.py       # Endpoints d'inventaire
│   ├── gestion_api.py          # CRUD Produits, Lots, Cellules
│   ├── rapports_api.py         # Endpoints de rapports
│   └── admin_api.py            # Administration système
│
├── db/                         # Couche d'accès aux données
│   ├── connection.py           # Gestion de la connexion PostgreSQL
│   ├── sge_database.py         # Requêtes et opérations SQL
│   └── setup_db.py             # Script d'initialisation de la BDD
│
├── gui/                        # Interface graphique Tkinter
│   ├── app.py                  # Fenêtre principale (orchestration)
│   ├── theme.py                # Thème visuel (couleurs, polices)
│   ├── components/             # Composants réutilisables
│   │   ├── sidebar.py          # Barre de navigation latérale
│   │   ├── topbar.py           # Barre supérieure
│   │   ├── footer.py           # Pied de page
│   │   └── widgets.py          # Widgets personnalisés
│   └── views/                  # Écrans de l'application
│       ├── dashboard_view.py   # Tableau de bord
│       ├── cartographie_view.py # Cartographie de l'entrepôt
│       ├── reception_view.py   # Gestion des réceptions
│       ├── expedition_view.py  # Gestion des expéditions
│       ├── inventaire_view.py  # Inventaire des stocks
│       ├── gestion_view.py     # CRUD Produits / Lots / Cellules
│       ├── rapports_view.py    # Rapports et analytics
│       └── admin_view.py       # Administration
│
├── services/                   # Logique métier
│   ├── stockage_service.py     # Service de stockage
│   ├── expedition_service.py   # Service d'expédition
│   └── rapport_service.py      # Service de rapports
│
├── tests/                      # Tests automatisés
│   ├── test_api.py             # Tests de l'API
│   ├── test_gui.py             # Tests de l'interface
│   ├── test_services.py        # Tests des services
│   └── test_validation.py      # Tests de validation
│
├── base de donnee/             # Scripts SQL PostgreSQL
│   ├── SGE_cre.sql             # Création du schéma
│   ├── SGE_inv.sql             # Invariants
│   ├── SGE_imm.sql             # Données de référence
│   ├── SGE_req.sql             # Requêtes / Vues
│   ├── SGE_tra.sql             # Triggers
│   ├── SGE_jdd_01.sql          # Jeu de données
│   ├── SGE_test-pos.sql        # Tests positifs
│   └── SGE_test-neg.sql        # Tests négatifs
│
├── main.py                     # Point d'entrée principal
├── config.py                   # Configuration globale
├── reset_db.py                 # Script de réinitialisation BDD
├── requirements.txt            # Dépendances Python
├── .gitignore                  # Fichiers exclus de Git
└── README.md                   # Ce fichier
```