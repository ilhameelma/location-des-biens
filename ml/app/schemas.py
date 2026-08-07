"""
Schémas Pydantic du micro-service IA.

Les champs obligatoires correspondent au schéma réel de `bien` (ville,
superficie, prix, nb_pieces). Les champs optionnels (quartier, chambres,
salles_de_bain, meuble) permettent une précision accrue si/quand le schéma
`bien` est étendu plus tard — voir feature_engineering.py pour le détail
des heuristiques appliquées quand ils sont absents.

`type_transaction` route chaque requête vers le jeu de modèles location ou
vente (voir feature_engineering.py / feature_engineering_vente.py) — deux
modèles entraînés séparément, sur des données et des features différentes.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

TypeTransaction = Literal["location", "vente"]


class BienInput(BaseModel):
    ville: str = Field(..., examples=["Casablanca"])
    superficie: float = Field(..., gt=0, examples=[90])
    nb_pieces: Optional[int] = Field(None, ge=1, examples=[3])
    type_bien: Optional[str] = Field(None, examples=["appartement"])
    type_transaction: TypeTransaction = Field(
        "location", description="Détermine le jeu de modèles utilisé (location ou vente)."
    )

    # Champs de précision optionnels (absents du schéma `bien` actuel)
    quartier: Optional[str] = Field(None, examples=["Maarif"])
    chambres: Optional[float] = Field(None, ge=0)
    salles_de_bain: Optional[float] = Field(None, ge=0)
    meuble: Optional[bool] = Field(None, description="null = inconnu — ignoré pour type_transaction='vente'")


# --- Estimation (16a) ---------------------------------------------------

class EstimationRequest(BienInput):
    pass


class EstimationResponse(BaseModel):
    prix_estime_dh: float
    fourchette_basse_dh: float
    fourchette_haute_dh: float
    marge_erreur_dh: float = Field(
        ...,
        description=(
            "Demi-largeur de la fourchette. Location : MAE fixe du modèle "
            "(~2679 DH). Vente : pourcentage du prix estimé (les prix de "
            "vente varient sur un ordre de grandeur bien plus large que les "
            "loyers, une marge fixe en DH n'aurait pas de sens)."
        ),
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
    # Détermine le catalogue bootstrap externe utilisé en mode cold start
    # (location: Mubawab/Sarouty location, vente: Mubawab/Sarouty vente).
    # Ignoré si `catalogue` est fourni (mode catalogue réel) : c'est alors
    # au back-end de garantir que ce catalogue ne mélange pas les deux types
    # de transaction (filtrage sur `bien.type_transaction` avant l'envoi).
    type_transaction: TypeTransaction = "location"

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
