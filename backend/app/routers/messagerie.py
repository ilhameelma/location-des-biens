"""
Router FastAPI pour la messagerie (étape 8 — Chat temps réel propriétaire-client).

Deux canaux exposés :
- REST classique : lister les conversations, lister/envoyer des messages
  (utile pour l'historique et comme repli si le WebSocket n'est pas disponible).
- WebSocket (`/conversations/ws/{conversation_id}`) : canal temps réel, utilisé
  par le front-end une fois la conversation ouverte, pour recevoir/envoyer
  les messages instantanément sans recharger.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..security import decode_access_token
from ..ws_manager import manager

router = APIRouter(prefix="/conversations", tags=["messagerie"])


# ============================================================
# Helpers
# ============================================================

def _to_conversation_out(conv: models.Conversation, current_user_id: uuid.UUID, db: Session) -> schemas.ConversationOut:
    """Construit un ConversationOut enrichi (nom de l'autre interlocuteur, dernier message, non-lus)."""
    if conv.client_id == current_user_id:
        autre = db.get(models.Utilisateur, conv.proprietaire_id)
    else:
        autre = db.get(models.Utilisateur, conv.client_id)

    dernier = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conv.id)
        .order_by(models.Message.date_envoi.desc())
        .first()
    )
    non_lus = (
        db.query(models.Message)
        .filter(
            models.Message.conversation_id == conv.id,
            models.Message.expediteur_id != current_user_id,
            models.Message.lu.is_(False),
        )
        .count()
    )
    bien_titre = None
    if conv.bien_id:
        bien = db.get(models.Bien, conv.bien_id)
        bien_titre = bien.titre if bien else None

    return schemas.ConversationOut(
        id=conv.id,
        bien_id=conv.bien_id,
        bien_titre=bien_titre,
        client_id=conv.client_id,
        proprietaire_id=conv.proprietaire_id,
        autre_nom=autre.nom if autre else "?",
        autre_prenom=autre.prenom if autre else "?",
        dernier_message=dernier.contenu if dernier else None,
        date_dernier_message=dernier.date_envoi if dernier else None,
        non_lus=non_lus,
    )


# ============================================================
# REST — Conversations
# ============================================================

@router.get("", response_model=list[schemas.ConversationOut])
def my_conversations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """Liste les conversations de l'utilisateur connecté, triées par activité récente."""
    query = db.query(models.Conversation)
    if current_user.role == "client":
        query = query.filter(models.Conversation.client_id == current_user.id)
    elif current_user.role == "proprietaire":
        query = query.filter(models.Conversation.proprietaire_id == current_user.id)
    else:
        # Un admin n'a pas de messagerie dédiée pour l'instant.
        return []

    conversations = [_to_conversation_out(c, current_user.id, db) for c in query.all()]
    conversations.sort(
        key=lambda c: c.date_dernier_message or datetime.min,
        reverse=True,
    )
    return conversations


@router.post("", response_model=schemas.ConversationOut, status_code=201)
def start_conversation(
    payload: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """
    Démarre une conversation avec un propriétaire (ou récupère la conversation
    existante si elle existe déjà pour ce couple client/propriétaire/bien).
    Réservé aux clients : c'est le client qui prend l'initiative du contact.
    """
    if current_user.role != "client":
        raise HTTPException(status_code=403, detail="Seul un client peut démarrer une conversation")

    proprietaire = db.get(models.Utilisateur, payload.proprietaire_id)
    if not proprietaire or proprietaire.role != "proprietaire":
        raise HTTPException(status_code=404, detail="Propriétaire introuvable")

    existing = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.client_id == current_user.id,
            models.Conversation.proprietaire_id == payload.proprietaire_id,
            models.Conversation.bien_id == payload.bien_id,
        )
        .first()
    )
    conv = existing or models.Conversation(
        client_id=current_user.id,
        proprietaire_id=payload.proprietaire_id,
        bien_id=payload.bien_id,
    )
    if not existing:
        db.add(conv)
        db.commit()
        db.refresh(conv)

    return _to_conversation_out(conv, current_user.id, db)


# ============================================================
# REST — Messages (historique + envoi de repli)
# ============================================================

@router.get("/{conversation_id}/messages", response_model=list[schemas.MessageOut])
def get_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    conv = db.get(models.Conversation, conversation_id)
    if not conv or current_user.id not in (conv.proprietaire_id, conv.client_id):
        raise HTTPException(status_code=403, detail="Accès refusé")

    messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.date_envoi.asc())
        .all()
    )

    # Marquer comme lus les messages reçus (pas envoyés par l'utilisateur courant)
    # au moment où il ouvre la conversation.
    a_marquer = [m for m in messages if m.expediteur_id != current_user.id and not m.lu]
    if a_marquer:
        for m in a_marquer:
            m.lu = True
        db.commit()

    return messages


@router.post("/{conversation_id}/messages", response_model=schemas.MessageOut, status_code=201)
async def send_message(
    conversation_id: uuid.UUID,
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """
    Envoi REST (repli si le WebSocket n'est pas connecté). Le message est
    aussi diffusé en temps réel aux sockets ouvertes sur cette conversation,
    pour que les deux canaux restent cohérents.
    """
    conv = db.get(models.Conversation, conversation_id)
    if not conv or current_user.id not in (conv.proprietaire_id, conv.client_id):
        raise HTTPException(status_code=403, detail="Accès refusé")

    contenu = payload.contenu.strip()
    if not contenu:
        raise HTTPException(status_code=422, detail="Le message ne peut pas être vide")

    message = models.Message(
        conversation_id=conversation_id, expediteur_id=current_user.id, contenu=contenu
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    await manager.broadcast(
        conversation_id,
        {
            "type": "message",
            "id": str(message.id),
            "conversation_id": str(conversation_id),
            "expediteur_id": str(current_user.id),
            "contenu": message.contenu,
            "date_envoi": message.date_envoi.isoformat(),
            "lu": message.lu,
        },
    )
    return message


# ============================================================
# WebSocket — Canal temps réel
# ============================================================
# Le navigateur ne peut pas ajouter de header Authorization à une connexion
# WebSocket : le token JWT (étape 5) est donc transmis en query param
# (ex: ws://localhost:8000/api/conversations/ws/<id>?token=...).

@router.websocket("/ws/{conversation_id}")
async def websocket_conversation(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(token)
    user_id = payload.get("sub") if payload else None
    user = db.get(models.Utilisateur, uuid.UUID(user_id)) if user_id else None
    if user is None:
        await websocket.close(code=4401)  # code custom : non authentifié
        return

    conv = db.get(models.Conversation, conversation_id)
    if not conv or user.id not in (conv.proprietaire_id, conv.client_id):
        await websocket.close(code=4403)  # code custom : accès refusé
        return

    await manager.connect(conversation_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            contenu = str(data.get("contenu", "")).strip()
            if not contenu:
                continue

            message = models.Message(
                conversation_id=conversation_id, expediteur_id=user.id, contenu=contenu
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            await manager.broadcast(
                conversation_id,
                {
                    "type": "message",
                    "id": str(message.id),
                    "conversation_id": str(conversation_id),
                    "expediteur_id": str(user.id),
                    "contenu": message.contenu,
                    "date_envoi": message.date_envoi.isoformat(),
                    "lu": message.lu,
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
