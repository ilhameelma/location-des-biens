"""
Router FastAPI pour le blog ImmoVision (anciennement "actualités").

Un administrateur ou une agence publie des articles (titre, contenu riche,
image optionnelle, catégorie) ; ils sont affichés sur la page d'accueil
publique (aperçu) et sur /blog (liste complète + fiche par slug), visibles
par tout visiteur, connecté ou non — comme le catalogue d'annonces (voir
`GET /biens`, rendu public via `get_optional_user`).

Propriété des articles :
- Un admin peut créer, modifier, dépublier ou supprimer N'IMPORTE QUEL
  article (rôle de modération).
- Une agence ne peut créer, modifier, dépublier ou supprimer QUE SES
  PROPRES articles.
- Le contenu riche (HTML produit par l'éditeur front) est systématiquement
  sanitizé via nh3 avant d'être stocké — jamais de HTML brut non filtré en
  base, quelle que soit la confiance accordée à l'auteur.
"""
import logging
import re
import unicodedata
import uuid
from typing import List, Optional

import nh3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import models, schemas, storage
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/actualites", tags=["actualites"])

logger = logging.getLogger(__name__)

# ============================================================
# Sanitization du contenu riche (éditeur CMS côté front)
# ============================================================
# Liste blanche volontairement restreinte à ce que l'éditeur riche produit
# réellement (titres, listes, liens, images, citations) — tout le reste
# (script, iframe, style inline, on*...) est retiré silencieusement par nh3.
_TAGS_AUTORISES = {
    "p", "br", "strong", "em", "u", "s",
    "h2", "h3", "h4",
    "ul", "ol", "li",
    "a", "img", "blockquote",
}
_ATTRIBUTS_AUTORISES = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title"},
}


def _sanitize_html(contenu: str) -> str:
    return nh3.clean(
        contenu,
        tags=_TAGS_AUTORISES,
        attributes=_ATTRIBUTS_AUTORISES,
        link_rel="nofollow noopener noreferrer",
    )


# ============================================================
# Génération du slug (URL SEO, ex. /blog/mon-nouvel-article)
# ============================================================
def _slugify(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    texte = re.sub(r"[^a-zA-Z0-9]+", "-", texte).strip("-").lower()
    return texte or "article"


def _slug_unique(db: Session, base_slug: str, exclure_id: Optional[uuid.UUID] = None) -> str:
    slug = base_slug
    suffixe = 1
    while True:
        query = db.query(models.Actualite).filter(models.Actualite.slug == slug)
        if exclure_id is not None:
            query = query.filter(models.Actualite.id != exclure_id)
        if query.first() is None:
            return slug
        suffixe += 1
        slug = f"{base_slug}-{suffixe}"


def _assurer_slug(db: Session, actualite: models.Actualite) -> None:
    """Rétro-remplit le slug d'un article créé avant cette évolution (slug
    NULL en base) — appelé au moment de la lecture, jamais de script de
    migration séparé nécessaire."""
    if actualite.slug:
        return
    base = _slugify(actualite.titre)
    actualite.slug = _slug_unique(db, base, exclure_id=actualite.id)
    db.commit()
    db.refresh(actualite)


# ============================================================
# Contrôle de propriété
# ============================================================
def _verifier_droit_edition(actualite: models.Actualite, current_user: models.Utilisateur) -> None:
    """Un admin peut tout modifier (modération) ; une agence uniquement ses
    propres articles."""
    if current_user.role == "admin":
        return
    if actualite.auteur_id == current_user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Vous ne pouvez modifier que vos propres articles",
    )


def _nom_affichage(auteur: Optional[models.Utilisateur]) -> str:
    """Nom affiché publiquement : la raison sociale de l'agence pour un
    article publié par une agence (visibilité/crédibilité voulue pour
    elle), "ImmoVision" pour un article admin ou en repli."""
    if auteur and auteur.role == "agence" and auteur.raison_sociale:
        return auteur.raison_sociale
    return "ImmoVision"


def _enrich(db: Session, actualites: list[models.Actualite]) -> list[schemas.ActualiteOut]:
    """Complète chaque article avec le nom de l'auteur et rétro-remplit le
    slug si absent (une seule requête groupée pour les auteurs, pas de
    N+1)."""
    if not actualites:
        return []

    for a in actualites:
        _assurer_slug(db, a)

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
                slug=a.slug,
                extrait=a.extrait,
                categorie=a.categorie,
                contenu_html=a.contenu_html,
                image_url=a.image_url,
                publie=a.publie,
                date_creation=a.date_creation,
                date_maj=a.date_maj,
                auteur_nom=auteur.nom if auteur else None,
                auteur_prenom=auteur.prenom if auteur else None,
                auteur_role=auteur.role if auteur else None,
                auteur_affichage=_nom_affichage(auteur),
            )
        )
    return result


