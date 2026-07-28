"""
Étape 11-12 — Variante "one-shot" (mode batch) de kafka_to_datalake.py

Contrairement au job de streaming continu (kafka_to_datalake.py), qui tourne
indéfiniment dans un terminal et peut prêter à confusion (est-il toujours
actif ? l'ai-je tué par accident en redémarrant le conteneur ?), ce script :

  1. lit tout ce qui est actuellement disponible dans les 5 topics Kafka
     (depuis le dernier point de reprise du checkpoint — le MÊME checkpoint
     que le job de streaming, donc aucun risque de doublon si vous alternez
     entre les deux) ;
  2. écrit ces données dans le data lake MinIO (couche bronze) ;
  3. s'arrête automatiquement (`trigger(availableNow=True)`) et affiche un
     résumé clair.

Pratique pour tester/démontrer le pipeline à la demande, sans laisser un
terminal de streaming ouvert en permanence. Pour la version "vraie
production" (traitement continu, quasi temps réel), utilisez
kafka_to_datalake.py.

Exécution :
    docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/kafka_to_datalake_batch.py
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_date

KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
TOPIC_PATTERN = "smartrent\\..*"

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "smartrent_admin"
MINIO_SECRET_KEY = "smartrent_minio_pwd"
DATALAKE_BUCKET = "smartrent-datalake"

OUTPUT_PATH = f"s3a://{DATALAKE_BUCKET}/bronze"
# Même checkpoint que le job de streaming : les deux modes partagent le même
# suivi de progression Kafka, donc pas de doublons ni de trous si vous
# alternez entre les deux.
CHECKPOINT_PATH = "/opt/spark-jobs/_checkpoints/bronze"


def build_spark_session() -> SparkSession:
    return (
        SparkSession.builder.appName("smartrent-kafka-to-datalake-batch")
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
        # Le checkpoint (sur le disque hôte) peut survivre à un redémarrage
        # de Kafka qui, lui, n'a pas de volume persistant (topics recréés
        # vides). Sans ceci, Spark plante avec "are gone. Some data may
        # have been missed" dès que les offsets du checkpoint ne
        # correspondent plus à ce qui existe réellement dans Kafka.
        .option("failOnDataLoss", "false")
        .load()
    )

    bronze = raw_stream.select(
        col("topic"),
        col("key").cast("string").alias("event_key"),
        col("value").cast("string").alias("payload_json"),
        col("timestamp").alias("kafka_timestamp"),
    ).withColumn("date_ingestion", current_date())

    print("[smartrent] Traitement des messages disponibles dans Kafka...")

    query = (
        bronze.writeStream.format("parquet")
        .option("path", OUTPUT_PATH)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .partitionBy("topic", "date_ingestion")
        .outputMode("append")
        .trigger(availableNow=True)  # traite ce qui existe, puis s'arrête seul
        .start()
    )

    query.awaitTermination()

    # query.lastProgress juste après awaitTermination() peut être en retard
    # (le reporting de progression de Structured Streaming est asynchrone) et
    # afficher 0 même si des lignes ont bien été écrites. On additionne donc
    # tous les batches réellement exécutés (recentProgress) plutôt que de se
    # fier au seul dernier événement de progression.
    total_rows = sum(p.get("numInputRows", 0) or 0 for p in query.recentProgress)
    print(f"[smartrent] Terminé. {total_rows} nouvelle(s) ligne(s) écrite(s) dans {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
