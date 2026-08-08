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


# ---------------------------------------------------------------------------
# PropertyRecommenderVentes — copie exacte de la définition utilisée dans
# ml/script/recomandation_prix_vente.ipynb. Même raison d'être que
# PropertyRecommender ci-dessus : nécessaire pour dépickler
# recommender_ventes_artifacts.joblib (voir model_loader.py pour l'alias
# de compatibilité __main__).
#
# Contrairement à PropertyRecommender (location), les colonnes numériques et
# catégorielles ne sont pas des constantes figées ici : elles sont détectées
# dynamiquement à partir du catalogue au moment de fit() (voir
# self.numeric_features / self.categorical_features, restaurés tels quels
# au dépicklage). Les colonnes catégorielles "ville_..." conservent les
# espaces d'origine du CSV (ex. "ville_Dar Bouazza") — cohérent avec
# modele_fraude_vente.joblib, mais PAS avec modele_estimation_vente.joblib
# qui attend des underscores (voir feature_engineering_vente.py).
# ---------------------------------------------------------------------------


def _detect_features_vente(df: pd.DataFrame) -> tuple[list, list]:
    exclude = {
        "prix_dh", "source", "titre", "ville", "quartier",
        "listing_id", "url", "description", "equipements",
    }
    all_features = [c for c in df.columns if c not in exclude]
    cat_features = [c for c in all_features if c.startswith("ville_")]
    num_features = [c for c in all_features if c not in cat_features]
    return num_features, cat_features


VENTE_DISPLAY_COLUMNS = ["titre", "ville", "quartier", "prix_dh", "surface_m2", "chambres"]


class PropertyRecommenderVentes:
    """Recommandeur content-based pour les annonces de VENTE."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.catalog: pd.DataFrame | None = None
        self.feature_matrix: np.ndarray | None = None
        self.similarity_matrix: np.ndarray | None = None
        self.numeric_features: list = []
        self.categorical_features: list = []

    def fit(self, df: pd.DataFrame) -> "PropertyRecommenderVentes":
        self.catalog = df.reset_index(drop=True)
        self.numeric_features, self.categorical_features = _detect_features_vente(self.catalog)

        numeric = self.catalog[self.numeric_features].astype(float)
        numeric_scaled = self.scaler.fit_transform(numeric)

        if self.categorical_features:
            categorical = self.catalog[self.categorical_features].astype(int).to_numpy()
            self.feature_matrix = np.hstack([numeric_scaled, categorical])
        else:
            self.feature_matrix = numeric_scaled

        self.similarity_matrix = cosine_similarity(self.feature_matrix)
        return self

    def recommend_similar_to(self, index: int, top_n: int = 5) -> pd.DataFrame:
        scores = self.similarity_matrix[index]
        order = np.argsort(scores)[::-1]
        order = [i for i in order if i != index][:top_n]
        result = self.catalog.iloc[order][VENTE_DISPLAY_COLUMNS].copy()
        result["score_similarite"] = scores[order]
        return result

    def recommend_from_preferences(self, preferences: dict, top_n: int = 5) -> pd.DataFrame:
        query_values = {}
        for col in self.numeric_features:
            if col == "prix_dh":
                query_values[col] = preferences.get("budget_dh", self.catalog["prix_dh"].median())
            elif col == "surface_m2":
                query_values[col] = preferences.get("surface_m2", self.catalog["surface_m2"].median())
            elif col == "chambres":
                query_values[col] = preferences.get("chambres", self.catalog["chambres"].median())
            elif col == "salles_de_bain":
                query_values[col] = preferences.get("salles_de_bain", self.catalog["salles_de_bain"].median())
            elif col == "quartier_prix_estime":
                query_values[col] = self._quartier_prix_estime_for_ville(preferences.get("ville"))
            elif col.endswith("_imputed"):
                query_values[col] = 0
            else:
                query_values[col] = self.catalog[col].median()

        numeric_query = pd.DataFrame([query_values[col] for col in self.numeric_features]).T
        numeric_query.columns = self.numeric_features
        numeric_query_scaled = self.scaler.transform(numeric_query)

        if self.categorical_features:
            ville_query = np.zeros((1, len(self.categorical_features)))
            ville_col_name = "ville_{}".format(preferences.get("ville", "Autre"))
            if ville_col_name in self.categorical_features:
                ville_query[0, self.categorical_features.index(ville_col_name)] = 1
            else:
                autre_col = "ville_Autre"
                if autre_col in self.categorical_features:
                    ville_query[0, self.categorical_features.index(autre_col)] = 1
            query_vector = np.hstack([numeric_query_scaled, ville_query])
        else:
            query_vector = numeric_query_scaled

        scores = cosine_similarity(query_vector, self.feature_matrix)[0]
        order = np.argsort(scores)[::-1][:top_n]

        result = self.catalog.iloc[order][VENTE_DISPLAY_COLUMNS].copy()
        result["score_similarite"] = scores[order]
        return result

    def _quartier_prix_estime_for_ville(self, ville: str | None) -> float:
        if ville is None:
            return self.catalog["quartier_prix_estime"].median()
        subset = self.catalog[self.catalog["ville"] == ville]
        if len(subset) == 0:
            return self.catalog["quartier_prix_estime"].median()
        return subset["quartier_prix_estime"].median()
