"""
Étape 16 — Intelligence artificielle

Endpoints appelés par le front-end (ou par d'autres endpoints back-end,
ex. suggestion de prix à la publication d'une annonce). Chaque endpoint a
deux variantes :
  - POST .../  avec un payload libre (simulation, formulaire de publication
    avant même que le bien existe en base)
  - GET .../{bien_id}  sur un bien déjà existant (fiche annonce, modération)
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user, require_role
from ..ml_client import MLServiceError, detecter_fraude, estimer_loyer, recommander
from ..schemas_ia import (
    SEUIL_CATALOGUE_REEL,
    BienEstimationInput,
    BienFraudeInput,
    RecommandationPreferences,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ia", tags=["intelligence-artificielle"])


def _bien_to_payload(bien: models.Bien) -> dict:
    return {
        "ville": bien.ville,
        "superficie": float(bien.superficie) if bien.superficie else None,
        "nb_pieces": bien.nb_pieces,
        "type_bien": bien.type_bien,
        "type_transaction": bien.type_transaction,
    }


def _get_bien_or_404(db: Session, bien_id: uuid.UUID) -> models.Bien:
    bien = db.get(models.Bien, bien_id)
    if not bien:
        raise HTTPException(status_code=404, detail="Bien introuvable")
    return bien


def _catalogue_reel_disponible(db: Session, type_transaction: str) -> list[dict]:
    """Biens actuellement disponibles pour le type de transaction demandé
    (location OU vente — jamais les deux mélangés, au format attendu par
    le micro-service IA (mode recommandation catalogue réel)."""
    biens = db.execute(
        select(models.Bien).where(
            models.Bien.statut == "disponible",
            models.Bien.type_transaction == type_transaction,
        )
    ).scalars().all()
    return [
        {
            "id": str(b.id),
            "titre": b.titre,
            "ville": b.ville,
            "prix": float(b.prix),
            "superficie": float(b.superficie) if b.superficie else 0,
            "nb_pieces": b.nb_pieces,
        }
        for b in biens
        if b.superficie  # la superficie est requise côté modèle
    ]


# ---------------------------------------------------------------------------
# Estimation de loyer (16a)
# ---------------------------------------------------------------------------

@router.post("/estimation")
def estimer(payload: BienEstimationInput, current_user: models.Utilisateur = Depends(get_current_user)):
    try:
        return estimer_loyer(payload.model_dump())
    except MLServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/estimation/{bien_id}")
def estimer_bien_existant(
    bien_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    bien = _get_bien_or_404(db, bien_id)
    try:
        return estimer_loyer(_bien_to_payload(bien))
    except MLServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ---------------------------------------------------------------------------
# Détection de fraude (16c) — réservé aux admins (outil de modération)
# ---------------------------------------------------------------------------

@router.post("/fraude")
def verifier_fraude(payload: BienFraudeInput, current_user: models.Utilisateur = Depends(require_role("admin"))):
    try:
        return detecter_fraude(payload.model_dump())
    except MLServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/fraude/{bien_id}")
def verifier_fraude_bien_existant(
    bien_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    bien = _get_bien_or_404(db, bien_id)
    payload = _bien_to_payload(bien)
    payload["prix_affiche_dh"] = float(bien.prix)
    try:
        return detecter_fraude(payload)
    except MLServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ---------------------------------------------------------------------------
# Recommandation (16b)
# ---------------------------------------------------------------------------

@router.post("/recommandation")
def recommander_depuis_preferences(
    payload: RecommandationPreferences,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    body = {
        "type_transaction": payload.type_transaction,
        "ville": payload.ville,
        "budget_dh": payload.budget_dh,
        "superficie": payload.superficie,
        "nb_pieces": payload.nb_pieces,
        "meuble": payload.meuble,
        "top_n": payload.top_n,
    }

    if payload.utiliser_catalogue_reel:
        catalogue = _catalogue_reel_disponible(db, payload.type_transaction)
        if len(catalogue) >= SEUIL_CATALOGUE_REEL:
            body["catalogue"] = catalogue
        else:
            logger.info(
                "Catalogue réel (%s) trop petit (%d biens, seuil=%d) — recommandation "
                "en mode bootstrap externe.", payload.type_transaction, len(catalogue), SEUIL_CATALOGUE_REEL,
            )

    try:
        return recommander(body)
    except MLServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/recommandation/{bien_id}")
def biens_similaires(
    bien_id: uuid.UUID,
    top_n: int = 5,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """Biens similaires à afficher sur une fiche annonce."""
    bien = _get_bien_or_404(db, bien_id)

    body = {
        "type_transaction": bien.type_transaction,
        "bien_reference": _bien_to_payload(bien),
        "top_n": top_n,
    }

    catalogue = [c for c in _catalogue_reel_disponible(db, bien.type_transaction) if c["id"] != str(bien_id)]
    if len(catalogue) >= SEUIL_CATALOGUE_REEL:
        body["catalogue"] = catalogue

    try:
        return recommander(body)
    except MLServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
