"""
Scraper Sarouty.ma - Annonces de location (via Playwright)
=============================================================
SmartRent Platform - PFE Data Engineering

Sarouty.ma utilise une pagination JavaScript (boutons cliquables).
On ne peut pas simplement changer ?page=N dans l'URL — il faut cliquer
sur les boutons de pagination pour charger la page suivante.

USAGE ACADÉMIQUE UNIQUEMENT
"""

import csv
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

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
    """'9 500 DH / Mois' -> 9500.0"""
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


def scrape_current_page(page: Page) -> list[Annonce]:
    """Parse les cartes de la page actuelle (déjà chargée)."""
    soup = BeautifulSoup(page.content(), "html.parser")
    cards = soup.select("div.MuiCard-root")

    if not cards:
        logger.warning("0 carte trouvée — le site a peut-être changé de structure.")
        return []

    results = []
    for card in cards:
        annonce = parse_card(card)
        if annonce:
            results.append(annonce)

    return results


def get_current_page_number(page: Page) -> int:
    """Récupère le numéro de page actuel depuis le bouton actif de pagination."""
    try:
        # Le bouton actif a généralement une classe ou un style différent
        # Cherchons un élément qui ressemble à un numéro de page actif
        soup = BeautifulSoup(page.content(), "html.parser")

        # Méthode 1 : chercher un bouton avec une classe "active" ou "selected"
        active_btn = soup.select_one("button.Mui-selected, button[aria-current='true'], .active, [aria-current='page']")
        if active_btn:
            text = active_btn.get_text(strip=True)
            if text.isdigit():
                return int(text)

        # Méthode 2 : chercher dans les liens de pagination
        pagination = soup.select("nav.MuiPagination-root button, .pagination button, [role='navigation'] button")
        for btn in pagination:
            classes = btn.get("class", [])
            if any(c in str(classes) for c in ["selected", "active", "Mui-selected"]):
                text = btn.get_text(strip=True)
                if text.isdigit():
                    return int(text)

    except Exception as e:
        logger.debug("Impossible de détecter la page actuelle: %s", e)

    return 1  # Par défaut, page 1


def click_next_page(page: Page, current_page: int) -> bool:
    """
    Clique sur le bouton de la page suivante.
    Retourne True si on a réussi à changer de page, False sinon.
    """
    try:
        next_page_num = current_page + 1
        logger.info("Tentative de clic sur la page %d...", next_page_num)

        # Stratégie 1 : chercher un bouton avec le numéro exact
        selectors = [
            f'button:has-text("{next_page_num}")',
            f'button.MuiPaginationItem-page:has-text("{next_page_num}")',
            f'[role="button"]:has-text("{next_page_num}")',
            f'a:has-text("{next_page_num}")',
        ]

        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    logger.info("Clic sur le bouton page %d (sélecteur: %s)", next_page_num, selector)
                    return True
            except PlaywrightTimeout:
                continue
            except Exception:
                continue

        # Stratégie 2 : chercher le bouton "Suivant" / flèche droite
        next_selectors = [
            'button[aria-label="Go to next page"]',
            'button[aria-label="Next"]',
            'button.MuiPaginationItem-next',
            'svg[data-testid="NavigateNextIcon"]',
            'button:has(svg[data-testid="NavigateNextIcon"])',
            'button:has-text(">")',
            '[aria-label="next"]',
        ]

        for selector in next_selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    # Vérifier si le bouton n'est pas désactivé
                    disabled = btn.get_attribute("disabled") or btn.get_attribute("aria-disabled")
                    if disabled and disabled.lower() in ("true", ""):
                        logger.info("Bouton 'Suivant' désactivé — dernière page atteinte.")
                        return False
                    btn.click()
                    logger.info("Clic sur le bouton 'Suivant' (%s)", selector)
                    return True
            except PlaywrightTimeout:
                continue
            except Exception:
                continue

        logger.warning("Aucun bouton de pagination trouvé pour la page %d", next_page_num)
        return False

    except Exception as e:
        logger.error("Erreur lors du clic pagination: %s", e)
        return False


def wait_for_page_load(page: Page, previous_page: int, timeout: int = 10000) -> bool:
    """Attend que la page ait changé (vérification du numéro de page)."""
    start_time = time.time()
    while time.time() - start_time < timeout / 1000:
        current = get_current_page_number(page)
        if current > previous_page:
            return True
        time.sleep(0.5)
    return False


def scrape_all() -> list[Annonce]:
    """Scrape toutes les pages en cliquant sur la pagination."""
    all_results: list[Annonce] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        )

        # Charger la première page
        logger.info("Chargement de la page 1 : %s", BASE_URL)
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)  # Laisse le JS s'exécuter

        current_page = 1

        while current_page <= MAX_PAGES:
            logger.info("=== Scraping page %d ===", current_page)

            # Parser la page actuelle
            results = scrape_current_page(page)
            logger.info("%d annonces trouvées sur la page %d", len(results), current_page)

            if not results and current_page > 1:
                logger.info("Plus d'annonces trouvées, arrêt.")
                break

            all_results.extend(results)

            # Sauvegarder un screenshot pour debug (optionnel)
            if current_page == 1:
                page.screenshot(path="debug_page_1.png")
                logger.info("Screenshot de la page 1 sauvegardé dans debug_page_1.png")

            # Essayer de passer à la page suivante
            if current_page >= MAX_PAGES:
                logger.info("Nombre maximum de pages atteint (%d).", MAX_PAGES)
                break

            success = click_next_page(page, current_page)
            if not success:
                logger.info("Impossible d'aller à la page suivante — fin du scraping.")
                break

            # Attendre que la page se charge
            page.wait_for_timeout(3000)  # Délai pour le chargement AJAX

            # Vérifier qu'on a bien changé de page
            new_page = get_current_page_number(page)
            if new_page <= current_page:
                # La pagination n'a pas changé, essayer de scroller pour charger plus
                logger.info("Page non changée, tentative de scroll...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                new_page = get_current_page_number(page)
                if new_page <= current_page:
                    logger.info("Toujours sur la même page après scroll — arrêt.")
                    break

            current_page = new_page
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
    logger.info("=== Lancement du scraper Sarouty.ma ===")
    logger.info("URL de base : %s", BASE_URL)
    logger.info("Pages max : %d | Délai : %.1fs", MAX_PAGES, DELAY_SECONDS)

    all_annonces = scrape_all()

    # Supprimer les doublons (basé sur listing_id)
    seen = set()
    unique_annonces = []
    for a in all_annonces:
        key = a.listing_id or a.titre
        if key not in seen:
            seen.add(key)
            unique_annonces.append(a)

    logger.info("Total : %d annonces uniques sur %d extraites", len(unique_annonces), len(all_annonces))
    save_to_csv(unique_annonces)

    # Afficher quelques exemples
    if unique_annonces:
        logger.info("--- Exemples ---")
        for a in unique_annonces[:5]:
            logger.info("  %s | %s DH | %s | %s m²", a.titre[:50], a.prix_dh, a.quartier, a.surface_m2)