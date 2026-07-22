import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


@router.get("", response_model=list[schemas.UtilisateurOut])
def list_utilisateurs(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    return db.query(models.Utilisateur).order_by(models.Utilisateur.date_creation.desc()).all()


@router.patch("/{utilisateur_id}/verifier", response_model=schemas.UtilisateurOut)
def verifier_utilisateur(
    utilisateur_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    """Un admin vérifie un compte propriétaire avant qu'il puisse publier (cf. cahier des charges)."""
    user = db.get(models.Utilisateur, utilisateur_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.statut_verification = "verifie"
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{utilisateur_id}/rejeter", response_model=schemas.UtilisateurOut)
def rejeter_utilisateur(
    utilisateur_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    user = db.get(models.Utilisateur, utilisateur_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.statut_verification = "rejete"
    db.commit()
    db.refresh(user)
    return user
