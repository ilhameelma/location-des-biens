"""
Diagnostic A — Kafka en mode STREAMING (readStream, comme le vrai job) mais
écriture vers la console au lieu de MinIO. Sert à vérifier si le problème
vient du mécanisme readStream lui-même (différent de spark.read en mode
batch, testé précédemment) ou de l'écriture S3A/MinIO.

Exécution :
    docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/diagnostic_readstream_console.py
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
TOPIC_PATTERN = "smartrent\\..*"
CHECKPOINT_PATH = "/opt/spark-jobs/_checkpoints/_diagnostic_console"


def main():
    spark = SparkSession.builder.appName("smartrent-diagnostic-readstream-console").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribePattern", TOPIC_PATTERN)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    out = raw_stream.select(
        col("topic"), col("partition"), col("offset"),
        col("key").cast("string").alias("key"),
    )

    query = (
        out.writeStream.format("console")
        .option("truncate", "false")
        .option("checkpointLocation", CHECKPOINT_PATH)
        .trigger(availableNow=True)
        .start()
    )
    query.awaitTermination()

    total_rows = sum(p.get("numInputRows", 0) or 0 for p in query.recentProgress)
    print(f"[diagnostic] {total_rows} ligne(s) vues par le readStream (checkpoint dédié, tout frais).")


if __name__ == "__main__":
    main()
