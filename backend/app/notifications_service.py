"""
Étape 9 — Notifications (Firebase Cloud Messaging, SMTP)

Point d'entrée unique utilisé par les autres routers (réservations,
paiements...) pour notifier un utilisateur suite à un événement métier.
Chaque appel à `notify()` :
  1. enregistre la notification en base (persistant, visible dans /notifications/me) ;
  2. la pousse en temps réel via WebSocket si l'utilisateur est connecté
     (voir app/ws_manager.py — même mécanisme que la messagerie de l'étape 8) ;
  3. envoie un email best-effort via SMTP si configuré (voir app/config.py) —
     un échec d'envoi d'email ne fait jamais échouer l'action métier déclenchante.

Firebase Cloud Messaging (push mobile/navigateur) : voir send_push() plus bas —
documenté comme perspective d'évolution, au même titre que Kubernetes (étape 21)
dans le cahier des charges, car il nécessite un flux d'enregistrement de token
d'appareil qui n'existe pas dans ce projet web.
"""
import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from . import models
from .config import settings
from .ws_manager import notif_manager, get_main_loop

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    """Envoi SMTP best-effort. No-op silencieux (avec warning) si non configuré."""
    if not settings.smtp_host:
        logger.info("SMTP non configuré — email '%s' non envoyé à %s.", subject, to_email)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except Exception as exc:
        # On ne bloque jamais une action métier (créer une réservation, un
        # paiement...) à cause d'un email qui échoue.
        logger.warning("Échec d'envoi de l'email '%s' à %s : %s", subject, to_email, exc)


def send_push(device_token: str, title: str, body: str) -> None:
    """
    Stub Firebase Cloud Messaging. Nécessiterait :
      - côté client : enregistrement d'un token d'appareil (app mobile ou
        service worker web + clés VAPID) via Firebase SDK ;
      - une table associant utilisateur_id <-> device_token ;
      - un appel à l'API FCM HTTP v1 avec `settings.fcm_server_key`.
    Aucun de ces éléments n'existe encore dans ce projet -> perspective
    d'évolution, comme documenté dans le cahier des charges pour Kubernetes.
    """
    if not settings.fcm_server_key:
        logger.info("FCM non configuré — push '%s' non envoyé.", title)
        return
    logger.info("send_push() est un stub : aucun appel FCM réel n'est effectué.")


def notify(
    db: Session,
    utilisateur_id,
    type_notification: str,
    contenu: str,
    email_subject: str | None = None,
) -> models.Notification:
    """
    Crée une notification pour `utilisateur_id`, la pousse en temps réel si
    l'utilisateur est connecté, et envoie un email si l'utilisateur n'a
    actuellement aucune connexion active à l'application (donc probablement
    hors ligne) et que le SMTP est configuré.
    """
    notification = models.Notification(
        utilisateur_id=utilisateur_id,
        type_notification=type_notification,
        contenu=contenu,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Poussée temps réel (fire-and-forget). `notify()` est appelée depuis des
    # endpoints FastAPI synchrones qui tournent dans un threadpool : on ne
    # peut donc pas simplement `await`/`create_task` ici. On planifie la
    # diffusion sur la boucle asyncio principale, capturée au démarrage
    # (voir app/main.py et set_main_loop()), avec run_coroutine_threadsafe,
    # qui est justement conçu pour être appelé depuis un autre thread.
    import asyncio

    payload = {
        "type": "notification",
        "id": str(notification.id),
        "type_notification": notification.type_notification,
        "contenu": notification.contenu,
        "lu": notification.lu,
        "date_creation": notification.date_creation.isoformat(),
    }
    loop = get_main_loop()
    if loop is not None:
        asyncio.run_coroutine_threadsafe(notif_manager.broadcast(utilisateur_id, payload), loop)

    # Email seulement si l'utilisateur n'a aucun onglet ouvert sur l'app.
    if notif_manager.online_count(utilisateur_id) == 0:
        user = db.get(models.Utilisateur, utilisateur_id)
        if user and user.email:
            send_email(user.email, email_subject or "SmartRent — Nouvelle notification", contenu)

    return notification
