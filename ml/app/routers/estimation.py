import logging

from fastapi import APIRouter, HTTPException, Request

from ..feature_engineering import build_price_features
from ..schemas import EstimationRequest, EstimationResponse

logger = logging.getLogger("ml_service.estimation")
router = APIRouter(prefix="/predict", tags=["estimation"])

# Demi-largeur de la fourchette = MAE mesuré sur le jeu de test à
# l'entraînement (voir rapport_entrainement.md). À mettre à jour si le
# modèle est ré-entraîné avec un score différent.
MARGE_ERREUR_DH = 2679.0


@router.post("/estimation", response_model=EstimationResponse)
def estimer_loyer(payload: EstimationRequest, request: Request) -> EstimationResponse:
    models = request.app.state.models
    if not models.ready:
        raise HTTPException(status_code=503, detail="Modèles non chargés")

    try:
        X = build_price_features(payload.model_dump(), models.market)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    prix_estime = float(models.price_model.predict(X)[0])

    return EstimationResponse(
        prix_estime_dh=round(prix_estime, -1),
        fourchette_basse_dh=round(max(0, prix_estime - MARGE_ERREUR_DH), -1),
        fourchette_haute_dh=round(prix_estime + MARGE_ERREUR_DH, -1),
        marge_erreur_dh=MARGE_ERREUR_DH,
    )
