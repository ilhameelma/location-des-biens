import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_role
from ..kafka_producer import publish_event
from ..kafka_topics import PAIEMENT_EFFECTUE
from ..notifications_service import notify

router = APIRouter(prefix="/paiements", tags=["paiements"])


@router.get("/me", response_model=list[schemas.PaiementOut])
def my_paiements(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    query = db.query(models.Paiement).join(models.Contrat, models.Contrat.id == models.Paiement.contrat_id)
    if current_user.role == "client":
        query = query.filter(models.Contrat.client_id == current_user.id)
    elif current_user.role == "proprietaire":
        query = query.filter(models.Contrat.proprietaire_id == current_user.id)
    return query.order_by(models.Paiement.date_paiement.desc()).all()


@router.post("", response_model=schemas.PaiementOut, status_code=status.HTTP_201_CREATED)
def create_paiement(
    payload: schemas.PaiementCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("client")),
):
    contrat = db.get(models.Contrat, payload.contrat_id)
    if not contrat or contrat.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    paiement = models.Paiement(**payload.model_dump(), statut="reussi")
    db.add(paiement)
    db.commit()
    db.refresh(paiement)

    bien = db.get(models.Bien, contrat.bien_id)
    bien_titre = bien.titre if bien else "votre bien"

    # Étape 10 — Collecte des données : publie l'événement métier vers Kafka
    publish_event(
        PAIEMENT_EFFECTUE,
        key=str(paiement.id),
        payload={
            "id": paiement.id,
            "contrat_id": paiement.contrat_id,
            "bien_id": contrat.bien_id,
            "ville": bien.ville if bien else None,
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
        contrat.proprietaire_id,
        "paiement",
        f"Paiement de {paiement.montant} MAD reçu pour « {bien_titre} ».",
        email_subject="SmartRent — Paiement reçu",
    )
    notify(
        db,
        current_user.id,
        "paiement",
        f"Votre paiement de {paiement.montant} MAD pour « {bien_titre} » a bien été enregistré.",
        email_subject="SmartRent — Confirmation de paiement",
    )

    return paiement
