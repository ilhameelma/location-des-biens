# SmartRent Platform — Phase 3 : Étape 13 — Orchestration (Apache Airflow)

Dans la continuité de `README_PHASE3_ETAPES_10-12.md` (Kafka → Spark → MinIO,
lancés manuellement). Cette étape automatise ce déclenchement avec Airflow.

---

## Principe

Jusqu'ici, le job Spark se lançait à la main :

```powershell
docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/kafka_to_datalake_batch.py
```

Le DAG Airflow `smartrent_kafka_to_datalake` exécute **exactement cette même
commande**, automatiquement, toutes les 10 minutes, puis relit la couche
bronze (`check_datalake.py`) pour vérifier que l'ingestion s'est bien passée.

```
Airflow (scheduler) ──docker exec──▶ conteneur smartrent_spark ──▶ spark-submit
        │
        └── planifie toutes les 10 min, 1 seul run actif à la fois
            (le job batch et le job streaming partagent le même checkpoint,
             donc jamais deux lectures Kafka simultanées)
```

### Pourquoi `docker exec` plutôt qu'un opérateur Airflow "Spark" natif ?

- Le conteneur `smartrent_spark` tourne déjà en permanence (`tail -f /dev/null`)
  avec les JAR et `spark-defaults.conf` déjà en place (étape 11). Le
  `SparkSubmitOperator` ou le `DockerOperator` recréeraient un contexte à
  chaque run — inutilement plus lourd et plus fragile ici.
- On réutilise donc la commande déjà validée manuellement aux étapes 11-12,
  ce qui limite les sources d'erreur pour un pipeline de taille PFE.

---

## Ce qui a été ajouté / modifié

| Fichier | Rôle |
|---|---|
| `airflow/Dockerfile` | Étend `apache/airflow:2.9.1` avec le CLI `docker` (`apt-get install docker.io`), nécessaire pour que le scheduler puisse faire `docker exec` |
| `airflow/dags/smartrent_kafka_to_datalake_dag.py` | Le DAG : 2 tâches (`run_kafka_to_datalake_batch` → `verify_datalake`), planifié toutes les 10 min, `max_active_runs=1` |
| `docker-compose.yml` | `airflow-init`, `airflow-webserver`, `airflow-scheduler` passent de `image:` à `build: ./airflow` ; `airflow-scheduler` monte en plus `/var/run/docker.sock` et tourne en `user: "0:0"` (root) pour pouvoir piloter le conteneur Spark |

**Rien ne change côté `smartrent_spark`** : Airflow ne fait qu'exécuter des
commandes dedans depuis l'extérieur, via le socket Docker de l'hôte.

---

## Installation

### 1. Placer les fichiers

```
location/
├── docker-compose.yml          # remplacé
├── airflow/
│   ├── Dockerfile              # nouveau
│   └── dags/
│       └── smartrent_kafka_to_datalake_dag.py   # nouveau
```

### 2. Reconstruire et relancer les services Airflow

```powershell
docker-compose down
docker-compose build airflow-init airflow-webserver airflow-scheduler
docker-compose up -d
docker-compose ps
```

> La première build installe le CLI `docker` dans l'image Airflow — ça prend
> une minute ou deux, une seule fois (image mise en cache ensuite).

### 3. Vérifier dans l'interface Airflow

