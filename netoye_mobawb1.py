"""
Nettoyage des données Mubawab - Locations UNIQUEMENT
====================================================
SmartRent Platform - PFE Data Engineering

Ce script nettoie les données scrappées de Mubawab pour ne garder
que les annonces de location valides (exclut ventes, nuitées, etc.)
CONSERVE LES BUREAUX À LOUER
"""

import csv
import logging
import re
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mubawab_cleaner")

# ===== CONFIGURATION =====
INPUT_CSV = Path("mubawab_locations_clean.csv")
OUTPUT_CSV = Path("mubawab_locations_clean_final.csv")

# ===== MOTS-CLÉS EXCLUS (VENTE) =====
SALE_KEYWORDS = [
    "vente", "vendre", "vendu", "achat", "acheter",
    "for sale", "sell", "sold", "buy", "purchase",
    "à vendre", "a vendre", "property for sale",
    "villa à vendre", "appartement à vendre",
    "vend", "vends",
    "hypothéquer", "hypothèque",
]

# ===== MOTS-CLÉS EXCLUS (LOCATIONS À LA NUITÉE) =====
NIGHT_KEYWORDS = [
    "nuit", "nuitée", "nuitées",
    "night", "per night", "overnight",
    "vacances", "saisonnière", "saisonnier",
    "touristique", "séjour", "location saisonnière",
    "par nuit", "à la nuit", "à la nuitée",
    "par jour", "quotidien",
    "minimum 3 nuits", "minimum 2 nuits",
    "par nuité", "pour une nuit",
    "séjour de", "location de vacances",
]

# ===== PRIX MIN/MAX POUR LES LOCATIONS (en DH) =====
PRICE_MIN = 2000       # En dessous, probablement une erreur ou une nuitée
PRICE_MAX = 100000     # Au-dessus, probablement une vente

# ===== PRIX MIN AU M² (pour détecter les prix aberrants) =====
PRICE_PER_SQM_MIN = 40    # En dessous, probablement une nuitée ou une erreur
PRICE_PER_SQM_MAX = 2000  # Au-dessus, probablement une erreur


def is_sale_announcement(titre: str, prix: Optional[float] = None) -> bool:
    """Vérifie si une annonce est une vente (et non une location)."""
    if not titre:
        return False
    
    titre_lower = titre.lower()
    
    for keyword in SALE_KEYWORDS:
        if keyword in titre_lower:
            logger.debug(f"Exclusion (mot-clé vente): {titre[:50]}")
            return True
    
    if prix is not None and prix > PRICE_MAX:
        logger.debug(f"Exclusion (prix trop élevé): {prix} DH - {titre[:50]}")
        return True
    
    return False


def is_night_rental(titre: str, prix: Optional[float] = None, 
                    surface: Optional[float] = None, 
                    description: str = "") -> bool:
    """Vérifie si une annonce est une location à la nuitée."""
    if not titre:
        return False
    
    texte_complet = (titre + " " + description).lower()
    
    for keyword in NIGHT_KEYWORDS:
        if keyword in texte_complet:
            logger.debug(f"Exclusion (mot-clé nuitée): {titre[:50]}")
            return True
    
    if prix is not None and surface is not None and surface > 0:
        price_per_sqm = prix / surface
        if price_per_sqm < PRICE_PER_SQM_MIN:
            logger.debug(f"Exclusion (prix/m² trop bas: {price_per_sqm:.1f} DH/m²): {titre[:50]}")
            return True
        if price_per_sqm > PRICE_PER_SQM_MAX:
            logger.debug(f"Exclusion (prix/m² trop élevé: {price_per_sqm:.1f} DH/m²): {titre[:50]}")
            return True
    
    return False


def is_colocation(titre: str, description: str = "") -> bool:
    """Vérifie si une annonce est une colocation."""
    texte_complet = (titre + " " + description).lower()
    keywords = ["colocation", "collocation", "coloc", "partage"]
    
    for keyword in keywords:
        if keyword in texte_complet:
            logger.debug(f"Exclusion (colocation): {titre[:50]}")
            return True
    return False


def parse_price_from_text(text: str) -> Optional[float]:
    """Extrait un prix depuis du texte."""
    if not text:
        return None
    
    # Si le prix est en Euros
    euro_match = re.search(r"(\d+(?:[.,]\d+)?)\s*€", text)
    if euro_match:
        euros = float(euro_match.group(1).replace(",", "."))
        # Conversion approximative (1€ ≈ 11 DH)
        return euros * 11
    
    # Sinon extraction des chiffres
    digits = re.sub(r"[^\d]", "", text)
    return float(digits) if digits else None


