"""Router FastAPI — formulaire de contact public (landing page).

Contrairement à `notifications_service.send_email()` (best-effort, échoue
silencieusement si SMTP n'est pas configuré ou indisponible — comportement
volontaire pour ne jamais bloquer une action métier interne), ce endpoint
est directement utilisateur : le visiteur doit savoir si son message est
réellement parti. On lève donc une erreur explicite en cas d'échec plutôt
que d'avaler l'exception.
"""
import logging
import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, HTTPException, status

from .. import schemas
from ..config import settings

router = APIRouter(prefix="/contact", tags=["contact"])

logger = logging.getLogger(__name__)


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def envoyer_message_contact(payload: schemas.ContactCreate):
    """
    Envoie le message du formulaire "Contact" de la landing page directement
    par email à `settings.contact_email`, via le même SMTP que le reste de
    la plateforme (`settings.smtp_*`).

    Remplace l'ancien comportement `mailto:` côté front (qui ouvrait le
    client mail local du visiteur au lieu d'envoyer réellement le message).
    """
    if not settings.smtp_host:
        # Configuration manquante côté serveur — on le dit clairement au
        # lieu de laisser le front-end croire que le message est parti.
        logger.warning(
            "Formulaire de contact : SMTP non configuré, message de %s non envoyé.",
            payload.email,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "L'envoi d'email n'est pas configuré côté serveur pour le moment. "
                "Merci de nous écrire directement à "
                f"{settings.contact_email}."
            ),
        )

    msg = EmailMessage()
    msg["Subject"] = f"[ImmoVision — Contact] Message de {payload.nom}"
    msg["From"] = settings.smtp_from
    msg["To"] = settings.contact_email
    # Permet de répondre directement au visiteur depuis la boîte mail
    # réceptrice, sans devoir recopier son adresse à la main.
    msg["Reply-To"] = payload.email
    msg.set_content(
        f"Nouveau message reçu depuis le formulaire de contact d'ImmoVision.\n\n"
        f"Nom : {payload.nom}\n"
        f"Email : {payload.email}\n\n"
        f"Message :\n{payload.message}\n"
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
    except Exception as exc:
        logger.warning("Échec d'envoi du message de contact (%s) : %s", payload.email, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "L'envoi du message a échoué. Merci de réessayer ou de nous "
                f"écrire directement à {settings.contact_email}."
            ),
        ) from exc
