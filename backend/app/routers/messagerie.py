import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/conversations", tags=["messagerie"])


@router.get("", response_model=list[schemas.ConversationOut])
def my_conversations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    query = db.query(models.Conversation)
    if current_user.role == "client":
        query = query.filter(models.Conversation.client_id == current_user.id)
    elif current_user.role == "proprietaire":
        query = query.filter(models.Conversation.proprietaire_id == current_user.id)
    return query.all()


@router.get("/{conversation_id}/messages", response_model=list[schemas.MessageOut])
def get_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    conv = db.get(models.Conversation, conversation_id)
    if not conv or current_user.id not in (conv.proprietaire_id, conv.client_id):
        raise HTTPException(status_code=403, detail="Accès refusé")
    return (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.date_envoi.asc())
        .all()
    )


@router.post("/{conversation_id}/messages", response_model=schemas.MessageOut, status_code=201)
def send_message(
    conversation_id: uuid.UUID,
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """
    Envoi REST simple. En étape 8, ce même endpoint sera doublé d'une diffusion
    WebSocket pour push instantané aux deux interlocuteurs.
    """
    conv = db.get(models.Conversation, conversation_id)
    if not conv or current_user.id not in (conv.proprietaire_id, conv.client_id):
        raise HTTPException(status_code=403, detail="Accès refusé")

    message = models.Message(
        conversation_id=conversation_id, expediteur_id=current_user.id, contenu=payload.contenu
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
