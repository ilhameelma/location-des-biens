"""
Étape 11/12 — Script de vérification : relit la couche bronze du data lake
(MinIO) et affiche un aperçu, pour confirmer que le job de streaming
(kafka_to_datalake.py) écrit bien les données attendues.

Exécution : voir data/spark/README.md
"""
from pyspark.sql import SparkSession

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "smartrent_admin"
MINIO_SECRET_KEY = "smartrent_minio_pwd"
BRONZE_PATH = "s3a://smartrent-datalake/bronze"


def main():
    spark = (
        SparkSession.builder.appName("smartrent-datalake-check")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # spark.read.parquet(BRONZE_PATH) déclenche la lecture "streaming sink" de
    # Spark : si un dossier _spark_metadata existe (toujours le cas avec
    # Structured Streaming), Spark lit la LISTE DE FICHIERS enregistrée dans
    # ce journal plutôt que le contenu réel du dossier. Avec plusieurs
    # sessions Spark indépendantes (job batch relancé manuellement à
    # plusieurs reprises), ce journal peut se désynchroniser : des fichiers
    # bien écrits sur disque/MinIO deviennent alors invisibles ici, sans
    # aucune erreur. Le glob + basePath ci-dessous force une vraie lecture du
    # contenu du dossier, en ignorant ce journal.
    df = (
        spark.read.option("basePath", BRONZE_PATH)
        .parquet(f"{BRONZE_PATH}/topic=*/date_ingestion=*")
    )
    print(f"[smartrent] {df.count()} lignes dans la couche bronze.")
    df.groupBy("topic", "date_ingestion").count().orderBy("topic").show(truncate=False)
    df.select("topic", "event_key", "payload_json", "kafka_timestamp").show(20, truncate=80)


if __name__ == "__main__":
    main()
