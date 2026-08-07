"""
Scraper Mubawab.ma - Annonces de VENTE UNIQUEMENT (appartements)
==================================================================
SmartRent Platform - PFE Data Engineering
Objectif : constituer un dataset d'entraînement pour le modèle d'estimation
de prix de vente, en complément du dataset Kaggle.

USAGE ACADÉMIQUE UNIQUEMENT — respecter :
- Rate limiting strict (délai entre requêtes, voir DELAY_SECONDS)
- Volume raisonnable (quelques centaines d'annonces, pas des dizaines de milliers)
- Ne jamais republier les données brutes (uniquement des features agrégées/anonymisées
  dans le rapport de PFE)
- CGU Mubawab : https://www.mubawab.ma/fr/privacy

⚠️ IMPORTANT — SÉLECTEURS CSS À VÉRIFIER AVANT UTILISATION
Les classes CSS ci-dessous (MUBAWAB_SELECTORS) sont des points de départ
raisonnables mais PEUVENT avoir changé depuis la rédaction de ce script.
Avant de lancer un run complet :
  1. Lancer scrape_page(url, page=1) sur UNE seule page
  2. Vérifier que le nombre d'annonces extraites correspond à ce que tu vois
     dans le navigateur
  3. Si 0 résultat : ouvrir la page dans le navigateur, clic droit sur une
     carte d'annonce > "Inspecter", et corriger MUBAWAB_SELECTORS en
     conséquence (voir fonction debug_dump_html() plus bas)
"""

import csv
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mubawab_scraper")

