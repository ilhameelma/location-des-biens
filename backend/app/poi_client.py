"""
Complément à l'étape 17 — Cartographie

Récupère les points d'intérêt (POI) à proximité des coordonnées GPS d'un
bien — hôtels, jardins/parcs, écoles, centres commerciaux — via l'API
Overpass d'OpenStreetMap (même écosystème que Leaflet + Nominatim déjà
utilisés à l'étape 17, gratuit, sans clé API).

Même philosophie "best-effort" que kafka_producer.py (étape 9) et
es_client.py (étape 18) : un souci réseau ou une lenteur d'Overpass ne
doit JAMAIS faire échouer l'affichage de la fiche détaillée d'un bien —
on renvoie simplement une liste vide avec `disponible=False`, affichée
par le front comme "non disponible pour le moment" plutôt qu'une erreur.

Un cache mémoire simple (TTL) évite de solliciter Overpass (instance
publique, partagée et rate-limitée) à chaque affichage de la même fiche.
"""
import logging
import math
import threading
import time
from datetime import datetime
from typing import Literal

import httpx

from .config import settings

logger = logging.getLogger(__name__)

Categorie = Literal["hotel", "jardin", "ecole", "commerce"]

CATEGORIE_LABELS: dict[Categorie, str] = {
    "hotel": "Hôtels",
    "jardin": "Jardins & parcs",
    "ecole": "Écoles & universités",
    "commerce": "Centres commerciaux",
}

# Tags OSM regroupés par catégorie affichée côté front, puis par clé — permet
# de construire une requête Overpass compacte (une seule clause `nwr` par
# clé, avec les valeurs combinées en regex) plutôt que 20 clauses séparées
# `node`/`way` par valeur. Requête plus légère = réponse Overpass plus rapide,
# ce qui compte pour rester sous le timeout côté back-end.
_CATEGORIE_TAGS: dict[Categorie, dict[str, list[str]]] = {
    "hotel": {"tourism": ["hotel", "guest_house"]},
    "jardin": {"leisure": ["park", "garden"]},
    "ecole": {"amenity": ["school", "university", "college", "kindergarten"]},
    "commerce": {"shop": ["mall", "department_store"]},
}

_MAX_PAR_CATEGORIE = 5

_cache: dict[tuple, tuple[float, dict, float]] = {}
_cache_lock = threading.Lock()
_CACHE_TTL_SECONDS = 6 * 60 * 60  # les commerces/écoles/hôtels ne bougent pas d'une heure à l'autre
_CACHE_TTL_ECHEC_SECONDS = 2 * 60  # évite de retester les 3 miroirs à chaque page pendant une panne


class PoiServiceUnavailable(Exception):
    """Overpass est injoignable ou a répondu trop lentement."""


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance à vol d'oiseau (formule de Haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _build_query(lat: float, lon: float, rayon_m: int) -> str:
    clauses = []
    for tags_par_cle in _CATEGORIE_TAGS.values():
        for cle, valeurs in tags_par_cle.items():
            alternatives = "|".join(valeurs)
            # nwr = node+way+relation en une seule clause (au lieu de node+way
            # séparés) ; le centre géométrique des way/relation est obtenu via
            # "out center" plus bas.
            clauses.append(f'nwr["{cle}"~"^({alternatives})$"](around:{rayon_m},{lat},{lon});')
    return f"[out:json][timeout:20];({''.join(clauses)});out center tags;"


