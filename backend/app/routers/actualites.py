"""
Router FastAPI pour les actualités de la plateforme.

Un administrateur publie des actualités (titre, contenu, image optionnelle) ;
elles sont affichées sur la page d'accueil publique (landing page), visibles
par tout visiteur, connecté ou non — comme le catalogue d'annonces (voir
`GET /biens`, rendu public via `get_optional_user`).
"""
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import models, schemas, storage
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/actualites", tags=["actualites"])

logger = logging.getLogger(__name__)


def _enrich(db: Session, actualites: list[models.Actualite]) -> list[schemas.ActualiteOut]:
    """Complète chaque actualité avec le nom de l'admin auteur (une seule
    requête groupée, pas de N+1)."""
    if not actualites:
        return []

    auteur_ids = {a.auteur_id for a in actualites}
    auteurs = {
        u.id: u
        for u in db.query(models.Utilisateur).filter(models.Utilisateur.id.in_(auteur_ids))
    }

    result = []
    for a in actualites:
        auteur = auteurs.get(a.auteur_id)
        result.append(
            schemas.ActualiteOut(
                id=a.id,
                auteur_id=a.auteur_id,
                titre=a.titre,
                contenu=a.contenu,
                image_url=a.image_url,
                publie=a.publie,
                date_creation=a.date_creation,
                date_maj=a.date_maj,
                auteur_nom=auteur.nom if auteur else None,
                auteur_prenom=auteur.prenom if auteur else None,
            )
        )
    return result


# ============================================================
# Consultation publique — landing page
# ============================================================

@router.get("", response_model=List[schemas.ActualiteOut])
def list_actualites_publiques(
    limite: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Actualités publiées, les plus récentes d'abord — utilisé par la
    landing page. Pas d'authentification requise. `limite` optionnel pour
    ne récupérer que les N dernières (ex. 3-4 sur la page d'accueil)."""
    query = (
        db.query(models.Actualite)
        .filter(models.Actualite.publie.is_(True))
        .order_by(models.Actualite.date_creation.desc())
    )
    if limite is not None:
        query = query.limit(limite)
    return _enrich(db, query.all())


# ============================================================
# Gestion admin
# ============================================================

@router.get("/admin", response_model=List[schemas.ActualiteOut])
def list_actualites_admin(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    """Toutes les actualités (publiées ou non) — page de gestion admin."""
    actualites = (
        db.query(models.Actualite).order_by(models.Actualite.date_creation.desc()).all()
    )
    return _enrich(db, actualites)


@router.post("", response_model=schemas.ActualiteOut, status_code=status.HTTP_201_CREATED)
def create_actualite(
    payload: schemas.ActualiteCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    actualite = models.Actualite(**payload.model_dump(), auteur_id=current_user.id)
    db.add(actualite)
    db.commit()
    db.refresh(actualite)
    return _enrich(db, [actualite])[0]


@router.patch("/{actualite_id}", response_model=schemas.ActualiteOut)
def update_actualite(
    actualite_id: uuid.UUID,
    payload: schemas.ActualiteUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    actualite = db.get(models.Actualite, actualite_id)
    if not actualite:
        raise HTTPException(status_code=404, detail="Actualité introuvable")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(actualite, field, value)

    db.commit()
    db.refresh(actualite)
    return _enrich(db, [actualite])[0]


@router.post("/{actualite_id}/image", response_model=schemas.ActualiteOut)
async def upload_image(
    actualite_id: uuid.UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    """Upload (ou remplace) l'image d'illustration d'une actualité, vers le
    même bucket MinIO que les photos de biens, sous un préfixe dédié
    `actualites/<actualite_id>/`."""
    actualite = db.get(models.Actualite, actualite_id)
    if not actualite:
        raise HTTPException(status_code=404, detail="Actualité introuvable")

    content = await image.read()
    content_type = image.content_type
    ext = ".png" if content_type == "image/png" else ".jpg"
    object_name = f"actualites/{actualite_id}/{uuid.uuid4().hex}{ext}"

    image_url = storage.upload_photo(object_name, content, content_type)
    actualite.image_url = image_url
    db.commit()
    db.refresh(actualite)
    return _enrich(db, [actualite])[0]


@router.delete("/{actualite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_actualite(
    actualite_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    actualite = db.get(models.Actualite, actualite_id)
    if not actualite:
        raise HTTPException(status_code=404, detail="Actualité introuvable")
    db.delete(actualite)
    db.commit()
    return None
