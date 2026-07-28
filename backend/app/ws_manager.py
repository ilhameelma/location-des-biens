"""
Étape 8 — Messagerie temps réel (WebSocket)

Gestionnaire de connexions WebSocket en mémoire : associe à chaque
conversation la liste des sockets actuellement connectés (0, 1 ou 2 —
le client et/ou le propriétaire), pour diffuser un nouveau message aux
deux interlocuteurs instantanément.

Limite assumée (projet pédagogique) : stockage en mémoire du process
Python -> ne fonctionne que pour une seule instance du back-end. Pour
passer à plusieurs instances (Kubernetes, étape 21), il faudrait un
relais partagé (ex: Redis Pub/Sub) entre les instances.
"""
import uuid
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)

    async def connect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[conversation_id].append(websocket)

    def disconnect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        conns = self._connections.get(conversation_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: uuid.UUID, payload: dict) -> None:
        """Envoie `payload` (JSON) à toutes les sockets connectées à cette conversation."""
        for ws in list(self._connections.get(conversation_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                # Socket morte / déconnectée sans avoir déclenché WebSocketDisconnect
                self.disconnect(conversation_id, ws)

    def online_count(self, conversation_id: uuid.UUID) -> int:
        return len(self._connections.get(conversation_id, []))


manager = ConnectionManager()

# Étape 9 — Notifications : même mécanisme que la messagerie (étape 8), mais
# la clé n'est plus une conversation, c'est l'utilisateur lui-même -> un canal
# "privé" par utilisateur connecté, sur lequel le back-end pousse en direct
# toute nouvelle notification (nouvelle demande de réservation, paiement
# reçu, changement de statut...).
notif_manager = ConnectionManager()


# ------------------------------------------------------------------
# La plupart des endpoints qui déclenchent une notification (créer une
# réservation, changer son statut, enregistrer un paiement...) sont des
# fonctions FastAPI *synchrones* : elles s'exécutent dans un threadpool,
# PAS dans la boucle asyncio principale. On ne peut donc pas y faire
# `await manager.broadcast(...)` ni récupérer la boucle courante avec
# `asyncio.get_event_loop()` (on est dans le mauvais thread).
#
# On capture donc la boucle asyncio principale une fois, au démarrage de
# l'app (voir main.py), et on s'en sert avec `run_coroutine_threadsafe`
# pour planifier la diffusion depuis n'importe quel thread en sécurité.
# ------------------------------------------------------------------
import asyncio  # noqa: E402

_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


def get_main_loop() -> asyncio.AbstractEventLoop | None:
    return _main_loop
