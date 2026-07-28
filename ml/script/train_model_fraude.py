"""
Modèle de détection de fraude (étape 16c)
=============================================
SmartRent Platform - PFE Data Engineering

Pas d'historique de fraude réelle disponible (logique — les vraies
plateformes ne publient pas ce genre de données). Approche retenue :
détection d'anomalies non-supervisée (Isolation Forest), validée par
injection de faux cas de fraude synthétiques évidents.

SIGNAL PRINCIPAL : écart_prix_pct
-----------------------------------
Réutilise le modèle d'estimation de loyer (étape 16a, modele_estimation_
loyer.joblib) pour calculer le prix ATTENDU de chaque bien, puis compare
au prix AFFICHÉ. Un écart très négatif (prix affiché très inférieur au
prix attendu) est le signal classique de l'arnaque "trop beau pour être
vrai" (faux compte, demande d'acompte avant visite, bien inexistant...).

    écart_prix_pct = (prix_affiché - prix_attendu) / prix_attendu

Ce signal est combiné à d'autres features (surface, chambres, quartier)
dans un Isolation Forest, qui détecte aussi d'autres profils d'anomalie
que le seul prix (ex. surface absurde pour le nombre de chambres).

VALIDATION
----------
Impossible d'évaluer un modèle non-supervisé avec MAE/R² comme le modèle
16a. À la place : injection de N annonces synthétiques manifestement
frauduleuses (prix divisé par 3-5 par rapport au marché) et mesure du
taux de détection — sert de test de non-régression basique.

SORTIES
-------
- modele_fraude.joblib
- rapport_fraude.md

USAGE
-----
python train_model_fraude.py
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

DATA_PATH = "dataset_locations_final.csv"
PRICE_MODEL_PATH = "modele_estimation_loyer.joblib"

# Mêmes features que le modèle d'estimation (16a) — nécessaire pour appeler
# .predict() dessus et obtenir le prix attendu
PRICE_MODEL_FEATURES = [
    "surface_m2", "chambres", "salles_de_bain", "quartier_prix_estime",
    "ville_Casablanca", "ville_Rabat", "ville_Marrakech", "ville_Tanger",
    "ville_Salé", "ville_Bouskoura", "ville_Dar Bouazza", "ville_Autre",
    "meuble_meuble", "meuble_non_meuble", "meuble_inconnu",
]

# Features données à l'Isolation Forest — le prix brut est volontairement
# exclu (déjà capturé, en relatif, par écart_prix_pct) pour ne pas faire
# double emploi et pour que le modèle généralise à tous les niveaux de prix
FRAUD_FEATURES = [
    "ecart_prix_pct", "surface_m2", "chambres", "salles_de_bain", "quartier_prix_estime",
]

DISPLAY_COLUMNS = ["titre", "ville", "quartier", "prix_dh", "prix_attendu", "ecart_prix_pct"]

CONTAMINATION = 0.05  # hypothèse : ~5% d'annonces suspectes dans un catalogue réel


def compute_expected_price(df: pd.DataFrame, price_model) -> pd.Series:
    X = df[PRICE_MODEL_FEATURES].copy()
    for col in X.columns:
        if X[col].dtype == bool:
            X[col] = X[col].astype(int)
    return pd.Series(price_model.predict(X), index=df.index)


def make_synthetic_fraud(df: pd.DataFrame, n: int = 40, seed: int = 42) -> pd.DataFrame:
    """Clone n annonces réelles en divisant leur prix par 3 à 5 — simule des
    annonces-appâts manifestement sous le marché. Sert uniquement à valider
    que le modèle les détecte, pas à l'entraînement."""
    rng = np.random.default_rng(seed)
    sample = df.sample(n, random_state=seed).copy()
    factors = rng.uniform(0.15, 0.35, size=n)  # prix ramené à 15-35% du prix réel
    sample["prix_dh"] = (sample["prix_dh"] * factors).round(-2)
    sample["titre"] = "[SYNTHÉTIQUE] " + sample["titre"].astype(str)
    return sample


