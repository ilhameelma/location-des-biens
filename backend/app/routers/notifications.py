"""
Router FastAPI pour les notifications (étape 9).

- REST : lister les notifications, en marquer une (ou toutes) comme lue(s),
  récupérer juste le compteur de non-lues (utile pour un badge léger avant
  même que le WebSocket ne soit connecté).
- WebSocket (`/notifications/ws?token=...`) : canal privé par utilisateur,
  sur lequel le back-end pousse en direct toute nouvelle notification
  (voir app/notifications_service.py, appelé depuis reservations.py et
  paiements.py). Même principe que la messagerie temps réel de l'étape 8,
  mais keyé par utilisateur plutôt que par conversation.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..security import decode_access_token
from ..ws_manager import notif_manager

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me", response_model=list[schemas.NotificationOut])
def my_notifications(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    return (
        db.query(models.Notification)
        .filter(models.Notification.utilisateur_id == current_user.id)
        .order_by(models.Notification.date_creation.desc())
        .all()
    )


@router.get("/me/compteur")
def unread_count(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """Compteur léger de notifications non lues (pour afficher le badge de la cloche)."""
    count = (
        db.query(models.Notification)
        .filter(
            models.Notification.utilisateur_id == current_user.id,
            models.Notification.lu.is_(False),
        )
        .count()
    )
    return {"non_lues": count}


@router.patch("/{notification_id}/lue", response_model=schemas.NotificationOut)
def mark_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    notif = db.get(models.Notification, notification_id)
    if not notif or notif.utilisateur_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    notif.lu = True
    db.commit()
    db.refresh(notif)
    return notif


@router.patch("/me/tout-lire")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    (
        db.query(models.Notification)
        .filter(
            models.Notification.utilisateur_id == current_user.id,
            models.Notification.lu.is_(False),
        )
        .update({"lu": True})
    )
    db.commit()
    return {"status": "ok"}


# ============================================================
# WebSocket — canal de push temps réel (privé, par utilisateur)
# ============================================================
@router.websocket("/ws")
async def websocket_notifications(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    cookie_token = websocket.cookies.get("smartrent_token")
    effective_token = cookie_token or token

    payload = decode_access_token(effective_token) if effective_token else None
    user_id = payload.get("sub") if payload else None
    user = db.get(models.Utilisateur, uuid.UUID(user_id)) if user_id else None
    if user is None:
        await websocket.close(code=4401)
        return

    await notif_manager.connect(user.id, websocket)
