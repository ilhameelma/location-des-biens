"""
Préparation du dataset d'entraînement — Estimation de loyer (étape 16a)
==========================================================================
SmartRent Platform - PFE Data Engineering

Fusionne les deux sources scrapées (Mubawab, Sarouty), unifie le schéma,
impute les valeurs manquantes de façon traçable, encode les variables
catégorielles, et produit un split train/test prêt pour scikit-learn.

ENTRÉES
-------
- mubawab_locations_clean_final.csv  (source: colonnes ville + quartier)
- sarouty_locations_clean.csv        (source: colonne quartier uniquement)

SORTIES
-------
- dataset_locations_fusionne.csv     (les 2 sources combinées, schéma unifié,
                                       AVANT imputation — pour audit/rapport)
- dataset_locations_final.csv        (APRÈS imputation + encodage, colonnes
                                       *_imputed en booléen pour traçabilité)
- train.csv / test.csv                (split 80/20, random_state=42)
- rapport_preparation.md              (statistiques à coller dans le rapport de PFE)

USAGE
-----
python prepare_dataset_estimation.py
"""

import pandas as pd
import numpy as np

MUBAWAB_PATH = "mubawab_locations_clean_final.csv"
SAROUTY_PATH = "sarouty_locations_clean.csv"

# ---------------------------------------------------------------------------
# Mapping quartier -> ville pour Sarouty (pas de colonne ville native).
# Construit à partir de la géographie marocaine connue, limité aux quartiers
# suffisamment fréquents pour être fiables. Couverture : ~94% des lignes
# Sarouty ; le reste est marqué "Inconnu" plutôt que deviné à tort.
# ---------------------------------------------------------------------------
QUARTIER_TO_VILLE = {
    # Casablanca et environs
    "Anfa": "Casablanca", "Maarif": "Casablanca", "Maarif Extension": "Casablanca",
    "Bourgogne": "Casablanca", "Racine": "Casablanca", "Racine extension": "Casablanca",
    "Gauthier": "Casablanca", "Centre ville": "Casablanca",
    "Centre Ville Casablanca": "Casablanca", "Hay Hassani": "Casablanca",
    "Ain Diab": "Casablanca", "Ain Diab Extension": "Casablanca",
    "Sidi Belyout": "Casablanca", "Val Fleuri": "Casablanca", "Palmier": "Casablanca",
    "Mers Sultan": "Casablanca", "Ferme Bretone": "Casablanca",
    "Casablanca Finance City": "Casablanca", "Californie": "Casablanca",
    "Belvédère": "Casablanca", "Ain Chock": "Casablanca", "CIL": "Casablanca",
    "Nejma": "Casablanca", "Aviation": "Casablanca", "Benjdia": "Casablanca",
    "Roches Noires": "Casablanca", "Almaz": "Casablanca", "Laymoune": "Casablanca",
    "Oasis": "Casablanca", "Boulevard Anfa": "Casablanca",
    "Boulevard Al Massira Al Khadra": "Casablanca", "Casa Marina": "Casablanca",
    "Val d'Anfa": "Casablanca", "Casa Anfa": "Casablanca", "Sidi Maarouf": "Casablanca",
    "Zenata": "Casablanca", "Ain Sebaa": "Casablanca", "Socrate": "Casablanca",
    "Triangle d'Or": "Casablanca", "Boulevard Ghandi": "Casablanca",
    "Bella Vista": "Casablanca", "Beauséjour": "Casablanca",
    "Quartier Sindibad": "Casablanca", "Casa Green Town": "Casablanca",
    "Zerktouni": "Casablanca", "Anfa Supérieur": "Casablanca", "La Gironde": "Casablanca",
    "Abdelmoumen": "Casablanca", "Ziraoui": "Casablanca",
    "Dar Bouazza": "Casablanca", "Bouskoura": "Casablanca",  # périphérie Casa
    "Nouaceur": "Casablanca", "mansouria": "Casablanca",
    # Rabat / Salé
    "Souissi": "Rabat", "Hay Riad": "Rabat", "Agdal": "Rabat",
    "Quartier Agdal Haut": "Rabat", "Quartier Agdal Bas": "Rabat",
    "Yacoub El Mansour": "Rabat", "rabat": "Rabat", "Quartier Hassan": "Rabat",
    "Hassan": "Rabat", "Salé": "Salé", "La Marina Salé": "Salé",
    "Bouknadel": "Salé", "Plage des Nations": "Salé", "Harhoura": "Rabat",
    "Skhirat plage": "Rabat",
    # Marrakech
    "Guéliz": "Marrakech", "Hivernage": "Marrakech", "Palmeraie": "Marrakech",
    "Hay Charaf": "Marrakech", "Route Amizmiz": "Marrakech",
    "Av Abdelkrim El Khattabi": "Marrakech", "Route de Tahanaoute": "Marrakech",
    "Menara": "Marrakech", "Annakhil": "Marrakech", "Mnar": "Marrakech",
    "Route de Tamansourt": "Marrakech",
    # Tanger
    "Malabata": "Tanger", "Mesnana": "Tanger", "Mers El Kheir": "Tanger",
    "Castilla": "Tanger", "Vieille montagne": "Tanger", "Marshan": "Tanger",
    "Tanja Balia": "Tanger",
    # Autres villes ponctuelles
    "Bouznika Bay": "Bouznika", "2 Mars": "Casablanca", "Moulay Youssef": "Casablanca",
    "Tamaris": "Casablanca",
}


