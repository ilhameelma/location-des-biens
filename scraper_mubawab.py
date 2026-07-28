"""
Scraper Mubawab.ma - Annonces de location (appartements)
==========================================================
SmartRent Platform - PFE Data Engineering
Objectif : constituer un dataset d'entraînement pour le modèle d'estimation
de loyer (étape 16a), en complément du dataset Kaggle (prix de vente).

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

BASE_URL = "https://www.mubawab.ma/fr/sc/appartements-a-louer"
DELAY_SECONDS = 3.0          # délai minimum entre 2 requêtes — ne pas descendre en dessous
MAX_PAGES = 30                # limite volontaire (~20-25 annonces/page selon le site)
OUTPUT_CSV = Path("mubawab_locations.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}

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


def parse_price(text: str) -> Optional[float]:
    """'14 000 DH' -> 14000.0"""
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

            pieces_match = re.search(r"(\d+)\s*Pi[eè]ces?", details_text, re.I)
            chambres_match = re.search(r"(\d+)\s*Ch(?:ambres?)?\.?", details_text, re.I)
            sdb_match = re.search(r"(\d+)\s*Salles? de bain", details_text, re.I)

            annonce = Annonce(
                source="mubawab",
                titre=title_el.get_text(strip=True) if title_el else "",
                prix_dh=parse_price(price_el.get_text(strip=True) if price_el else ""),
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
            results.append(annonce)
        except Exception as exc:  # une carte malformée ne doit pas arrêter tout le run
            logger.debug("Carte ignorée (parsing échoué): %s", exc)
            continue

    return results


def scrape_all(max_pages: int = MAX_PAGES) -> list[Annonce]:
    all_results: list[Annonce] = []
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
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(annonces[0]).keys()))
        writer.writeheader()
        for a in annonces:
            writer.writerow(asdict(a))
    logger.info("%d annonces sauvegardées dans %s", len(annonces), path)


if __name__ == "__main__":
    # Étape 1 (recommandé) : tester sur 1 page avant de lancer le run complet
    logger.info("Test sur la première page...")
    test_results = scrape_page(BASE_URL)
    logger.info("%d annonces extraites sur la page de test", len(test_results))

    if not test_results:
        logger.error(
            "Aucune annonce extraite. Lance debug_dump_html('%s') et vérifie "
            "MUBAWAB_SELECTORS avant de continuer.", BASE_URL
        )
    else:
        logger.info("Sélecteurs OK, lancement du scraping complet...")
        all_annonces = scrape_all()
        save_to_csv(all_annonces)
