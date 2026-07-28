"""
SmartRent Platform — Étape 13/14 : Orchestration Airflow

Ce DAG automatise l'ensemble du pipeline data :

    docker exec smartrent_spark spark-submit kafka_to_datalake_batch.py   (étape 11-12)
    docker exec smartrent_spark spark-submit check_datalake.py            (vérification)
    docker exec smartrent_spark spark-submit load_to_warehouse.py         (étape 14, nouveau)

Pourquoi `docker exec` plutôt qu'un opérateur Airflow "natif" (SparkSubmitOperator,
DockerOperator...) ?
- Le conteneur `smartrent_spark` tourne déjà en permanence ("tail -f /dev/null"),
  avec les JAR et la config déjà en place (spark-defaults.conf) — inutile de
  recréer un conteneur à chaque run (ce que ferait DockerOperator).
- SparkSubmitOperator nécessite un client Spark local dans le conteneur Airflow ;
  ici, on réutilise simplement la même commande que celle déjà validée
  manuellement aux étapes 11-12, ce qui limite les sources d'erreur.

Prérequis (voir docker-compose.yml et airflow/Dockerfile) :
- image Airflow personnalisée avec le CLI `docker` installé
- /var/run/docker.sock monté dans le conteneur airflow-scheduler
- driver JDBC PostgreSQL présent dans data/spark/jars/ (étape 14, voir
  data/spark/jars/download_jars.ps1)
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

SPARK_CONTAINER = "smartrent_spark"
SPARK_SUBMIT = "/opt/spark/bin/spark-submit"
JOBS_DIR = "/opt/spark-jobs"

default_args = {
    "owner": "smartrent",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="smartrent_kafka_to_datalake",
    description=(
        "Etapes 11-14 - pipeline Kafka -> Spark -> MinIO (bronze) "
        "-> PostgreSQL (data warehouse dw), automatise"
    ),
    default_args=default_args,
    schedule="*/10 * * * *",   # toutes les 10 minutes ; ajuster selon la demo
    start_date=datetime(2026, 7, 1),
    catchup=False,
    # Le job batch et le job streaming partagent le même checkpoint (étape 11) :
    # on interdit donc les runs concurrents pour éviter toute lecture Kafka
    # simultanée sur ce même checkpoint.
    max_active_runs=1,
    tags=["smartrent", "phase3", "kafka", "spark", "datalake", "warehouse"],
) as dag:

    run_batch_etl = BashOperator(
        task_id="run_kafka_to_datalake_batch",
        bash_command=(
            f"docker exec {SPARK_CONTAINER} {SPARK_SUBMIT} "
            f"{JOBS_DIR}/kafka_to_datalake_batch.py"
        ),
    )

    verify_datalake = BashOperator(
        task_id="verify_datalake",
        bash_command=(
            f"docker exec {SPARK_CONTAINER} {SPARK_SUBMIT} "
            f"{JOBS_DIR}/check_datalake.py"
        ),
    )

    # Étape 14 — relit toute la couche bronze et recharge le data warehouse
    # PostgreSQL (schéma dw) en "full reload". Placée après verify_datalake
    # pour ne recharger le DW qu'une fois l'ingestion bronze confirmée.
    load_to_warehouse = BashOperator(
        task_id="load_to_warehouse",
        bash_command=(
            f"docker exec {SPARK_CONTAINER} {SPARK_SUBMIT} "
            f"{JOBS_DIR}/load_to_warehouse.py"
        ),
    )

    run_batch_etl >> verify_datalake >> load_to_warehouse
