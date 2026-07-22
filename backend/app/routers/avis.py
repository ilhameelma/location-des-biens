import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/avis", tags=["avis"])


@router.post("", response_model=schemas.AvisOut, status_code=201)
def create_avis(
    payload: schemas.AvisCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    avis = models.Avis(**payload.model_dump(), client_id=current_user.id)
    db.add(avis)
    db.commit()
    db.refresh(avis)
    return avis


@router.get("/me", response_model=list[schemas.AvisOut])
def my_avis(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    return db.query(models.Avis).filter(models.Avis.client_id == current_user.id).all()


@router.get("/proprietaire/{proprietaire_id}", response_model=list[schemas.AvisOut])
def avis_recus(proprietaire_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(models.Avis).filter(models.Avis.proprietaire_id == proprietaire_id).all()
