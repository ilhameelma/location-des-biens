"""Router FastAPI pour la gestion des biens immobiliers (propriétaire)."""
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, storage
from ..database import get_db
from ..deps import get_current_user, require_role, get_optional_user
from ..kafka_producer import publish_event
from ..kafka_topics import BIEN_CREE
from .. import es_client

router = APIRouter(prefix="/biens", tags=["biens"])


# ============================================================
# Endpoints
# ============================================================

@router.get("", response_model=List[schemas.BienOut])
def search_biens(
    ville: str | None = None,
    type_bien: str | None = None,
    type_transaction: str | None = None,
    prix_max: float | None = None,
    prix_min: float | None = None,
    superficie_min: float | None = None,
    superficie_max: float | None = None,
    nb_pieces_min: int | None = None,
    q: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    rayon_km: float | None = None,
    tri: str = "pertinence",
    db: Session = Depends(get_db),
    # Endpoint réellement public (recherche + landing page) : la dépendance
    # optionnelle ne rejette jamais la requête faute de token — corrige un bug
    # où `get_current_user` (obligatoire) renvoyait 401 "Not authenticated"
    # pour tout visiteur non connecté, alors que ce paramètre `user` n'est
    # même pas utilisé plus bas dans la fonction.
    user: models.Utilisateur | None = Depends(get_optional_user),
):
    """
    Recherche publique des biens (espace client) : ne renvoie que les biens
    au statut "disponible".

    Étape 18 — Recherche avancée : la recherche est déléguée à Elasticsearch
    (texte libre `q` sur titre/ville/adresse/description, filtres prix/
    superficie/nb_pieces, recherche géographique par rayon autour de
    `lat`/`lon`, tri par pertinence/prix/date). Si Elasticsearch est
    indisponible, on bascule automatiquement sur un filtrage SQL classique
    (comportement identique à avant l'étape 18) — la recherche continue de
    fonctionner, juste sans texte libre ni tri par pertinence.
    """
    try:
        ids = es_client.search_biens(
            q=q,
            ville=ville,
            type_bien=type_bien,
            type_transaction=type_transaction,
            prix_min=prix_min,
            prix_max=prix_max,
            superficie_min=superficie_min,
            superficie_max=superficie_max,
            nb_pieces_min=nb_pieces_min,
            lat=lat,
            lon=lon,
            rayon_km=rayon_km,
            tri=tri,
        )
        if not ids:
            return []
        rows = (
            db.query(models.Bien)
            .options(joinedload(models.Bien.photos))
            .filter(models.Bien.id.in_(ids))
            .all()
        )
        # Elasticsearch renvoie déjà les IDs triés (pertinence/prix/date) ;
        # PostgreSQL ne garantit pas l'ordre d'un IN(...), on le restaure ici.
        by_id = {str(r.id): r for r in rows}
        return [by_id[i] for i in ids if i in by_id]
    except es_client.ElasticsearchUnavailable:
        pass  # repli SQL ci-dessous

    query = (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos))
        .filter(models.Bien.statut == "disponible")
    )
    if ville:
        query = query.filter(models.Bien.ville.ilike(f"%{ville}%"))
    if type_bien:
        query = query.filter(models.Bien.type_bien == type_bien)
    if type_transaction:
        query = query.filter(models.Bien.type_transaction == type_transaction)
    if prix_max is not None:
        query = query.filter(models.Bien.prix <= prix_max)
    if prix_min is not None:
        query = query.filter(models.Bien.prix >= prix_min)
    if superficie_min is not None:
        query = query.filter(models.Bien.superficie >= superficie_min)
    if superficie_max is not None:
        query = query.filter(models.Bien.superficie <= superficie_max)
    if nb_pieces_min is not None:
        query = query.filter(models.Bien.nb_pieces >= nb_pieces_min)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Bien.titre.ilike(like)) | (models.Bien.description.ilike(like))
        )

    if tri == "prix_asc":
        query = query.order_by(models.Bien.prix.asc())
    elif tri == "prix_desc":
        query = query.order_by(models.Bien.prix.desc())
    else:
        query = query.order_by(models.Bien.date_publication.desc())

    return query.all()


@router.get("/me/annonces", response_model=List[schemas.BienOut])
def list_my_biens(
    type_transaction: str | None = None,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """Liste les biens du propriétaire connecté (avec photos), filtrable par
    type_transaction (location|vente)."""
    query = (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos))
        .filter(models.Bien.proprietaire_id == user.id)
    )
    if type_transaction:
        query = query.filter(models.Bien.type_transaction == type_transaction)
    return query.order_by(models.Bien.date_publication.desc()).all()


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

    # Étape 10 — Collecte des données : publie l'événement métier vers Kafka
    publish_event(
        BIEN_CREE,
        key=str(bien.id),
        payload={
            "id": bien.id,
            "proprietaire_id": bien.proprietaire_id,
            "titre": bien.titre,
            "type_bien": bien.type_bien,
            "ville": bien.ville,
            "prix": float(bien.prix),
            "statut": bien.statut,
            "date_publication": bien.date_publication,
        },
    )

    # Étape 18 — Recherche avancée : indexe le bien dans Elasticsearch
    es_client.index_bien(bien)

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

    # Étape 18 — Recherche avancée : réindexe le bien (titre/prix/statut/position... modifiés)
    es_client.index_bien(bien)

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

    # Supprimer les fichiers physiques dans MinIO
    for photo in bien.photos:
        object_name = storage.object_name_from_url(photo.url)
        if object_name:
            storage.delete_photo(object_name)

    db.delete(bien)
    db.commit()

    # Étape 18 — Recherche avancée : retire le bien de l'index Elasticsearch
    es_client.delete_bien(bien_id)

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
    Les fichiers sont envoyés vers le bucket MinIO ("smartrent-photos"),
    sous la clé "biens/<bien_id>/<uuid>.<ext>" ; l'URL publique MinIO
    résultante est enregistrée dans `photo_bien.url`.
    """
    bien = db.get(models.Bien, bien_id)
    if not bien or bien.proprietaire_id != user.id:
        raise HTTPException(status_code=404, detail="Bien non trouvé")

    saved_photos = []

    for idx, photo in enumerate(photos):
        ext = os.path.splitext(photo.filename or "")[1] or ".jpg"
        object_name = f"biens/{bien_id}/{uuid.uuid4().hex}{ext}"

        content = await photo.read()
        photo_url = storage.upload_photo(object_name, content, photo.content_type)

        ordre = int(ordres[idx]) if idx < len(ordres) else idx
        db_photo = models.PhotoBien(
            bien_id=bien_id,
            url=photo_url,
            ordre=ordre,
        )
        db.add(db_photo)
        saved_photos.append(db_photo)

    db.commit()
    for p in saved_photos:
        db.refresh(p)

    return saved_photos