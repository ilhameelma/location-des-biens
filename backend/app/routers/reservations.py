import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import ROLES_ANNONCEURS, require_role
from ..kafka_producer import publish_event
from ..kafka_topics import CONTRAT_SIGNE, RESERVATION_CREEE, RESERVATION_STATUT_MAJ
from ..notifications_service import notify

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

    # Étape 10 — Collecte des données : publie l'événement métier vers Kafka
    publish_event(
        RESERVATION_CREEE,
        key=str(reservation.id),
        payload={
            "id": reservation.id,
            "bien_id": reservation.bien_id,
            "client_id": reservation.client_id,
            "proprietaire_id": bien.proprietaire_id,
            "ville": bien.ville,
            "date_debut": reservation.date_debut,
            "date_fin": reservation.date_fin,
            "statut": reservation.statut,
            "date_creation": reservation.date_creation,
        },
    )

    notify(
        db,
        bien.proprietaire_id,
        "reservation",
        f"Nouvelle demande de réservation pour « {bien.titre} » de la part de "
        f"{current_user.prenom} {current_user.nom}.",
        email_subject="SmartRent — Nouvelle demande de réservation",
    )

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
    current_user: models.Utilisateur = Depends(require_role(*ROLES_ANNONCEURS)),
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
    current_user: models.Utilisateur = Depends(require_role(*ROLES_ANNONCEURS)),
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

    # Étape 10 — Collecte des données : publie les événements métier vers Kafka
    publish_event(
        RESERVATION_STATUT_MAJ,
        key=str(reservation.id),
        payload={
            "id": reservation.id,
            "bien_id": reservation.bien_id,
            "client_id": reservation.client_id,
            "statut": reservation.statut,
        },
    )

    if payload.statut == "confirmee":
        db.refresh(contrat)
        publish_event(
            CONTRAT_SIGNE,
            key=str(contrat.id),
            payload={
                "id": contrat.id,
                "bien_id": contrat.bien_id,
                "ville": bien.ville,
                "proprietaire_id": contrat.proprietaire_id,
                "client_id": contrat.client_id,
                "montant_loyer": float(contrat.montant_loyer),
                "date_debut": contrat.date_debut,
                "date_fin": contrat.date_fin,
                "statut": contrat.statut,
                "date_creation": contrat.date_creation,
            },
        )

    libelles = {
        "confirmee": "confirmée",
        "refusee": "refusée",
        "annulee": "annulée",
    }
    libelle = libelles.get(payload.statut, payload.statut)
    notify(
        db,
        reservation.client_id,
        "reservation",
        f"Votre réservation pour « {bien.titre} » a été {libelle}.",
        email_subject="SmartRent — Mise à jour de votre réservation",
    )

    return reservation
