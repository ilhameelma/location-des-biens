# ============================================================
# SmartRent Platform — image Airflow personnalisée (étape 13)
#
# Pourquoi ce Dockerfile plutôt que l'image officielle telle quelle ?
# Le scheduler Airflow doit pouvoir lancer les jobs Spark en exécutant
# `docker exec smartrent_spark spark-submit ...` (même commande que celle
# lancée manuellement depuis PowerShell aux étapes 11-12). Pour ça, il lui
# faut le client `docker` (CLI) à l'intérieur de son propre conteneur,
# ce que l'image apache/airflow de base ne fournit pas.
#
# Le conteneur Spark, lui, ne change pas : Airflow ne fait qu'exécuter des
# commandes dedans depuis l'extérieur, via le socket Docker de l'hôte.
# ============================================================
FROM apache/airflow:2.9.1

USER root

# Le paquet "docker.io" de Debian embarque un client Docker ancien (API 1.41),
# incompatible avec un moteur Docker Desktop récent qui exige au moins l'API
# 1.44 ("client version 1.41 is too old"). On installe donc directement le
# binaire officiel du client Docker (CLI seule, pas le démon) depuis
# download.docker.com plutôt que le paquet apt.
ARG DOCKER_CLI_VERSION=26.1.4
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_CLI_VERSION}.tgz" -o /tmp/docker.tgz \
    && tar -xzf /tmp/docker.tgz -C /tmp \
    && mv /tmp/docker/docker /usr/local/bin/docker \
    && chmod +x /usr/local/bin/docker \
    && rm -rf /tmp/docker /tmp/docker.tgz \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
