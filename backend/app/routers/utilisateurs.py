import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import ROLES_ANNONCEURS, require_role

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


@router.get("/{utilisateur_id}/profil-public", response_model=schemas.ProprietairePublicOut)
def profil_public_proprietaire(utilisateur_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Fiche profil publique d'un propriétaire : nom, ancienneté sur la
    plateforme, nombre d'annonces actives, note moyenne — consultable par
    tout visiteur (ex. lien depuis une fiche bien ou l'espace admin), sans
    exposer de donnée sensible (email, téléphone).
    """
    user = db.get(models.Utilisateur, utilisateur_id)
    if not user or user.role not in ROLES_ANNONCEURS:
        raise HTTPException(status_code=404, detail="Propriétaire introuvable")

    nb_biens_actifs = (
        db.query(func.count(models.Bien.id))
        .filter(
            models.Bien.proprietaire_id == utilisateur_id,
            models.Bien.statut == "disponible",
        )
        .scalar()
    ) or 0

    note_moyenne, nb_avis = db.query(
        func.avg(models.Avis.note), func.count(models.Avis.id)
    ).filter(models.Avis.proprietaire_id == utilisateur_id).one()

    return schemas.ProprietairePublicOut(
        id=user.id,
        nom=user.nom,
        prenom=user.prenom,
        role=user.role,
        raison_sociale=user.raison_sociale,
        date_creation=user.date_creation,
        nb_biens_actifs=nb_biens_actifs,
        note_moyenne=round(float(note_moyenne), 1) if note_moyenne is not None else None,
        nb_avis=nb_avis or 0,
    )


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


@router.delete("/{utilisateur_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_utilisateur(
    utilisateur_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    """
    Suppression définitive d'un compte par un admin.

    - Un admin ne peut pas se supprimer lui-même (évite de se retrouver sans
      accès admin par erreur).
    - Grâce à `ON DELETE CASCADE` sur toutes les FK vers `utilisateur` dans le
      schéma SQL (biens, réservations, avis, réclamations, messages,
      notifications, favoris...), la suppression entraîne automatiquement
      celle de toutes les données liées à ce compte.
    """
    if utilisateur_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte",
        )
    user = db.get(models.Utilisateur, utilisateur_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()