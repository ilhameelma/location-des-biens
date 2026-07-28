"""
Diagnostic C — reproduit EXACTEMENT la mécanique du vrai job
(kafka_to_datalake_batch.py) : readStream Kafka -> writeStream parquet
partitionné -> S3A/MinIO, avec trigger(availableNow=True). Seule différence :
chemin de sortie et checkpoint isolés, pour ne pas toucher aux données
réelles. Sert à vérifier si c'est la COMBINAISON streaming+partitionBy+S3A
qui pose problème (chacun testé individuellement fonctionne).

Exécution :
    docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/diagnostic_full_combo.py
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_date

KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
TOPIC_PATTERN = "smartrent\\..*"

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "smartrent_admin"
MINIO_SECRET_KEY = "smartrent_minio_pwd"

OUTPUT_PATH = "s3a://smartrent-datalake/_diagnostic_combo"
CHECKPOINT_PATH = "/opt/spark-jobs/_checkpoints/_diagnostic_combo"


def main():
    spark = (
        SparkSession.builder.appName("smartrent-diagnostic-full-combo")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribePattern", TOPIC_PATTERN)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

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
        .trigger(availableNow=True)
        .start()
    )
    query.awaitTermination()

    total_rows = sum(p.get("numInputRows", 0) or 0 for p in query.recentProgress)
    print(f"[diagnostic] {total_rows} ligne(s) traitée(s) par le writeStream vers {OUTPUT_PATH}.")

    # Relecture en bypassant le journal _spark_metadata, comme check_datalake.py
    reread = spark.read.option("basePath", OUTPUT_PATH).parquet(f"{OUTPUT_PATH}/topic=*/date_ingestion=*")
    print(f"[diagnostic] {reread.count()} ligne(s) relue(s) physiquement depuis {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
