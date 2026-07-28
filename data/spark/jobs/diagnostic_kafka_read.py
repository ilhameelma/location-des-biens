"""
Diagnostic — lecture Kafka en mode batch STATIQUE (spark.read, pas
spark.readStream), sans checkpoint, sans écriture. Sert uniquement à vérifier
si Spark arrive à lire les messages actuellement présents dans Kafka, en
éliminant complètement le mécanisme de streaming/checkpoint/sink de
l'équation.

Exécution :
    docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/diagnostic_kafka_read.py
"""
from pyspark.sql import SparkSession

KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
TOPIC_PATTERN = "smartrent\\..*"


def main():
    spark = SparkSession.builder.appName("smartrent-diagnostic-kafka-read").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    df = (
        spark.read.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribePattern", TOPIC_PATTERN)
        .option("startingOffsets", "earliest")
        .option("endingOffsets", "latest")
        .load()
    )

    print(f"[diagnostic] {df.count()} message(s) lu(s) directement depuis Kafka.")
    df.selectExpr(
        "topic", "partition", "offset", "CAST(key AS STRING) AS key", "CAST(value AS STRING) AS value"
    ).show(50, truncate=80)


if __name__ == "__main__":
    main()
