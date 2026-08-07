# Rapport de préparation — Dataset Estimation des Prix de Vente

## 1. Volumétrie
- Total après fusion et dédoublonnage : **2470** annonces
  - Mubawab : 1689 (68.4%)
  - Sarouty : 781 (31.6%)
- Ville inconnue (quartier Sarouty non mappé) : 102 (4%)

## 2. Statistiques des prix de vente
- Moyenne : 1,950,247 DH
- Médiane : 1,490,000 DH
- Min : 101,200 DH
- Max : 35,000,000 DH
- Écart-type : 1,889,584 DH

## 3. Imputation des valeurs manquantes
Stratégie hiérarchique : médiane par ville, puis médiane globale en dernier recours.
Colonnes `*_imputed` (booléen) ajoutées pour tracer quelles valeurs sont réelles vs imputées.

| Colonne | % imputé |
|---------|----------|
| surface_m2 | 27.9% |
| chambres | 39.6% |
| salles_de_bain | 53.2% |

## 4. Répartition par ville (top 10)
ville
Casablanca     1086
Marrakech       470
Tanger          147
Rabat           131
Inconnu         102
Zenata           53
Agadir           51
Bouskoura        48
Dar Bouazza      45
Kénitra          42

## 5. Encodage des variables
- **Quartier** : Target encoding vers le prix médian, lissé par ville (smoothing=10).
  Calculé UNIQUEMENT sur le train pour éviter toute fuite de la cible.
- **Ville** : One-hot encoding.
- **Source** : Colonne "source" (mubawab/sarouty) conservée pour audit.

## 6. Split train/test
- Train : 1976 lignes (80.0%)
- Test  : 494 lignes (20.0%)
- random_state=42, split 80/20 effectué AVANT le target encoding du quartier

## 7. Prochaine étape
Entraînement d'un modèle de régression (RandomForest ou XGBoost) sur `train_ventes.csv`,
target = `prix_dh`, évaluation sur `test_ventes.csv` (MAE, RMSE, R²).

---
*Généré automatiquement par prepare_dataset_estimation_ventes.py*
