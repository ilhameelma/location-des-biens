import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .model_loader import load_models
from .routers import estimation, fraude, recommandation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ml_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage du micro-service IA — chargement des modèles...")
    app.state.models = load_models()
    yield
    logger.info("Arrêt du micro-service IA.")


app = FastAPI(
    title="SmartRent — Micro-service IA",
    description=(
        "Expose les 3 modèles de la Phase 4 (étape 16) : estimation de "
        "loyer, recommandation, détection de fraude. Appelé uniquement "
        "par le back-end principal, jamais directement par le front-end."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estimation.router)
app.include_router(recommandation.router)
app.include_router(fraude.router)


@app.get("/health")
def health():
    ready = getattr(app.state, "models", None) is not None and app.state.models.ready
    return {"status": "ok" if ready else "loading", "models_ready": ready}
