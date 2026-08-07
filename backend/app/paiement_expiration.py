"""
Processus de paiement après confirmation d'une réservation.

Quand une réservation est confirmée (voir routers/reservations.py), un
contrat est généré automatiquement avec une date limite de paiement
(`Contrat.date_limite_paiement` = confirmation + `settings.delai_paiement_heures`,
24h par défaut). Ce module vérifie périodiquement, en arrière-plan, les
contrats dont ce délai est dépassé sans paiement `reussi` associé, et
annule automatiquement la réservation correspondante.

Même philosophie "best-effort" que kafka_producer.py / es_client.py /
poi_client.py : une erreur ici ne doit jamais faire planter le back-end,
au pire un contrat impayé sera traité au passage suivant.

Approche volontairement simple (boucle asyncio lancée au démarrage du
process FastAPI, voir app/main.py) plutôt qu'une nouvelle dépendance
(APScheduler) ou un DAG Airflow séparé : le besoin est une simple
vérification périodique légère, cohérente avec le reste du projet où
Airflow est réservé au pipeline data (Kafka → Spark → Data Warehouse).
"""
import asyncio
import logging
from datetime import datetime

from . import models
from .config import settings
from .database import SessionLocal
from .kafka_producer import publish_event
from .kafka_topics import RESERVATION_STATUT_MAJ
from .notifications_service import notify

logger = logging.getLogger(__name__)


def annuler_reservations_non_payees() -> int:
    """
    Parcourt les contrats actifs dont la date limite de paiement est
    dépassée et sans paiement réussi associé : résilie le contrat, annule
    la réservation liée, remet le bien disponible, notifie client et
    propriétaire. Renvoie le nombre de réservations annulées.

    Ouvre sa propre session DB (conçue pour tourner hors d'une requête
    HTTP, voir boucle_verification_paiements ci-dessous).
    """
    db = SessionLocal()
    nb_annulees = 0
    try:
        maintenant = datetime.utcnow()
        contrats_expires = (
            db.query(models.Contrat)
            .filter(
                models.Contrat.statut == "actif",
                models.Contrat.date_limite_paiement.isnot(None),
                models.Contrat.date_limite_paiement < maintenant,
            )
            .all()
        )

        for contrat in contrats_expires:
            paiement_reussi = (
                db.query(models.Paiement)
                .filter(models.Paiement.contrat_id == contrat.id, models.Paiement.statut == "reussi")
                .first()
            )
            if paiement_reussi:
                # Payé entre-temps (petite fenêtre entre le paiement et le
                # prochain passage de cette vérification) : rien à faire.
                continue

            bien = db.get(models.Bien, contrat.bien_id)
            reservation = (
                db.get(models.Reservation, contrat.reservation_id) if contrat.reservation_id else None
            )

            contrat.statut = "resilie"
            if reservation:
                reservation.statut = "annulee"
            if bien and bien.statut == "loue":
                bien.statut = "disponible"

            db.commit()
            nb_annulees += 1

            titre = bien.titre if bien else "ce bien"
            notify(
                db,
                contrat.client_id,
                "reservation",
                f"Votre réservation pour « {titre} » a été annulée automatiquement : "
                f"le paiement n'a pas été effectué dans le délai de "
                f"{settings.delai_paiement_heures}h après confirmation.",
                email_subject="SmartRent — Réservation annulée (paiement non effectué)",
            )
            notify(
                db,
                contrat.proprietaire_id,
                "reservation",
                f"La réservation de « {titre} » a été annulée automatiquement : "
                "le client n'a pas effectué le paiement dans le délai imparti. "
                "Le bien est de nouveau disponible à la réservation.",
                email_subject="SmartRent — Réservation annulée (paiement non effectué)",
            )

            if reservation:
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

            logger.info(
                "Réservation %s annulée automatiquement (paiement non effectué avant %s)",
                reservation.id if reservation else contrat.id,
                contrat.date_limite_paiement,
            )
    except Exception:
        logger.exception("Échec de la vérification périodique des paiements en attente")
        db.rollback()
    finally:
        db.close()

    return nb_annulees


async def boucle_verification_paiements() -> None:
    """
    Tâche d'arrière-plan lancée une fois au démarrage du back-end (voir
    `@app.on_event("startup")` dans app/main.py) : vérifie toutes les
    `settings.verification_paiements_intervalle_secondes` (15 min par
    défaut) l'existence de contrats impayés dont le délai est dépassé, et
    les annule. Tourne indéfiniment tant que le process est actif.

    Le calcul (synchrone, requêtes SQL) est exécuté dans un thread séparé
    (`run_in_executor`) pour ne jamais bloquer la boucle asyncio
    principale — celle qui sert aussi les WebSockets (messagerie,
    notifications, voir ws_manager.py).
    """
    while True:
        try:
            nb = await asyncio.get_running_loop().run_in_executor(None, annuler_reservations_non_payees)
            if nb:
                logger.info(
                    "%d réservation(s) annulée(s) automatiquement pour paiement non effectué", nb
                )
        except Exception:
            logger.exception("Erreur dans la boucle de vérification des paiements")
        await asyncio.sleep(settings.verification_paiements_intervalle_secondes)
