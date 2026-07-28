"""
Scraper Sarouty.ma - Annonces de location (via Playwright)
=============================================================
SmartRent Platform - PFE Data Engineering

Sarouty.ma est une application React/Material-UI (MUI) : les annonces sont
injectées en JavaScript après chargement de la page, donc un simple
requests.get() ne verrait rien. Playwright pilote un vrai navigateur pour
laisser le JS s'exécuter, puis on parse le HTML final avec BeautifulSoup.

Sélecteurs validés le 2026-07-27 sur un export réel de la page (25/25
cartes correctement extraites : titre, prix, ville/quartier, chambres,
salles de bain, surface). On s'appuie sur les classes MUI stables
(MuiCard-root, MuiTypography-h5, MuiTypography-h4, MuiTypography-body1)
plutôt que sur les classes "css-xxxxx" générées par Emotion, qui elles
peuvent changer à chaque déploiement du site.

⚠️ Limite connue : l'URL individuelle de chaque annonce n'est pas présente
dans le HTML statique (navigation gérée en JS côté client, sans <a href>
classique). On conserve l'identifiant interne (data-listing-id) à la place
— suffisant pour un dataset d'entraînement, pas pour retourner sur l'annonce.

USAGE ACADÉMIQUE UNIQUEMENT :
- Rate limiting strict (voir DELAY_SECONDS)
- Volume raisonnable (quelques centaines d'annonces)
- CGU Sarouty : https://www.sarouty.ma/conditions-generales-dutilisation/

INSTALLATION
------------
pip install playwright beautifulsoup4 --break-system-packages
playwright install chromium
"""

import csv
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sarouty_scraper")

BASE_URL = "https://www.sarouty.ma/louer/appartements-a-louer/"
DELAY_SECONDS = 3.0
MAX_PAGES = 20
OUTPUT_CSV = Path("sarouty_locations.csv")


@dataclass
class Annonce:
    source: str
    listing_id: Optional[str]
    titre: str
    prix_dh: Optional[float]
    quartier: Optional[str]
    surface_m2: Optional[float]
    chambres: Optional[int]
    salles_de_bain: Optional[int]


def parse_price(text: str) -> Optional[float]:
    """'9 500 DH / Mois' -> 9500.0 (gère aussi les marqueurs unicode RTL)"""
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return float(digits) if digits else None


def parse_int(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def parse_card(card) -> Optional[Annonce]:
    h5s = card.select("h5.MuiTypography-h5")
    if not h5s:
        return None

    title = h5s[0].get_text(strip=True)
    price_text = next((h.get_text(strip=True) for h in h5s if "DH" in h.get_text()), "")

    ville_el = card.select_one("p.MuiTypography-body1")
    quartier = ville_el.get_text(strip=True) if ville_el else None

    details: dict[str, str] = {}
    for h4 in card.select("h4.MuiTypography-h4"):
        spans = h4.select("span.MuiTypography-body1")
        if len(spans) >= 2:
            details[spans[1].get_text(strip=True)] = spans[0].get_text(strip=True)

    listing_id_el = card.select_one("[data-listing-id]")
    listing_id = listing_id_el["data-listing-id"] if listing_id_el else None

    return Annonce(
        source="sarouty",
        listing_id=listing_id,
        titre=title,
        prix_dh=parse_price(price_text),
        quartier=quartier,
        surface_m2=parse_int(details.get("m²", "")),
        chambres=parse_int(details.get("Chambres", "")),
        salles_de_bain=parse_int(details.get("Salles de bain", details.get("Salle de bain", ""))),
    )


def debug_screenshot(page: Page, path: str = "debug_sarouty.png") -> None:
    page.screenshot(path=path, full_page=True)
    logger.info("Capture sauvegardée dans %s", path)


def debug_dump_rendered_html(page: Page, path: str = "debug_sarouty_rendered.html") -> None:
    Path(path).write_text(page.content(), encoding="utf-8")
    logger.info("HTML rendu sauvegardé dans %s", path)


def scrape_page(page: Page, url: str) -> list[Annonce]:
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)  # laisse le JS peupler la liste

    soup = BeautifulSoup(page.content(), "html.parser")
    cards = soup.select("div.MuiCard-root")

    if not cards:
        logger.warning("0 carte trouvée sur %s — le site a peut-être changé de structure.", url)
        return []

    results = []
    for card in cards:
        annonce = parse_card(card)
        if annonce:
            results.append(annonce)

    return results


def scrape_all() -> list[Annonce]:
    all_results: list[Annonce] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ))

        for page_num in range(1, MAX_PAGES + 1):
            # ⚠️ Format de pagination à confirmer manuellement (clique sur
            # "page suivante" dans le navigateur et compare l'URL obtenue) —
            # ce paramètre ?page=N est une hypothèse raisonnable pour un
            # site MUI mais pas garantie.
            url = BASE_URL if page_num == 1 else f"{BASE_URL}?page={page_num}"
            logger.info("Scraping page %d/%d : %s", page_num, MAX_PAGES, url)

            page_results = scrape_page(page, url)
            if not page_results:
                logger.info("Plus d'annonces trouvées, arrêt à la page %d", page_num)
                break

            all_results.extend(page_results)
            time.sleep(DELAY_SECONDS)

        browser.close()

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
    logger.info("Test sur la première page...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        debug_screenshot(page)
        soup = BeautifulSoup(page.content(), "html.parser")
        test_results = [parse_card(c) for c in soup.select("div.MuiCard-root")]
        test_results = [r for r in test_results if r]
        browser.close()

    logger.info("%d annonces extraites sur la page de test", len(test_results))
    if not test_results:
        logger.error("Aucune annonce extraite — structure du site probablement modifiée.")
    else:
        for r in test_results[:3]:
            logger.info("Exemple : %s", r)
        logger.info("Sélecteurs OK, lancement du scraping complet...")
        all_annonces = scrape_all()
        save_to_csv(all_annonces)