def main():
    df = pd.read_csv(DATA_PATH)
    price_model = joblib.load(PRICE_MODEL_PATH)

    df["prix_attendu"] = compute_expected_price(df, price_model)
    df["ecart_prix_pct"] = (df["prix_dh"] - df["prix_attendu"]) / df["prix_attendu"]

    print(f"Catalogue : {len(df)} biens")
    print(f"Écart prix moyen : {df['ecart_prix_pct'].mean():.1%} | écart-type : {df['ecart_prix_pct'].std():.1%}")

    # --- Entraînement Isolation Forest sur les biens réels ---
    iso = IsolationForest(
        n_estimators=300,
        contamination=CONTAMINATION,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(df[FRAUD_FEATURES])

    df["anomaly_score"] = -iso.score_samples(df[FRAUD_FEATURES])  # + haut = + suspect
    df["suspect_isolation_forest"] = iso.predict(df[FRAUD_FEATURES]) == -1

    # --- Règle explicite complémentaire sur le prix ---
    # L'Isolation Forest dilue le signal quand une seule feature (le prix)
    # est anormale et que les autres (surface, chambres...) restent dans la
    # norme — cas typique d'une annonce-appât à prix cassé sur un bien par
    # ailleurs "normal". Une règle directe sur le percentile de
    # ecart_prix_pct comble ce point faible, sans remplacer l'Isolation
    # Forest qui reste utile pour les anomalies multivariées (ex. surface
    # incohérente avec le nombre de chambres).
    seuil_prix_bas = df["ecart_prix_pct"].quantile(0.05)
    df["suspect_prix_bas"] = df["ecart_prix_pct"] < seuil_prix_bas

    df["est_suspect"] = df["suspect_isolation_forest"] | df["suspect_prix_bas"]

    print(f"Seuil règle prix bas (5e percentile) : {seuil_prix_bas:.1%}")

    n_suspects = df["est_suspect"].sum()
    print(f"\n{n_suspects} biens marqués suspects sur {len(df)} ({100*n_suspects/len(df):.1f}%)")

    print("\n=== Top 10 annonces les plus suspectes (données réelles) ===")
    top_suspects = df.sort_values("anomaly_score", ascending=False).head(10)
    print(top_suspects[DISPLAY_COLUMNS].to_string(index=False))

    # --- Validation : injection de fraude synthétique ---
    synthetic = make_synthetic_fraud(df, n=40)
    synthetic["prix_attendu"] = compute_expected_price(synthetic, price_model)
    synthetic["ecart_prix_pct"] = (synthetic["prix_dh"] - synthetic["prix_attendu"]) / synthetic["prix_attendu"]

    synthetic_scores = -iso.score_samples(synthetic[FRAUD_FEATURES])
    synthetic_isolation_flags = iso.predict(synthetic[FRAUD_FEATURES]) == -1
    synthetic_prix_flags = synthetic["ecart_prix_pct"] < seuil_prix_bas
    synthetic_flags = synthetic_isolation_flags | synthetic_prix_flags
    detection_rate = synthetic_flags.mean()

    print(f"\n=== Validation — {len(synthetic)} fausses annonces synthétiques (prix divisé par 3-5) ===")
    print(f"Taux de détection : {detection_rate:.1%} ({synthetic_flags.sum()}/{len(synthetic)} détectées)")
    print("\nExemples non détectés (faux négatifs, à examiner) :")
    missed = synthetic[~synthetic_flags][DISPLAY_COLUMNS].head(5)
    print(missed.to_string(index=False) if len(missed) else "  (aucun — détection à 100%)")

    # --- Faux positifs potentiels parmi les biens réels non suspects ---
    # (biens légitimes avec un profil un peu atypique mais pas frauduleux —
    # à examiner manuellement pour calibrer si besoin)

    # --- Sauvegarde ---
    joblib.dump(
        {"model": iso, "features": FRAUD_FEATURES, "seuil_prix_bas": seuil_prix_bas},
        "modele_fraude.joblib",
    )
    print("\nModèle sauvegardé : modele_fraude.joblib")

    report = f"""# Rapport — modèle de détection de fraude (Isolation Forest, v1)

## Approche
Approche hybride : (1) une règle explicite sur le percentile bas de l'écart
au prix attendu (calculé par le modèle d'estimation 16a), et (2) un
Isolation Forest multivarié (surface, chambres, salles de bain, quartier,
écart de prix) pour capter les anomalies non réductibles au seul prix
(ex. surface incohérente avec le nombre de chambres). Une annonce est
marquée suspecte si l'une des deux méthodes la signale.

La règle seule sur le prix a été ajoutée après un premier test montrant que
l'Isolation Forest seul ne détectait que 32,5% des cas de fraude
synthétique évidente (prix divisé par 3-5) — le signal du prix était dilué
parmi 4 autres features qui, elles, restaient dans la norme. La combinaison
règle + modèle corrige ce point faible tout en gardant la capacité de
détection multivariée.

## Résultats sur le catalogue réel
- {len(df)} biens analysés
- {n_suspects} marqués suspects ({100*n_suspects/len(df):.1f}%)
- Écart de prix moyen au marché : {df['ecart_prix_pct'].mean():.1%}

### Top 10 les plus suspects
{top_suspects[DISPLAY_COLUMNS].to_string(index=False)}

⚠️ Un score élevé ne prouve pas la fraude — ça signale une annonce à
vérifier manuellement (prix anormalement bas pour ses caractéristiques,
qui peut aussi s'expliquer par une urgence de location, un bien à
rénover, une erreur de saisie du propriétaire, etc.). C'est un outil
d'aide à la modération, pas une décision automatique de suppression.

## Validation — fraude synthétique
{len(synthetic)} annonces synthétiques créées (clones de biens réels,
prix divisé par 3 à 5 — scénario "trop beau pour être vrai").

**Taux de détection : {detection_rate:.1%}** ({synthetic_flags.sum()}/{len(synthetic)})

## Limites connues à mentionner dans le rapport de PFE
- Aucune vraie donnée de fraude pour valider en conditions réelles — la
  validation synthétique teste seulement le cas "prix anormalement bas",
  pas les autres patterns de fraude (faux compte, photos volées,
  usurpation d'identité, paiement hors plateforme...) qui nécessitent
  d'autres signaux (comportement de compte, vitesse de publication,
  répétition d'annonces similaires) non disponibles pour l'instant
- Le seuil de contamination (5%) est une hypothèse arbitraire, à recalibrer
  une fois de vraies réclamations disponibles via `reclamation` (schéma
  transactionnel) et `dw.fait_paiement`
- Dépend de la qualité du modèle d'estimation (16a, R²=0.59 actuellement)
  — un modèle de prix plus précis améliorera directement la détection

## Prochaine étape
1. Exposer via `/predict/fraude` dans le micro-service IA — appelé à la
   publication d'une annonce, score affiché à l'admin en modération
   (`GET /admin/biens` avec tri par score de suspicion)
2. Une fois `reclamation` alimentée par de vrais signalements,
   ré-entraîner avec ces cas comme référence de calibration
3. Ajouter des signaux comportementaux (paiements, fréquence de
   publication) une fois `dw.fait_paiement` suffisamment peuplé
"""
    with open("rapport_fraude.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\nRapport sauvegardé : rapport_fraude.md")


if __name__ == "__main__":
    main()
