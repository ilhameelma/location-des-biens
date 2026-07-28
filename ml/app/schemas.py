"""
Schémas Pydantic du micro-service IA.

Les champs obligatoires correspondent au schéma réel de `bien` (ville,
superficie, prix, nb_pieces). Les champs optionnels (quartier, chambres,
salles_de_bain, meuble) permettent une précision accrue si/quand le schéma
`bien` est étendu plus tard — voir feature_engineering.py pour le détail
des heuristiques appliquées quand ils sont absents.
"""

from typing import Optional

from pydantic import BaseModel, Field


class BienInput(BaseModel):
    ville: str = Field(..., examples=["Casablanca"])
    superficie: float = Field(..., gt=0, examples=[90])
    nb_pieces: Optional[int] = Field(None, ge=1, examples=[3])
    type_bien: Optional[str] = Field(None, examples=["appartement"])

    # Champs de précision optionnels (absents du schéma `bien` actuel)
    quartier: Optional[str] = Field(None, examples=["Maarif"])
    chambres: Optional[float] = Field(None, ge=0)
    salles_de_bain: Optional[float] = Field(None, ge=0)
    meuble: Optional[bool] = Field(None, description="null = inconnu")


# --- Estimation (16a) ---------------------------------------------------

class EstimationRequest(BienInput):
    pass


class EstimationResponse(BaseModel):
    prix_estime_dh: float
    fourchette_basse_dh: float
    fourchette_haute_dh: float
    marge_erreur_dh: float = Field(
        ..., description="MAE du modèle sur le jeu de test (~2679 DH) — sert de demi-largeur de fourchette"
    )


# --- Fraude (16c) ---------------------------------------------------------

class FraudeRequest(BienInput):
    prix_affiche_dh: float = Field(..., gt=0, description="Prix réellement affiché sur l'annonce à vérifier")


class FraudeResponse(BaseModel):
    est_suspect: bool
    prix_attendu_dh: float
    ecart_prix_pct: float
    raison: str
    anomaly_score: float


# --- Recommandation (16b) --------------------------------------------------

class BienCatalogue(BaseModel):
    """Un bien réel du catalogue SmartRent, tel que fourni par le back-end
    (GET /biens) — utilisé pour recommander parmi de VRAIS biens plutôt
    que le catalogue bootstrap externe, dès que le volume le permet."""
    id: str
    titre: Optional[str] = None
    ville: str
    quartier: Optional[str] = None
    prix: float
    superficie: float
    nb_pieces: Optional[int] = None
    chambres: Optional[float] = None
    salles_de_bain: Optional[float] = None
    meuble: Optional[bool] = None


class RecommandationRequest(BaseModel):
    # Mode 1 : biens similaires à une référence
    bien_reference: Optional[BienInput] = None

    # Mode 2 : à partir de critères explicites (pas de bien de référence)
    ville: Optional[str] = None
    budget_dh: Optional[float] = None
    superficie: Optional[float] = None
    nb_pieces: Optional[int] = None
    meuble: Optional[bool] = None

    # Catalogue réel optionnel — si fourni, la recommandation se fait
    # DEDANS (biens réels SmartRent) plutôt que dans le catalogue bootstrap
    # externe (Mubawab/Sarouty) utilisé par défaut en mode cold start
    catalogue: Optional[list[BienCatalogue]] = None

    top_n: int = Field(5, ge=1, le=20)


class RecommandationItem(BaseModel):
    id: Optional[str] = None
    titre: Optional[str] = None
    ville: str
    quartier: Optional[str] = None
    prix_dh: float
    superficie_m2: Optional[float] = None
    score_similarite: float


class RecommandationResponse(BaseModel):
    source_catalogue: str = Field(..., description="'reel' ou 'bootstrap_externe'")
    resultats: list[RecommandationItem]