def clean_annonce(row: dict) -> Optional[dict]:
    """Nettoie une annonce individuelle."""
    titre = row.get("titre", "")
    prix_str = row.get("prix_dh", "")
    surface_str = row.get("surface_m2", "")
    description = row.get("description", "")
    
    # Si le prix est vide, essayer de l'extraire du titre ou de la description
    prix = None
    if prix_str and prix_str.strip():
        try:
            prix = float(prix_str)
        except ValueError:
            prix = parse_price_from_text(prix_str)
    else:
        # Essayer d'extraire le prix du titre ou de la description
        prix = parse_price_from_text(titre) or parse_price_from_text(description)
    
    # Si pas de prix, exclure
    if prix is None:
        logger.debug(f"Exclusion (prix manquant): {titre[:50]}")
        return None
    
    # Vérifier les mots-clés de vente
    if is_sale_announcement(titre, prix):
        return None
    
    # Vérifier les nuitées
    surface = None
    if surface_str and surface_str.strip():
        try:
            surface = float(surface_str)
        except ValueError:
            surface = None
    
    if is_night_rental(titre, prix, surface, description):
        return None
    
    # Vérifier les colocations (MAIS PAS LES BUREAUX)
    if is_colocation(titre, description):
        return None
    
    # Vérifier le prix minimum
    if prix < PRICE_MIN:
        logger.debug(f"Exclusion (prix trop bas): {prix} DH - {titre[:50]}")
        return None
    
    # Vérifier le prix maximum
    if prix > PRICE_MAX:
        logger.debug(f"Exclusion (prix trop élevé): {prix} DH - {titre[:50]}")
        return None
    
    # Vérifier la surface
    if surface is not None:
        if surface < 10 or surface > 2000:
            logger.debug(f"Exclusion (surface aberrante): {surface} m²")
            return None
        
        # Vérifier prix/m²
        price_per_sqm = prix / surface
        if price_per_sqm < PRICE_PER_SQM_MIN or price_per_sqm > PRICE_PER_SQM_MAX:
            logger.debug(f"Exclusion (prix/m² aberrant: {price_per_sqm:.1f} DH/m²)")
            return None
    
    # Nettoyer les colonnes
    row["prix_dh"] = prix
    
    # Si la surface est vide mais présente dans la description
    if surface is None:
        surface_match = re.search(r"(\d+)\s*m[²2]", description, re.I)
        if surface_match:
            surface = float(surface_match.group(1))
            row["surface_m2"] = surface
    
    return row


def clean_mubawab_file(input_path: Path, output_path: Path) -> None:
    """Nettoie le fichier CSV Mubawab."""
    if not input_path.exists():
        logger.error(f"Fichier {input_path} non trouvé")
        return
    
    cleaned_rows = []
    total_rows = 0
    excluded_count = 0
    
    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            total_rows += 1
            cleaned = clean_annonce(row)
            if cleaned:
                cleaned_rows.append(cleaned)
            else:
                excluded_count += 1
    
    logger.info(f"Total: {total_rows} | Conservées: {len(cleaned_rows)} | Exclues: {excluded_count}")
    
    if cleaned_rows:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in cleaned_rows:
                writer.writerow(row)
        logger.info(f"{len(cleaned_rows)} annonces sauvegardées dans {output_path}")


def print_statistics(input_path: Path) -> None:
    """Affiche des statistiques sur les données nettoyées."""
    if not input_path.exists():
        return
    
    import pandas as pd
    
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    
    logger.info("=== STATISTIQUES MUSAWAH NETTOYE ===")
    logger.info(f"Total annonces: {len(df)}")
    
    if not df.empty:
        # Prix
        prices = df["prix_dh"].dropna()
        if not prices.empty:
            logger.info(f"Prix moyen: {prices.mean():.0f} DH")
            logger.info(f"Prix min: {prices.min():.0f} DH")
            logger.info(f"Prix max: {prices.max():.0f} DH")
        
        # Villes
        villes = df["ville"].value_counts().head(10)
        logger.info("Top 10 villes:")
        for ville, count in villes.items():
            if pd.notna(ville):
                logger.info(f"  {ville}: {count}")
        
        # Quartiers
        quartiers = df["quartier"].value_counts().head(10)
        logger.info("Top 10 quartiers:")
        for quartier, count in quartiers.items():
            if pd.notna(quartier):
                logger.info(f"  {quartier}: {count}")
        
        # Vérifier si des bureaux sont présents
        bureaux = df[df["titre"].str.contains("bureau|Bureau", na=False)]
        if not bureaux.empty:
            logger.info(f"=== BUREAUX CONSERVÉS ({len(bureaux)}) ===")
            for _, row in bureaux.iterrows():
                logger.info(f"  {row['titre'][:50]} | {row['prix_dh']} DH | {row['ville']}")


if __name__ == "__main__":
    logger.info("=== Nettoyage des données Mubawab (BUREAUX CONSERVÉS) ===")
    
    # Nettoyer le fichier
    clean_mubawab_file(INPUT_CSV, OUTPUT_CSV)
    
    # Afficher les statistiques
    print_statistics(OUTPUT_CSV)