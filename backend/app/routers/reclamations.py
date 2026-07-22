import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_role

router = APIRouter(prefix="/reclamations", tags=["reclamations"])


@router.post("", response_model=schemas.ReclamationOut, status_code=201)
def create_reclamation(
    payload: schemas.ReclamationCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    reclamation = models.Reclamation(**payload.model_dump(), utilisateur_id=current_user.id)
    db.add(reclamation)
    db.commit()
    db.refresh(reclamation)
    return reclamation


@router.get("", response_model=list[schemas.ReclamationOut])
def list_reclamations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    return db.query(models.Reclamation).order_by(models.Reclamation.date_creation.desc()).all()


@router.patch("/{reclamation_id}/statut", response_model=schemas.ReclamationOut)
def update_statut(
    reclamation_id: uuid.UUID,
    payload: schemas.ReclamationStatutUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    reclamation = db.get(models.Reclamation, reclamation_id)
    if not reclamation:
        raise HTTPException(status_code=404, detail="Réclamation introuvable")
    reclamation.statut = payload.statut
    db.commit()
    db.refresh(reclamation)
    return reclamation
