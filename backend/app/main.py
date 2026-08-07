from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from . import storage, ws_manager, es_client
from .routers import (
    auth,
    biens,
    reservations,
    contrats,
    paiements,
    avis,
    reclamations,
    favoris,
    messagerie,
    notifications,
    utilisateurs,
    ia,
    recherches,
    projets,
    actualites,
)

# Crée les tables si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

# Étape 7 — Stockage des images : crée le bucket MinIO au démarrage
# (s'il n'existe pas déjà) et lui applique une politique de lecture publique.
storage.ensure_bucket()

# Étape 18 — Recherche avancée : crée l'index Elasticsearch au démarrage
# (s'il n'existe pas déjà). Best-effort : si Elasticsearch n'est pas encore
# lancé, l'application démarre quand même (repli SQL automatique, voir
# app/routers/biens.py et app/es_client.py).
es_client.ensure_index()

app = FastAPI(
    title="SmartRent Platform API",
    description="API REST du back-end SmartRent",
    version="0.1.0",
)


@app.on_event("startup")
async def _capture_main_event_loop():
    """
    Étape 9 — Notifications : mémorise la boucle asyncio principale pour
    pouvoir y planifier en toute sécurité la diffusion WebSocket des
    notifications depuis les endpoints synchrones (voir app/notifications_service.py).
    """
    import asyncio

    ws_manager.set_main_loop(asyncio.get_running_loop())


@app.on_event("startup")
async def _demarrer_verification_paiements():
    """
    Processus de paiement après confirmation d'une réservation : lance en
    arrière-plan la vérification périodique des contrats impayés dont le
    délai est dépassé (voir app/paiement_expiration.py). `create_task` ne
    bloque pas le démarrage — la boucle tourne indéfiniment à côté du
    reste de l'application.
    """
    import asyncio

    from .paiement_expiration import boucle_verification_paiements

    asyncio.create_task(boucle_verification_paiements())

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
# Note : les photos de biens (étape 7) ne sont plus servies par le
# back-end. Elles sont uploadées vers MinIO (voir app/storage.py et
# app/routers/biens.py) et servies directement par MinIO via une URL
# publique (ex: http://localhost:9000/smartrent-photos/biens/...).
# ============================================================
# ROUTERS API
# ============================================================
app.include_router(auth.router, prefix="/api")
app.include_router(utilisateurs.router, prefix="/api")
app.include_router(biens.router, prefix="/api")
app.include_router(reservations.router, prefix="/api")
app.include_router(contrats.router, prefix="/api")
app.include_router(paiements.router, prefix="/api")
app.include_router(avis.router, prefix="/api")
app.include_router(reclamations.router, prefix="/api")
app.include_router(favoris.router, prefix="/api")
app.include_router(messagerie.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(ia.router, prefix="/api")
app.include_router(recherches.router, prefix="/api")
app.include_router(projets.router, prefix="/api")
app.include_router(actualites.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}