- http://localhost:8081 (`admin` / `admin`)
- Le DAG `smartrent_kafka_to_datalake` doit apparaître dans la liste.
- Il est créé **en pause** par défaut (comportement standard d'Airflow) :
  activer le toggle en haut à gauche du DAG pour qu'il commence à tourner
  toutes les 10 minutes.
- Pour tester immédiatement sans attendre : bouton ▶️ *Trigger DAG*.

### 4. Vérifier l'exécution

Dans l'UI Airflow : cliquer sur le DAG → *Graph* → cliquer sur une tâche →
*Logs*. Vous devriez voir le même type de sortie que lors des lancements
manuels (`[smartrent] Traitement des messages disponibles dans Kafka...`,
puis le récapitulatif de `check_datalake.py`).

Vous pouvez aussi vérifier directement en ligne de commande :

```powershell
docker logs smartrent_airflow_scheduler --tail 50
```

---

## Ajuster la fréquence

Dans `smartrent_kafka_to_datalake_dag.py`, la ligne :

```python
schedule="*/10 * * * *",   # toutes les 10 minutes
```

utilise la syntaxe cron classique (`minute heure jour mois jour_semaine`).
Pour une démo en soutenance, vous pouvez temporairement mettre
`"*/2 * * * *"` (toutes les 2 minutes) puis remettre une valeur plus
raisonnable ensuite.

---

## Problèmes potentiels et solutions

| Problème | Cause | Solution |
|---|---|---|
| `docker: command not found` dans les logs de la tâche | Image Airflow pas reconstruite après ajout du `Dockerfile` | `docker-compose build airflow-scheduler` puis `docker-compose up -d` |
| `permission denied` sur `/var/run/docker.sock` | Le scheduler ne tourne pas en root | Vérifier que `user: "0:0"` est bien présent sous `airflow-scheduler` dans `docker-compose.yml` |
| `client version 1.41 is too old. Minimum supported API version is 1.44` (tâche en échec silencieux / `up_for_retry` répété) | Le paquet `docker.io` de Debian embarque un client Docker trop ancien pour un moteur Docker Desktop récent | Corrigé dans ce zip : le `Dockerfile` installe désormais le binaire officiel du client Docker (`download.docker.com`) au lieu du paquet apt — rebuild obligatoire : `docker-compose build airflow-init airflow-webserver airflow-scheduler` |
| Logs de tâche vides dans l'UI + `jwt.exceptions.InvalidSignatureError` / `403 FORBIDDEN` dans `docker logs smartrent_airflow_scheduler` | `secret_key` différente entre le webserver et le scheduler (générée aléatoirement si non fixée), donc le webserver n'arrive pas à récupérer les logs du scheduler | Corrigé dans ce zip : `AIRFLOW__WEBSERVER__SECRET_KEY` fixée à la même valeur sur `airflow-init`, `airflow-webserver` et `airflow-scheduler` |
| Le DAG n'apparaît pas dans l'UI | Erreur de syntaxe Python dans le DAG, ou dossier mal monté | `docker logs smartrent_airflow_scheduler` (Airflow log les erreurs de parsing des DAG au démarrage) ; vérifier que `./airflow/dags` existe bien à la racine, au même niveau que `docker-compose.yml` |
| Tâche `run_kafka_to_datalake_batch` échoue avec `No such container: smartrent_spark` | Le conteneur Spark n'est pas démarré | `docker-compose up -d spark` avant de déclencher le DAG |
| Deux runs qui se marchent dessus / erreur de checkpoint Spark | `max_active_runs` mal configuré | Ne pas modifier `max_active_runs=1` dans le DAG — c'est voulu, le job batch et le job streaming partagent le même checkpoint (étape 11) |

---

## Prochaine étape (14) — Data warehouse

Le pipeline Kafka → Spark → MinIO (bronze) tourne maintenant de façon
autonome. L'étape 14 consiste à ajouter une couche de transformation
supplémentaire (silver/gold, ou directement un schéma en étoile) qui lit la
couche bronze du data lake et charge des données agrégées prêtes pour
l'analyse dans un data warehouse (PostgreSQL — schéma dédié — ou
ClickHouse), avant les tableaux de bord Power BI (étape 15).

Une piste naturelle : ajouter une **troisième tâche** au DAG existant
(`run_batch_etl >> verify_datalake >> load_to_warehouse`), plutôt qu'un DAG
séparé — pour garder un seul pipeline orchestré de bout en bout.
