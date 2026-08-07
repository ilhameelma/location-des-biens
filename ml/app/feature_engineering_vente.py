"""
Feature engineering — annonces de VENTE
===========================================================================
Miroir de feature_engineering.py (location), mais pour les 3 modèles VENTE
(modele_estimation_vente.joblib, modele_fraude_vente.joblib,
recommender_ventes_artifacts.joblib) — entraînés séparément sur un dataset
distinct (scraping Mubawab + Sarouty, annonces de VENTE uniquement), avec un
schéma de features différent de celui des modèles location :

- Pas de colonne "meublé" (peu pertinente pour une vente).
- Des colonnes `<champ>_imputed` explicites (le modèle a appris à pondérer
  différemment une valeur réelle vs devinée), alors que le modèle location
  ne trace pas cette information.
- Une liste de villes plus large (18 villes + "Autre" + "Inconnu").

PIÈGE DE NOMMAGE À CONNAÎTRE (hérité des notebooks d'entraînement d'origine,
reconstruit ici à l'identique — volontaire, pas une erreur) :
- Le modèle de PRIX (LightGBM) a été entraîné après un nettoyage des noms de
  colonnes (espaces -> underscore, obligatoire pour XGBoost/LightGBM) :
  "ville_Dar Bouazza" -> "ville_Dar_Bouazza".
- Le modèle de FRAUDE (IsolationForest, scikit-learn) a, lui, été entraîné
  directement sur le CSV brut, SANS ce nettoyage : il attend "ville_Dar
  Bouazza" (avec l'espace d'origine).
Les deux modèles n'attendent donc PAS exactement les mêmes noms de colonnes
pour les 3 villes composées ("Dar Bouazza", "El Jadida", "El Mansouria") —
d'où les deux listes de colonnes ci-dessous (VENTE_VILLE_COLONNES_PRIX vs
VENTE_VILLE_COLONNES_FRAUDE) plutôt qu'une seule.
"""

import pandas as pd

# Ordre EXACT attendu par modele_estimation_vente.joblib (LightGBM) —
# vérifié via model.feature_name_. Ne JAMAIS réordonner sans réentraîner.
PRICE_MODEL_FEATURES_VENTE = [
    "chambres", "chambres_imputed", "quartier_prix_estime",
    "salles_de_bain", "salles_de_bain_imputed",
    "surface_m2", "surface_m2_imputed",
    "ville_Agadir", "ville_Autre", "ville_Bouskoura", "ville_Casablanca",
    "ville_Dar_Bouazza", "ville_El_Jadida", "ville_El_Mansouria", "ville_Fès",
    "ville_Inconnu", "ville_Kénitra", "ville_Marrakech", "ville_Martil",
    "ville_Mohammedia", "ville_Médiouna", "ville_Nouaceur", "ville_Rabat",
    "ville_Salé", "ville_Skhirat", "ville_Tanger", "ville_Temara", "ville_Zenata",
]

# Villes "affichables" (telles que renvoyées par normalize_ville_vente) —
# sert à construire les deux jeux de colonnes one-hot ci-dessous.
KNOWN_VILLES_VENTE = [
    "Agadir", "Bouskoura", "Casablanca", "Dar Bouazza", "El Jadida",
    "El Mansouria", "Fès", "Kénitra", "Marrakech", "Martil", "Mohammedia",
    "Médiouna", "Nouaceur", "Rabat", "Salé", "Skhirat", "Tanger", "Temara",
    "Zenata",
]
_TOUTES_CATEGORIES_VILLE = KNOWN_VILLES_VENTE + ["Autre", "Inconnu"]

# Colonnes non liées à la ville, communes aux deux modèles (prix + fraude).
_FEATURES_NUMERIQUES_COMMUNES = [
    "chambres", "chambres_imputed", "quartier_prix_estime",
    "salles_de_bain", "salles_de_bain_imputed",
    "surface_m2", "surface_m2_imputed",
]


def normalize_ville_vente(ville: str) -> str:
    """Ramène une ville à l'une des catégories connues, 'Autre' si non
    reconnue, 'Inconnu' si vide (reflète le sens de la colonne "Inconnu"
    présente dans le dataset d'entraînement — annonces sans ville identifiée
    lors du scraping, distinct de "Autre" = ville connue mais hors top-liste)."""
    ville_clean = (ville or "").strip()
    if not ville_clean:
        return "Inconnu"
    ville_title = ville_clean.title()
    for v in KNOWN_VILLES_VENTE:
        if v.title() == ville_title:
            return v
    return "Autre"


