"""
Diagnostic B — écrit un DataFrame factice (rien à voir avec Kafka) vers
MinIO en Parquet, puis le relit. Sert à vérifier que la connexion S3A vers
MinIO (endpoint, identifiants, permissions bucket) fonctionne, indépendamment
de tout ce qui touche à Kafka/streaming.

Exécution :
    docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/diagnostic_write_s3a.py
"""
from pyspark.sql import SparkSession

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "smartrent_admin"
MINIO_SECRET_KEY = "smartrent_minio_pwd"
TEST_PATH = "s3a://smartrent-datalake/_diagnostic_write_test"


def main():
    spark = (
        SparkSession.builder.appName("smartrent-diagnostic-write-s3a")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    df = spark.createDataFrame([(1, "a"), (2, "b"), (3, "c")], ["id", "val"])
    print(f"[diagnostic] Écriture de {df.count()} lignes vers {TEST_PATH}...")
    df.write.mode("overwrite").parquet(TEST_PATH)
    print("[diagnostic] Écriture terminée sans erreur. Relecture...")

    reread = spark.read.parquet(TEST_PATH)
    print(f"[diagnostic] {reread.count()} ligne(s) relue(s) depuis MinIO.")
    reread.show()


if __name__ == "__main__":
    main()
