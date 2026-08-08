"""
Chargement des artefacts ML au démarrage du micro-service.
Un seul chargement en mémoire (pas de rechargement par requête).

Depuis l'ajout de la séparation location/vente : 6 artefacts au total
(3 par type de transaction), tous chargés au démarrage — la sélection
location vs vente se fait ensuite par routeur, au niveau de chaque requête
(voir routers/estimation.py, fraude.py, recommandation.py), selon le champ
`type_transaction` du payload.
"""

import logging
import sys
from pathlib import Path

import joblib

from .config import settings
from .feature_engineering import MarketReference
from .feature_engineering_vente import MarketReferenceVente
from .recommender_model import PropertyRecommender, PropertyRecommenderVentes

logger = logging.getLogger("ml_service.model_loader")

# Compatibilité de dépicklage : les deux recommandeurs (*_artifacts.joblib)
# ont été sauvegardés pendant que leur script d'entraînement respectif
# tournait en __main__. Pickle retrouve les classes par leur module
# d'origine — on republie donc les deux classes sous __main__ juste avant
# le chargement, pour que joblib.load() les retrouve quel que soit le
# contexte d'exécution du micro-service.
sys.modules["__main__"].PropertyRecommender = PropertyRecommender
sys.modules["__main__"].PropertyRecommenderVentes = PropertyRecommenderVentes


class Models:
    """Conteneur simple pour les 6 modèles (location + vente) + les 2
    références marché, injecté dans les routers via l'état de l'application
    FastAPI (app.state.models)."""

    def __init__(self):
        # --- Location ---
        self.price_model = None
        self.fraud_model = None
        self.fraud_features: list[str] | None = None
        self.fraud_seuil_prix_bas: float | None = None
        self.recommender = None
        self.market: MarketReference | None = None

        # --- Vente ---
        self.price_model_vente = None
        self.fraud_model_vente = None
        self.fraud_features_vente: list[str] | None = None
        self.fraud_seuil_prix_bas_vente: float | None = None
        self.recommender_vente = None
        self.market_vente: MarketReferenceVente | None = None

        self.ready = False


def load_models() -> Models:
    models_dir = Path(settings.models_dir)
    m = Models()

    price_path = models_dir / "modele_estimation_loyer.joblib"
    fraud_path = models_dir / "modele_fraude.joblib"
    reco_path = models_dir / "recommender_artifacts.joblib"

    price_path_vente = models_dir / "modele_estimation_vente.joblib"
    fraud_path_vente = models_dir / "modele_fraude_vente.joblib"
    reco_path_vente = models_dir / "recommender_ventes_artifacts.joblib"

    all_paths = (price_path, fraud_path, reco_path, price_path_vente, fraud_path_vente, reco_path_vente)
    missing = [p for p in all_paths if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Modèles introuvables : {[str(p) for p in missing]}. "
            f"Vérifie ML_MODELS_DIR (actuellement '{models_dir}')."
        )

    # --- Location ---
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

    # --- Vente ---
    logger.info("Chargement modele_estimation_vente.joblib ...")
    m.price_model_vente = joblib.load(price_path_vente)

    logger.info("Chargement modele_fraude_vente.joblib ...")
    fraud_artifact_vente = joblib.load(fraud_path_vente)
    m.fraud_model_vente = fraud_artifact_vente["model"]
    m.fraud_features_vente = fraud_artifact_vente["features"]
    m.fraud_seuil_prix_bas_vente = fraud_artifact_vente["seuil_prix_bas"]

    logger.info("Chargement recommender_ventes_artifacts.joblib ...")
    m.recommender_vente = joblib.load(reco_path_vente)
    m.market_vente = MarketReferenceVente(m.recommender_vente.catalog)

    m.ready = True
    logger.info("Les 6 modèles (location + vente) sont chargés et prêts.")
    return m
