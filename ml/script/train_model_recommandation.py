"""
Modèle de recommandation — Content-Based Filtering (étape 16b)
==================================================================
SmartRent Platform - PFE Data Engineering

Pas d'historique d'interactions utilisateurs disponible pour l'instant
(pas de collaborative filtering possible) → recommandation basée sur les
CARACTÉRISTIQUES des biens (ville, quartier, prix, surface, chambres,
meublé...). Avantage : fonctionne dès le premier bien publié sur la
plateforme, pas besoin d'attendre du volume d'interactions.

DEUX MODES DE RECOMMANDATION
-----------------------------
1. recommend_similar_to(listing_index)
   "Vous avez consulté ce bien, voici des biens similaires"
   → cas d'usage classique fiche annonce ("biens similaires")

2. recommend_from_preferences(preferences_dict)
   "Voici les biens qui correspondent le mieux à vos critères"
   → cas d'usage recherche/onboarding (aucun bien consulté encore)

MÉTHODE
-------
Chaque bien est représenté par un vecteur de features (numériques
standardisées + catégorielles déjà en one-hot). La similarité entre deux
biens = similarité cosinus entre leurs vecteurs. Pas d'entraînement au
sens strict (pas de cible à prédire) — le "modèle" est le calcul de ce
vecteur + la matrice de similarité pré-calculée.

SORTIES
-------
- recommender_artifacts.joblib   (scaler + matrice de features + catalogue
                                    de biens — à charger dans le
                                    micro-service IA pour servir les
                                    recommandations en production)
- rapport_recommandation.md

USAGE
-----
python train_model_recommandation.py
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

DATA_PATH = "dataset_locations_final.csv"

NUMERIC_FEATURES = ["prix_dh", "surface_m2", "chambres", "salles_de_bain", "quartier_prix_estime"]
CATEGORICAL_FEATURES = [
    "ville_Casablanca", "ville_Rabat", "ville_Marrakech", "ville_Tanger",
    "ville_Salé", "ville_Bouskoura", "ville_Dar Bouazza", "ville_Autre",
    "meuble_meuble", "meuble_non_meuble", "meuble_inconnu",
]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

DISPLAY_COLUMNS = ["titre", "ville", "quartier", "prix_dh", "surface_m2", "chambres"]


class PropertyRecommender:
    """Recommandeur content-based. Reproduit la logique qui tournera dans
    le micro-service IA (mêmes features que le modèle d'estimation, moins
    prix_dh en entrée puisqu'il fait ici partie de la similarité elle-même)."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.catalog: pd.DataFrame | None = None
        self.feature_matrix: np.ndarray | None = None
        self.similarity_matrix: np.ndarray | None = None

    def fit(self, df: pd.DataFrame) -> "PropertyRecommender":
        self.catalog = df.reset_index(drop=True)

        numeric = self.catalog[NUMERIC_FEATURES].astype(float)
        numeric_scaled = self.scaler.fit_transform(numeric)

        categorical = self.catalog[CATEGORICAL_FEATURES].astype(int).to_numpy()

        self.feature_matrix = np.hstack([numeric_scaled, categorical])
        self.similarity_matrix = cosine_similarity(self.feature_matrix)
        return self

    def recommend_similar_to(self, index: int, top_n: int = 5) -> pd.DataFrame:
        """Biens les plus similaires à celui d'index donné (hors lui-même)."""
        scores = self.similarity_matrix[index]
        order = np.argsort(scores)[::-1]
        order = [i for i in order if i != index][:top_n]
        result = self.catalog.iloc[order][DISPLAY_COLUMNS].copy()
        result["score_similarite"] = scores[order]
        return result

    def recommend_from_preferences(self, preferences: dict, top_n: int = 5) -> pd.DataFrame:
        """Recommandation à partir de critères explicites (pas de bien de
        référence) — ex. un nouvel utilisateur qui filtre sa recherche.

        preferences attend les clés :
          ville (str, ex. 'Casablanca'), budget_dh (float),
          surface_m2 (float), chambres (int), salles_de_bain (int),
          meuble (bool ou None si indifférent)
        """
        numeric_query = pd.DataFrame([[
            preferences.get("budget_dh", self.catalog["prix_dh"].median()),
            preferences.get("surface_m2", self.catalog["surface_m2"].median()),
            preferences.get("chambres", self.catalog["chambres"].median()),
            preferences.get("salles_de_bain", self.catalog["salles_de_bain"].median()),
            self._quartier_prix_estime_for_ville(preferences.get("ville")),
        ]], columns=NUMERIC_FEATURES)
        numeric_query_scaled = self.scaler.transform(numeric_query)

        ville_cols = [c for c in CATEGORICAL_FEATURES if c.startswith("ville_")]
        ville_query = np.zeros((1, len(ville_cols)))
        ville_col_name = f"ville_{preferences.get('ville', 'Autre')}"
        if ville_col_name in ville_cols:
            ville_query[0, ville_cols.index(ville_col_name)] = 1
        else:
            ville_query[0, ville_cols.index("ville_Autre")] = 1

        meuble = preferences.get("meuble")
        meuble_query = np.array([[
            1 if meuble is True else 0,
            1 if meuble is False else 0,
            1 if meuble is None else 0,
        ]])

        query_vector = np.hstack([numeric_query_scaled, ville_query, meuble_query])
        scores = cosine_similarity(query_vector, self.feature_matrix)[0]
        order = np.argsort(scores)[::-1][:top_n]

        result = self.catalog.iloc[order][DISPLAY_COLUMNS].copy()
        result["score_similarite"] = scores[order]
        return result

    def _quartier_prix_estime_for_ville(self, ville: str | None) -> float:
        if ville is None:
            return self.catalog["quartier_prix_estime"].median()
        subset = self.catalog[self.catalog["ville"] == ville]
        if len(subset) == 0:
            return self.catalog["quartier_prix_estime"].median()
        return subset["quartier_prix_estime"].median()


def main():
    df = pd.read_csv(DATA_PATH)

    recommender = PropertyRecommender()
    recommender.fit(df)

    print(f"Catalogue chargé : {len(df)} biens, {len(ALL_FEATURES)} features")

    # --- Démo 1 : biens similaires à une annonce donnée ---
    demo_index = df.sample(1, random_state=7).index[0]
    reference = df.iloc[demo_index][DISPLAY_COLUMNS]
    print("\n=== DEMO 1 — Biens similaires à une annonce consultée ===")
    print("Annonce de référence :")
    print(reference.to_string())

    similar = recommender.recommend_similar_to(demo_index, top_n=5)
    print("\nBiens similaires recommandés :")
    print(similar.to_string(index=False))

    # --- Démo 2 : recommandation à partir de préférences (pas de bien consulté) ---
    print("\n=== DEMO 2 — Recommandation à partir de critères de recherche ===")
    preferences = {
        "ville": "Casablanca",
        "budget_dh": 10000,
        "surface_m2": 90,
        "chambres": 2,
        "salles_de_bain": 1,
        "meuble": True,
    }
    print("Critères recherchés :", preferences)

    recs = recommender.recommend_from_preferences(preferences, top_n=5)
    print("\nBiens recommandés :")
    print(recs.to_string(index=False))

    # --- Sauvegarde ---
    joblib.dump(recommender, "recommender_artifacts.joblib")
    print("\nRecommandeur sauvegardé : recommender_artifacts.joblib")

    report = f"""# Rapport — modèle de recommandation (content-based, v1)

## Approche
Content-based filtering : chaque bien est représenté par un vecteur de
caractéristiques (prix, surface, chambres, salles de bain, quartier
[via `quartier_prix_estime`], ville, meublé), standardisées puis comparées
par similarité cosinus. Aucun historique d'interaction requis — fonctionne
dès le premier bien publié.

## Catalogue
- {len(df)} biens (fusion Mubawab + Sarouty, même base que le modèle
  d'estimation)
- Features utilisées : {', '.join(ALL_FEATURES)}

## Deux modes servis
1. **`recommend_similar_to(index)`** — "biens similaires" sur une fiche
   annonce (cas d'usage classique)
2. **`recommend_from_preferences(dict)`** — recommandation à partir de
   critères de recherche explicites, sans bien de référence (utile pour un
   nouvel utilisateur sans historique)

## Exemple — Démo 1 (biens similaires)
Référence :
{df.iloc[df.sample(1, random_state=7).index[0]][DISPLAY_COLUMNS].to_string()}

Recommandations :
{similar.to_string(index=False)}

## Exemple — Démo 2 (à partir de préférences)
Critères : {preferences}

Recommandations :
{recs.to_string(index=False)}

## Limites connues
- Purement content-based : ne capture pas les préférences comportementales
  réelles (ex. deux utilisateurs qui aiment les mêmes biens pour des
  raisons non capturées par les features) — c'est le rôle du collaborative
  filtering, impossible tant que `dw.fait_reservation`/avis n'ont pas
  assez de volume
- Le vecteur ne contient pas encore : équipements (parking, piscine,
  ascenseur...), état du bien, étage — comme pour le modèle d'estimation,
  ces informations existent en texte libre dans les descriptions mais ne
  sont pas encore extraites

## Prochaine étape
1. Exposer via `/predict/recommandation` dans le micro-service IA
2. Une fois `dw.fait_reservation` et `avis` alimentés par du vrai trafic,
   ajouter une composante collaborative filtering en complément
   (approche hybride) plutôt que de tout remplacer d'un coup
"""
    with open("rapport_recommandation.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Rapport sauvegardé : rapport_recommandation.md")


if __name__ == "__main__":
    main()
