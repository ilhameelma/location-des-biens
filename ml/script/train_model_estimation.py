"""
Entraînement du modèle d'estimation de loyer (étape 16a) — v1
=================================================================
SmartRent Platform - PFE Data Engineering

Entraîne et compare deux modèles sur train.csv / test.csv (produits par
prepare_dataset_estimation.py) :
  - Régression linéaire  : baseline simple, sert de référence minimale
  - RandomForestRegressor : modèle principal, capture les non-linéarités
    (ex. l'effet de la surface n'est pas le même à 40m² qu'à 300m²)

Un modèle n'est utile que s'il bat clairement la baseline — sinon la
complexité supplémentaire de RandomForest n'est pas justifiée.

SORTIES
-------
- modele_estimation_loyer.joblib   (le modèle RandomForest entraîné,
                                      rechargeable avec joblib.load())
- rapport_entrainement.md          (métriques, importance des features,
                                      à coller dans le rapport de PFE)

USAGE
-----
python train_model_estimation.py
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Features d'entrée du modèle — cf. discussion : ville et meuble en one-hot,
# quartier via target encoding (quartier_prix_estime), pas de texte brut.
FEATURE_COLUMNS = [
    "surface_m2", "chambres", "salles_de_bain", "quartier_prix_estime",
    "ville_Casablanca", "ville_Rabat", "ville_Marrakech", "ville_Tanger",
    "ville_Salé", "ville_Bouskoura", "ville_Dar Bouazza", "ville_Autre",
    "meuble_meuble", "meuble_non_meuble", "meuble_inconnu",
]
TARGET_COLUMN = "prix_dh"


def load_xy(path: str):
    df = pd.read_csv(path)
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans {path} : {missing}")
    X = df[FEATURE_COLUMNS].copy()
    # Sécurité : les colonnes one-hot doivent être 0/1 numériques (pas bool)
    for col in X.columns:
        if X[col].dtype == bool:
            X[col] = X[col].astype(int)
    y = df[TARGET_COLUMN]
    return X, y


def evaluate(model, X_test, y_test, name: str) -> dict:
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

    print(f"\n--- {name} ---")
    print(f"MAE  : {mae:,.0f} DH  (erreur absolue moyenne)")
    print(f"RMSE : {rmse:,.0f} DH  (pénalise plus les grosses erreurs)")
    print(f"MAPE : {mape:.1f}%    (erreur relative moyenne)")
    print(f"R²   : {r2:.3f}      (part de variance expliquée, 1.0 = parfait)")

    return {"nom": name, "mae": mae, "rmse": rmse, "mape": mape, "r2": r2}


def main():
    X_train, y_train = load_xy("train.csv")
    X_test, y_test = load_xy("test.csv")

    print(f"Train : {len(X_train)} lignes | Test : {len(X_test)} lignes")
    print(f"Features utilisées ({len(FEATURE_COLUMNS)}) : {FEATURE_COLUMNS}")

    # --- Baseline : régression linéaire ---
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_metrics = evaluate(lr, X_test, y_test, "Régression linéaire (baseline)")

    # --- Modèle principal : RandomForest ---
    rf = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_metrics = evaluate(rf, X_test, y_test, "RandomForest")

    # --- Importance des features (RandomForest) ---
    importances = pd.Series(rf.feature_importances_, index=FEATURE_COLUMNS)
    importances = importances.sort_values(ascending=False)
    print("\n--- Importance des features (RandomForest) ---")
    print(importances.to_string())

    # --- Sauvegarde du modèle ---
    joblib.dump(rf, "modele_estimation_loyer.joblib")
    print("\nModèle sauvegardé : modele_estimation_loyer.joblib")

    # --- Rapport ---
    verdict = (
        "Le RandomForest bat clairement la baseline — capture bien les "
        "non-linéarités du marché (effet ville/quartier, surface, etc.)."
        if rf_metrics["r2"] > lr_metrics["r2"] + 0.02
        else "Le RandomForest n'apporte pas de gain net vs la régression "
             "linéaire — à investiguer (features insuffisantes ? volume "
             "encore trop faible ? bruit dans les annonces scrapées ?)."
    )

    report = f"""# Rapport d'entraînement — modèle d'estimation de loyer (v1)

## Données
- Train : {len(X_train)} lignes
- Test  : {len(X_test)} lignes
- Features ({len(FEATURE_COLUMNS)}) : {', '.join(FEATURE_COLUMNS)}

## Résultats

| Modèle | MAE (DH) | RMSE (DH) | MAPE | R² |
|---|---|---|---|---|
| Régression linéaire | {lr_metrics['mae']:,.0f} | {lr_metrics['rmse']:,.0f} | {lr_metrics['mape']:.1f}% | {lr_metrics['r2']:.3f} |
| RandomForest | {rf_metrics['mae']:,.0f} | {rf_metrics['rmse']:,.0f} | {rf_metrics['mape']:.1f}% | {rf_metrics['r2']:.3f} |

**Verdict** : {verdict}

## Importance des features (RandomForest)
{importances.to_string()}

## Lecture des métriques (pour le rapport de PFE)
- **MAE** : en moyenne, la prédiction se trompe de X DH par rapport au loyer réel
- **RMSE** : plus sensible aux grosses erreurs que le MAE (utile pour repérer
  les cas extrêmes mal prédits, ex. villas de luxe)
- **MAPE** : erreur en %, plus parlant pour comparer entre petits et gros loyers
- **R²** : proportion de la variation des loyers expliquée par le modèle
  (0 = pas mieux que prédire la moyenne à chaque fois, 1 = parfait)

## Limites connues à mentionner
- Dataset encore petit (~2000 annonces) pour un modèle de production
- {round(100*X_train['surface_m2'].isna().sum()/len(X_train)) if X_train['surface_m2'].isna().any() else 0}% de valeurs imputées sur certaines features (voir rapport_preparation.md)
- Données scrapées à un instant T (juillet 2026) — pas de saisonnalité captée
- Prochaine itération : ré-entraîner sur les données réelles de la plateforme
  (`dw.fait_bien`) une fois le volume suffisant (stratégie cold start)

## Prochaine étape
Exposer ce modèle via une API FastAPI (`/predict/estimation`) dans le
micro-service IA, appelée par le back-end principal lors de la publication
d'une annonce (suggestion de prix au propriétaire).
"""
    with open("rapport_entrainement.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\nRapport sauvegardé : rapport_entrainement.md")


if __name__ == "__main__":
    main()
