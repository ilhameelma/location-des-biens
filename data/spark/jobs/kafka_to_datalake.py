"""
Étape 11 — ETL / traitement (Apache Spark)
Étape 12 — Data lake (MinIO)

Job Spark Structured Streaming qui :
  1. se connecte aux topics Kafka publiés par le back-end (étape 10 —
     voir backend/app/kafka_producer.py et backend/app/kafka_topics.py) ;
  2. écrit chaque message brut (JSON) dans le data lake MinIO, au format
     Parquet, partitionné par topic et par date d'ingestion — c'est la
     couche "bronze" : données brutes, non transformées, non nettoyées.

Ce job tourne en continu (streaming) : il lit les nouveaux messages au fur
et à mesure qu'ils sont publiés, avec un micro-batch toutes les 30 secondes.
`startingOffsets=earliest` permet de récupérer aussi les messages déjà
publiés avant le premier lancement du job (ex. la réservation de test).

Aucun parsing de schéma n'est fait ici volontairement : chaque topic a une
structure différente (bien, réservation, contrat, paiement), et le rôle de
la couche bronze est justement de conserver le JSON brut tel quel pour
traçabilité/rejeu. Le nettoyage et l'agrégation (par ville, par mois...)
seront faits par un second job qui lit cette couche bronze et écrit une
couche "silver/gold" consommée par le data warehouse (étape 14).

Exécution : voir data/spark/README.md
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_date

# --- Kafka -----------------------------------------------------------------
# Listener interne Docker (voir KAFKA_ADVERTISED_LISTENERS dans
# docker-compose.yml) : le conteneur Spark est sur le même réseau Docker
# que Kafka, donc on utilise le nom de service "kafka", pas "localhost".
KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
TOPIC_PATTERN = "smartrent\\..*"  # les 5 topics de l'étape 10

# --- MinIO (data lake) -------------------------------------------------------
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "smartrent_admin"
MINIO_SECRET_KEY = "smartrent_minio_pwd"
DATALAKE_BUCKET = "smartrent-datalake"

OUTPUT_PATH = f"s3a://{DATALAKE_BUCKET}/bronze"
CHECKPOINT_PATH = "/opt/spark-jobs/_checkpoints/bronze"


def build_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("smartrent-kafka-to-datalake")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


def main():
    spark = build_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribePattern", TOPIC_PATTERN)
        .option("startingOffsets", "earliest")
        # Voir kafka_to_datalake_batch.py pour l'explication : évite un
        # plantage si le checkpoint (persistant) référence des offsets
        # qui n'existent plus dans Kafka (non persistant par défaut).
        .option("failOnDataLoss", "false")
        .load()
    )

    # Couche bronze : JSON brut + métadonnées Kafka (traçabilité/rejeu),
    # partitionné par topic et par date d'ingestion.
    bronze = raw_stream.select(
        col("topic"),
        col("key").cast("string").alias("event_key"),
        col("value").cast("string").alias("payload_json"),
        col("timestamp").alias("kafka_timestamp"),
    ).withColumn("date_ingestion", current_date())

    query = (
        bronze.writeStream.format("parquet")
        .option("path", OUTPUT_PATH)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .partitionBy("topic", "date_ingestion")
        .outputMode("append")
        .trigger(processingTime="30 seconds")
        .start()
    )

    print(f"[smartrent] Streaming Kafka -> {OUTPUT_PATH} démarré. Ctrl+C pour arrêter.")
    query.awaitTermination()


if __name__ == "__main__":
    main()
