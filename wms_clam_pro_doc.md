# WMS-CLAM-PRO — Guide de Conception & Documentation Système

Ce document rassemble les informations essentielles concernant l'architecture, la structure, l'origine du nom et les justifications techniques des choix de conception du logiciel **WMS-CLAM-PRO** développé pour la **Société Amazones et Centaures (SAC)**.

---

## 1. Origine du nom : WMS-CLAM-PRO

Le nom **WMS-CLAM-PRO** n'est pas un hasard ; il s'agit d'un acronyme métier qui reflète fidèlement les quatre piliers fondamentaux de la gestion des stocks au sein de notre application :

$$\text{WMS} - \underbrace{\textbf{C}\ \textbf{L}\ \textbf{A}\ \textbf{M}}_{\text{Cores Métiers}} - \text{PRO}$$

*   **WMS** (*Warehouse Management System*) : Indique la catégorie logicielle du produit (gestion de flux physiques, d'emplacements et de préparation de commandes).
*   **C** — **Cellules** : Représente la cartographie physique de l'entrepôt (zones E0, E1, E2, E3, RECEP, EXPED) et la gestion de leurs contraintes (dimensions, masse maximale).
*   **L** — **Lots** : Représente l'unité de stockage tracée (chaque lot possède une quantité, une origine "neuf" ou "récupéré", et une date d'entrée).
*   **A** — **Articles (Produits)** : Le catalogue de référence gérant les spécificités des produits (matériels, logiciels ou emballages) et leurs dimensions physiques.
*   **M** — **Mouvements & Marchandises** : Concerne les flux physiques entrants (Réception) et sortants (Expédition) ainsi que l'affectation dynamique des stocks.
*   **PRO** : Version professionnelle optimisée, garantissant la cohérence transactionnelle de la base de données.

---

## 2. Structure Détaillée du Projet

Le projet adopte une architecture modulaire et découplée (séparation strict du Frontend et du Backend) :

```
sge_project/
│
├── api/                        # BACKEND : Serveur API REST (Flask)
│   ├── server.py               # Point d'entrée de l'API & Middleware CORS
│   ├── dashboard_api.py        # Endpoints pour le Dashboard et la Cartographie
│   ├── gestion_api.py          # Routes CRUD (Produits, Lots, Cellules)
│   ├── reception_api.py        # Logique de réception (Phase A & B)
│   ├── expedition_api.py       # Logique d'expédition
│   ├── inventaire_api.py       # Visualisation des stocks physiques
│   ├── rapports_api.py         # Récupération des rapports d'exceptions
│   └── admin_api.py            # Contrôle et maintenance du serveur
│
├── db/                         # ACCÈS AUX DONNÉES (DAL)
│   ├── connection.py           # Pool de connexions PostgreSQL (thread-safe)
│   ├── sge_database.py         # Requêtes SQL et appels de fonctions PostgreSQL
│   └── setup_db.py             # Script d'initialisation de la base
│
├── gui/                        # FRONTEND : Interface Graphique (Tkinter)
│   ├── app.py                  # Fenêtre maîtresse & routage des vues
│   ├── theme.py                # Design System (Charte graphique "Industrial Light")
│   ├── components/             # Composants d'interface réutilisables
│   │   ├── sidebar.py          # Barre latérale de navigation
│   │   ├── topbar.py           # En-tête avec statut du serveur
│   │   ├── footer.py           # Pied de page avec copyrights
│   │   └── widgets.py          # Widgets sur mesure (DataTable, ZoneMap, StatCard)
│   └── views/                  # Écrans fonctionnels de l'application
│       ├── dashboard_view.py   # Tableau de bord analytique
│       ├── cartographie_view.py # Grilles de l'entrepôt en temps réel
│       ├── reception_view.py   # Interface de réception de marchandises
│       ├── expedition_view.py  # Interface d'expédition
│       ├── inventaire_view.py  # Consultation des stocks en temps réel
│       ├── gestion_view.py     # Administration CRUD des données de base
│       └── rapports_view.py    # Suivi des écarts et rapports d'anomalies
│
├── services/                   # LOGIQUE MÉTIER & ALGORITHMES
│   ├── stockage_service.py     # Algorithme de placement optimal (Glouton 3D)
│   ├── expedition_service.py   # Logique de prélèvement (FIFO/LIFO)
│   └── rapport_service.py      # Générateur d'alertes en cas d'écarts
│
├── base de donnee/             # ENGIN PERSISTANCE (SQL)
│   ├── SGE_cre.sql             # Définition des tables (DDL)
│   ├── SGE_inv.sql             # Contraintes d'intégrité & Vues temps réel
│   ├── SGE_imm.sql             # Initialisation des nomenclatures de base
│   ├── SGE_req.sql             # Fonctions de calcul (Taux d'occupation, etc.)
│   ├── SGE_tra.sql             # Triggers de validation (Calculs de poids automatique)
│   └── SGE_jdd_01.sql          # Jeu de données de test standardisé
│
├── main.py                     # Point d'entrée global de l'application
├── config.py                   # Configuration centralisée (BDD, API, Thème)
├── reset_db.py                 # Utilitaire de réinitialisation de la BDD
└── requirements.txt            # Liste des dépendances Python requises
```

