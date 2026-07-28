"""
Classe PropertyRecommender — copie exacte de la définition utilisée dans
ml/train_model_recommandation.py, dans un module réellement importable.

Nécessaire pour dépickler recommender_artifacts.joblib : joblib/pickle
retrouve la classe par son chemin de module d'origine (`__main__` quand le
script d'entraînement est lancé directement), qui n'existe plus une fois le
service démarré ailleurs. Voir model_loader.py pour l'alias de compatibilité
qui fait le lien.
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

NUMERIC_FEATURES = ["prix_dh", "surface_m2", "chambres", "salles_de_bain", "quartier_prix_estime"]
CATEGORICAL_FEATURES = [
    "ville_Casablanca", "ville_Rabat", "ville_Marrakech", "ville_Tanger",
    "ville_Salé", "ville_Bouskoura", "ville_Dar Bouazza", "ville_Autre",
    "meuble_meuble", "meuble_non_meuble", "meuble_inconnu",
]
DISPLAY_COLUMNS = ["titre", "ville", "quartier", "prix_dh", "surface_m2", "chambres"]


class PropertyRecommender:
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
        scores = self.similarity_matrix[index]
        order = np.argsort(scores)[::-1]
        order = [i for i in order if i != index][:top_n]
        result = self.catalog.iloc[order][DISPLAY_COLUMNS].copy()
        result["score_similarite"] = scores[order]
        return result

    def recommend_from_preferences(self, preferences: dict, top_n: int = 5) -> pd.DataFrame:
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

    def _quartier_prix_estime_for_ville(self, ville):
        if ville is None:
            return self.catalog["quartier_prix_estime"].median()
        subset = self.catalog[self.catalog["ville"] == ville]
        if len(subset) == 0:
            return self.catalog["quartier_prix_estime"].median()
        return subset["quartier_prix_estime"].median()
