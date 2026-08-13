"""Router FastAPI — statistiques publiques (landing page).

Endpoint public unique, sans authentification requise, qui calcule les
métriques affichées sur la landing page (`biens en ligne`, `villes
couvertes`, `espaces dédiés`) directement en base de données, plutôt que de
laisser le front-end les déduire d'une liste de biens potentiellement
tronquée (`GET /biens` limite ses résultats Elasticsearch à 50 par défaut).

Aucune donnée sensible n'est exposée ici : uniquement des compteurs agrégés.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/stats", tags=["statistiques"])


@router.get("/publiques")
def get_stats_publiques(db: Session = Depends(get_db)):
    """
    Métriques affichées sur la landing page, calculées automatiquement :

    - `biens_en_ligne` : nombre total de biens au statut `disponible`
      (pas seulement les 50 premiers renvoyés par la recherche Elasticsearch).
    - `villes_couvertes` : nombre de villes distinctes parmi ces biens.
    - `espaces_dedies` : nombre de rôles utilisateur **distincts** réellement
      présents en base (`admin`, `client`, `proprietaire`, `agence`,
      `promoteur`, `conciergerie`... — jusqu'à 6 valeurs possibles, voir
      `schemas.Role`). Chaque rôle compte pour un espace, sans regroupement.
    """
    biens_disponibles = (
        db.query(models.Bien).filter(models.Bien.statut == "disponible")
    )

    biens_en_ligne = biens_disponibles.count()

    villes_couvertes = (
        db.query(func.count(func.distinct(models.Bien.ville)))
        .filter(models.Bien.statut == "disponible")
        .scalar()
        or 0
    )

    espaces_dedies = (
        db.query(func.count(func.distinct(models.Utilisateur.role))).scalar() or 0
    )

    return {
        "biens_en_ligne": biens_en_ligne,
        "villes_couvertes": villes_couvertes,
        "espaces_dedies": espaces_dedies,
    }
