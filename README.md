# 🏠 Immovision Platform

**Plateforme intelligente de gestion et de location / vente immobilière** — Projet de fin d'études (Data Engineering).

SmartRent met en relation clients, propriétaires et administrateurs autour d'annonces immobilières, avec une chaîne complète d'ingénierie des données (Kafka → Spark → data lake → data warehouse → Power BI), des modèles d'intelligence artificielle (estimation de loyer, recommandation, détection de fraude), une cartographie interactive et une recherche avancée.

---

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Structure du dépôt](#structure-du-dépôt)
- [Démarrage rapide (Docker)](#démarrage-rapide-docker)
- [Développement en local](#développement-en-local)
- [URLs et services](#urls-et-services)
- [Intelligence artificielle](#intelligence-artificielle)
- [Pipeline de données](#pipeline-de-données)
- [Base de données et migrations](#base-de-données-et-migrations)
- [Déploiement sur Azure](#déploiement-sur-azure)
- [Sécurité](#sécurité)
- [Problèmes connus](#problèmes-connus)
- [Avancement du projet](#avancement-du-projet)
- [Documentation complémentaire](#documentation-complémentaire)

---

## Fonctionnalités

### Trois espaces utilisateurs

| Rôle | Fonctionnalités principales |
|---|---|
| **Client** | Recherche (onglets Louer / Acheter), filtres avancés, carte interactive, fiche détaillée avec galerie photo, biens similaires, réservation / offre, messagerie, avis, réclamations, historique de recherche |
| **Propriétaire** | Publication d'annonces (location ou vente), suggestion de prix par IA, géolocalisation sur carte, gestion de ses biens, suivi des réservations, contrats, paiements |
| **Administrateur** | Modération des annonces, vérification anti-fraude par IA, gestion des utilisateurs, traitement des réclamations |

### Fonctionnalités transverses

- Authentification **JWT + BCrypt**, contrôle d'accès par rôle
- **Messagerie temps réel** (WebSocket) et **notifications** (in-app, temps réel, email)
- Stockage des photos sur **MinIO** (compatible S3)
- Carrousel photo, fiche détaillée `/biens/:id` avec carte et **commodités à proximité** (hôtels, parcs, écoles, centres commerciaux — calculées une fois via Overpass puis stockées)
- Distinction **vente / location** (`type_transaction`)
- **Recherche avancée Elasticsearch** (texte libre, prix, superficie, pièces, recherche géographique, tri) avec repli automatique sur SQL
- **Historique de recherche** par client (15 dernières recherches, relançables en un clic)
- Confirmation d'une réservation → génération automatique du contrat

---

## Architecture

```
                       Navigateur
                           │
                       Nginx :80/443
              ┌────────────┼─────────────┐
              ▼                          ▼
        Frontend (React)        Backend FastAPI (/api)
                                        │
        ┌───────────┬───────────┬───────┴────┬──────────────┐
        ▼           ▼           ▼            ▼              ▼
   PostgreSQL     MinIO    Elasticsearch   Kafka      Micro-service IA
 (transactionnel) (photos)  (recherche)      │         (estimation,
        ▲                                    ▼          recommandation,
        │                                  Spark         fraude)
        │                                    │
        │                                    ▼
        │                           MinIO (data lake, bronze)
        │                                    │
        └──── schéma dw (étoile) ◀── Airflow (toutes les 10 min)
                      │
                      ▼
                  Power BI
```

---

## Stack technique

| Couche | Technologies |
|---|---|
| Front-end | React, Vite, TypeScript, Tailwind CSS, Leaflet / OpenStreetMap |
| Back-end | FastAPI (Python 3.12), SQLAlchemy, WebSocket, JWT |
| Base transactionnelle | PostgreSQL (UUID via `pgcrypto`, JSONB) |
| Stockage objets | MinIO |
| Recherche | Elasticsearch (analyseur `french`, `geo_point`) |
| Streaming / ETL | Apache Kafka, Spark Structured Streaming |
| Orchestration | Apache Airflow |
| Data warehouse | PostgreSQL, schéma `dw` (modèle en étoile) |
| BI | Power BI |
| IA | scikit-learn (RandomForest, Isolation Forest), similarité cosinus, LightGBM |
| Infra | Docker, Docker Compose, Nginx, Azure VM |

---

## Structure du dépôt

```
location-des-biens/
├── docker-compose.yml          # Stack complète
├── .env.example                # Variables racine (à copier en .env)
├── nginx/nginx.conf            # Point d'entrée unique
├── postgres/
│   ├── smartrent_schema.sql    # Schéma transactionnel
│   ├── warehouse_schema.sql    # Schéma dw (data warehouse)
│   └── migration_*.sql         # Migrations pour une base existante
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── main.py, config.py, database.py, models.py, schemas.py
│   │   ├── security.py, deps.py, storage.py, ws_manager.py
│   │   ├── kafka_producer.py, notifications_service.py
│   │   ├── ml_client.py, es_client.py, poi_client.py
│   │   └── routers/            # auth, biens, reservations, contrats, paiements,
│   │                           # avis, reclamations, messagerie, notifications,
│   │                           # utilisateurs, ia, recherches
│   └── scripts/                # reindex_elasticsearch.py, calculer_proximites_existants.py,
│                               # create_kafka_topics.py
├── ml_service/                 # Micro-service IA (port 8001)
├── ml/                         # Entraînement : scrapers, nettoyage, notebooks, datasets
├── airflow/                    # Dockerfile + DAGs
├── data/spark/                 # Jobs Spark, JAR, configuration
└── frontend/                   # Application React
    └── src/ components/ pages/ (client, proprietaire, admin) types/ lib/ routes/
```

---

## Démarrage rapide (Docker)

Prérequis : Docker et Docker Compose.

```bash
git clone https://github.com/ilhameelma/location-des-biens.git
cd location-des-biens

# Fichiers de configuration (valeurs par défaut valables pour un test local)
cp .env.example .env
cp backend/.env.docker.example backend/.env
cp ml_service/.env.docker.example ml_service/.env

# Lancer toute la stack
docker compose up -d --build
docker compose ps        # attendre "healthy" / "Up"
```

Sur une base déjà peuplée (premier démarrage après mise à jour) :

```bash
docker compose exec backend python scripts/reindex_elasticsearch.py
docker compose exec backend python scripts/calculer_proximites_existants.py
```

> Sous PowerShell, remplacer `cp` par `Copy-Item`.

---

## Développement en local

Pour le rechargement à chaud, on peut lancer chaque service hors Docker (l'infrastructure reste dans Docker).

```bash
# 1. Infrastructure
docker compose up -d postgres minio kafka elasticsearch

# 2. Micro-service IA (port 8001)
cd ml_service && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# 3. Back-end (port 8000)
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 4. Front-end (port 5173)
cd frontend
npm install
npm run dev
```

> ⚠️ Toujours utiliser **`kafka-python-ng`** (et non `kafka-python`) : le paquet officiel est cassé sur Python 3.12.

---

## URLs et services

| Service | URL (Docker, via Nginx) |
|---|---|
| Application SmartRent | http://localhost |
| Documentation API (Swagger) | http://localhost/docs |
| ReDoc | http://localhost/redoc |
| Kafka UI | http://localhost:8082 |
| Console MinIO | http://localhost:9001 |
| Airflow | http://localhost:8081 |
| Elasticsearch | http://localhost:9200 |

En développement local sans Nginx : front `:5173`, API `:8000/docs`, IA `:8001/docs`.

Les identifiants de développement sont définis dans `.env` (voir `.env.example`). **Ne jamais les réutiliser en production.**

---

## Intelligence artificielle

Un micro-service indépendant (`ml_service/`, port 8001) expose trois modèles, appelés uniquement par le back-end (`/api/ia/*`).

| Modèle | Approche | Résultat |
|---|---|---|
| **Estimation de loyer** | RandomForest (vs régression linéaire en baseline) | MAE ≈ 2 679 DH, R² ≈ 0,59 |
| **Recommandation** | Content-based (similarité cosinus), bascule automatique vers le catalogue réel dès 5 biens disponibles | « Biens similaires » + recommandation par critères |
| **Détection de fraude** | Isolation Forest + règle sur l'écart de prix | 97,5 % de détection sur fraude synthétique |

**Données d'entraînement** : ~1 945 annonces collectées sur Mubawab.ma et Sarouty.ma (Avito.ma exclu car son `robots.txt` interdit le crawling), nettoyées et fusionnées, avec target encoding du quartier.

**Intégration** : suggestion de prix (propriétaire), biens similaires (client), vérification de fraude (admin).

---

## Pipeline de données

```
Back-end ──▶ Kafka (5 topics) ──▶ Spark ──▶ MinIO (bronze, partitionné topic/date)
                                              │
                          Airflow (toutes les 10 min) :
      run_kafka_to_datalake_batch ▶ verify_datalake ▶ load_to_warehouse
                                                          │
                                                          ▼
                                       PostgreSQL schéma dw (2 dimensions, 4 faits, 4 vues)
                                                          │
                                                          ▼
                                                      Power BI
```

Power BI se connecte via le connecteur PostgreSQL natif, sur le schéma `dw` uniquement.

---

## Base de données et migrations

`postgres/smartrent_schema.sql` n'est exécuté qu'à la **première création** du volume PostgreSQL. Pour une base existante, appliquer les migrations manuellement :

```bash
cat postgres/migration_type_transaction.sql     | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
cat postgres/migration_proximite_bien.sql       | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
cat postgres/migration_recherche_historique.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
```

Garder `models.py` / `schemas.py` synchronisés avec `smartrent_schema.sql` à chaque évolution.

---

## Déploiement sur Azure

La plateforme tourne sur une seule VM Azure for Students (Ubuntu 24.04, `Standard_B4s_v2`, 4 vCPU / 16 Go, région `polandcentral`), tous les services étant conteneurisés.

**Workflow de mise à jour**

```
PC  : développement + tests → git push origin main
VM  : git pull origin main
VM  : docker compose up -d --build <service_modifié>
VM  : appliquer les migrations SQL si le schéma a changé
```

**Économiser le crédit Azure** : toujours désallouer la VM entre les sessions.

```bash
az vm deallocate --resource-group <groupe> --name <vm>
az vm start      --resource-group <groupe> --name <vm>
```

Tous les services ont `restart: unless-stopped` : la stack redémarre seule après un `az vm start`.

Détails (contraintes de région et de taille de VM propres à Azure for Students, Nginx, HTTPS, sauvegardes) : voir les documents listés plus bas.

---

## Sécurité

- Ne **jamais** commiter de fichier `.env` réel (seuls les `.env.example` sont versionnés) ; vérifier avec `git status` avant chaque push.
- Changer en production : `JWT_SECRET_KEY`, mots de passe PostgreSQL / MinIO / Airflow, `SMTP_PASSWORD`.
- Ne laisser ouverts au public que les ports **22, 80, 443** (NSG Azure + `ufw`) ; fermer 5432, 9200, 9092, 8081, 8082, 9001.
- Activer HTTPS (Let's Encrypt / Certbot) avec un nom de domaine.
- Ne **jamais** exécuter `docker compose down -v` une fois des données réelles présentes (supprime les volumes, donc la base).
- Sauvegarder régulièrement PostgreSQL :
  ```bash
  docker compose exec postgres pg_dump -U smartrent smartrent_db > backup_$(date +%Y%m%d).sql
  ```

---

## Problèmes connus

| Symptôme | Piste |
|---|---|
| Front-end « en retard » | Rebuild (`docker compose up -d --build frontend`) puis rafraîchissement forcé (Ctrl+Shift+R) ; `VITE_API_URL` est figé au build |
| `ModuleNotFoundError: kafka.vendor.six.moves` | Désinstaller `kafka-python` et `kafka-python-ng`, réinstaller uniquement `kafka-python-ng` |
| Elasticsearch `unhealthy` | Souvent `vm.max_map_count` trop bas (WSL2) ; le back-end reste fonctionnel grâce au repli SQL |
| `/docs` affiche l'app React | `nginx.conf` doit router `/docs`, `/redoc`, `/openapi.json` vers le back-end |
| Photos 404 | Vérifier `MINIO_PUBLIC_ENDPOINT` (domaine/IP public, sans port) et la route `/smartrent-photos/` dans Nginx |
| WebSocket ne se connecte pas | `PUBLIC_API_URL` doit être une URL absolue (`http://domaine/api`) |
| Healthcheck frontend `unhealthy` | Cosmétique : cibler `127.0.0.1` plutôt que `localhost` dans le `HEALTHCHECK` |
| Un volume Spark/JAR ignoré | `docker restart smartrent_spark` après tout ajout de JAR |

---

## Avancement du projet

| Phase | Contenu | État |
|---|---|---|
| 1 — Cadrage et conception | Backlog, MCD/MLD (11 entités), schéma SQL | ✅ |
| 2 — Développement | Front-end, back-end, sécurité, MinIO, messagerie, notifications | ✅ |
| 3 — Ingénierie des données | Kafka, Spark, data lake, Airflow, data warehouse, Power BI | ✅ |
| 4 — IA et fonctionnalités avancées | Estimation, recommandation, fraude, cartographie, recherche avancée | ✅ |
| 5 — Qualité et déploiement | Dockerisation complète, déploiement Azure | ✅ (tests, CI/CD GitHub Actions et Kubernetes en perspective) |

### Limites et perspectives

- Dataset d'entraînement modeste (~2 000 annonces) ; R² perfectible.
- Recommandation content-based uniquement (pas de collaborative filtering faute d'historique).
- Détection de fraude validée sur cas synthétiques seulement.
- Workflow de **vente** simplifié : « Faire une offre » réutilise l'endpoint de réservation (pas de compromis / acte).
- L'admin ne liste que les biens `disponible` (endpoint dédié à ajouter pour `en_attente` / `suspendu` / `vendu`).
- À venir : tests automatisés (Pytest, Postman), pipeline CI/CD GitHub Actions, Kubernetes (perspective), nom de domaine + HTTPS.

---

## Documentation complémentaire

| Document | Sujet |
|---|---|
| `README_PROJET_COMPLET.md` | Récapitulatif des phases 1 à 4 |
| `README_PHASE4_ETAPE16.md` | IA : scraping, modèles, micro-service |
| `README_AMELIORATIONS_UI_VENTE_LOCATION.md` | Carrousel, fiche détaillée, vente / location |
| `README_HISTORIQUE_RECHERCHE.md` | Historique de recherche client |
| `README_proximites_stockage.md` | Commodités à proximité stockées en base |
| `README_DOCKER.md` | Dockerisation complète et Nginx |
| `README_VM_AZURE_STUDENTS.md` | Création de la VM Azure for Students |
| `README_DEPLOIEMENT_AZURE.md` | Procédure générique de déploiement |
| `README_DEPLOIEMENT_REALISE.md` | Déploiement effectivement réalisé |

---

## Licence

Projet académique (PFE). Licence à préciser avant toute diffusion.
