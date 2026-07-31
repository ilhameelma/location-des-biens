import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/avis", tags=["avis"])


def _enrich(db: Session, avis_list: list[models.Avis]) -> list[schemas.AvisOut]:
    """Complète chaque avis avec le nom du client et le titre du bien concerné,
    via deux requêtes groupées (pas une par avis) — utilisé par les pages
    « Mes avis » (client) et « Avis reçus » (propriétaire)."""
    if not avis_list:
        return []

    client_ids = {a.client_id for a in avis_list}
    bien_ids = {a.bien_id for a in avis_list}

    clients = {
        u.id: u
        for u in db.query(models.Utilisateur).filter(models.Utilisateur.id.in_(client_ids))
    }
    biens = {b.id: b for b in db.query(models.Bien).filter(models.Bien.id.in_(bien_ids))}

    result = []
    for a in avis_list:
        client = clients.get(a.client_id)
        bien = biens.get(a.bien_id)
        result.append(
            schemas.AvisOut(
                id=a.id,
                client_id=a.client_id,
                proprietaire_id=a.proprietaire_id,
                bien_id=a.bien_id,
                note=a.note,
                commentaire=a.commentaire,
                date_creation=a.date_creation,
                client_nom=client.nom if client else None,
                client_prenom=client.prenom if client else None,
                bien_titre=bien.titre if bien else None,
            )
        )
    return result


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
    return _enrich(db, [avis])[0]


@router.get("/me", response_model=list[schemas.AvisOut])
def my_avis(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    """Page « Mes avis » (client) : les avis que j'ai laissés."""
    avis_list = (
        db.query(models.Avis)
        .filter(models.Avis.client_id == current_user.id)
        .order_by(models.Avis.date_creation.desc())
        .all()
    )
    return _enrich(db, avis_list)


@router.get("/proprietaire/me", response_model=list[schemas.AvisOut])
def mes_avis_recus(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """Page « Avis clients » (propriétaire) : les avis laissés par mes clients
    sur mes biens."""
    avis_list = (
        db.query(models.Avis)
        .filter(models.Avis.proprietaire_id == current_user.id)
        .order_by(models.Avis.date_creation.desc())
        .all()
    )
    return _enrich(db, avis_list)


@router.get("/proprietaire/{proprietaire_id}", response_model=list[schemas.AvisOut])
def avis_recus(proprietaire_id: uuid.UUID, db: Session = Depends(get_db)):
    """Consultation publique des avis d'un propriétaire (ex. affichée sur une
    fiche bien) — pas d'authentification requise."""
    avis_list = (
        db.query(models.Avis)
        .filter(models.Avis.proprietaire_id == proprietaire_id)
        .order_by(models.Avis.date_creation.desc())
        .all()
    )
    return _enrich(db, avis_list)
