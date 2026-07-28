"""
Étape 14 — Data warehouse (PostgreSQL, schéma "dw")

Relit la couche bronze du data lake (étape 12, MinIO), parse le JSON brut de
chaque topic Kafka, reconstruit le modèle en étoile décrit dans
postgres/warehouse_schema.sql (dw.dim_date, dw.dim_ville, dw.fait_*), puis
recharge l'ensemble via JDBC dans PostgreSQL.

Stratégie : "full reload" (TRUNCATE ... RESTART IDENTITY CASCADE, puis
ré-insertion complète) à chaque exécution. Possible et volontaire ici car
la couche bronze est la source de vérité rejouable dans son intégralité —
pas besoin d'un mécanisme d'upsert incrémental pour un volume de PFE, et ça
évite toute divergence silencieuse entre deux exécutions.

Cas particulier — réservations : un événement "reservation.creee" contient
toutes les infos (bien, client, propriétaire, ville, dates), mais un
"reservation.statut_maj" ne contient que (id, statut). On combine donc les
deux : infos de base depuis l'événement de création, statut final = dernier
"statut_maj" reçu pour cette réservation (sinon le statut de création).

Exécution :
    docker exec -it smartrent_spark /opt/spark/bin/spark-submit /opt/spark-jobs/load_to_warehouse.py
"""
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------

MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "smartrent_admin"
MINIO_SECRET_KEY = "smartrent_minio_pwd"
BRONZE_PATH = "s3a://smartrent-datalake/bronze"

# Même base PostgreSQL que la base transactionnelle (service "postgres" du
# docker-compose.yml, Phase 1), schéma dédié "dw" (voir warehouse_schema.sql).
PG_HOST = "postgres"
PG_PORT = 5432
PG_DB = "smartrent_db"
PG_USER = "smartrent"
PG_PASSWORD = "smartrent_pwd"
PG_JDBC_URL = f"jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}"
PG_JDBC_PROPS = {
    "user": PG_USER,
    "password": PG_PASSWORD,
    "driver": "org.postgresql.Driver",
    "stringtype": "unspecified",
}

TOPIC_BIEN_CREE = "smartrent.bien.cree"
TOPIC_RESERVATION_CREEE = "smartrent.reservation.creee"
TOPIC_RESERVATION_STATUT_MAJ = "smartrent.reservation.statut_maj"
TOPIC_CONTRAT_SIGNE = "smartrent.contrat.signe"
TOPIC_PAIEMENT_EFFECTUE = "smartrent.paiement.effectue"

MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

# ------------------------------------------------------------
# Schémas JSON des payloads (voir backend/app/routers/*.py, publish_event)
# ------------------------------------------------------------

SCHEMA_BIEN = StructType([
    StructField("id", StringType()),
    StructField("proprietaire_id", StringType()),
    StructField("titre", StringType()),
    StructField("type_bien", StringType()),
    StructField("ville", StringType()),
    StructField("prix", DoubleType()),
    StructField("statut", StringType()),
    StructField("date_publication", StringType()),
])

SCHEMA_RESERVATION_CREEE = StructType([
    StructField("id", StringType()),
    StructField("bien_id", StringType()),
    StructField("client_id", StringType()),
    StructField("proprietaire_id", StringType()),
    StructField("ville", StringType()),
    StructField("date_debut", StringType()),
    StructField("date_fin", StringType()),
    StructField("statut", StringType()),
    StructField("date_creation", StringType()),
])

SCHEMA_RESERVATION_MAJ = StructType([
    StructField("id", StringType()),
    StructField("bien_id", StringType()),
    StructField("client_id", StringType()),
    StructField("statut", StringType()),
])

SCHEMA_CONTRAT = StructType([
    StructField("id", StringType()),
    StructField("bien_id", StringType()),
    StructField("ville", StringType()),
    StructField("proprietaire_id", StringType()),
    StructField("client_id", StringType()),
    StructField("montant_loyer", DoubleType()),
    StructField("date_debut", StringType()),
    StructField("date_fin", StringType()),
    StructField("statut", StringType()),
    StructField("date_creation", StringType()),
])

SCHEMA_PAIEMENT = StructType([
    StructField("id", StringType()),
    StructField("contrat_id", StringType()),
    StructField("bien_id", StringType()),
    StructField("ville", StringType()),
    StructField("proprietaire_id", StringType()),
    StructField("client_id", StringType()),
    StructField("montant", DoubleType()),
    StructField("methode", StringType()),
    StructField("statut", StringType()),
    StructField("date_paiement", StringType()),
])


def build_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("smartrent-load-to-warehouse")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .getOrCreate()
    )


