# Étape 11-12 (Kafka + S3A/MinIO) et étape 14 (JDBC PostgreSQL) — télécharge
# une bonne fois pour toutes les JAR nécessaires, pour ne plus jamais les
# re-télécharger à chaque `spark-submit`.
#
# Utilisation (depuis la racine du projet) :
#   cd data\spark\jars
#   .\download_jars.ps1
#
# Si vous aviez déjà lancé ce script avant l'étape 14, relancez-le une fois :
# seul le driver PostgreSQL (nouveau) sera téléchargé, les 14 JAR déjà
# présentes seront ignorées ("[déjà présent]").

$ErrorActionPreference = "Stop"

$jars = @(
    "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar",
    "https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.1/spark-token-provider-kafka-0-10_2.12-3.4.1.jar",
    "https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.3.2/kafka-clients-3.3.2.jar",
    "https://repo1.maven.org/maven2/org/lz4/lz4-java/1.8.0/lz4-java-1.8.0.jar",
    "https://repo1.maven.org/maven2/org/xerial/snappy/snappy-java/1.1.10.1/snappy-java-1.1.10.1.jar",
    "https://repo1.maven.org/maven2/org/slf4j/slf4j-api/2.0.6/slf4j-api-2.0.6.jar",
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-runtime/3.3.4/hadoop-client-runtime-3.3.4.jar",
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-api/3.3.4/hadoop-client-api-3.3.4.jar",
    "https://repo1.maven.org/maven2/commons-logging/commons-logging/1.1.3/commons-logging-1.1.3.jar",
    "https://repo1.maven.org/maven2/com/google/code/findbugs/jsr305/3.0.0/jsr305-3.0.0.jar",
    "https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar",
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar",
    "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar",
    "https://repo1.maven.org/maven2/org/wildfly/openssl/wildfly-openssl/1.0.7.Final/wildfly-openssl-1.0.7.Final.jar",
    # Étape 14 — driver JDBC PostgreSQL, nécessaire à load_to_warehouse.py
    # pour écrire dans dw.* via spark.write.jdbc(...).
    "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar"
)

$destDir = $PSScriptRoot
Write-Host "Téléchargement de $($jars.Count) JAR dans $destDir ..."

foreach ($url in $jars) {
    $fileName = Split-Path $url -Leaf
    $destPath = Join-Path $destDir $fileName
    if (Test-Path $destPath) {
        Write-Host "  [déjà présent] $fileName"
        continue
    }
    Write-Host "  [téléchargement] $fileName"
    Invoke-WebRequest -Uri $url -OutFile $destPath
}

Write-Host ""
Write-Host "Terminé. $((Get-ChildItem $destDir -Filter *.jar).Count) JAR présents dans $destDir."
