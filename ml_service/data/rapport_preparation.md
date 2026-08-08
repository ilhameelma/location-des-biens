# Rapport de préparation — dataset estimation de loyer

## Volumétrie
- Total après fusion et dédoublonnage : **1945** annonces
  - Mubawab : 843
  - Sarouty : 1102
- Ville inconnue (quartier Sarouty non mappé) : 91 (4%)

## Imputation des valeurs manquantes
Stratégie hiérarchique : médiane par ville, puis médiane globale en dernier
recours. Colonnes `*_imputed` (booléen) ajoutées pour tracer quelles valeurs
sont réelles vs imputées — à mentionner comme limite dans le rapport de PFE.

| Colonne | % imputé |
|---|---|
| surface_m2 | 16.8% |
| chambres | 23.7% |
| salles_de_bain | 35.1% |

## Répartition par ville (top 10)
ville
Casablanca     1204
Rabat           359
Marrakech       122
Inconnu          91
Tanger           84
Dar Bouazza      19
Bouskoura        19
Salé             14
Temara            7
Mohammedia        5

## Encodage du quartier (target encoding)
122 quartiers distincts rendaient le one-hot inexploitable (colonnes trop
creuses pour ~2000 lignes). Chaque quartier est donc représenté par une
seule colonne numérique `quartier_prix_estime` : le prix médian réellement
observé dans ce quartier sur le train, lissé vers la médiane de la ville
pour les quartiers peu représentés (facteur de lissage = 10 annonces).
Calculé strictement sur le train pour éviter toute fuite de la cible vers
le test.

## Split train/test
- Train : 1556 lignes
- Test  : 389 lignes
- random_state=42, split 80/20 (effectué AVANT le target encoding du
  quartier, pour la même raison de fuite de données)

## Prochaine étape
Entraînement d'un modèle de régression (RandomForest ou XGBoost) sur
`train.csv`, target = `prix_dh`, évaluation sur `test.csv` (MAE, RMSE, R²).
