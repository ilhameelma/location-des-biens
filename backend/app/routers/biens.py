"""Router FastAPI pour la gestion des biens immobiliers (propriétaire)."""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, storage, watermark
from ..database import get_db
from ..deps import ROLES_ANNONCEURS, get_current_user, require_role, get_optional_user
from ..kafka_producer import publish_event
from ..kafka_topics import BIEN_CREE
from .. import es_client
from .. import poi_client
from ..config import settings

router = APIRouter(prefix="/biens", tags=["biens"])

logger = logging.getLogger(__name__)


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
            .options(joinedload(models.Bien.photos), joinedload(models.Bien.proprietaire))
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
        .options(joinedload(models.Bien.photos), joinedload(models.Bien.proprietaire))
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
    user: models.Utilisateur = Depends(require_role(*ROLES_ANNONCEURS)),
):
    """Liste les biens de l'annonceur connecté — propriétaire, agence,
    promoteur ou courtier (avec photos), filtrable par type_transaction
    (location|vente)."""
    query = (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos), joinedload(models.Bien.proprietaire))
        .filter(models.Bien.proprietaire_id == user.id)
    )
    if type_transaction:
        query = query.filter(models.Bien.type_transaction == type_transaction)
    return query.order_by(models.Bien.date_publication.desc()).all()


@router.get("/proprietaire/{proprietaire_id}", response_model=List[schemas.BienOut])
def list_biens_by_proprietaire(
    proprietaire_id: uuid.UUID,
    type_transaction: str | None = None,
    db: Session = Depends(get_db),
    # Consultation publique (fiche profil d'un propriétaire, lien "Voir
    # toutes ses annonces" depuis une fiche bien) : pas de connexion requise.
    user: models.Utilisateur | None = Depends(get_optional_user),
):
    """
    Liste les biens d'un propriétaire donné.

    Même règle de visibilité que la recherche publique (`GET /biens`) : un
    visiteur, un client ou un autre propriétaire ne voient que les biens au
    statut "disponible". Le propriétaire consultant sa propre liste (ou un
    admin) voient en plus ses annonces en_attente/loué/vendu/suspendu.
    """
    proprietaire = db.get(models.Utilisateur, proprietaire_id)
    if not proprietaire or proprietaire.role not in ROLES_ANNONCEURS:
        raise HTTPException(status_code=404, detail="Propriétaire introuvable")

    query = (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos), joinedload(models.Bien.proprietaire))
        .filter(models.Bien.proprietaire_id == proprietaire_id)
    )

    est_proprietaire_ou_admin = user is not None and (
        user.id == proprietaire_id or user.role == "admin"
    )
    if not est_proprietaire_ou_admin:
        query = query.filter(models.Bien.statut == "disponible")
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
    bien = (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos), joinedload(models.Bien.proprietaire))
        .filter(models.Bien.id == bien_id)
        .first()
    )
    if not bien:
        raise HTTPException(status_code=404, detail="Bien non trouvé")
    return bien


@router.get("/{bien_id}/proximite", response_model=schemas.ProximiteOut)
def get_proximite_bien(
    bien_id: uuid.UUID,
    rayon_km: float = settings.poi_rayon_km_defaut,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(get_current_user),
):
    """
    Points d'intérêt à proximité du bien (hôtels, jardins/parcs, écoles,
    centres commerciaux) — voir app/poi_client.py.

    Sert en priorité les proximités déjà calculées et stockées avec
    l'annonce (`bien.proximite_data`, calculées en arrière-plan à la
    publication) plutôt que de resolliciter Overpass — c'est ce cache
    persistant qui rend l'affichage quasi instantané au lieu d'attendre
    plusieurs secondes à chaque ouverture de la fiche. Le calcul à la
    volée ne reste utilisé qu'en repli : rayon non standard demandé, ou
    calcul d'arrière-plan pas encore terminé (bien tout juste publié).

    Best-effort : si Overpass est indisponible ou lent, renvoie
    `disponible: false` avec des catégories vides plutôt qu'une erreur —
    la fiche du bien reste consultable normalement.
    """
    bien = db.get(models.Bien, bien_id)
    if not bien:
        raise HTTPException(status_code=404, detail="Bien non trouvé")
    if bien.latitude is None or bien.longitude is None:
        return schemas.ProximiteOut(disponible=False, categories={})

    rayon = max(0.2, min(rayon_km, 5.0))  # borne raisonnable : 200 m à 5 km
    rayon_defaut = abs(rayon - settings.poi_rayon_km_defaut) < 0.01

    if (
        rayon_defaut
        and bien.proximite_data
        and bien.proximite_calculee_le
        and (datetime.utcnow() - bien.proximite_calculee_le) < timedelta(days=settings.proximite_ttl_jours)
    ):
        return bien.proximite_data

    resultat = poi_client.get_proximite(bien.latitude, bien.longitude, rayon)

    # Persiste le résultat pour la prochaine consultation — couvre le cas
    # d'un bien publié avant cette fonctionnalité, ou dont le calcul
    # d'arrière-plan n'a pas encore abouti au moment de ce premier appel.
    if rayon_defaut and resultat.get("disponible"):
        bien.proximite_data = resultat
        bien.proximite_calculee_le = datetime.utcnow()
        db.commit()

    return resultat


