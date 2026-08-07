"""
Préparation du dataset d'entraînement — Estimation de prix de vente (étape 16a)
==========================================================================
SmartRent Platform - PFE Data Engineering

Fusionne les deux sources scrapées (Mubawab Ventes, Sarouty Ventes), unifie le schéma,
impute les valeurs manquantes de façon traçable, encode les variables
catégorielles, et produit un split train/test prêt pour scikit-learn.

ENTRÉES
-------
- mubawab_ventes_clean.csv       (source: colonnes ville + quartier)
- sarouty_ventes_clean.csv       (source: colonne quartier uniquement)

SORTIES
-------
- dataset_ventes_fusionne.csv    (les 2 sources combinées, schéma unifié,
                                   AVANT imputation — pour audit/rapport)
- dataset_ventes_final.csv       (APRÈS imputation + encodage, colonnes
                                   *_imputed en booléen pour traçabilité)
- train.csv / test.csv            (split 80/20, random_state=42)
- rapport_preparation_ventes.md  (statistiques à coller dans le rapport de PFE)

USAGE
-----
python prepare_dataset_estimation_ventes.py
"""

import pandas as pd
import numpy as np
import re

MUBAWAB_PATH = "mubawab_ventes_clean.csv"
SAROUTY_PATH = "sarouty_ventes_clean_final.csv"