# ===== URL DE BASE POUR LES VENTES =====
BASE_URL = "https://www.mubawab.ma/fr/sc/appartements-a-vendre"
DELAY_SECONDS = 3.0          # délai minimum entre 2 requêtes — ne pas descendre en dessous
MAX_PAGES = 60              # limite volontaire (~20-25 annonces/page selon le site)
OUTPUT_CSV = Path("mubawab_ventes.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

# ===== MOTS-CLÉS EXCLUS (LOCATION) =====
RENT_KEYWORDS = [
    "location", "louer", "loué", "louage", "bail", "locatif",
    "for rent", "rental", "to let", "leased",
    "à louer", "a louer", "appartement à louer", "location mensuelle",
    "loyer", "mois", "/ mois", "par mois", "mensuel", "mensuelle",
    "للإيجار",  # Location en arabe
    "إيجار",    # Location en arabe
    "كراء",     # Location en arabe (dialecte marocain)
]

# ===== PRIX MIN/MAX POUR LES VENTES (en DH) =====
PRICE_MIN = 100000      # En dessous, probablement une erreur ou une location
PRICE_MAX = 50000000    # Au-dessus, probablement une erreur

# ===== PRIX MIN/MAX AU M² (pour détecter les prix aberrants) =====
PRICE_PER_SQM_MIN = 3000   # En dessous, probablement une location ou une erreur
PRICE_PER_SQM_MAX = 100000 # Au-dessus, probablement une erreur

# Sélecteurs à vérifier / ajuster (voir avertissement en tête de fichier)
MUBAWAB_SELECTORS = {
    "card": "li.listingBox, div.listingBox",         # conteneur d'une annonce
    "price": ".priceTag",
    "title": "h2.listingTit, .adTitle",
    "link": "a",
    "location": ".listingH3, .locationCard",
    "surface": ".adSurface, [class*=surface]",
    "details_text": ".listingDetails",                # bloc contenant pièces/chambres/sdb
    "description": ".listingP, .listingText",
}


@dataclass
class Annonce:
    source: str
    titre: str
    prix_dh: Optional[float]
    ville: Optional[str]
    quartier: Optional[str]
    surface_m2: Optional[float]
    pieces: Optional[int]
    chambres: Optional[int]
    salles_de_bain: Optional[int]
    meuble: Optional[bool]
    equipements: str
    description: str
    url: str


def is_rent_announcement(titre: str, prix: Optional[float] = None) -> bool:
    """
    Vérifie si une annonce est une location (et non une vente).
    Retourne True si c'est une location (à exclure).
    """
    if not titre:
        return False
    
    titre_lower = titre.lower()
    
    # Vérifier les mots-clés de location dans le titre
    for keyword in RENT_KEYWORDS:
        if keyword in titre_lower:
            logger.debug(f"Exclusion (mot-clé location): {titre[:50]}")
            return True
    
    # Vérifier les prix aberrants (trop bas = location)
    if prix is not None:
        if prix < PRICE_MIN:
            logger.debug(f"Exclusion (prix trop bas pour une vente): {prix} DH - {titre[:50]}")
            return True
    
    return False


def parse_price(text: str) -> Optional[float]:
    """'1 250 000 DH' -> 1250000.0"""
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return float(digits) if digits else None


def parse_surface(text: str) -> Optional[float]:
    """'160 m²' -> 160.0"""
    if not text:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    return float(match.group(1).replace(",", ".")) if match else None


def parse_int(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def parse_location(text: str) -> tuple[Optional[str], Optional[str]]:
    """'Ville Verte, Bouskoura' -> ('Bouskoura', 'Ville Verte')"""
    if not text:
        return None, None
    parts = [p.strip() for p in text.split(",")]
    if len(parts) >= 2:
        return parts[-1], parts[0]
    return parts[0], None


def debug_dump_html(url: str, out_path: str = "debug_mubawab.html") -> None:
    """Utilitaire de diagnostic : sauvegarde le HTML brut d'une page pour
    inspection manuelle si les sélecteurs ne trouvent aucune annonce."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    Path(out_path).write_text(resp.text, encoding="utf-8")
    logger.info("HTML brut sauvegardé dans %s (%d octets)", out_path, len(resp.text))


def clean_annonce(annonce: Annonce) -> Optional[Annonce]:
    """
    Nettoyage supplémentaire des annonces :
    - Vérification que les données sont cohérentes
    - Suppression des valeurs aberrantes
    """
    # Si le prix est None ou hors plage
    if annonce.prix_dh is None:
        return None
    
    # Vérification supplémentaire des prix
    if annonce.prix_dh < PRICE_MIN or annonce.prix_dh > PRICE_MAX:
        logger.debug(f"Exclusion (prix hors plage): {annonce.prix_dh} DH - {annonce.titre[:50]}")
        return None
    
    # Vérification de la surface (si présent, doit être plausible)
    if annonce.surface_m2 is not None:
        if annonce.surface_m2 < 10 or annonce.surface_m2 > 2000:
            logger.debug(f"Exclusion (surface aberrante): {annonce.surface_m2} m²")
            return None
        
        # Vérification du prix au m²
        price_per_sqm = annonce.prix_dh / annonce.surface_m2
        if price_per_sqm < PRICE_PER_SQM_MIN or price_per_sqm > PRICE_PER_SQM_MAX:
            logger.debug(f"Exclusion (prix/m² aberrant: {price_per_sqm:.1f} DH/m²)")
            return None
    
    # Vérification des chambres (si présent, doit être >= 0 et <= 20)
    if annonce.chambres is not None and (annonce.chambres < 0 or annonce.chambres > 20):
        return None
    
    # Vérification des salles de bain
    if annonce.salles_de_bain is not None and (annonce.salles_de_bain < 0 or annonce.salles_de_bain > 20):
        return None
    
    return annonce


def scrape_page(url: str) -> list[Annonce]:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cards = soup.select(MUBAWAB_SELECTORS["card"])
    if not cards:
        logger.warning(
            "0 annonce trouvée sur %s — les sélecteurs CSS ont probablement changé. "
            "Lance debug_dump_html('%s') puis inspecte le HTML.", url, url
        )
        return []

    results = []
    excluded_count = 0
    for card in cards:
        try:
            price_el = card.select_one(MUBAWAB_SELECTORS["price"])
            title_el = card.select_one(MUBAWAB_SELECTORS["title"])
            link_el = title_el.select_one("a") if title_el else card.select_one("a")
            loc_el = card.select_one(MUBAWAB_SELECTORS["location"])
            surface_el = card.select_one(MUBAWAB_SELECTORS["surface"])
            details_el = card.select_one(MUBAWAB_SELECTORS["details_text"])
            desc_el = card.select_one(MUBAWAB_SELECTORS["description"])

            details_text = details_el.get_text(" ", strip=True) if details_el else ""
            ville, quartier = parse_location(loc_el.get_text(strip=True) if loc_el else "")
            titre = title_el.get_text(strip=True) if title_el else ""
            prix = parse_price(price_el.get_text(strip=True) if price_el else "")

            # Vérifier si c'est une location (à exclure)
            if is_rent_announcement(titre, prix):
                excluded_count += 1
                continue

            pieces_match = re.search(r"(\d+)\s*Pi[eè]ces?", details_text, re.I)
            chambres_match = re.search(r"(\d+)\s*Ch(?:ambres?)?\.?", details_text, re.I)
            sdb_match = re.search(r"(\d+)\s*Salles? de bain", details_text, re.I)

            annonce = Annonce(
                source="mubawab",
                titre=titre,
                prix_dh=prix,
                ville=ville,
                quartier=quartier,
                surface_m2=parse_surface(surface_el.get_text(strip=True) if surface_el else ""),
                pieces=int(pieces_match.group(1)) if pieces_match else None,
                chambres=int(chambres_match.group(1)) if chambres_match else None,
                salles_de_bain=int(sdb_match.group(1)) if sdb_match else None,
                meuble="meublé" in details_text.lower() or "meuble" in details_text.lower(),
                equipements=details_text,
                description=desc_el.get_text(" ", strip=True) if desc_el else "",
                url=link_el["href"] if link_el and link_el.has_attr("href") else "",
            )
            
            # Nettoyage supplémentaire
            cleaned = clean_annonce(annonce)
            if cleaned:
                results.append(cleaned)
            else:
                excluded_count += 1
                
        except Exception as exc:  # une carte malformée ne doit pas arrêter tout le run
            logger.debug("Carte ignorée (parsing échoué): %s", exc)
            continue

    if excluded_count > 0:
        logger.debug(f"{excluded_count} annonces exclues (locations/erreurs) sur cette page")

    return results


def scrape_all(max_pages: int = MAX_PAGES) -> list[Annonce]:
    all_results: list[Annonce] = []
    total_excluded = 0

    for page in range(1, max_pages + 1):
        # ⚠️ Format de pagination à confirmer : Mubawab utilise généralement
        # ?p=N sur ce type de listing. Vérifie en cliquant "page suivante"
        # dans ton navigateur et compare avec l'URL obtenue.
        url = BASE_URL if page == 1 else f"{BASE_URL}:p:{page}"
        logger.info("Scraping page %d/%d : %s", page, max_pages, url)

        page_results = scrape_page(url)
        if not page_results:
            logger.info("Plus d'annonces trouvées, arrêt à la page %d", page)
            break

        all_results.extend(page_results)
        time.sleep(DELAY_SECONDS)  # respect du serveur — ne pas réduire

    return all_results


def save_to_csv(annonces: list[Annonce], path: Path = OUTPUT_CSV) -> None:
    if not annonces:
        logger.warning("Aucune annonce à sauvegarder.")
        return
    
    # Supprimer les doublons (basé sur url)
    seen = set()
    unique_annonces = []
    duplicates = 0
    
    for a in annonces:
        key = a.url or a.titre
        if key not in seen:
            seen.add(key)
            unique_annonces.append(a)
        else:
            duplicates += 1
    
    if duplicates > 0:
        logger.info(f"{duplicates} doublons supprimés")
    
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(annonces[0]).keys()))
        writer.writeheader()
        for a in unique_annonces:
            writer.writerow(asdict(a))
    logger.info("%d annonces de vente sauvegardées dans %s", len(unique_annonces), path)


def print_statistics(annonces: list[Annonce]) -> None:
    """Affiche des statistiques sur les annonces scrappées."""
    if not annonces:
        return
    
    prices = [a.prix_dh for a in annonces if a.prix_dh is not None]
    surfaces = [a.surface_m2 for a in annonces if a.surface_m2 is not None]
    
    logger.info("=== STATISTIQUES DES VENTES ===")
    logger.info(f"Total annonces: {len(annonces)}")
    
    if prices:
        logger.info(f"Prix moyen: {sum(prices)/len(prices):,.0f} DH")
        logger.info(f"Prix min: {min(prices):,.0f} DH")
        logger.info(f"Prix max: {max(prices):,.0f} DH")
    
    if surfaces:
        logger.info(f"Surface moyenne: {sum(surfaces)/len(surfaces):.1f} m²")
    
    # Top villes
    villes = {}
    for a in annonces:
        if a.ville:
            villes[a.ville] = villes.get(a.ville, 0) + 1
    
    if villes:
        top_villes = sorted(villes.items(), key=lambda x: x[1], reverse=True)[:10]
        logger.info("Top 10 villes:")
        for v, count in top_villes:
            logger.info(f"  {v}: {count} annonces")
    
    # Statistiques par type de bien
    studios = sum(1 for a in annonces if a.chambres == 1)
    t2 = sum(1 for a in annonces if a.chambres == 2)
    t3 = sum(1 for a in annonces if a.chambres == 3)
    t4_plus = sum(1 for a in annonces if a.chambres and a.chambres >= 4)
    
    logger.info("=== RÉPARTITION PAR TYPE ===")
    logger.info(f"  Studios (1 chambre): {studios}")
    logger.info(f"  T2 (2 chambres): {t2}")
    logger.info(f"  T3 (3 chambres): {t3}")
    logger.info(f"  T4+ (4+ chambres): {t4_plus}")


if __name__ == "__main__":
    # Étape 1 (recommandé) : tester sur 1 page avant de lancer le run complet
    logger.info("=== Lancement du scraper Mubawab.ma (VENTES UNIQUEMENT) ===")
    logger.info("URL de base : %s", BASE_URL)
    logger.info("Pages max : %d | Délai : %.1fs", MAX_PAGES, DELAY_SECONDS)
    logger.info(f"Filtres:")
    logger.info(f"  - Prix entre {PRICE_MIN:,} et {PRICE_MAX:,} DH")
    logger.info(f"  - Prix/m² entre {PRICE_PER_SQM_MIN:,} et {PRICE_PER_SQM_MAX:,} DH/m²")
    logger.info(f"  - Exclusion des mots-clés de location (français + arabe)")
    
    logger.info("Test sur la première page...")
    test_results = scrape_page(BASE_URL)
    logger.info("%d annonces de vente extraites sur la page de test", len(test_results))

    if not test_results:
        logger.error(
            "Aucune annonce extraite. Lance debug_dump_html('%s') et vérifie "
            "MUBAWAB_SELECTORS avant de continuer.", BASE_URL
        )
    else:
        logger.info("Sélecteurs OK, lancement du scraping complet...")
        all_annonces = scrape_all()
        save_to_csv(all_annonces)
        print_statistics(all_annonces)
        
        # Afficher quelques exemples
        if all_annonces:
            logger.info("--- Exemples de ventes ---")
            for a in all_annonces[:5]:
                logger.info("  %s | %s DH | %s | %s m²", 
                           a.titre[:40], f"{a.prix_dh:,.0f}", a.ville, a.surface_m2)