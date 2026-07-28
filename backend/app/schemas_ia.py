"""Schémas des endpoints /ia/* — étape 16, séparés de schemas.py pour ne
pas alourdir le fichier principal avec des champs propres au micro-service IA."""

from typing import Optional

from pydantic import BaseModel, Field


class BienEstimationInput(BaseModel):
    ville: str
    superficie: float
    nb_pieces: Optional[int] = None
    type_bien: Optional[str] = None
    quartier: Optional[str] = None
    chambres: Optional[float] = None
    salles_de_bain: Optional[float] = None
    meuble: Optional[bool] = None


class BienFraudeInput(BienEstimationInput):
    prix_affiche_dh: float


class RecommandationPreferences(BaseModel):
    ville: Optional[str] = None
    budget_dh: Optional[float] = None
    superficie: Optional[float] = None
    nb_pieces: Optional[int] = None
    meuble: Optional[bool] = None
    top_n: int = Field(5, ge=1, le=20)
    utiliser_catalogue_reel: bool = Field(
        True,
        description="Si True et qu'assez de biens disponibles existent en base, "
                    "recommande parmi eux plutôt que dans le catalogue bootstrap externe.",
    )


# Nombre minimum de biens disponibles en base pour basculer sur le
# catalogue réel plutôt que le catalogue bootstrap externe (cold start)
SEUIL_CATALOGUE_REEL = 5
