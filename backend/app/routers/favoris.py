"""Router FastAPI pour les annonces enregistrées ("favoris") côté client."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/favoris", tags=["favoris"])


@router.post("", response_model=schemas.FavoriOut, status_code=201)
def add_favori(
    payload: schemas.FavoriCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    bien = db.get(models.Bien, payload.bien_id)
    if not bien:
        raise HTTPException(status_code=404, detail="Bien introuvable")

    existing = (
        db.query(models.Favori)
        .filter(
            models.Favori.utilisateur_id == current_user.id,
            models.Favori.bien_id == payload.bien_id,
        )
        .first()
    )
    if existing:
        # Idempotent : l'annonce est déjà enregistrée, on renvoie l'existant
        # plutôt que de lever une erreur (évite un cas d'échec si l'utilisateur
        # double-clique ou recharge la page).
        return existing

    favori = models.Favori(utilisateur_id=current_user.id, bien_id=payload.bien_id)
    db.add(favori)
    db.commit()
    db.refresh(favori)
    return favori


@router.delete("/{bien_id}", status_code=204)
def remove_favori(
    bien_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    favori = (
        db.query(models.Favori)
        .filter(
            models.Favori.utilisateur_id == current_user.id,
            models.Favori.bien_id == bien_id,
        )
        .first()
    )
    if favori:
        db.delete(favori)
        db.commit()
    return None


@router.get("/me/ids", response_model=list[uuid.UUID])
def my_favori_ids(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    """Liste légère des bien_id enregistrés — utilisée par la fiche détaillée
    d'une annonce pour savoir si le bouton "Enregistrer" doit apparaître actif,
    sans avoir à recharger la liste complète des biens."""
    rows = (
        db.query(models.Favori.bien_id)
        .filter(models.Favori.utilisateur_id == current_user.id)
        .all()
    )
    return [r[0] for r in rows]


@router.get("/me", response_model=list[schemas.BienOut])
def my_favoris(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    """Page « Annonces enregistrées » (client) : les biens mis de côté,
    du plus récemment enregistré au plus ancien."""
    biens = (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos))
        .join(models.Favori, models.Favori.bien_id == models.Bien.id)
        .filter(models.Favori.utilisateur_id == current_user.id)
        .order_by(models.Favori.date_creation.desc())
        .all()
    )
    return biens
