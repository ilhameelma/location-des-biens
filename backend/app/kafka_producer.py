"""
Étape 10 — Collecte des données (Apache Kafka)

Point d'entrée unique utilisé par les autres routers (biens, réservations,
paiements...) pour publier un événement métier vers Kafka, dès que
l'action correspondante a été validée en base.

Même philosophie que app/notifications_service.py (étape 9) :
  - un seul appel, `publish_event()`, depuis les endpoints ;
  - best-effort et non-bloquant : si Kafka est indisponible (au démarrage
    ou temporairement), on logue un avertissement mais on ne fait JAMAIS
    échouer l'action métier appelante (créer un bien, une réservation...) ;
  - le producer est initialisé paresseusement (au premier événement), pas
    au chargement du module, pour ne pas empêcher le back-end de démarrer
    si Docker/Kafka n'est pas encore lancé.

Ces événements sont consommés en aval par Spark (étape 11), stockés bruts
dans le data lake MinIO (étape 12), orchestrés par Airflow (étape 13), puis
agrégés dans le data warehouse (étape 14) et visualisés dans Power BI
(étape 15).
"""
import json
import logging
import threading
from datetime import date, datetime
from uuid import UUID

from kafka import KafkaProducer
from kafka.errors import KafkaError

from .config import settings

logger = logging.getLogger(__name__)

_producer: KafkaProducer | None = None
_disabled = False  # passe à True après un échec de connexion, pour ne pas
                    # retenter (et ralentir) chaque requête HTTP suivante
_lock = threading.Lock()


def _json_default(obj):
    """Sérialise les types non-JSON natifs utilisés par les modèles SQLAlchemy."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def _get_producer() -> KafkaProducer | None:
    global _producer, _disabled

    if _disabled:
        return None
    if _producer is not None:
        return _producer

    with _lock:
        if _producer is not None:
            return _producer
        try:
            _producer = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                client_id=settings.kafka_client_id,
                value_serializer=lambda v: json.dumps(v, default=_json_default).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k is not None else None,
                linger_ms=50,
                request_timeout_ms=3000,
                api_version_auto_timeout_ms=3000,
                retries=1,
            )
            logger.info("Producer Kafka connecté à %s.", settings.kafka_bootstrap_servers)
        except Exception as exc:
            logger.warning(
                "Kafka indisponible (%s) — la collecte d'événements (étape 10) est "
                "désactivée pour cette session du back-end. L'application continue "
                "de fonctionner normalement.",
                exc,
            )
            _disabled = True
            return None

    return _producer


def publish_event(topic: str, payload: dict, key: str | None = None) -> None:
    """
    Publie un événement métier vers un topic Kafka.

    - `topic` : voir app/kafka_topics.py
    - `payload` : dict JSON-sérialisable (UUID/datetime gérés automatiquement)
    - `key` : clé de partitionnement Kafka (ex. l'id du bien), optionnelle

    Ne lève jamais d'exception : un souci Kafka ne doit jamais faire
    échouer une requête HTTP métier.
    """
    producer = _get_producer()
    if producer is None:
        return
    try:
        producer.send(topic, key=key, value=payload)
        # flush non bloquant en tâche de fond serait plus robuste, mais pour
        # un projet de cette taille un flush périodique implicite (via
        # linger_ms) suffit ; on peut forcer un flush() ici si on préfère
        # la simplicité à la performance :
        # producer.flush(timeout=1)
    except KafkaError as exc:
        logger.warning("Échec de publication Kafka sur le topic '%s' : %s", topic, exc)
