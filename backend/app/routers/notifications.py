import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

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