# ---------------------------------------------------------------------------
# Mapping quartier -> ville pour Sarouty (pas de colonne ville native).
# Construit à partir de la géographie marocaine connue, limité aux quartiers
# suffisamment fréquents pour être fiables. Couverture : ~94% des lignes
# Sarouty ; le reste est marqué "Inconnu" plutôt que deviné à tort.
# ---------------------------------------------------------------------------
QUARTIER_TO_VILLE = {
    # ======================== CASABLANCA ========================
    "Anfa": "Casablanca", 
    "Maarif": "Casablanca", 
    "Maarif Extension": "Casablanca",
    "Bourgogne": "Casablanca", 
    "Racine": "Casablanca", 
    "Racine extension": "Casablanca",
    "Gauthier": "Casablanca", 
    "Centre ville": "Casablanca",
    "Centre Ville Casablanca": "Casablanca", 
    "Hay Hassani": "Casablanca",
    "Ain Diab": "Casablanca", 
    "Ain Diab Extension": "Casablanca",
    "Sidi Belyout": "Casablanca", 
    "Val Fleuri": "Casablanca", 
    "Palmier": "Casablanca",
    "Mers Sultan": "Casablanca", 
    "Ferme Bretone": "Casablanca",
    "Ferme Bretonne (Hay Arraha)": "Casablanca",
    "Casablanca Finance City": "Casablanca", 
    "Californie": "Casablanca",
    "Belvédère": "Casablanca", 
    "Ain Chock": "Casablanca", 
    "CIL": "Casablanca",
    "Nejma": "Casablanca", 
    "Aviation": "Casablanca", 
    "Benjdia": "Casablanca",
    "Roches Noires": "Casablanca", 
    "Almaz": "Casablanca", 
    "Laymoune": "Casablanca",
    "Oasis": "Casablanca", 
    "Boulevard Anfa": "Casablanca",
    "Boulevard Al Massira Al Khadra": "Casablanca", 
    "Casa Marina": "Casablanca",
    "Val d'Anfa": "Casablanca", 
    "Casa Anfa": "Casablanca", 
    "Sidi Maarouf": "Casablanca",
    "Zenata": "Casablanca", 
    "Ain Sebaa": "Casablanca", 
    "Aïn Sebaâ": "Casablanca",
    "Socrate": "Casablanca",
    "Triangle d'Or": "Casablanca", 
    "Boulevard Ghandi": "Casablanca",
    "Bella Vista": "Casablanca", 
    "Beauséjour": "Casablanca",
    "Quartier Sindibad": "Casablanca", 
    "Casa Green Town": "Casablanca",
    "Zerktouni": "Casablanca", 
    "Anfa Supérieur": "Casablanca", 
    "La Gironde": "Casablanca",
    "Abdelmoumen": "Casablanca", 
    "Ziraoui": "Casablanca",
    "Dar Bouazza": "Casablanca", 
    "Bouskoura": "Casablanca",
    "Nouaceur": "Casablanca", 
    "El Mansouria": "Casablanca",
    "Mansouria": "Casablanca",
    "Tamaris": "Casablanca",
    "Sidi Rahal": "Casablanca",
    "Sidi rahal": "Casablanca",
    "Tamansourt": "Casablanca",
    "Tamensourt": "Casablanca",
    "Oulfa": "Casablanca",
    "Hay Almassira 2": "Casablanca",
    "Hay Mohammadi": "Casablanca",
    "Sidi Moumen": "Casablanca",
    "Derb Sultan": "Casablanca",
    "Derb Ghallef": "Casablanca",
    "Bernoussi": "Casablanca",
    "Lissasfa": "Casablanca",
    "Mabella": "Casablanca",
    "Mabrouka": "Casablanca",
    "Nassim": "Casablanca",
    "2 Mars": "Casablanca",
    "Alsace Lorraine": "Casablanca",
    "Mandarina": "Casablanca",
    "Mandarona": "Casablanca",
    "Errahma": "Casablanca",
    "La Siesta": "Casablanca",
    "Wafa": "Casablanca",
    "Mansouria": "Casablanca",
    "El Alia": "Casablanca",
    # ======================== RABAT / SALÉ ========================
    "Souissi": "Rabat", 
    "Hay Riad": "Rabat", 
    "Agdal": "Rabat",
    "Quartier Agdal Haut": "Rabat", 
    "Quartier Agdal Bas": "Rabat",
    "Yacoub El Mansour": "Rabat", 
    "rabat": "Rabat", 
    "Quartier Hassan": "Rabat",
    "Hassan": "Rabat", 
    "Riyad": "Rabat",
    "L'Ocean": "Rabat",
    "Océan": "Rabat",
    "Aviation - Mabella": "Rabat",
    "Kebibat": "Rabat",
    "Harhoura": "Rabat",
    "Skhirat": "Rabat",
    "Salé": "Salé", 
    "La Marina Salé": "Salé",
    "Bouknadel": "Salé", 
    "Plage des Nations": "Salé",
    "Plage des nations": "Salé",
    "Sala el Jadida": "Salé",
    "Bab al bahr": "Salé",
    "Medina": "Salé",
    # ======================== MARRAKECH ========================
    "Guéliz": "Marrakech", 
    "Gueliz": "Marrakech",
    "Hivernage": "Marrakech", 
    "Palmeraie": "Marrakech",
    "Hay Charaf": "Marrakech", 
    "Route Amizmiz": "Marrakech",
    "Av Abdelkrim El Khattabi": "Marrakech", 
    "Route de Tahanaoute": "Marrakech",
    "Menara": "Marrakech", 
    "Annakhil": "Marrakech", 
    "Mnar": "Marrakech",
    "Route de Tamansourt": "Marrakech",
    "Avenue Mohammed VI": "Marrakech",
    "Boulevard Med 6": "Marrakech",
    "Route de Casablanca": "Marrakech",
    "Route de Casa": "Marrakech",
    "Agdal": "Marrakech",
    "Semlalia": "Marrakech",
    "Samlalia": "Marrakech",
    "Majorelle": "Marrakech",
    "Izdihar": "Marrakech",
    "Hay Izdihar": "Marrakech",
    "Al izdihar": "Marrakech",
    "Targa": "Marrakech",
    "Hay Targa": "Marrakech",
    "Mhamid": "Marrakech",
    "Mabrouka": "Marrakech",
    "Bouaakkaz": "Marrakech",
    "Chrifia": "Marrakech",
    "Route de Safi": "Marrakech",
    "Daoudiate": "Marrakech",
    "Massira": "Marrakech",
    "Massira 1": "Marrakech",
    "Massira 2": "Marrakech",
    "Azzouzia": "Marrakech",
    "Hay Saada": "Marrakech",
    "Saada": "Marrakech",
    "Ain Mezouar": "Marrakech",
    "AIN MEZOUAR": "Marrakech",
    "Arset Sbaia": "Marrakech",
    "Camp Al Ghoul": "Marrakech",
    "Victor Hugo": "Marrakech",
    "Ennakhil (Palmeraie)": "Marrakech",
    "Route de Ouarzazate": "Marrakech",
    "Route de Fès": "Marrakech",
    "Fassi": "Marrakech",
    # ======================== TANGER ========================
    "Malabata": "Tanger", 
    "Mesnana": "Tanger", 
    "Mers El Kheir": "Tanger",
    "Castilla": "Tanger", 
    "Vieille montagne": "Tanger", 
    "Marshan": "Tanger",
    "Tanja Balia": "Tanger",
    "Tanger City Center": "Tanger",
    "Centre": "Tanger",
    "De La Plage": "Tanger",
    "Plage": "Tanger",
    "Boukhalef": "Tanger",
    "Beni Touzine": "Tanger",
    "Administratif": "Tanger",
    "Route Nationale Assilah": "Tanger",
    "Moujahidine": "Tanger",
    "Ziaten": "Tanger",
    "Mghogha": "Tanger",
    "Sania": "Tanger",
    "Manar": "Tanger",
    "Du Golf": "Tanger",
    "Iberie": "Tanger",
    "Tanja Balia": "Tanger",
    "Bel Air - Val fleuri": "Tanger",
    "Val Fleuri": "Tanger",
    "Centre ville": "Tanger",
    "Hay Hassani": "Tanger",
    "Foret Diplomatique": "Tanger",
    # ======================== AUTRES VILLES ========================
    "Agadir": "Agadir",
    "Ville Nouvelle": "Agadir",
    "Haut Founty": "Agadir",
    "Hay Houda": "Agadir",
    "Abattoirs": "Agadir",
    "Taddart Anza": "Agadir",
    "El Mdrassi": "Tétouan",
    "Tétouan": "Tétouan",
    "Wilaya": "Tétouan",
    "Tamouda": "Tétouan",
    "Martil": "Martil",
    "M'Diq": "M'Diq",
    "Cabo Negro": "Cabo Negro",
    "Asilah": "Asilah",
    "Saïdia": "Saïdia",
    "saidia": "Saïdia",
    "Bouznika": "Bouznika",
    "Bouznika Bay": "Bouznika",
    "Plage Oued Cherrat": "Bouznika",
    "El Jadida": "El Jadida",
    "Ennajd": "El Jadida",
    "Kenitra": "Kénitra",
    "Kénitra": "Kénitra",
    "Maamora": "Kénitra",
    "Mimosas": "Kénitra",
    "La Ville Haute": "Kénitra",
    "Meknes": "Meknès",
    "Meknès": "Meknès",
    "Hamria": "Meknès",
    "Fès": "Fès",
    "Fes City Center": "Fès",
    "Narjis": "Fès",
    "Champ de course": "Fès",
    "Ifrane": "Ifrane",
    "Mohammedia": "Mohammedia",
    "Quartier du Parc": "Mohammedia",
    "Mannesmann": "Mohammedia",
    "Béni Yakhlef": "Béni Yakhlef",
    "Had Soualem": "Had Soualem",
    "Settat": "Settat",
    "Berrechid": "Berrechid",
    "Benslimane": "Benslimane",
    "Oualidia": "Oualidia",
    "Sidi Bennour": "Sidi Bennour",
    "Tit Mellil": "Tit Mellil",
    "Chellalate": "Chellalate",
    "Médiouna": "Médiouna",
    "Essaouira": "Essaouira",
    "Laâyoune": "Laâyoune",
    "Dakhla": "Dakhla",
    "Sidi Bouzid": "Sidi Bouzid",
    "Oujda": "Oujda",
    "Al Hoceima": "Al Hoceima",
    "Tnine Aglou": "Tnine Aglou",
    "Ait Melloul": "Ait Melloul",
    "Lamharza Essahel": "Lamharza Essahel",
}


