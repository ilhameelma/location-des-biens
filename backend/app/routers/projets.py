"""Router FastAPI pour les projets immobiliers (rôle `promoteur`).

Un promoteur ne publie jamais un bien isolément : il crée d'abord un projet
(ex. "Résidence Al Manar", Tanger), puis publie ses lots (des `Bien` normaux,
avec `projet_id` pointant vers ce projet) via le endpoint habituel
`POST /biens` — voir la validation dans routers/biens.py::create_bien.

Ce router ne gère donc que le cycle de vie du projet lui-même ; les lots
restent gérés depuis l'espace "Mes biens" (comme pour les autres rôles
annonceurs), avec en plus un endpoint public `GET /projets/{id}/lots` pour
afficher tous les lots d'un projet sur sa fiche.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/projets", tags=["projets"])


def _enrich(db: Session, projets: list[models.ProjetImmobilier]) -> list[schemas.ProjetOut]:
    """Complète chaque projet avec le nombre de lots, la fourchette de prix
    et l'identité du promoteur — deux requêtes groupées, pas une par projet."""
    if not projets:
        return []

    promoteur_ids = {p.promoteur_id for p in projets}
    promoteurs = {
        u.id: u
        for u in db.query(models.Utilisateur).filter(models.Utilisateur.id.in_(promoteur_ids))
    }

    projet_ids = [p.id for p in projets]
    lots = (
        db.query(models.Bien).filter(models.Bien.projet_id.in_(projet_ids)).all()
        if projet_ids
        else []
    )
    lots_par_projet: dict[uuid.UUID, list[models.Bien]] = {}
    for lot in lots:
        lots_par_projet.setdefault(lot.projet_id, []).append(lot)

    result = []
    for p in projets:
        mes_lots = lots_par_projet.get(p.id, [])
        prix = [float(l.prix) for l in mes_lots]
        promoteur = promoteurs.get(p.promoteur_id)
        result.append(
            schemas.ProjetOut(
                id=p.id,
                promoteur_id=p.promoteur_id,
                nom=p.nom,
                description=p.description,
                type_bien=p.type_bien,
                ville=p.ville,
                adresse=p.adresse,
                latitude=p.latitude,
                longitude=p.longitude,
                statut=p.statut,
                date_livraison_prevue=p.date_livraison_prevue,
                date_creation=p.date_creation,
                nb_lots=len(mes_lots),
                nb_lots_disponibles=len([l for l in mes_lots if l.statut == "disponible"]),
                prix_min=min(prix) if prix else None,
                prix_max=max(prix) if prix else None,
                promoteur_nom=promoteur.nom if promoteur else None,
                promoteur_prenom=promoteur.prenom if promoteur else None,
                promoteur_raison_sociale=promoteur.raison_sociale if promoteur else None,
            )
        )
    return result


@router.get("", response_model=list[schemas.ProjetOut])
def list_projets(ville: str | None = None, db: Session = Depends(get_db)):
    """Liste publique des projets immobiliers (promotion neuve) — consultable
    par tout visiteur, comme la recherche de biens classique."""
    query = db.query(models.ProjetImmobilier)
    if ville:
        query = query.filter(models.ProjetImmobilier.ville.ilike(f"%{ville}%"))
    projets = query.order_by(models.ProjetImmobilier.date_creation.desc()).all()
    return _enrich(db, projets)


@router.get("/me", response_model=list[schemas.ProjetOut])
def my_projets(
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("promoteur")),
):
    """Page « Mes projets » (promoteur connecté)."""
    projets = (
        db.query(models.ProjetImmobilier)
        .filter(models.ProjetImmobilier.promoteur_id == user.id)
        .order_by(models.ProjetImmobilier.date_creation.desc())
        .all()
    )
    return _enrich(db, projets)


@router.get("/{projet_id}", response_model=schemas.ProjetOut)
def get_projet(projet_id: uuid.UUID, db: Session = Depends(get_db)):
    projet = db.get(models.ProjetImmobilier, projet_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return _enrich(db, [projet])[0]


@router.get("/{projet_id}/lots", response_model=list[schemas.BienOut])
def get_lots(projet_id: uuid.UUID, db: Session = Depends(get_db)):
    """Tous les lots (biens) rattachés à ce projet — fiche projet publique."""
    projet = db.get(models.ProjetImmobilier, projet_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return (
        db.query(models.Bien)
        .options(joinedload(models.Bien.photos), joinedload(models.Bien.proprietaire))
        .filter(models.Bien.projet_id == projet_id)
        .order_by(models.Bien.date_publication.desc())
        .all()
    )


@router.post("", response_model=schemas.ProjetOut, status_code=status.HTTP_201_CREATED)
def create_projet(
    payload: schemas.ProjetCreate,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("promoteur")),
):
    projet = models.ProjetImmobilier(**payload.model_dump(), promoteur_id=user.id)
    db.add(projet)
    db.commit()
    db.refresh(projet)
    return _enrich(db, [projet])[0]


@router.patch("/{projet_id}", response_model=schemas.ProjetOut)
def update_projet(
    projet_id: uuid.UUID,
    payload: schemas.ProjetUpdate,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("promoteur")),
):
    projet = db.get(models.ProjetImmobilier, projet_id)
    if not projet or projet.promoteur_id != user.id:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(projet, field, value)

    db.commit()
    db.refresh(projet)
    return _enrich(db, [projet])[0]


@router.delete("/{projet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_projet(
    projet_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.Utilisateur = Depends(require_role("promoteur")),
):
    """Supprime un projet.

    Bloqué (409) si des lots y sont encore rattachés — le promoteur doit
    d'abord les supprimer individuellement depuis "Mes biens", pour éviter
    la suppression accidentelle en cascade d'annonces déjà publiées
    (potentiellement déjà réservées/vendues). Le FK `bien.projet_id` est en
    `ON DELETE SET NULL` côté base pour rester sûr même en cas de suppression
    directe en SQL.
    """
    projet = db.get(models.ProjetImmobilier, projet_id)
    if not projet or projet.promoteur_id != user.id:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    nb_lots = db.query(models.Bien).filter(models.Bien.projet_id == projet_id).count()
    if nb_lots > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Impossible de supprimer : {nb_lots} lot(s) encore rattaché(s) à ce projet.",
        )

    db.delete(projet)
    db.commit()
    return None
