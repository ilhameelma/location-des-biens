import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/contrats", tags=["contrats"])


@router.get("/me", response_model=list[schemas.ContratOut])
def my_contrats(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    query = db.query(models.Contrat)
    if current_user.role == "client":
        query = query.filter(models.Contrat.client_id == current_user.id)
    elif current_user.role == "proprietaire":
        query = query.filter(models.Contrat.proprietaire_id == current_user.id)
    return query.order_by(models.Contrat.date_creation.desc()).all()


@router.patch("/{contrat_id}/resilier", response_model=schemas.ContratOut)
def resilier_contrat(
    contrat_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    contrat = db.get(models.Contrat, contrat_id)
    if not contrat:
        raise HTTPException(status_code=404, detail="Contrat introuvable")
    if current_user.id not in (contrat.proprietaire_id, contrat.client_id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    contrat.statut = "resilie"
    bien = db.get(models.Bien, contrat.bien_id)
    if bien:
        bien.statut = "disponible"
    db.commit()
    db.refresh(contrat)
    return contrat
