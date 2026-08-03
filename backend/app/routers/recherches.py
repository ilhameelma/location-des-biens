"""Router FastAPI pour l'historique de recherche côté client.

Chaque recherche significative effectuée sur la page de recherche est
enregistrée (critères + libellé lisible calculé côté front) pour permettre
au client de relancer une recherche récente en un clic — même logique
d'enregistrement "best-effort" que les favoris : un échec d'enregistrement
de l'historique ne doit jamais empêcher l'affichage des résultats de
recherche eux-mêmes (géré côté front, voir SearchPage.tsx).
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/recherches", tags=["recherches"])

# Nombre de recherches conservées par client — au-delà, les plus anciennes
# sont automatiquement supprimées à chaque nouvel ajout (historique borné,
# pas de purge manuelle à prévoir).
MAX_HISTORIQUE_PAR_CLIENT = 15


@router.post("", response_model=schemas.RechercheOut, status_code=201)
def add_recherche(
    payload: schemas.RechercheCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    # Dédoublonnage : si la recherche la plus récente du client a exactement
    # les mêmes critères, on ne réinsère pas une ligne quasi identique (cas
    # fréquent : l'utilisateur retouche un filtre puis revient en arrière).
    derniere = (
        db.query(models.RechercheHistorique)
        .filter(models.RechercheHistorique.client_id == current_user.id)
        .order_by(models.RechercheHistorique.date_recherche.desc())
        .first()
    )
    if derniere and derniere.criteres == payload.criteres:
        return derniere

    recherche = models.RechercheHistorique(
        client_id=current_user.id,
        label=payload.label,
        criteres=payload.criteres,
    )
    db.add(recherche)
    db.flush()

    # Purge des entrées excédentaires au-delà de MAX_HISTORIQUE_PAR_CLIENT
    ids_a_garder = (
        db.query(models.RechercheHistorique.id)
        .filter(models.RechercheHistorique.client_id == current_user.id)
        .order_by(models.RechercheHistorique.date_recherche.desc())
        .limit(MAX_HISTORIQUE_PAR_CLIENT)
        .subquery()
    )
    (
        db.query(models.RechercheHistorique)
        .filter(
            models.RechercheHistorique.client_id == current_user.id,
            models.RechercheHistorique.id.notin_(ids_a_garder.select()),
        )
        .delete(synchronize_session=False)
    )

    db.commit()
    db.refresh(recherche)
    return recherche


@router.get("/me", response_model=list[schemas.RechercheOut])
def my_recherches(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    return (
        db.query(models.RechercheHistorique)
        .filter(models.RechercheHistorique.client_id == current_user.id)
        .order_by(models.RechercheHistorique.date_recherche.desc())
        .limit(MAX_HISTORIQUE_PAR_CLIENT)
        .all()
    )


@router.delete("/me", status_code=204)
def clear_recherches(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    db.query(models.RechercheHistorique).filter(
        models.RechercheHistorique.client_id == current_user.id
    ).delete()
    db.commit()
    return None


@router.delete("/{recherche_id}", status_code=204)
def delete_recherche(
    recherche_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    recherche = (
        db.query(models.RechercheHistorique)
        .filter(
            models.RechercheHistorique.id == recherche_id,
            models.RechercheHistorique.client_id == current_user.id,
        )
        .first()
    )
    if recherche:
        db.delete(recherche)
        db.commit()
    return None