@router.post("", response_model=schemas.BienOut, status_code=status.HTTP_201_CREATED)
def create_bien(
    payload: schemas.BienCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role(*ROLES_ANNONCEURS)),
):
    """
    Crée une nouvelle annonce (bien immobilier). Règles spécifiques selon le
    rôle de l'annonceur connecté :

    - proprietaire : comportement historique, aucune contrainte supplémentaire.
    - agence       : comme proprietaire, avec mandant_nom/téléphone optionnels
                     (l'agence peut publier pour son propre compte ou pour un tiers).
    - promoteur    : doit obligatoirement rattacher le lot à un projet qui lui
                     appartient déjà (POST /projets au préalable) ; les champs
                     mandant_* n'ont pas de sens ici et sont ignorés.
    - courtier     : mandant_nom/téléphone optionnels (le bien est généralement
                     publié "sous mandat" au nom d'un propriétaire tiers, mais le
                     courtier peut choisir de ne pas le préciser) ; projet_id
                     est réservé au promoteur.
    """
    data = payload.model_dump()

    if user.role == "promoteur":
        if not data.get("projet_id"):
            raise HTTPException(
                status_code=422,
                detail="Un promoteur doit publier un lot au sein d'un projet existant "
                "(champ projet_id requis) — créez d'abord le projet via POST /projets.",
            )
        projet = db.get(models.ProjetImmobilier, data["projet_id"])
        if not projet or projet.promoteur_id != user.id:
            raise HTTPException(status_code=404, detail="Projet introuvable")
        data["mandant_nom"] = None
        data["mandant_telephone"] = None
    elif user.role == "courtier":
        data["projet_id"] = None
    else:  # proprietaire, agence
        if data.get("projet_id"):
            raise HTTPException(
                status_code=422,
                detail="Seul un promoteur peut rattacher une annonce à un projet immobilier.",
            )

    bien = models.Bien(
        **data,
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

    # Complément étape 17 — proximités : calculées en arrière-plan (après
    # l'envoi de la réponse) et stockées avec l'annonce, pour que la fiche
    # du bien n'ait ensuite plus jamais à attendre Overpass. Ne bloque pas
    # la publication : si le bien n'a pas encore de position GPS, ce sera
    # fait au prochain PATCH qui en ajoute une (voir update_bien ci-dessous).
    if bien.latitude is not None and bien.longitude is not None:
        background_tasks.add_task(poi_client.calculer_et_stocker_proximite, str(bien.id))

    return bien


@router.patch("/{bien_id}", response_model=schemas.BienOut)
def update_bien(
    bien_id: uuid.UUID,
    payload: schemas.BienUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role(*ROLES_ANNONCEURS)),
):
    """Met à jour un bien existant."""
    bien = db.get(models.Bien, bien_id)
    if not bien or bien.proprietaire_id != user.id:
        raise HTTPException(status_code=404, detail="Bien non trouvé")

    champs_modifies = payload.model_dump(exclude_unset=True)
    position_modifiee = "latitude" in champs_modifies or "longitude" in champs_modifies

    for field, value in champs_modifies.items():
        setattr(bien, field, value)

    # La position a changé : les proximités stockées correspondent à
    # l'ancien emplacement et ne sont plus valables — on les invalide tout
    # de suite (plutôt que d'afficher les commodités du mauvais endroit
    # jusqu'au recalcul) et on relance le calcul en arrière-plan.
    if position_modifiee:
        bien.proximite_data = None
        bien.proximite_calculee_le = None

    db.commit()
    db.refresh(bien)

    # Étape 18 — Recherche avancée : réindexe le bien (titre/prix/statut/position... modifiés)
    es_client.index_bien(bien)

    if position_modifiee and bien.latitude is not None and bien.longitude is not None:
        background_tasks.add_task(poi_client.calculer_et_stocker_proximite, str(bien.id))

    return bien


@router.delete("/{bien_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bien(
    bien_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role(*ROLES_ANNONCEURS, "admin")),
):
    """Supprime un bien et ses photos.

    Un propriétaire ne peut supprimer que ses propres annonces. Un admin peut
    supprimer n'importe quelle annonce (ex. suite à l'alerte automatique
    déclenchée quand une annonce dépasse SEUIL_RECLAMATIONS_ANNONCE
    réclamations, voir routers/reclamations.py).
    """
    bien = db.get(models.Bien, bien_id)
    if not bien:
        raise HTTPException(status_code=404, detail="Bien non trouvé")
    if user.role != "admin" and bien.proprietaire_id != user.id:
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
    user: models.Utilisateur = Depends(require_role(*ROLES_ANNONCEURS)),
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
        content = await photo.read()
        content_type = photo.content_type

        # Filigrane "ImmoVision.ma" incrusté dans le fichier avant stockage
        # (comme Avito) — best-effort : si l'image est illisible/corrompue
        # ou si le filigrane est désactivé, on stocke l'original tel quel
        # plutôt que de faire échouer tout l'upload.
        try:
            content, content_type = watermark.apply_watermark(content)
        except watermark.WatermarkDisabled:
            pass
        except Exception as exc:
            logger.warning("Filigrane impossible pour '%s' : %s", photo.filename, exc)

        ext = ".png" if content_type == "image/png" else ".jpg"
        object_name = f"biens/{bien_id}/{uuid.uuid4().hex}{ext}"

        photo_url = storage.upload_photo(object_name, content, content_type)

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