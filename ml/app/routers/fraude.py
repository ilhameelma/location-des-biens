import logging

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from ..feature_engineering import build_price_features
from ..feature_engineering_vente import KNOWN_VILLES_VENTE, build_fraud_row_vente, build_price_features_vente
from ..schemas import FraudeRequest, FraudeResponse

logger = logging.getLogger("ml_service.fraude")
router = APIRouter(prefix="/predict", tags=["fraude"])


def _detecter_fraude_location(payload: FraudeRequest, data: dict, models) -> FraudeResponse:
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

    return _construire_reponse(prix_attendu, ecart_prix_pct, anomaly_score, suspect_isolation_forest, suspect_prix_bas)


def _detecter_fraude_vente(payload: FraudeRequest, data: dict, models) -> FraudeResponse:
    try:
        X_price = build_price_features_vente(data, models.market_vente)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    prix_attendu = float(models.price_model_vente.predict(X_price)[0])
    ecart_prix_pct = (payload.prix_affiche_dh - prix_attendu) / prix_attendu

    # Le modèle de fraude VENTE (IsolationForest) attend des noms de colonnes
    # "bruts" (avec espaces pour "Dar Bouazza"/"El Jadida"/"El Mansouria"),
    # différents de ceux du modèle de prix LightGBM ci-dessus — voir le
    # docstring de feature_engineering_vente.py pour le détail de ce piège.
    valeurs, ville_norm = build_fraud_row_vente(data, models.market_vente)
    row = dict(valeurs)
    for v in KNOWN_VILLES_VENTE + ["Autre", "Inconnu"]:
        row[f"ville_{v}"] = 1 if v == ville_norm else 0
    row["ecart_prix_pct"] = ecart_prix_pct
    X_fraud = pd.DataFrame([row]).reindex(columns=models.fraud_features_vente, fill_value=0)

    anomaly_score = float(-models.fraud_model_vente.score_samples(X_fraud)[0])
    suspect_isolation_forest = bool(models.fraud_model_vente.predict(X_fraud)[0] == -1)
    suspect_prix_bas = ecart_prix_pct < models.fraud_seuil_prix_bas_vente

    return _construire_reponse(prix_attendu, ecart_prix_pct, anomaly_score, suspect_isolation_forest, suspect_prix_bas)


def _construire_reponse(
    prix_attendu: float,
    ecart_prix_pct: float,
    anomaly_score: float,
    suspect_isolation_forest: bool,
    suspect_prix_bas: bool,
) -> FraudeResponse:
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


@router.post("/fraude", response_model=FraudeResponse)
def detecter_fraude(payload: FraudeRequest, request: Request) -> FraudeResponse:
    models = request.app.state.models
    if not models.ready:
        raise HTTPException(status_code=503, detail="Modèles non chargés")

    data = payload.model_dump()

    if payload.type_transaction == "vente":
        return _detecter_fraude_vente(payload, data, models)
    return _detecter_fraude_location(payload, data, models)