def load_mubawab() -> pd.DataFrame:
    """Charge et nettoie les données Mubawab Ventes."""
    df = pd.read_csv(MUBAWAB_PATH)
    
    # Supprimer les colonnes inutiles pour la prédiction
    drop_cols = ["pieces", "equipements", "meuble", "description", "url"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    
    df["source"] = "mubawab"
    
    # Nettoyer les noms de quartiers
    df["quartier"] = df["quartier"].fillna("Inconnu")
    df["quartier"] = df["quartier"].str.strip().str.title()
    
    # Standardiser quelques quartiers
    quartier_map = {
        "Les Princesses": "Les princesses",
        "Les princesses": "Les princesses",
        "Maârif": "Maarif",
        "Maarif": "Maarif",
        "Maârif Extension": "Maarif Extension",
        "Gueliz": "Guéliz",
        "Belvedere": "Belvédère",
        "Bourgogne Ouest": "Bourgogne",
        "Bourgogne Est": "Bourgogne",
        "Sidi Belyout": "Bourgogne",
        "Casa Marina": "Marina Casablanca",
        "Casablanca Marina": "Marina Casablanca",
    }
    df["quartier"] = df["quartier"].replace(quartier_map)
    
    # Garder les colonnes nécessaires
    keep = ["source", "titre", "prix_dh", "ville", "quartier", "surface_m2",
            "chambres", "salles_de_bain"]
    return df[[c for c in keep if c in df.columns]]


def load_sarouty() -> pd.DataFrame:
    """Charge et nettoie les données Sarouty Ventes."""
    df = pd.read_csv(SAROUTY_PATH)
    
    # Ajouter la ville via le mapping
    df["ville"] = df["quartier"].map(QUARTIER_TO_VILLE).fillna("Inconnu")
    df["source"] = "sarouty"
    
    # Supprimer les doublons évidents (test)
    df = df[~df["titre"].str.lower().str.contains("test", na=False)]
    
    # Garder les colonnes nécessaires
    keep = ["source", "titre", "prix_dh", "ville", "quartier", "surface_m2",
            "chambres", "salles_de_bain"]
    return df[[c for c in keep if c in df.columns]]


def merge_sources() -> pd.DataFrame:
    """Fusionne les deux sources et dédoublonne."""
    mub = load_mubawab()
    sar = load_sarouty()
    
    merged = pd.concat([mub, sar], ignore_index=True)
    
    # Nettoyage commun
    merged["ville"] = merged["ville"].str.strip().str.title()
    merged["ville"] = merged["ville"].replace({"Rabat": "Rabat", "Casablanca": "Casablanca"})
    
    # Suppression des doublons (titre + prix + surface)
    merged = merged.drop_duplicates(subset=["titre", "prix_dh", "ville", "surface_m2"])
    
    # Supprimer les prix aberrants (plus de 100M ou moins de 10k)
    merged = merged[(merged["prix_dh"] >= 10000) & (merged["prix_dh"] <= 100000000)]
    
    return merged


def impute(df: pd.DataFrame) -> pd.DataFrame:
    """Impute les valeurs manquantes avec stratégie hiérarchique."""
    df = df.copy()
    numeric_cols = ["surface_m2", "chambres", "salles_de_bain"]
    
    # Tracer les valeurs imputées
    for col in numeric_cols:
        df[f"{col}_imputed"] = df[col].isna()
    
    # Imputation hiérarchique : médiane (ville, chambres) -> médiane (ville) -> médiane globale
    for col in numeric_cols:
        global_median = df[col].median()
        # Médiane par ville
        ville_median = df.groupby("ville")[col].transform("median")
        df[col] = df[col].fillna(ville_median)
        # Si toujours NaN, médiane globale
        df[col] = df[col].fillna(global_median)
    
    return df


def encode_ville_meuble(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot pour la ville (faible cardinalité)."""
    df = df.copy()
    
    # Regrouper les villes rares
    ville_counts = df["ville"].value_counts()
    rare_villes = ville_counts[ville_counts < 10].index
    df["ville_grp"] = df["ville"].where(~df["ville"].isin(rare_villes), "Autre")
    
    # One-hot encoding
    df = pd.get_dummies(df, columns=["ville_grp"], prefix=["ville"])
    return df


def target_encode_quartier(train: pd.DataFrame, test: pd.DataFrame, smoothing: int = 10):
    """
    Encode le quartier par le prix médian qu'il porte, lissé vers la
    médiane de la ville pour les quartiers peu représentés.
    Calculé UNIQUEMENT sur le train pour éviter toute fuite de la cible.
    """
    ville_median_global = train["prix_dh"].median()
    ville_median = train.groupby("ville")["prix_dh"].median()
    
    # Statistiques par (ville, quartier)
    stats = train.groupby(["ville", "quartier"])["prix_dh"].agg(["median", "count"])
    stats = stats.rename(columns={"median": "quartier_median", "count": "n"})
    stats = stats.reset_index()
    stats["ville_median"] = stats["ville"].map(ville_median).fillna(ville_median_global)
    
    # Lissage
    stats["quartier_prix_estime"] = (
        stats["n"] * stats["quartier_median"] + smoothing * stats["ville_median"]
    ) / (stats["n"] + smoothing)
    
    lookup = stats.set_index(["ville", "quartier"])["quartier_prix_estime"]
    
    def apply_encoding(df: pd.DataFrame) -> pd.Series:
        values = []
        for _, row in df.iterrows():
            key = (row["ville"], row["quartier"])
            if key in lookup.index:
                values.append(lookup.loc[key])
            else:
                values.append(ville_median.get(row["ville"], ville_median_global))
        return pd.Series(values, index=df.index)
    
    train = train.copy()
    test = test.copy()
    train["quartier_prix_estime"] = apply_encoding(train)
    test["quartier_prix_estime"] = apply_encoding(test)
    
    return train, test


def main():
    print("=" * 80)
    print("Préparation du dataset d'entraînement — Estimation des prix de vente")
    print("=" * 80)
    
    # 1. Chargement et fusion
    print("\n📊 1. Chargement et fusion des sources...")
    merged = merge_sources()
    merged.to_csv("dataset_ventes_fusionne.csv", index=False)
    print(f"   ✅ Fusionné : {len(merged)} lignes")
    
    # 2. Imputation
    print("\n🔧 2. Imputation des valeurs manquantes...")
    final = impute(merged)
    print(f"   ✅ Imputé : {len(final)} lignes")
    
    # 3. Split train/test
    print("\n📊 3. Split train/test (80/20)...")
    train_raw = final.sample(frac=0.8, random_state=42)
    test_raw = final.drop(train_raw.index)
    print(f"   ✅ Train : {len(train_raw)} lignes")
    print(f"   ✅ Test  : {len(test_raw)} lignes")
    
    # 4. Target encoding du quartier (calculé sur le train UNIQUEMENT)
    print("\n🏘️ 4. Target encoding des quartiers...")
    train_raw, test_raw = target_encode_quartier(train_raw, test_raw)
    print(f"   ✅ Quartiers encodés")
    
    # 5. One-hot encoding des villes
    print("\n🏙️ 5. One-hot encoding des villes...")
    train = encode_ville_meuble(train_raw)
    test = encode_ville_meuble(test_raw)
    
    # Alignement des colonnes
    train, test = train.align(test, join="outer", axis=1, fill_value=0)
    print(f"   ✅ Villes encodées : {len(train.columns)} colonnes")
    
    # 6. Sauvegarde
    print("\n💾 6. Sauvegarde des datasets...")
    final_encoded = pd.concat([train, test]).sort_index()
    final_encoded.to_csv("dataset_ventes_final.csv", index=False)
    train.to_csv("train_ventes.csv", index=False)
    test.to_csv("test_ventes.csv", index=False)
    print("   ✅ Dataset final : dataset_ventes_final.csv")
    print("   ✅ Train          : train_ventes.csv")
    print("   ✅ Test           : test_ventes.csv")
    
    # 7. Rapport
    print("\n📝 7. Génération du rapport...")
    n_total = len(merged)
    n_mub = (merged["source"] == "mubawab").sum()
    n_sar = (merged["source"] == "sarouty").sum()
    n_ville_inconnue = (merged["ville"] == "Inconnu").sum()
    
    # Statistiques par ville
    ville_stats = merged["ville"].value_counts().head(10)
    
    # Statistiques des prix
    prix_stats = merged["prix_dh"].describe()
    
    report = f"""# Rapport de préparation — Dataset Estimation des Prix de Vente

## 1. Volumétrie
- Total après fusion et dédoublonnage : **{n_total}** annonces
  - Mubawab : {n_mub} ({100*n_mub/n_total:.1f}%)
  - Sarouty : {n_sar} ({100*n_sar/n_total:.1f}%)
- Ville inconnue (quartier Sarouty non mappé) : {n_ville_inconnue} ({100*n_ville_inconnue//n_total}%)

## 2. Statistiques des prix de vente
- Moyenne : {prix_stats['mean']:,.0f} DH
- Médiane : {prix_stats['50%']:,.0f} DH
- Min : {prix_stats['min']:,.0f} DH
- Max : {prix_stats['max']:,.0f} DH
- Écart-type : {prix_stats['std']:,.0f} DH

## 3. Imputation des valeurs manquantes
Stratégie hiérarchique : médiane par ville, puis médiane globale en dernier recours.
Colonnes `*_imputed` (booléen) ajoutées pour tracer quelles valeurs sont réelles vs imputées.

| Colonne | % imputé |
|---------|----------|
| surface_m2 | {100*final['surface_m2_imputed'].mean():.1f}% |
| chambres | {100*final['chambres_imputed'].mean():.1f}% |
| salles_de_bain | {100*final['salles_de_bain_imputed'].mean():.1f}% |

## 4. Répartition par ville (top 10)
{ville_stats.to_string()}

## 5. Encodage des variables
- **Quartier** : Target encoding vers le prix médian, lissé par ville (smoothing=10).
  Calculé UNIQUEMENT sur le train pour éviter toute fuite de la cible.
- **Ville** : One-hot encoding.
- **Source** : Colonne "source" (mubawab/sarouty) conservée pour audit.

## 6. Split train/test
- Train : {len(train)} lignes ({100*len(train)/(len(train)+len(test)):.1f}%)
- Test  : {len(test)} lignes ({100*len(test)/(len(train)+len(test)):.1f}%)
- random_state=42, split 80/20 effectué AVANT le target encoding du quartier

## 7. Prochaine étape
Entraînement d'un modèle de régression (RandomForest ou XGBoost) sur `train_ventes.csv`,
target = `prix_dh`, évaluation sur `test_ventes.csv` (MAE, RMSE, R²).

---
*Généré automatiquement par prepare_dataset_estimation_ventes.py*
"""
    
    with open("rapport_preparation_ventes.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n" + "=" * 80)
    print(report)
    print("=" * 80)
    print("\n✅ TRAITEMENT TERMINÉ !")


if __name__ == "__main__":
    main()