import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_role

router = APIRouter(prefix="/paiements", tags=["paiements"])


@router.get("/me", response_model=list[schemas.PaiementOut])
def my_paiements(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    query = db.query(models.Paiement).join(models.Contrat, models.Contrat.id == models.Paiement.contrat_id)
    if current_user.role == "client":
        query = query.filter(models.Contrat.client_id == current_user.id)
    elif current_user.role == "proprietaire":
        query = query.filter(models.Contrat.proprietaire_id == current_user.id)
    return query.order_by(models.Paiement.date_paiement.desc()).all()


@router.post("", response_model=schemas.PaiementOut, status_code=status.HTTP_201_CREATED)
def create_paiement(
    payload: schemas.PaiementCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    contrat = db.get(models.Contrat, payload.contrat_id)
    if not contrat or contrat.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    paiement = models.Paiement(**payload.model_dump(), statut="reussi")
    db.add(paiement)
    db.commit()
    db.refresh(paiement)
    return paiement