def load_mubawab() -> pd.DataFrame:
    df = pd.read_csv(MUBAWAB_PATH)
    df = df.drop(columns=[c for c in ("pieces", "equipements") if c in df.columns])
    df["source"] = "mubawab"
    keep = ["source", "titre", "prix_dh", "ville", "quartier", "surface_m2",
            "chambres", "salles_de_bain", "meuble"]
    return df[[c for c in keep if c in df.columns]]


def load_sarouty() -> pd.DataFrame:
    df = pd.read_csv(SAROUTY_PATH)
    df["ville"] = df["quartier"].map(QUARTIER_TO_VILLE).fillna("Inconnu")
    df["meuble"] = np.nan  # non disponible côté Sarouty
    df["source"] = "sarouty"
    keep = ["source", "titre", "prix_dh", "ville", "quartier", "surface_m2",
            "chambres", "salles_de_bain", "meuble"]
    return df[[c for c in keep if c in df.columns]]


def merge_sources() -> pd.DataFrame:
    mub = load_mubawab()
    sar = load_sarouty()
    merged = pd.concat([mub, sar], ignore_index=True)

    # Nettoyages simples communs
    merged["ville"] = merged["ville"].str.strip().str.title()
    merged.loc[merged["ville"] == "Rabat", "ville"] = "Rabat"  # normalise casse
    merged = merged.drop_duplicates(subset=["titre", "prix_dh", "ville", "surface_m2"])

    return merged


