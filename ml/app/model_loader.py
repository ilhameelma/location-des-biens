"""
Chargement des artefacts ML au démarrage du micro-service.
Un seul chargement en mémoire (pas de rechargement par requête).
"""

import logging
import sys
from pathlib import Path

import joblib

from .config import settings
from .feature_engineering import MarketReference
from .recommender_model import PropertyRecommender

logger = logging.getLogger("ml_service.model_loader")

# Compatibilité de dépicklage : recommender_artifacts.joblib a été sauvegardé
# pendant que le script d'entraînement tournait en __main__. Pickle retrouve
# les classes par leur module d'origine — on republie donc la classe sous
# __main__ juste avant le chargement, pour que joblib.load() la retrouve
# quel que soit le contexte d'exécution du micro-service.
sys.modules["__main__"].PropertyRecommender = PropertyRecommender

logger = logging.getLogger("ml_service.model_loader")


class Models:
    """Conteneur simple pour les 3 modèles + la référence marché, injecté
    dans les routers via l'état de l'application FastAPI (app.state.models)."""

    def __init__(self):
        self.price_model = None
        self.fraud_model = None
        self.fraud_features: list[str] | None = None
        self.fraud_seuil_prix_bas: float | None = None
        self.recommender = None
        self.market: MarketReference | None = None
        self.ready = False


def load_models() -> Models:
    models_dir = Path(settings.models_dir)
    m = Models()

    price_path = models_dir / "modele_estimation_loyer.joblib"
    fraud_path = models_dir / "modele_fraude.joblib"
    reco_path = models_dir / "recommender_artifacts.joblib"

    missing = [p for p in (price_path, fraud_path, reco_path) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Modèles introuvables : {[str(p) for p in missing]}. "
            f"Vérifie ML_MODELS_DIR (actuellement '{models_dir}')."
        )

    logger.info("Chargement modele_estimation_loyer.joblib ...")
    m.price_model = joblib.load(price_path)

    logger.info("Chargement modele_fraude.joblib ...")
    fraud_artifact = joblib.load(fraud_path)
    m.fraud_model = fraud_artifact["model"]
    m.fraud_features = fraud_artifact["features"]
    m.fraud_seuil_prix_bas = fraud_artifact["seuil_prix_bas"]

    logger.info("Chargement recommender_artifacts.joblib ...")
    m.recommender = joblib.load(reco_path)

    m.market = MarketReference(m.recommender.catalog)

    m.ready = True
    logger.info("Les 3 modèles sont chargés et prêts.")
    return m
