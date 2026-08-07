import logging

from fastapi import APIRouter, HTTPException, Request

from ..feature_engineering import build_price_features
from ..feature_engineering_vente import build_price_features_vente
from ..schemas import EstimationRequest, EstimationResponse

logger = logging.getLogger("ml_service.estimation")
router = APIRouter(prefix="/predict", tags=["estimation"])

# Demi-largeur de la fourchette LOCATION = MAE mesuré sur le jeu de test à
# l'entraînement (voir rapport_preparation.md). À mettre à jour si le
# modèle est ré-entraîné avec un score différent.
MARGE_ERREUR_DH_LOCATION = 2679.0

# Demi-largeur de la fourchette VENTE, en pourcentage du prix estimé plutôt
# qu'un montant DH fixe (un bien à 300 000 DH et un bien à 15 000 000 DH n'ont
# pas la même marge d'erreur absolue). Valeur approximative faute de jeu de
# test dédié dans cette livraison (voir README_ia_vente.md) — à recalibrer
# dès qu'un vrai split train/test vente est disponible.
MARGE_ERREUR_PCT_VENTE = 0.30


@router.post("/estimation", response_model=EstimationResponse)
def estimer_prix(payload: EstimationRequest, request: Request) -> EstimationResponse:
    models = request.app.state.models
    if not models.ready:
        raise HTTPException(status_code=503, detail="Modèles non chargés")

    data = payload.model_dump()

    if payload.type_transaction == "vente":
        try:
            X = build_price_features_vente(data, models.market_vente)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        prix_estime = float(models.price_model_vente.predict(X)[0])
        marge = prix_estime * MARGE_ERREUR_PCT_VENTE
    else:
        try:
            X = build_price_features(data, models.market)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        prix_estime = float(models.price_model.predict(X)[0])
        marge = MARGE_ERREUR_DH_LOCATION

    return EstimationResponse(
        prix_estime_dh=round(prix_estime, -1),
        fourchette_basse_dh=round(max(0, prix_estime - marge), -1),
        fourchette_haute_dh=round(prix_estime + marge, -1),
        marge_erreur_dh=round(marge, -1),
    )
