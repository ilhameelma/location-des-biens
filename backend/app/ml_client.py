"""
Étape 16 — Intelligence artificielle

Client HTTP vers le micro-service IA (dossier ml_service/, exécuté comme
processus séparé — voir ml_service/README.md).

Contrairement à kafka_producer.py / notifications_service.py, ces appels
ne sont PAS best-effort silencieux : quand l'utilisateur demande
explicitement une estimation/recommandation/vérification de fraude,
une panne du micro-service doit remonter comme une erreur claire
(503) plutôt que d'être avalée silencieusement.
"""

import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class MLServiceError(Exception):
    """Le micro-service IA est indisponible ou a renvoyé une erreur."""


def _post(path: str, json_payload: dict) -> dict:
    url = f"{settings.ml_service_url}{path}"
    try:
        response = httpx.post(url, json=json_payload, timeout=settings.ml_service_timeout_seconds)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Micro-service IA a renvoyé une erreur (%s) : %s", exc.response.status_code, exc.response.text)
        raise MLServiceError(exc.response.json().get("detail", str(exc))) from exc
    except httpx.RequestError as exc:
        logger.warning("Micro-service IA injoignable sur %s : %s", url, exc)
        raise MLServiceError("Le service IA est temporairement indisponible.") from exc


def estimer_loyer(bien_payload: dict) -> dict:
    return _post("/predict/estimation", bien_payload)


def detecter_fraude(bien_payload: dict) -> dict:
    return _post("/predict/fraude", bien_payload)


def recommander(payload: dict) -> dict:
    return _post("/predict/recommandation", payload)
