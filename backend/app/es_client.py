"""
Étape 18 — Recherche avancée (Elasticsearch)

Indexe les biens dans Elasticsearch au fil de l'eau (création / mise à jour /
suppression, appelé depuis app/routers/biens.py) pour permettre une recherche
multicritères rapide (texte libre sur titre/description, filtres ville / type
/ prix / superficie / nb_pieces, recherche géographique par rayon en
s'appuyant sur les coordonnées GPS de l'étape 17, tri par pertinence).

Même philosophie que app/kafka_producer.py (étape 10) et
app/notifications_service.py (étape 9) :
  - client initialisé paresseusement (au premier appel), jamais au chargement
    du module, pour ne pas empêcher le back-end de démarrer si Docker/ES
    n'est pas encore lancé ;
  - best-effort et non-bloquant côté écriture (index_bien / delete_bien) :
    un souci Elasticsearch ne fait JAMAIS échouer une requête HTTP métier
    (créer/modifier/supprimer un bien) ;
  - côté lecture (search_biens), en revanche, l'appelant (routers/biens.py)
    doit pouvoir détecter l'indisponibilité pour basculer sur un repli SQL
    classique (filtre PostgreSQL) — search_biens lève donc une exception
    explicite plutôt que de l'avaler.
"""
import logging
import threading
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError, NotFoundError

from .config import settings

logger = logging.getLogger(__name__)

_client: Elasticsearch | None = None
_disabled = False
_lock = threading.Lock()

INDEX_MAPPING = {
    "id": {"type": "keyword"},
    "proprietaire_id": {"type": "keyword"},
    "titre": {
        "type": "text",
        "analyzer": "french",
        "fields": {"raw": {"type": "keyword"}},
    },
    "description": {"type": "text", "analyzer": "french"},
    "type_bien": {"type": "keyword"},
    "type_transaction": {"type": "keyword"},
    "adresse": {"type": "text", "analyzer": "french"},
    "ville": {
        "type": "text",
        "analyzer": "french",
        "fields": {"raw": {"type": "keyword"}},
    },
    "position": {"type": "geo_point"},
    "superficie": {"type": "float"},
    "prix": {"type": "float"},
    "nb_pieces": {"type": "integer"},
    "statut": {"type": "keyword"},
    "date_publication": {"type": "date"},
}


def _get_client() -> Elasticsearch | None:
    global _client, _disabled

    if _disabled:
        return None
    if _client is not None:
        return _client

    with _lock:
        if _client is not None:
            return _client
        try:
            client = Elasticsearch(settings.elasticsearch_url, request_timeout=3)
            if not client.ping():
                raise ESConnectionError("ping failed")
            _client = client
            logger.info("Client Elasticsearch connecté à %s.", settings.elasticsearch_url)
        except Exception as exc:
            logger.warning(
                "Elasticsearch indisponible (%s) — la recherche avancée (étape 18) "
                "bascule sur le filtrage SQL classique pour cette session. "
                "L'application continue de fonctionner normalement.",
                exc,
            )
            _disabled = True
            return None

    return _client


def ensure_index() -> None:
    """Crée l'index `smartrent_biens` s'il n'existe pas déjà. Best-effort,
    appelé une fois au démarrage du back-end (voir app/main.py)."""
    client = _get_client()
    if client is None:
        return
    try:
        if not client.indices.exists(index=settings.elasticsearch_index):
            client.indices.create(index=settings.elasticsearch_index, mappings={"properties": INDEX_MAPPING})
            logger.info("Index Elasticsearch '%s' créé.", settings.elasticsearch_index)
    except Exception as exc:
        logger.warning("Impossible de créer/vérifier l'index Elasticsearch : %s", exc)


def _bien_to_document(bien) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "id": str(bien.id),
        "proprietaire_id": str(bien.proprietaire_id),
        "titre": bien.titre,
        "description": bien.description,
        "type_bien": bien.type_bien,
        "type_transaction": bien.type_transaction,
        "adresse": bien.adresse,
        "ville": bien.ville,
        "superficie": float(bien.superficie) if bien.superficie is not None else None,
        "prix": float(bien.prix),
        "nb_pieces": bien.nb_pieces,
        "statut": bien.statut,
        "date_publication": bien.date_publication.isoformat() if bien.date_publication else None,
    }
    if bien.latitude is not None and bien.longitude is not None:
        doc["position"] = {"lat": bien.latitude, "lon": bien.longitude}
    return doc