def read_bronze(spark):
    # Même contournement que check_datalake.py (étape 12) : glob + basePath
    # pour ignorer le journal _spark_metadata du sink streaming.
    return (
        spark.read.option("basePath", BRONZE_PATH)
        .parquet(f"{BRONZE_PATH}/topic=*/date_ingestion=*")
    )


def parse_topic(raw, topic: str, schema: StructType):
    return (
        raw.filter(F.col("topic") == topic)
        .withColumn("data", F.from_json(F.col("payload_json"), schema))
        .select("data.*", F.col("kafka_timestamp"))
    )


def build_reservation_df(raw):
    created = parse_topic(raw, TOPIC_RESERVATION_CREEE, SCHEMA_RESERVATION_CREEE).dropDuplicates(["id"])

    w = Window.partitionBy("id").orderBy(F.col("kafka_timestamp").desc())
    latest_update = (
        parse_topic(raw, TOPIC_RESERVATION_STATUT_MAJ, SCHEMA_RESERVATION_MAJ)
        .withColumn("rn", F.row_number().over(w))
        .filter(F.col("rn") == 1)
        .select(F.col("id").alias("id_upd"), F.col("statut").alias("statut_maj"))
    )

    return (
        created.join(latest_update, created["id"] == latest_update["id_upd"], "left")
        .select(
            F.col("id").alias("reservation_id"),
            F.col("bien_id"),
            F.col("client_id"),
            F.col("proprietaire_id"),
            F.col("ville"),
            F.to_date("date_debut").alias("date_debut"),
            F.to_date("date_fin").alias("date_fin"),
            F.coalesce(F.col("statut_maj"), F.col("statut")).alias("statut"),
            F.to_timestamp("date_creation").alias("date_creation"),
        )
    )


def build_bien_df(raw):
    return (
        parse_topic(raw, TOPIC_BIEN_CREE, SCHEMA_BIEN)
        .dropDuplicates(["id"])
        .select(
            F.col("id").alias("bien_id"),
            F.col("proprietaire_id"),
            F.col("ville"),
            F.col("type_bien"),
            F.col("prix"),
            F.col("statut"),
            F.to_timestamp("date_publication").alias("date_publication"),
        )
    )


def build_contrat_df(raw):
    return (
        parse_topic(raw, TOPIC_CONTRAT_SIGNE, SCHEMA_CONTRAT)
        .dropDuplicates(["id"])
        .select(
            F.col("id").alias("contrat_id"),
            F.col("bien_id"),
            F.col("proprietaire_id"),
            F.col("client_id"),
            F.col("ville"),
            F.col("montant_loyer"),
            F.to_date("date_debut").alias("date_debut"),
            F.to_date("date_fin").alias("date_fin"),
            F.col("statut"),
            # Le payload de l'événement ne porte que "date_creation" (pas de
            # "date_signature" distincte) ; on l'utilise comme timestamp de
            # signature, cohérent avec le fait que le contrat est
            # auto-généré à la confirmation de la réservation.
            F.to_timestamp("date_creation").alias("date_signature"),
        )
    )


def build_paiement_df(raw):
    return (
        parse_topic(raw, TOPIC_PAIEMENT_EFFECTUE, SCHEMA_PAIEMENT)
        .dropDuplicates(["id"])
        .select(
            F.col("id").alias("paiement_id"),
            F.col("contrat_id"),
            F.col("bien_id"),
            F.col("proprietaire_id"),
            F.col("client_id"),
            F.col("ville"),
            F.col("montant"),
            F.col("methode"),
            F.col("statut"),
            F.to_timestamp("date_paiement").alias("date_paiement"),
        )
    )


def build_dim_ville(*dfs_with_ville):
    villes = None
    for df in dfs_with_ville:
        col = df.select(F.col("ville")).where(F.col("ville").isNotNull())
        villes = col if villes is None else villes.union(col)
    distinct_villes = villes.distinct()
    w = Window.orderBy("ville")
    return distinct_villes.withColumn("ville_id", F.row_number().over(w)).select("ville_id", "ville")