def impute(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = ["surface_m2", "chambres", "salles_de_bain"]

    for col in numeric_cols:
        df[f"{col}_imputed"] = df[col].isna()

    # Imputation hiérarchique : médiane (ville, chambres) -> médiane (ville) -> médiane globale
    for col in numeric_cols:
        global_median = df[col].median()
        ville_median = df.groupby("ville")[col].transform("median")
        df[col] = df[col].fillna(ville_median)
        df[col] = df[col].fillna(global_median)

    # meuble : catégorie à 3 états plutôt qu'un booléen forcé
    df["meuble_cat"] = df["meuble"].map(
        lambda v: "meuble" if v is True else ("non_meuble" if v is False else "inconnu")
    )
    df = df.drop(columns=["meuble"])

    return df


def encode_ville_meuble(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot pour ville et meuble — faible cardinalité, pas de risque de
    fuite de données (ne dépend pas de la cible prix_dh)."""
    df = df.copy()
    ville_counts = df["ville"].value_counts()
    rare_villes = ville_counts[ville_counts < 10].index
    df["ville_grp"] = df["ville"].where(~df["ville"].isin(rare_villes), "Autre")
    df = pd.get_dummies(df, columns=["ville_grp", "meuble_cat"], prefix=["ville", "meuble"])
    return df


def target_encode_quartier(train: pd.DataFrame, test: pd.DataFrame, smoothing: int = 10):
    """Encode le quartier par le prix médian qu'il porte, lissé vers la
    médiane de la ville pour les quartiers peu représentés. Calculé
    UNIQUEMENT sur le train pour éviter toute fuite de la cible vers le test
    (règle d'or du target encoding).

    encoded = (n_quartier * médiane_quartier + smoothing * médiane_ville)
              / (n_quartier + smoothing)
    """
    ville_median_global = train["prix_dh"].median()
    ville_median = train.groupby("ville")["prix_dh"].median()

    stats = train.groupby(["ville", "quartier"])["prix_dh"].agg(["median", "count"])
    stats = stats.rename(columns={"median": "quartier_median", "count": "n"})
    stats = stats.reset_index()
    stats["ville_median"] = stats["ville"].map(ville_median).fillna(ville_median_global)
    stats["quartier_prix_estime"] = (
        stats["n"] * stats["quartier_median"] + smoothing * stats["ville_median"]
    ) / (stats["n"] + smoothing)

    lookup = stats.set_index(["ville", "quartier"])["quartier_prix_estime"]

    def apply_encoding(df: pd.DataFrame) -> pd.Series:
        keys = list(zip(df["ville"], df["quartier"]))
        values = []
        for ville, quartier in keys:
            if (ville, quartier) in lookup.index:
                values.append(lookup.loc[(ville, quartier)])
            else:
                # quartier jamais vu en train : repli sur la médiane de la ville
                values.append(ville_median.get(ville, ville_median_global))
        return pd.Series(values, index=df.index)

    train = train.copy()
    test = test.copy()
    train["quartier_prix_estime"] = apply_encoding(train)
    test["quartier_prix_estime"] = apply_encoding(test)

    return train, test


def main():
    merged = merge_sources()
    merged.to_csv("dataset_locations_fusionne.csv", index=False)

    final = impute(merged)

    # Split train/test AVANT le target encoding du quartier (évite la fuite
    # de données : les statistiques de prix par quartier ne doivent être
    # calculées que sur le train)
    train_raw = final.sample(frac=0.8, random_state=42)
    test_raw = final.drop(train_raw.index)

    train_raw, test_raw = target_encode_quartier(train_raw, test_raw)

    train = encode_ville_meuble(train_raw)
    test = encode_ville_meuble(test_raw)
    # Alignement des colonnes (au cas où une ville/catégorie rare n'apparaît
    # que dans l'un des deux jeux)
    train, test = train.align(test, join="outer", axis=1, fill_value=0)

    final_encoded = pd.concat([train, test]).sort_index()
    final_encoded.to_csv("dataset_locations_final.csv", index=False)

    train.to_csv("train.csv", index=False)
    test.to_csv("test.csv", index=False)

    # Rapport
    n_total = len(merged)
    n_mub = (merged["source"] == "mubawab").sum()
    n_sar = (merged["source"] == "sarouty").sum()
    n_ville_inconnue = (merged["ville"] == "Inconnu").sum()

    report = f"""# Rapport de préparation — dataset estimation de loyer

## Volumétrie
- Total après fusion et dédoublonnage : **{n_total}** annonces
  - Mubawab : {n_mub}
  - Sarouty : {n_sar}
- Ville inconnue (quartier Sarouty non mappé) : {n_ville_inconnue} ({100*n_ville_inconnue//n_total}%)

## Imputation des valeurs manquantes
Stratégie hiérarchique : médiane par ville, puis médiane globale en dernier
recours. Colonnes `*_imputed` (booléen) ajoutées pour tracer quelles valeurs
sont réelles vs imputées — à mentionner comme limite dans le rapport de PFE.

| Colonne | % imputé |
|---|---|
| surface_m2 | {100*final['surface_m2_imputed'].mean():.1f}% |
| chambres | {100*final['chambres_imputed'].mean():.1f}% |
| salles_de_bain | {100*final['salles_de_bain_imputed'].mean():.1f}% |

## Répartition par ville (top 10)
{merged['ville'].value_counts().head(10).to_string()}

## Encodage du quartier (target encoding)
122 quartiers distincts rendaient le one-hot inexploitable (colonnes trop
creuses pour ~2000 lignes). Chaque quartier est donc représenté par une
seule colonne numérique `quartier_prix_estime` : le prix médian réellement
observé dans ce quartier sur le train, lissé vers la médiane de la ville
pour les quartiers peu représentés (facteur de lissage = 10 annonces).
Calculé strictement sur le train pour éviter toute fuite de la cible vers
le test.

## Split train/test
- Train : {len(train)} lignes
- Test  : {len(test)} lignes
- random_state=42, split 80/20 (effectué AVANT le target encoding du
  quartier, pour la même raison de fuite de données)

## Prochaine étape
Entraînement d'un modèle de régression (RandomForest ou XGBoost) sur
`train.csv`, target = `prix_dh`, évaluation sur `test.csv` (MAE, RMSE, R²).
"""
    with open("rapport_preparation.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(report)


if __name__ == "__main__":
    main()
