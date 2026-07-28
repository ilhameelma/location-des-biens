# Étape 11-12 — ETL Spark & Data lake MinIO

## 1. Télécharger les JAR une seule fois (recommandé)

Plutôt que de laisser `spark-submit --packages` re-télécharger ~330 Mo de
dépendances Maven à chaque lancement, on les télécharge une fois pour
toutes dans `data/spark/jars/`, monté dans le conteneur et ajouté
automatiquement au classpath (voir `data/spark/conf/spark-defaults.conf`).

```powershell
cd data\spark\jars
.\download_jars.ps1
cd ..\..\..
```

Ça télécharge les 14 JAR (connecteur Kafka + S3A/MinIO) directement depuis
Maven Central vers votre machine — une seule fois, ~330 Mo. Une fois fait,
plus jamais besoin de `--packages`.

## 2. Mettre à jour l'infrastructure

Remplacez votre `docker-compose.yml` par celui fourni ici (il ajoute le
service `spark`, `minio-init`, et monte désormais aussi `data/spark/jars`
et `data/spark/conf`), puis :

```powershell
docker-compose up -d
docker-compose ps   # vérifier que "smartrent_spark" et "smartrent_minio_init" tournent
```

`minio-init` crée automatiquement le bucket `smartrent-datalake` puis s'arrête
(normal — ce n'est pas un service qui tourne en continu, comme `airflow-init`).

## 3. Lancer le job de streaming (Kafka → MinIO)

Plus besoin de `--packages` : les JAR sont déjà sur le classpath via
`spark-defaults.conf`.

```powershell
docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/kafka_to_datalake.py
```

Le démarrage est maintenant quasi instantané (plus de téléchargement Ivy).
Vous devriez voir directement :

```
[smartrent] Streaming Kafka -> s3a://smartrent-datalake/bronze démarré. Ctrl+C pour arrêter.
```

**Laissez ce terminal ouvert** — c'est un job de streaming, il tourne en continu
(micro-batch toutes les 30 secondes) tant que vous ne l'arrêtez pas
(Ctrl+C, ou `docker exec smartrent_spark ...` dans un nouveau terminal pour le
relancer plus tard).

Comme `startingOffsets=earliest`, il va immédiatement récupérer aussi la
réservation de test déjà publiée dans Kafka avant ce premier lancement.

## 4. Vérifier ce qui a été écrit dans le data lake

Dans un **second terminal**, pendant que le job tourne (ou après l'avoir arrêté) :

```powershell
docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/check_datalake.py
```

Vous devriez voir un décompte de lignes par topic/date, et un aperçu du JSON brut.

Vous pouvez aussi consulter le bucket directement dans la console MinIO
(http://localhost:9001, `smartrent_admin` / `smartrent_minio_pwd`) :
`smartrent-datalake` → `bronze` → dossiers partitionnés par `topic=...` puis
`date_ingestion=...`, contenant des fichiers `.parquet`.

## 5. Tester le pipeline complet

Avec le job de streaming actif :
1. Créez un bien, confirmez la réservation existante, faites un paiement.
2. Regardez le terminal du job Spark : un nouveau micro-batch (toutes les 30s)
   doit afficher qu'il a traité des lignes.
3. Relancez `check_datalake.py` : les nouveaux topics (`bien.cree`,
   `contrat.signe`, `paiement.effectue`...) doivent apparaître.

## Structure ajoutée

```
location/
├── docker-compose.yml          # + service "spark", "minio-init"
└── data/
    └── spark/
        ├── jobs/
        │   ├── kafka_to_datalake.py   # streaming Kafka -> bronze (Parquet)
        │   └── check_datalake.py      # relit la couche bronze pour vérification
        ├── jars/
        │   └── download_jars.ps1      # télécharge les 14 JAR une seule fois
        ├── conf/
        │   └── spark-defaults.conf    # ajoute jars/ au classpath automatiquement
        └── checkpoints/                # offsets Kafka du streaming (généré au 1er lancement)
```

## Prochaine étape (13)

Une fois la couche bronze validée, l'étape suivante est l'orchestration
Airflow : un DAG qui déclenche (a) ce job de streaming ou une variante batch,
et (b) un second job Spark qui nettoie/agrège la couche bronze vers une
couche prête pour le data warehouse (étape 14).