def _fetch_overpass(lat: float, lon: float, rayon_m: int) -> list[dict]:
    """
    Interroge Overpass en essayant plusieurs miroirs dans l'ordre
    (`settings.overpass_urls`) : l'instance publique historique
    overpass-api.de renvoie régulièrement 406 Not Acceptable depuis
    qu'elle filtre le trafic qui "ressemble" à du scraping automatisé —
    problème connu et documenté côté communauté OSM, pas un bug côté
    SmartRent. On bascule donc automatiquement sur un miroir alternatif
    (overpass.kumi.systems, overpass.private.coffee...) sans jamais faire
    échouer l'affichage de la fiche du bien.
    """
    query = _build_query(lat, lon, rayon_m)
    headers = {
        # Certains miroirs (dont overpass-api.de) rejettent les requêtes
        # sans identification claire du client — bonne pratique pour toute
        # infrastructure OSM publique partagée.
        "User-Agent": "SmartRentPFE/1.0 (projet PFE Data Engineering ; contact via l'application)",
        "Accept": "application/json",
    }
    # Timeout scindé : la connexion échoue vite si le miroir est injoignable,
    # mais Overpass peut légitimement mettre plusieurs secondes à calculer une
    # requête géographique même simplifiée — un timeout de lecture trop court
    # (l'erreur "read operation timed out" observée en pratique) coupait des
    # requêtes qui auraient fini par aboutir.
    timeout = httpx.Timeout(
        connect=5.0,
        read=settings.overpass_timeout_seconds,
        write=5.0,
        pool=5.0,
    )
    dernieres_erreurs: list[str] = []

    for url in settings.overpass_urls:
        try:
            response = httpx.post(url, data={"data": query}, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.json().get("elements", [])
        except httpx.HTTPStatusError as exc:
            logger.warning("Overpass (%s) a renvoyé une erreur %s, essai du miroir suivant", url, exc.response.status_code)
            dernieres_erreurs.append(f"{url} -> HTTP {exc.response.status_code}")
        except httpx.RequestError as exc:
            logger.warning("Overpass (%s) injoignable (%s), essai du miroir suivant", url, exc)
            dernieres_erreurs.append(f"{url} -> {exc}")

    raise PoiServiceUnavailable("; ".join(dernieres_erreurs))


def _categorie_de(tags: dict) -> Categorie | None:
    for categorie, tags_par_cle in _CATEGORIE_TAGS.items():
        for cle, valeurs in tags_par_cle.items():
            if tags.get(cle) in valeurs:
                return categorie
    return None


def get_proximite(lat: float, lon: float, rayon_km: float = 1.5) -> dict:
    """
    Renvoie les POI groupés par catégorie autour de (lat, lon), triés par
    distance croissante, limités à `_MAX_PAR_CATEGORIE` par catégorie.

    Structure renvoyée (toujours ce format, même en cas d'échec Overpass) :
        {
            "disponible": bool,
            "categories": {
                "hotel": [{"nom": ..., "distance_km": ..., "lat": ..., "lon": ...}, ...],
                "jardin": [...],
                "ecole": [...],
                "commerce": [...],
            },
        }
    """
    rayon_m = int(rayon_km * 1000)
    cache_key = (round(lat, 4), round(lon, 4), rayon_m)

    with _cache_lock:
        cached = _cache.get(cache_key)
        if cached and (time.time() - cached[0]) < cached[2]:
            return cached[1]

    resultat: dict = {
        "disponible": True,
        "categories": {c: [] for c in CATEGORIE_LABELS},
    }

    try:
        elements = _fetch_overpass(lat, lon, rayon_m)
    except PoiServiceUnavailable:
        resultat["disponible"] = False
        with _cache_lock:
            _cache[cache_key] = (time.time(), resultat, _CACHE_TTL_ECHEC_SECONDS)
        return resultat

    vus: set[tuple] = set()
    par_categorie: dict[Categorie, list[dict]] = {c: [] for c in CATEGORIE_LABELS}

    for el in elements:
        tags = el.get("tags", {})
        nom = tags.get("name")
        if not nom:
            continue  # POI sans nom : peu utile à afficher côté fiche annonce

        categorie = _categorie_de(tags)
        if categorie is None:
            continue

        if el.get("type") == "node":
            poi_lat, poi_lon = el.get("lat"), el.get("lon")
        else:  # "way" — le centre géométrique est renvoyé grâce à `out center`
            center = el.get("center") or {}
            poi_lat, poi_lon = center.get("lat"), center.get("lon")
        if poi_lat is None or poi_lon is None:
            continue

        dedup_key = (categorie, nom, round(poi_lat, 4), round(poi_lon, 4))
        if dedup_key in vus:
            continue
        vus.add(dedup_key)

        par_categorie[categorie].append(
            {
                "nom": nom,
                "distance_km": round(_distance_km(lat, lon, poi_lat, poi_lon), 2),
                "lat": poi_lat,
                "lon": poi_lon,
            }
        )

    for categorie, pois in par_categorie.items():
        pois.sort(key=lambda p: p["distance_km"])
        resultat["categories"][categorie] = pois[:_MAX_PAR_CATEGORIE]

    with _cache_lock:
        _cache[cache_key] = (time.time(), resultat, _CACHE_TTL_SECONDS)

    return resultat


def calculer_et_stocker_proximite(bien_id: str) -> None:
    """
    Calcule les proximités d'un bien (rayon par défaut) et les stocke sur
    la ligne `bien` elle-même (`proximite_data` / `proximite_calculee_le`),
    afin que la fiche annonce n'ait plus jamais à attendre Overpass pour un
    affichage normal — seul le premier calcul, à la publication, est lent.

    Conçu pour tourner en tâche d'arrière-plan (FastAPI `BackgroundTasks`,
    exécutée après l'envoi de la réponse HTTP de création/màj du bien) :
    ouvre donc sa propre session DB plutôt que de réutiliser celle de la
    requête (fermée entre-temps). Best-effort comme le reste du module —
    une erreur ici ne doit jamais faire planter le back-end ; au pire, la
    fiche du bien recalculera à la volée au premier affichage (voir
    `GET /biens/{id}/proximite` dans routers/biens.py).
    """
    # Import différé pour éviter tout import circulaire au chargement du
    # module (models -> database -> ... ; poi_client reste indépendant du
    # reste de l'app tant qu'on ne rentre pas dans cette fonction).
    from . import models
    from .database import SessionLocal

    db = SessionLocal()
    try:
        bien = db.get(models.Bien, bien_id)
        if not bien or bien.latitude is None or bien.longitude is None:
            return

        resultat = get_proximite(bien.latitude, bien.longitude, settings.poi_rayon_km_defaut)
        if not resultat.get("disponible"):
            # Overpass indisponible au moment du calcul : on ne stocke rien
            # plutôt que d'écraser une éventuelle donnée déjà valide, et on
            # laisse `GET /biens/{id}/proximite` retenter à la volée plus tard.
            logger.info("Proximité indisponible pour le bien %s (Overpass injoignable), non stockée", bien_id)
            return

        bien.proximite_data = resultat
        bien.proximite_calculee_le = datetime.utcnow()
        db.commit()
    except Exception:
        logger.exception("Échec du calcul/stockage de la proximité pour le bien %s", bien_id)
        db.rollback()
    finally:
        db.close()
