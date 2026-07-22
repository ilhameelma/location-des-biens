"""Router FastAPI pour la gestion des biens immobiliers (propriétaire)."""
import uuid
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_role

router = APIRouter(prefix="/biens", tags=["biens"])

# ============================================================
# Upload de photos — dossier de stockage local
# ============================================================
UPLOAD_DIR = "uploads/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def serve_uploads(app):
    """
    À appeler dans main.py pour servir les fichiers uploadés.
    Exemple dans main.py :
        from app.routers.biens import serve_uploads
        serve_uploads(app)
    """
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ============================================================
# Endpoints
# ============================================================

@router.get("/me/annonces", response_model=List[schemas.BienOut])
def list_my_biens(
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """Liste les biens du propriétaire connecté (avec photos)."""
    biens = (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos))
        .filter(models.Bien.proprietaire_id == user.id)
        .order_by(models.Bien.date_publication.desc())
        .all()
    )
    return biens


@router.get("/{bien_id}", response_model=schemas.BienOut)
def get_bien(
    bien_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(get_current_user),
):
    """Récupère un bien par son ID."""
    bien = db.get(models.Bien, bien_id)
    if not bien:
        raise HTTPException(status_code=404, detail="Bien non trouvé")
    return bien


@router.post("", response_model=schemas.BienOut, status_code=status.HTTP_201_CREATED)
def create_bien(
    payload: schemas.BienCreate,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """Crée une nouvelle annonce (bien immobilier)."""
    bien = models.Bien(
        **payload.model_dump(),
        proprietaire_id=user.id,
        statut="disponible",
    )
    db.add(bien)
    db.commit()
    db.refresh(bien)
    return bien


@router.patch("/{bien_id}", response_model=schemas.BienOut)
def update_bien(
    bien_id: uuid.UUID,
    payload: schemas.BienUpdate,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """Met à jour un bien existant."""
    bien = db.get(models.Bien, bien_id)
    if not bien or bien.proprietaire_id != user.id:
        raise HTTPException(status_code=404, detail="Bien non trouvé")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(bien, field, value)

    db.commit()
    db.refresh(bien)
    return bien


@router.delete("/{bien_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bien(
    bien_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """Supprime un bien et ses photos."""
    bien = db.get(models.Bien, bien_id)
    if not bien or bien.proprietaire_id != user.id:
        raise HTTPException(status_code=404, detail="Bien non trouvé")

    # Supprimer les fichiers physiques
    for photo in bien.photos:
        filepath = os.path.join(UPLOAD_DIR, os.path.basename(photo.url))
        if os.path.exists(filepath):
            os.remove(filepath)

    db.delete(bien)
    db.commit()
    return None


# ============================================================
# Upload de photos
# ============================================================

@router.post("/{bien_id}/photos", response_model=List[schemas.PhotoBienOut])
async def upload_photos(
    bien_id: uuid.UUID,
    photos: List[UploadFile] = File(...),
    ordres: List[str] = Form(default=[]),
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """
    Upload des photos pour un bien.
    Les fichiers sont stockés localement dans 'uploads/photos/'.
    """
    bien = db.get(models.Bien, bien_id)
    if not bien or bien.proprietaire_id != user.id:
        raise HTTPException(status_code=404, detail="Bien non trouvé")

    saved_photos = []

    for idx, photo in enumerate(photos):
        ext = os.path.splitext(photo.filename or "")[1] or ".jpg"
        filename = f"{bien_id}_{idx}_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        content = await photo.read()
        with open(filepath, "wb") as f:
            f.write(content)

        ordre = int(ordres[idx]) if idx < len(ordres) else idx
        db_photo = models.PhotoBien(
            bien_id=bien_id,
            url=f"/uploads/photos/{filename}",
            ordre=ordre,
        )
        db.add(db_photo)
        saved_photos.append(db_photo)

    db.commit()
    for p in saved_photos:
        db.refresh(p)

    return saved_photos