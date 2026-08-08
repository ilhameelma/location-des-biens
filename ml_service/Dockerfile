# ============================================================
# SmartRent — Micro-service IA (Dockerfile)
# À placer à la racine du dossier qui contient requirements.txt, app/ et
# models/ (chez toi ce dossier peut s'appeler "ml" ou "ml_service" selon
# ton repo — voir la note dans README_DOCKER.md sur le nom de contexte
# à utiliser dans docker-compose.yml).
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# libgomp1 : requis par LightGBM (modele_estimation_vente.joblib) au runtime
# curl : uniquement pour le HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app/ + models/ (les .joblib sont EMBARQUÉS dans l'image — pas de
# ré-entraînement au démarrage du conteneur, cf. .dockerignore qui exclut
# script/ et data/, inutiles pour servir les prédictions)
COPY app/ ./app/
COPY models/ ./models/

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=10 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
