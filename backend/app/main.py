import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routers import (
    auth,
    biens,
    reservations,
    contrats,
    paiements,
    avis,
    reclamations,
    messagerie,
    notifications,
    utilisateurs,
)

# Crée les tables si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartRent Platform API",
    description="API REST du back-end SmartRent",
    version="0.1.0",
)

# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SERVIR LES FICHIERS UPLOADÉS (photos, documents)
# IMPORTANT : doit être AVANT les routers API pour éviter
# que /api n'intercepte les requêtes /uploads
# ============================================================
os.makedirs("uploads/photos", exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

# ============================================================
# ROUTERS API
# ============================================================
app.include_router(auth.router, prefix="/api")
app.include_router(biens.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(utilisateurs.router, prefix="/api")
app.include_router(biens.router, prefix="/api")
app.include_router(reservations.router, prefix="/api")
app.include_router(contrats.router, prefix="/api")
app.include_router(paiements.router, prefix="/api")
app.include_router(avis.router, prefix="/api")
app.include_router(reclamations.router, prefix="/api")
app.include_router(messagerie.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}