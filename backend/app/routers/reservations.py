import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("", response_model=schemas.ReservationOut, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: schemas.ReservationCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    bien = db.get(models.Bien, payload.bien_id)
    if not bien or bien.statut != "disponible":
        raise HTTPException(status_code=400, detail="Ce bien n'est pas disponible à la réservation")

    reservation = models.Reservation(**payload.model_dump(), client_id=current_user.id)
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.get("/me", response_model=list[schemas.ReservationOut])
def my_reservations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    return (
        db.query(models.Reservation)
        .filter(models.Reservation.client_id == current_user.id)
        .order_by(models.Reservation.date_creation.desc())
        .all()
    )


@router.get("/recues", response_model=list[schemas.ReservationOut])
def received_reservations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    """Demandes reçues sur les biens du propriétaire connecté."""
    return (
        db.query(models.Reservation)
        .join(models.Bien, models.Bien.id == models.Reservation.bien_id)
        .filter(models.Bien.proprietaire_id == current_user.id)
        .order_by(models.Reservation.date_creation.desc())
        .all()
    )


@router.patch("/{reservation_id}/statut", response_model=schemas.ReservationOut)
def update_statut(
    reservation_id: uuid.UUID,
    payload: schemas.ReservationStatutUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("proprietaire")),
):
    reservation = db.get(models.Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation introuvable")

    bien = db.get(models.Bien, reservation.bien_id)
    if bien.proprietaire_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    reservation.statut = payload.statut

    if payload.statut == "confirmee":
        bien.statut = "loue"
        # Génère automatiquement le contrat associé (étape 4, en lien avec la table contrat)
        contrat = models.Contrat(
            reservation_id=reservation.id,
            bien_id=bien.id,
            proprietaire_id=bien.proprietaire_id,
            client_id=reservation.client_id,
            date_debut=reservation.date_debut,
            date_fin=reservation.date_fin,
            montant_loyer=bien.prix,
            statut="actif",
        )
        db.add(contrat)

    db.commit()
    db.refresh(reservation)
    return reservation