# ============================================================
# Consultation publique — landing page + page /blog
# ============================================================

@router.get("", response_model=List[schemas.ActualiteOut])
def list_actualites_publiques(
    limite: Optional[int] = None,
    categorie: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Articles publiés, les plus récents d'abord — utilisés par la landing
    page (aperçu, `limite`) et la page /blog (liste complète, `categorie`
    en filtre optionnel). Pas d'authentification requise."""
    query = (
        db.query(models.Actualite)
        .filter(models.Actualite.publie.is_(True))
        .order_by(models.Actualite.date_creation.desc())
    )
    if categorie is not None:
        query = query.filter(models.Actualite.categorie == categorie)
    if limite is not None:
        query = query.limit(limite)
    return _enrich(db, query.all())


@router.get("/slug/{slug}", response_model=schemas.ActualiteOut)
def get_actualite_par_slug(slug: str, db: Session = Depends(get_db)):
    """Fiche article publique (/blog/<slug>) — seuls les articles publiés
    sont accessibles par ce chemin."""
    actualite = (
        db.query(models.Actualite)
        .filter(models.Actualite.slug == slug, models.Actualite.publie.is_(True))
        .first()
    )
    if not actualite:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return _enrich(db, [actualite])[0]


# ============================================================
# Gestion admin + agence
# ============================================================

@router.get("/admin", response_model=List[schemas.ActualiteOut])
def list_actualites_admin(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin", "agence")),
):
    """Articles (publiés ou non) — page de gestion. Un admin voit tout ;
    une agence ne voit que ses propres articles."""
    query = db.query(models.Actualite).order_by(models.Actualite.date_creation.desc())
    if current_user.role != "admin":
        query = query.filter(models.Actualite.auteur_id == current_user.id)
    return _enrich(db, query.all())


@router.post("", response_model=schemas.ActualiteOut, status_code=status.HTTP_201_CREATED)
def create_actualite(
    payload: schemas.ActualiteCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin", "agence")),
):
    slug = _slug_unique(db, _slugify(payload.titre))
    actualite = models.Actualite(
        titre=payload.titre,
        contenu_html=_sanitize_html(payload.contenu_html),
        extrait=payload.extrait,
        categorie=payload.categorie,
        slug=slug,
        auteur_id=current_user.id,
    )
    db.add(actualite)
    db.commit()
    db.refresh(actualite)
    return _enrich(db, [actualite])[0]


@router.patch("/{actualite_id}", response_model=schemas.ActualiteOut)
def update_actualite(
    actualite_id: uuid.UUID,
    payload: schemas.ActualiteUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin", "agence")),
):
    actualite = db.get(models.Actualite, actualite_id)
    if not actualite:
        raise HTTPException(status_code=404, detail="Article introuvable")
    _verifier_droit_edition(actualite, current_user)

    donnees = payload.model_dump(exclude_unset=True)
    if "contenu_html" in donnees:
        donnees["contenu_html"] = _sanitize_html(donnees["contenu_html"])
    # Le slug n'est jamais recalculé automatiquement lors d'une modification
    # de titre : il reste stable une fois publié (URL déjà éventuellement
    # partagée/indexée par les moteurs de recherche).
    for field, value in donnees.items():
        setattr(actualite, field, value)

    db.commit()
    db.refresh(actualite)
    return _enrich(db, [actualite])[0]


@router.post("/{actualite_id}/image", response_model=schemas.ActualiteOut)
async def upload_image(
    actualite_id: uuid.UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin", "agence")),
):
    """Upload (ou remplace) l'image d'illustration d'un article, vers le
    même bucket MinIO que les photos de biens, sous un préfixe dédié
    `actualites/<actualite_id>/`."""
    actualite = db.get(models.Actualite, actualite_id)
    if not actualite:
        raise HTTPException(status_code=404, detail="Article introuvable")
    _verifier_droit_edition(actualite, current_user)

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
    current_user: models.Utilisateur = Depends(require_role("admin", "agence")),
):
    actualite = db.get(models.Actualite, actualite_id)
    if not actualite:
        raise HTTPException(status_code=404, detail="Article introuvable")
    _verifier_droit_edition(actualite, current_user)
    db.delete(actualite)
    db.commit()
    return None
