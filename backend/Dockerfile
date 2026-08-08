# ============================================================
# SmartRent — Back-end FastAPI (Dockerfile)
# À placer à la racine de ton dossier backend/ (à côté de requirements.txt,
# du dossier app/, etc.) — remplace/ajoute ce fichier tel quel.
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# curl : uniquement pour le HEALTHCHECK ci-dessous (pas de compilation
# nécessaire : psycopg2-binary, Pillow, etc. sont fournis en wheels précompilées)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Le dossier uploads/photos existe dans le repo (ancien mécanisme de
# stockage local pré-MinIO) — conservé pour compatibilité mais non utilisé
# activement, les photos passent désormais par MinIO (voir app/storage.py)
RUN mkdir -p uploads/photos

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=10 \
    CMD curl -f http://localhost:8000/docs || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