def index_bien(bien) -> None:
    """Indexe (ou réindexe) un bien. Ne lève jamais d'exception."""
    client = _get_client()
    if client is None:
        return
    try:
        client.index(
            index=settings.elasticsearch_index,
            id=str(bien.id),
            document=_bien_to_document(bien),
        )
    except Exception as exc:
        logger.warning("Échec d'indexation Elasticsearch du bien %s : %s", bien.id, exc)


def delete_bien(bien_id) -> None:
    """Supprime un bien de l'index. Ne lève jamais d'exception."""
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(index=settings.elasticsearch_index, id=str(bien_id))
    except NotFoundError:
        pass
    except Exception as exc:
        logger.warning("Échec de suppression Elasticsearch du bien %s : %s", bien_id, exc)


class ElasticsearchUnavailable(Exception):
    """Levée par search_biens() pour signaler à l'appelant de basculer sur SQL."""


def search_biens(
    *,
    q: str | None = None,
    ville: str | None = None,
    type_bien: str | None = None,
    type_transaction: str | None = None,
    prix_min: float | None = None,
    prix_max: float | None = None,
    superficie_min: float | None = None,
    superficie_max: float | None = None,
    nb_pieces_min: int | None = None,
    lat: float | None = None,
    lon: float | None = None,
    rayon_km: float | None = None,
    tri: str = "pertinence",
    taille: int = 50,
) -> list[str]:
    """
    Recherche multicritères de biens `disponible` dans Elasticsearch.
    Retourne la liste des IDs (str) triés selon `tri`, à réhydrater ensuite
    depuis PostgreSQL par l'appelant (pour conserver le schéma BienOut
    complet, avec les photos).

    Lève ElasticsearchUnavailable si le service est indisponible, pour que
    l'appelant puisse basculer sur un repli SQL classique.
    """
    client = _get_client()
    if client is None:
        raise ElasticsearchUnavailable("Elasticsearch indisponible")

    must: list[dict] = []
    filters: list[dict] = [{"term": {"statut": "disponible"}}]

    if q:
        must.append(
            {
                "multi_match": {
                    "query": q,
                    "fields": ["titre^3", "ville^2", "adresse", "description"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        )
    if ville:
        filters.append({"match": {"ville": {"query": ville, "operator": "and"}}})
    if type_bien:
        filters.append({"term": {"type_bien": type_bien}})
    if type_transaction:
        filters.append({"term": {"type_transaction": type_transaction}})
    if prix_min is not None or prix_max is not None:
        rng: dict[str, float] = {}
        if prix_min is not None:
            rng["gte"] = prix_min
        if prix_max is not None:
            rng["lte"] = prix_max
        filters.append({"range": {"prix": rng}})
    if superficie_min is not None or superficie_max is not None:
        rng = {}
        if superficie_min is not None:
            rng["gte"] = superficie_min
        if superficie_max is not None:
            rng["lte"] = superficie_max
        filters.append({"range": {"superficie": rng}})
    if nb_pieces_min is not None:
        filters.append({"range": {"nb_pieces": {"gte": nb_pieces_min}}})
    if lat is not None and lon is not None and rayon_km is not None:
        filters.append(
            {"geo_distance": {"distance": f"{rayon_km}km", "position": {"lat": lat, "lon": lon}}}
        )

    query: dict[str, Any] = {"bool": {"must": must or [{"match_all": {}}], "filter": filters}}
    sort: list[dict] | None = None

    if tri == "prix_asc":
        sort = [{"prix": "asc"}]
    elif tri == "prix_desc":
        sort = [{"prix": "desc"}]
    elif tri == "recent":
        sort = [{"date_publication": "desc"}]
    # "pertinence" (défaut) : tri implicite par _score Elasticsearch, pas de "sort" explicite

    try:
        res = client.search(
            index=settings.elasticsearch_index,
            query=query,
            sort=sort,
            size=taille,
        )
    except Exception as exc:
        logger.warning("Échec de recherche Elasticsearch : %s", exc)
        raise ElasticsearchUnavailable(str(exc)) from exc

    return [hit["_id"] for hit in res["hits"]["hits"]]