def build_dim_date(*date_cols):
    """date_cols : liste de (dataframe, nom_de_colonne_timestamp_ou_date)."""
    dates = None
    for df, col_name in date_cols:
        d = df.select(F.to_date(F.col(col_name)).alias("date_id")).where(F.col(col_name).isNotNull())
        dates = d if dates is None else dates.union(d)
    distinct_dates = dates.distinct()

    mois_fr = F.array([F.lit(x) for x in MOIS_FR])
    jours_fr = F.array([F.lit(x) for x in JOURS_FR])

    return (
        distinct_dates
        .withColumn("annee", F.year("date_id"))
        .withColumn("mois", F.month("date_id"))
        .withColumn("trimestre", F.quarter("date_id"))
        .withColumn("jour", F.dayofmonth("date_id"))
        .withColumn("nom_mois", F.element_at(mois_fr, F.col("mois")))
        # Spark dayofweek() : 1=dimanche .. 7=samedi -> on remappe en 1=lundi..7=dimanche
        .withColumn("dow_spark", F.dayofweek("date_id"))
        .withColumn("jour_semaine_idx", F.when(F.col("dow_spark") == 1, 7).otherwise(F.col("dow_spark") - 1))
        .withColumn("jour_semaine", F.element_at(jours_fr, F.col("jour_semaine_idx")))
        .select("date_id", "annee", "trimestre", "mois", "nom_mois", "jour", "jour_semaine")
    )


def with_ville_id(df, dim_ville):
    return df.join(dim_ville, on="ville", how="left").drop("ville")


def truncate_warehouse(spark):
    """Vide toutes les tables dw.* avant rechargement (CASCADE gère l'ordre
    des FK, RESTART IDENTITY remet dim_ville.ville_id à 1)."""
    jvm = spark._jvm
    conn = jvm.java.sql.DriverManager.getConnection(PG_JDBC_URL, PG_USER, PG_PASSWORD)
    try:
        stmt = conn.createStatement()
        stmt.execute(
            "TRUNCATE TABLE dw.fait_bien, dw.fait_reservation, dw.fait_contrat, "
            "dw.fait_paiement, dw.dim_ville, dw.dim_date RESTART IDENTITY CASCADE"
        )
        stmt.close()
    finally:
        conn.close()


def write_table(df, table: str):
    (
        df.write.mode("append")
        .jdbc(url=PG_JDBC_URL, table=table, properties=PG_JDBC_PROPS)
    )


def main():
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    raw = read_bronze(spark).cache()

    reservation_df = build_reservation_df(raw)
    bien_df = build_bien_df(raw)
    contrat_df = build_contrat_df(raw)
    paiement_df = build_paiement_df(raw)

    dim_ville = build_dim_ville(reservation_df, bien_df, contrat_df, paiement_df).cache()
    dim_date = build_dim_date(
        (bien_df, "date_publication"),
        (reservation_df, "date_creation"),
        (contrat_df, "date_signature"),
        (paiement_df, "date_paiement"),
    ).cache()

    fait_bien = with_ville_id(bien_df, dim_ville).withColumn(
        "date_id", F.to_date("date_publication")
    ).select(
        "bien_id", "proprietaire_id", "ville_id", "type_bien", "prix", "statut",
        "date_id", "date_publication",
    )

    fait_reservation = with_ville_id(reservation_df, dim_ville).withColumn(
        "date_id", F.to_date("date_creation")
    ).select(
        "reservation_id", "bien_id", "client_id", "proprietaire_id", "ville_id",
        "statut", "date_debut", "date_fin", "date_id", "date_creation",
    )

    fait_contrat = with_ville_id(contrat_df, dim_ville).withColumn(
        "date_id", F.to_date("date_signature")
    ).select(
        "contrat_id", "bien_id", "proprietaire_id", "client_id", "ville_id",
        "montant_loyer", "statut", "date_debut", "date_fin", "date_id", "date_signature",
    )

    fait_paiement = with_ville_id(paiement_df, dim_ville).withColumn(
        "date_id", F.to_date("date_paiement")
    ).select(
        "paiement_id", "contrat_id", "bien_id", "proprietaire_id", "client_id",
        "ville_id", "montant", "methode", "statut", "date_id", "date_paiement",
    )

    print("[smartrent] Vidage du data warehouse (dw.*) avant rechargement...")
    truncate_warehouse(spark)

    print("[smartrent] Chargement des dimensions...")
    write_table(dim_date, "dw.dim_date")
    write_table(dim_ville, "dw.dim_ville")

    print("[smartrent] Chargement des faits...")
    write_table(fait_bien, "dw.fait_bien")
    write_table(fait_reservation, "dw.fait_reservation")
    write_table(fait_contrat, "dw.fait_contrat")
    write_table(fait_paiement, "dw.fait_paiement")

    print(
        f"[smartrent] Terminé. "
        f"{fait_bien.count()} bien(s), {fait_reservation.count()} réservation(s), "
        f"{fait_contrat.count()} contrat(s), {fait_paiement.count()} paiement(s), "
        f"{dim_ville.count()} ville(s), {dim_date.count()} date(s)."
    )


if __name__ == "__main__":
    main()