---

## 3. Justifications des Choix de Conception

### 3.1 Architecture Client-Serveur (Flask ↔ Tkinter)
*   **Pourquoi découpler l'interface du code ?**  
    Le fait de séparer le frontend (Tkinter) du backend (Flask API) permet d'isoler complètement la logique de présentation de la logique de calcul.
*   **Évolutivité future** : Si la société SAC décide demain de remplacer l'interface de bureau Tkinter par une application Web (React/Vue) ou une application mobile pour terminaux de codes-barres (Android/iOS), **l'API Flask et toute la logique SQL restent inchangées**.
*   **Résilience** : Le frontend communique via des requêtes HTTP asynchrones (via des threads en tâche de fond). Si un écran plante ou se fige, le serveur API et la base de données ne sont pas corrompus.

### 3.2 Positionnement des Règles Métier (Triggers et Vues SQL)
*   **Pourquoi coder les contraintes côté PostgreSQL plutôt qu'en Python ?**  
    Les contraintes de surcharge (masse maximale d'une cellule), les vérifications d'invariants et le calcul en temps réel du stock sont implémentés sous forme de **triggers (SGE_tra.sql)** et de **vues (SGE_inv.sql)**.
*   **Sécurité absolue de la donnée** : Peu importe l'application qui se connecte à la base de données (l'application WMS, un script d'import Python, ou un outil d'administration comme pgAdmin), il est **physiquement impossible** d'insérer des données incohérentes ou de dépasser la charge maximale autorisée d'une cellule.
*   **Performance** : Les calculs de masse cumulée et d'occupation sont délégués au moteur SQL de PostgreSQL, qui est extrêmement optimisé pour ce type d'opérations d'agrégation.

### 3.3 Pool de Connexions Thread-Safe (`connection.py`)
*   **Pourquoi un pool de connexions ?**  
    L'application Tkinter fait des appels asynchrones sur plusieurs threads pour ne pas bloquer l'interface. En parallèle, Flask traite les requêtes HTTP de manière concourante.
*   **Justification** : Ouvrir et fermer une connexion PostgreSQL à chaque requête est très coûteux en performances. Le pool maintient un ensemble de connexions réutilisables de manière sécurisée sans risque d'accès concurrent destructeur (*Race Conditions*).

### 3.4 Algorithme de Placement (Stockage Glouton 3D)
*   **Pourquoi ce choix ?**  
    Lorsqu'un colis est reçu, le système doit déterminer automatiquement la meilleure cellule disponible. L'algorithme vérifie :
    1. La compatibilité de la zone de stockage.
    2. La capacité physique restante en volume (Longueur $\times$ Largeur $\times$ Hauteur).
    3. La capacité en masse (Masse maximale autorisée de la cellule $-$ Masse actuelle cumulée des lots présents).
*   **Justification** : L'algorithme trie les cellules éligibles selon leur taux d'occupation actuel afin d'optimiser le compactage de l'espace ou d'équilibrer la charge au sein de l'entrepôt.

### 3.5 Choix Graphiques : Charte "Industrial Light" (`theme.py`)
*   **Pourquoi pas le style par défaut de Tkinter ?**  
    Le style d'origine de Tkinter (Windows 95) n'est plus adapté aux standards professionnels modernes.
*   **Justification** : Le design a été entièrement personnalisé avec une palette inspirée du Material Design 3 (couleur primaire bleue `#00629d`, surfaces épurées, typographie à haute lisibilité `Hanken Grotesk` et police monospace `Consolas` / `JetBrains Mono` pour les données tabulaires). Les codes couleur (Vert = Libre, Orange = Partiel, Rouge = Critique/Occupé) permettent une prise de décision rapide et intuitive pour les opérateurs d'entrepôt.
