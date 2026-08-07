import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..deps import ROLES_ANNONCEURS, require_role
from ..kafka_producer import publish_event
from ..kafka_topics import CONTRAT_SIGNE, PAIEMENT_EFFECTUE, RESERVATION_CREEE, RESERVATION_STATUT_MAJ
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


# ------------------------------------------------------------
# Réservation instantanée avec paiement immédiat (carte/virement) — le
# client réserve ET paie en une seule étape, avant toute validation du
# propriétaire (comme Booking). Complète create_reservation ci-dessus, qui
# reste utilisée telle quelle pour les offres d'achat (type_transaction
# "vente", voir le check ci-dessous) et reste la voie "demande classique".
# ------------------------------------------------------------
@router.post(
    "/instantanee",
    response_model=schemas.ReservationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation_instantanee(
    payload: schemas.ReservationInstantaneeCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    bien = db.get(models.Bien, payload.bien_id)
    if not bien or bien.statut != "disponible":
        raise HTTPException(status_code=400, detail="Ce bien n'est pas disponible à la réservation")
    if bien.type_transaction != "location":
        raise HTTPException(
            status_code=400,
            detail="Le paiement immédiat n'est disponible que pour les locations. "
            "Utilisez « Faire une offre » pour un bien à vendre.",
        )

    reservation = models.Reservation(
        bien_id=bien.id,
        client_id=current_user.id,
        date_debut=payload.date_debut,
        date_fin=payload.date_fin,
        statut="confirmee",
    )
    db.add(reservation)
    bien.statut = "loue"
    db.flush()  # attribue reservation.id sans clôturer la transaction

    maintenant = datetime.utcnow()
    contrat = models.Contrat(
        reservation_id=reservation.id,
        bien_id=bien.id,
        proprietaire_id=bien.proprietaire_id,
        client_id=current_user.id,
        date_signature=maintenant,
        date_debut=reservation.date_debut,
        date_fin=reservation.date_fin,
        montant_loyer=bien.prix,
        statut="actif",
        date_limite_annulation=maintenant + timedelta(hours=settings.delai_annulation_heures),
    )
    db.add(contrat)
    db.flush()

    paiement = models.Paiement(
        contrat_id=contrat.id,
        montant=bien.prix,
        methode=payload.methode_paiement,
        reference_transaction=payload.reference_transaction,
        statut="reussi",
    )
    db.add(paiement)

    db.commit()
    db.refresh(reservation)
    db.refresh(contrat)
    db.refresh(paiement)

    # Étape 10 — Collecte des données : les 4 événements métier concernés
    # sont publiés d'un coup (création + confirmation immédiate + contrat +
    # paiement), plutôt qu'étalés dans le temps comme dans le flux classique.
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
    publish_event(
        PAIEMENT_EFFECTUE,
        key=str(paiement.id),
        payload={
            "id": paiement.id,
            "contrat_id": paiement.contrat_id,
            "bien_id": contrat.bien_id,
            "ville": bien.ville,
            "proprietaire_id": contrat.proprietaire_id,
            "client_id": current_user.id,
            "montant": float(paiement.montant),
            "methode": paiement.methode,
            "statut": paiement.statut,
            "date_paiement": paiement.date_paiement,
        },
    )

    notify(
        db,
        bien.proprietaire_id,
        "reservation",
        f"Réservation payée et confirmée pour « {bien.titre} » par "
        f"{current_user.prenom} {current_user.nom} ({paiement.montant} MAD, "
        f"{ 'carte bancaire' if paiement.methode == 'carte_bancaire' else 'virement' }).",
        email_subject="SmartRent — Nouvelle réservation payée",
    )
    notify(
        db,
        current_user.id,
        "paiement",
        f"Paiement de {paiement.montant} MAD confirmé pour « {bien.titre} ». "
        f"Réservation confirmée. Vous pouvez encore l'annuler gratuitement pendant "
        f"{settings.delai_annulation_heures}h depuis « Mes réservations ».",
        email_subject="SmartRent — Réservation et paiement confirmés",
    )

    return reservation


@router.post("/{reservation_id}/annuler", response_model=schemas.ReservationOut)
def annuler_reservation_instantanee(
    reservation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    """Annulation gratuite (avec remboursement) d'une réservation payée
    instantanément, tant qu'on est dans la fenêtre de
    `settings.delai_annulation_heures` (24h par défaut) — voir
    Reservation.peut_annuler dans app/models.py."""
    reservation = (
        db.query(models.Reservation)
        .options(joinedload(models.Reservation.contrat).joinedload(models.Contrat.paiements))
        .filter(models.Reservation.id == reservation_id)
        .first()
    )
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation introuvable")
    if reservation.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    if not reservation.peut_annuler:
        raise HTTPException(
            status_code=400,
            detail="Cette réservation ne peut plus être annulée gratuitement "
            f"(fenêtre de {settings.delai_annulation_heures}h dépassée ou déjà traitée).",
        )

    contrat = reservation.contrat
    bien = db.get(models.Bien, reservation.bien_id)

    reservation.statut = "annulee"
    contrat.statut = "resilie"
    if bien and bien.statut == "loue":
        bien.statut = "disponible"

    for paiement in contrat.paiements:
        if paiement.statut == "reussi":
            paiement.statut = "rembourse"

    db.commit()
    db.refresh(reservation)

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

    titre = bien.titre if bien else "ce bien"
    notify(
        db,
        current_user.id,
        "paiement",
        f"Votre réservation pour « {titre} » a été annulée et votre paiement sera remboursé.",
        email_subject="SmartRent — Réservation annulée, remboursement en cours",
    )
    notify(
        db,
        contrat.proprietaire_id,
        "reservation",
        f"Le client a annulé sa réservation pour « {titre} » dans le délai gratuit de "
        f"{settings.delai_annulation_heures}h. Le bien est de nouveau disponible.",
        email_subject="SmartRent — Réservation annulée par le client",
    )

    return reservation


@router.get("/me", response_model=list[schemas.ReservationOut])
def my_reservations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    return (
        db.query(models.Reservation)
        # Charge le contrat (et ses paiements) en une seule requête
        # supplémentaire plutôt qu'au fil de l'eau (N+1) : nécessaire pour
        # que ReservationOut.contrat_id / paiement_effectue / etc. (voir
        # models.py, propriétés calculées) soient disponibles sans coût
        # significatif, même avec de nombreuses réservations.
        .options(joinedload(models.Reservation.contrat).joinedload(models.Contrat.paiements))
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
        # Processus de paiement : le client dispose de `delai_paiement_heures`
        # (24h par défaut) à partir de maintenant pour payer, sans quoi la
        # réservation sera annulée automatiquement (voir app/paiement_expiration.py).
        contrat = models.Contrat(
            reservation_id=reservation.id,
            bien_id=bien.id,
            proprietaire_id=bien.proprietaire_id,
            client_id=reservation.client_id,
            date_debut=reservation.date_debut,
            date_fin=reservation.date_fin,
            montant_loyer=bien.prix,
            statut="actif",
            date_limite_paiement=datetime.utcnow() + timedelta(hours=settings.delai_paiement_heures),
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
    message = f"Votre réservation pour « {bien.titre} » a été {libelle}."
    if payload.statut == "confirmee":
        message += (
            f" Vous disposez de {settings.delai_paiement_heures}h pour effectuer le paiement "
            "depuis votre espace « Mes réservations », sans quoi elle sera annulée automatiquement."
        )
    notify(
        db,
        reservation.client_id,
        "reservation",
        message,
        email_subject="SmartRent — Mise à jour de votre réservation",
    )

    return reservation
