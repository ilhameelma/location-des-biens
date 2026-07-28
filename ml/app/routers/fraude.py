import logging

from fastapi import APIRouter, HTTPException, Request

from ..feature_engineering import build_price_features
from ..schemas import FraudeRequest, FraudeResponse

logger = logging.getLogger("ml_service.fraude")
router = APIRouter(prefix="/predict", tags=["fraude"])


@router.post("/fraude", response_model=FraudeResponse)
def detecter_fraude(payload: FraudeRequest, request: Request) -> FraudeResponse:
    models = request.app.state.models
    if not models.ready:
        raise HTTPException(status_code=503, detail="Modèles non chargés")

    data = payload.model_dump()
    try:
        X_price = build_price_features(data, models.market)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    prix_attendu = float(models.price_model.predict(X_price)[0])
    ecart_prix_pct = (payload.prix_affiche_dh - prix_attendu) / prix_attendu

    # Reconstruit exactement les features utilisées à l'entraînement du
    # modèle de fraude (voir ml/train_model_fraude.py : FRAUD_FEATURES)
    X_fraud = X_price[["surface_m2", "chambres", "salles_de_bain", "quartier_prix_estime"]].copy()
    X_fraud.insert(0, "ecart_prix_pct", ecart_prix_pct)
    X_fraud = X_fraud[models.fraud_features]

    anomaly_score = float(-models.fraud_model.score_samples(X_fraud)[0])
    suspect_isolation_forest = bool(models.fraud_model.predict(X_fraud)[0] == -1)
    suspect_prix_bas = ecart_prix_pct < models.fraud_seuil_prix_bas

    est_suspect = suspect_isolation_forest or suspect_prix_bas

    if suspect_prix_bas:
        raison = (
            f"Prix affiché {abs(ecart_prix_pct):.0%} en dessous du prix attendu pour "
            f"ce type de bien — signal classique d'annonce-appât"
        )
    elif suspect_isolation_forest:
        raison = "Profil du bien atypique (combinaison surface/chambres/quartier inhabituelle)"
    else:
        raison = "Aucune anomalie détectée"

    return FraudeResponse(
        est_suspect=est_suspect,
        prix_attendu_dh=round(prix_attendu, -1),
        ecart_prix_pct=round(ecart_prix_pct, 4),
        raison=raison,
        anomaly_score=round(anomaly_score, 4),
    )
