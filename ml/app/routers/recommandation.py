"""
Endpoint de recommandation — double mode :

1. MODE "catalogue réel" (payload.catalogue fourni, non vide)
   Recommande parmi de VRAIS biens SmartRent transmis par le back-end
   (ex. résultat de GET /biens). Le scaler de similarité est recalculé à
   la volée sur ce catalogue — s'adapte naturellement au fur et à mesure
   que la plateforme accumule de vraies annonces.

2. MODE "bootstrap externe" (par défaut, catalogue absent/vide)
   Recommande dans le catalogue Mubawab/Sarouty pré-entraîné
   (recommender_artifacts.joblib) — utile en cold start, quand la
   plateforme n'a pas encore assez de biens réels pour un mode 1 pertinent.

Le back-end décide quel mode utiliser en choisissant d'envoyer ou non un
catalogue (voir ia_client.py côté backend).
"""

import logging

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from ..feature_engineering import build_price_features, normalize_ville
from ..schemas import RecommandationItem, RecommandationRequest, RecommandationResponse

logger = logging.getLogger("ml_service.recommandation")
router = APIRouter(prefix="/predict", tags=["recommandation"])

LIVE_NUMERIC_FEATURES = ["prix", "superficie", "nb_pieces"]


def _recommend_in_live_catalogue(payload: RecommandationRequest) -> list[RecommandationItem]:
    catalogue = payload.catalogue
    df = pd.DataFrame([b.model_dump() for b in catalogue])
    df["nb_pieces"] = df["nb_pieces"].fillna(df["nb_pieces"].median() if df["nb_pieces"].notna().any() else 2)

    numeric = df[LIVE_NUMERIC_FEATURES].astype(float)
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric)

    villes = sorted(df["ville"].apply(normalize_ville).unique())
    ville_norm = df["ville"].apply(normalize_ville)
    ville_dummies = pd.get_dummies(ville_norm).reindex(columns=villes, fill_value=0).to_numpy()

    meuble_dummies = np.column_stack([
        (df["meuble"] == True).astype(int),   # noqa: E712
        (df["meuble"] == False).astype(int),  # noqa: E712
        df["meuble"].isna().astype(int),
    ])

    feature_matrix = np.hstack([numeric_scaled, ville_dummies, meuble_dummies])

    # --- Construction du vecteur requête (bien de référence ou préférences) ---
    if payload.bien_reference is not None:
        ref = payload.bien_reference
        query_num = pd.DataFrame(
            [[np.nan, ref.superficie, ref.nb_pieces or df["nb_pieces"].median()]],
            columns=LIVE_NUMERIC_FEATURES,
        )
        # Pas de prix pour une simple description de bien -> médiane du catalogue
        query_num["prix"] = df["prix"].median()
        query_ville = normalize_ville(ref.ville)
        query_meuble = ref.meuble
    else:
        query_num = pd.DataFrame(
            [[
                payload.budget_dh or df["prix"].median(),
                payload.superficie or df["superficie"].median(),
                payload.nb_pieces or df["nb_pieces"].median(),
            ]],
            columns=LIVE_NUMERIC_FEATURES,
        )
        query_ville = normalize_ville(payload.ville or "")
        query_meuble = payload.meuble

    query_num_scaled = scaler.transform(query_num[LIVE_NUMERIC_FEATURES])
    query_ville_dummy = pd.Series(0, index=villes)
    if query_ville in query_ville_dummy.index:
        query_ville_dummy[query_ville] = 1
    query_meuble_dummy = np.array([[
        1 if query_meuble is True else 0,
        1 if query_meuble is False else 0,
        1 if query_meuble is None else 0,
    ]])

    query_vector = np.hstack([query_num_scaled, query_ville_dummy.to_numpy().reshape(1, -1), query_meuble_dummy])
    scores = cosine_similarity(query_vector, feature_matrix)[0]
    order = np.argsort(scores)[::-1][: payload.top_n]

    results = []
    for i in order:
        row = df.iloc[i]
        results.append(RecommandationItem(
            id=row.get("id"),
            titre=row.get("titre"),
            ville=row["ville"],
            quartier=row.get("quartier"),
            prix_dh=float(row["prix"]),
            superficie_m2=float(row["superficie"]),
            score_similarite=round(float(scores[i]), 4),
        ))
    return results


def _recommend_in_bootstrap_catalogue(payload: RecommandationRequest, models) -> list[RecommandationItem]:
    recommender = models.recommender

    if payload.bien_reference is not None:
        ref_data = payload.bien_reference.model_dump()
        X_ref = build_price_features(ref_data, models.market)
        prix_estime_ref = float(models.price_model.predict(X_ref)[0])
        preferences = {
            "ville": normalize_ville(payload.bien_reference.ville),
            "budget_dh": prix_estime_ref,
            "surface_m2": payload.bien_reference.superficie,
            "chambres": payload.bien_reference.chambres or payload.bien_reference.nb_pieces,
            "salles_de_bain": payload.bien_reference.salles_de_bain,
            "meuble": payload.bien_reference.meuble,
        }
    else:
        preferences = {
            "ville": normalize_ville(payload.ville or ""),
            "budget_dh": payload.budget_dh,
            "surface_m2": payload.superficie,
            "chambres": payload.nb_pieces,
            "meuble": payload.meuble,
        }
        preferences = {k: v for k, v in preferences.items() if v is not None}

    df_reco = recommender.recommend_from_preferences(preferences, top_n=payload.top_n)

    results = []
    for _, row in df_reco.iterrows():
        results.append(RecommandationItem(
            id=None,
            titre=row.get("titre"),
            ville=row["ville"],
            quartier=row.get("quartier"),
            prix_dh=float(row["prix_dh"]),
            superficie_m2=float(row.get("surface_m2")) if pd.notna(row.get("surface_m2")) else None,
            score_similarite=round(float(row["score_similarite"]), 4),
        ))
    return results


@router.post("/recommandation", response_model=RecommandationResponse)
def recommander(payload: RecommandationRequest, request: Request) -> RecommandationResponse:
    models = request.app.state.models
    if not models.ready:
        raise HTTPException(status_code=503, detail="Modèles non chargés")

    if payload.bien_reference is None and payload.ville is None and not payload.catalogue:
        raise HTTPException(
            status_code=422,
            detail="Fournir soit 'bien_reference', soit au moins un critère de préférence (ville, budget_dh...)",
        )

    if payload.catalogue:
        if len(payload.catalogue) < 2:
            raise HTTPException(status_code=422, detail="Le catalogue réel doit contenir au moins 2 biens")
        resultats = _recommend_in_live_catalogue(payload)
        source = "reel"
    else:
        resultats = _recommend_in_bootstrap_catalogue(payload, models)
        source = "bootstrap_externe"

    return RecommandationResponse(source_catalogue=source, resultats=resultats)