class MarketReferenceVente:
    """Statistiques de marché VENTE, calculées une fois au démarrage à partir
    du catalogue du recommandeur vente (recommender_ventes_artifacts.joblib)
    — sert à combler les champs absents du schéma `bien` réel (chambres,
    salles_de_bain, quartier_prix_estime), comme MarketReference (location)."""

    def __init__(self, catalog: pd.DataFrame):
        self.ville_median_prix = catalog.groupby("ville")["prix_dh"].median()
        self.ville_median_chambres = catalog.groupby("ville")["chambres"].median()
        self.ville_median_sdb = catalog.groupby("ville")["salles_de_bain"].median()
        self.global_median_prix = catalog["prix_dh"].median()
        self.global_median_chambres = catalog["chambres"].median()
        self.global_median_sdb = catalog["salles_de_bain"].median()

        if "quartier" in catalog.columns and "quartier_prix_estime" in catalog.columns:
            self.quartier_prix = (
                catalog.groupby(["ville", "quartier"])["quartier_prix_estime"].median()
            )
        else:
            self.quartier_prix = pd.Series(dtype=float)

    def prix_reference_ville(self, ville: str) -> float:
        return self.ville_median_prix.get(ville, self.global_median_prix)

    def chambres_reference_ville(self, ville: str) -> float:
        return self.ville_median_chambres.get(ville, self.global_median_chambres)

    def salles_de_bain_reference_ville(self, ville: str) -> float:
        return self.ville_median_sdb.get(ville, self.global_median_sdb)

    def quartier_prix_estime(self, ville: str, quartier: str | None) -> float:
        if quartier and (ville, quartier) in self.quartier_prix.index:
            return float(self.quartier_prix.loc[(ville, quartier)])
        return self.prix_reference_ville(ville)


def _valeurs_communes(bien: dict, market: MarketReferenceVente) -> tuple[dict, str]:
    """Construit les 7 valeurs numériques communes aux modèles prix + fraude,
    et la ville normalisée. Mêmes heuristiques que feature_engineering.py
    (location), + un flag *_imputed à 1 chaque fois qu'une heuristique a dû
    être utilisée (le modèle vente a été entraîné avec ce signal)."""
    ville_norm = normalize_ville_vente(bien.get("ville", ""))

    surface = bien.get("superficie") or bien.get("surface_m2")
    if surface is None:
        raise ValueError("Le champ 'superficie' (m²) est requis pour l'estimation")

    chambres = bien.get("chambres")
    chambres_imputee = chambres is None
    if chambres is None:
        chambres = bien.get("nb_pieces")
        chambres_imputee = chambres is None  # toujours True si nb_pieces aussi absent
    if chambres is None:
        chambres = market.chambres_reference_ville(ville_norm)
        chambres_imputee = True

    salles_de_bain = bien.get("salles_de_bain")
    sdb_imputee = salles_de_bain is None
    if salles_de_bain is None:
        # Même règle empirique que le modèle location : logement de 2 pièces
        # ou moins -> 1 salle de bain, sinon 2.
        salles_de_bain = 1 if chambres <= 2 else 2

    quartier = bien.get("quartier")
    quartier_prix_estime = market.quartier_prix_estime(ville_norm, quartier)

    valeurs = {
        "surface_m2": float(surface),
        "surface_m2_imputed": 0,  # superficie toujours fournie (champ requis)
        "chambres": float(chambres),
        "chambres_imputed": int(chambres_imputee),
        "salles_de_bain": float(salles_de_bain),
        "salles_de_bain_imputed": int(sdb_imputee),
        "quartier_prix_estime": float(quartier_prix_estime),
    }
    return valeurs, ville_norm


def build_price_features_vente(bien: dict, market: MarketReferenceVente) -> pd.DataFrame:
    """Vecteur de features pour modele_estimation_vente.joblib (LightGBM) —
    noms de colonnes ville "nettoyés" (underscore)."""
    valeurs, ville_norm = _valeurs_communes(bien, market)
    row = dict(valeurs)
    for v in _TOUTES_CATEGORIES_VILLE:
        row[f"ville_{v.replace(' ', '_')}"] = 1 if v == ville_norm else 0
    return pd.DataFrame([row])[PRICE_MODEL_FEATURES_VENTE]


def build_fraud_row_vente(bien: dict, market: MarketReferenceVente) -> tuple[dict, str]:
    """Valeurs numériques + ville normalisée pour le modèle de fraude — les
    colonnes ville "brutes" (avec espaces) sont ajoutées par le router
    fraude.py au moment de reconstruire le DataFrame dans l'ordre exact de
    `models.fraud_features_vente` (voir routers/fraude.py)."""
    return _valeurs_communes(bien, market)
