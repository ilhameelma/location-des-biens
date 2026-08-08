"""
Mapping schéma réel (`bien` SmartRent) -> features des modèles entraînés
===========================================================================
Le schéma transactionnel actuel de `bien` (voir backend/app/models.py) ne
contient que : ville, superficie, prix, nb_pieces, type_bien, adresse.

Les modèles ont été entraînés sur un schéma plus détaillé (scraping Mubawab
+ Sarouty) avec : chambres, salles_de_bain, quartier, meublé — des
attributs qui n'existent pas encore dans `bien`.

CHOIX ASSUMÉ : plutôt que de bloquer les 3 endpoints IA tant que le schéma
`bien` n'est pas étendu, ce module comble les champs manquants avec des
heuristiques explicites et documentées ci-dessous. Les endpoints acceptent
aussi ces champs en optionnel : s'ils sont fournis (une fois le schéma
étendu), l'heuristique est simplement ignorée.

HEURISTIQUES (à documenter dans le rapport de PFE comme limite connue) :
- chambres := nb_pieces si fourni, sinon médiane connue pour la ville
- salles_de_bain := 1 si chambres <= 2, sinon 2 (règle empirique simple,
  cohérente avec le marché marocain observé dans le dataset d'entraînement)
- quartier_prix_estime := prix médian du quartier si `quartier` fourni et
  connu du catalogue de référence, sinon prix médian de la ville, sinon
  médiane globale (même logique de repli qu'à l'entraînement)
- meuble := "inconnu" si non fourni (catégorie neutre, pas de biais)
"""

import pandas as pd

# Doit rester identique à FEATURE_COLUMNS / PRICE_MODEL_FEATURES des
# scripts d'entraînement (ml/script/train_model_estimation.py et
# train_model_fraude.py) — toute divergence casserait model.predict().
PRICE_MODEL_FEATURES = [
    "surface_m2", "chambres", "salles_de_bain", "quartier_prix_estime",
    "ville_Casablanca", "ville_Rabat", "ville_Marrakech", "ville_Tanger",
    "ville_Salé", "ville_Bouskoura", "ville_Dar Bouazza", "ville_Autre",
    "meuble_meuble", "meuble_non_meuble", "meuble_inconnu",
]

KNOWN_VILLES = [
    "Casablanca", "Rabat", "Marrakech", "Tanger", "Salé", "Bouskoura", "Dar Bouazza",
]


class MarketReference:
    """Statistiques de marché calculées une fois au démarrage à partir du
    catalogue du recommandeur (bootstrap Mubawab/Sarouty) — sert de table
    de référence pour combler les champs absents du schéma `bien` réel."""

    def __init__(self, catalog: pd.DataFrame):
        self.ville_median_prix = catalog.groupby("ville")["prix_dh"].median()
        self.ville_median_chambres = catalog.groupby("ville")["chambres"].median()
        self.global_median_prix = catalog["prix_dh"].median()
        self.global_median_chambres = catalog["chambres"].median()

        if "quartier" in catalog.columns and "quartier_prix_estime" in catalog.columns:
            self.quartier_prix = (
                catalog.groupby(["ville", "quartier"])["quartier_prix_estime"]
                .median()
            )
        else:
            self.quartier_prix = pd.Series(dtype=float)

    def prix_reference_ville(self, ville: str) -> float:
        return self.ville_median_prix.get(ville, self.global_median_prix)

    def chambres_reference_ville(self, ville: str) -> float:
        return self.ville_median_chambres.get(ville, self.global_median_chambres)

    def quartier_prix_estime(self, ville: str, quartier: str | None) -> float:
        if quartier and (ville, quartier) in self.quartier_prix.index:
            return float(self.quartier_prix.loc[(ville, quartier)])
        return self.prix_reference_ville(ville)


def normalize_ville(ville: str) -> str:
    """Ramène une ville à l'une des colonnes one-hot connues, 'Autre' sinon."""
    ville_clean = (ville or "").strip().title()
    return ville_clean if ville_clean in KNOWN_VILLES else "Autre"


def build_price_features(bien: dict, market: MarketReference) -> pd.DataFrame:
    """Construit le vecteur de features pour modele_estimation_loyer /
    modele_fraude à partir d'un bien au format réel (+ champs optionnels
    de précision : quartier, chambres, salles_de_bain, meuble)."""
    ville = bien.get("ville", "")
    ville_norm = normalize_ville(ville)

    surface = bien.get("superficie") or bien.get("surface_m2")
    if surface is None:
        raise ValueError("Le champ 'superficie' (m²) est requis pour l'estimation")

    chambres = bien.get("chambres")
    if chambres is None:
        chambres = bien.get("nb_pieces")
    if chambres is None:
        chambres = market.chambres_reference_ville(ville)

    salles_de_bain = bien.get("salles_de_bain")
    if salles_de_bain is None:
        salles_de_bain = 1 if chambres <= 2 else 2

    quartier = bien.get("quartier")
    quartier_prix_estime = market.quartier_prix_estime(ville_norm, quartier)

    meuble = bien.get("meuble")  # True / False / None

    row = {
        "surface_m2": float(surface),
        "chambres": float(chambres),
        "salles_de_bain": float(salles_de_bain),
        "quartier_prix_estime": float(quartier_prix_estime),
        "ville_Casablanca": 0, "ville_Rabat": 0, "ville_Marrakech": 0,
        "ville_Tanger": 0, "ville_Salé": 0, "ville_Bouskoura": 0,
        "ville_Dar Bouazza": 0, "ville_Autre": 0,
        "meuble_meuble": 1 if meuble is True else 0,
        "meuble_non_meuble": 1 if meuble is False else 0,
        "meuble_inconnu": 1 if meuble is None else 0,
    }
    row[f"ville_{ville_norm}"] = 1

    return pd.DataFrame([row])[PRICE_MODEL_FEATURES]
