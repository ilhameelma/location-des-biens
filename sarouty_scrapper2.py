"""
Scraper Sarouty.ma - Annonces de location UNIQUEMENT (via Playwright)
======================================================================
SmartRent Platform - PFE Data Engineering

Sarouty.ma utilise une pagination JavaScript (boutons cliquables).
On ne peut pas simplement changer ?page=N dans l'URL — il faut cliquer
sur les boutons de pagination pour charger la page suivante.

FILTRE : EXCLUT LES ANNONCES DE VENTE ET LES LOCATIONS À LA NUITÉE
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
MAX_PAGES = 60
OUTPUT_CSV = Path("sarouty_locations_clean.csv")

# ===== MOTS-CLÉS EXCLUS (VENTE) =====
SALE_KEYWORDS = [
    "vente", "vendre", "vendu", "achat", "acheter",
    "for sale", "sell", "sold", "buy", "purchase",
    "à vendre", "a vendre", "property for sale",
    "للبيع",  # Vente en arabe
    "بيع",    # Vente en arabe
]

# ===== MOTS-CLÉS EXCLUS (LOCATIONS À LA NUITÉE) =====
NIGHT_KEYWORDS = [
    "nuit", "nuitée", "nuitées",
    "night", "per night", "overnight",
    "vacances", "saisonnière", "saisonnier",
    "touristique", "séjour", "location saisonnière",
    "par nuit", "à la nuit", "à la nuitée",
    "jour", "par jour", "quotidien",
    "minimum 3 nuits", "minimum 2 nuits",
]

# ===== PRIX MIN/MAX POUR LES LOCATIONS (en DH) =====
PRICE_MIN = 2000       # En dessous, probablement une erreur ou une nuitée
PRICE_MAX = 100000    # Au-dessus, probablement une vente

# ===== PRIX MIN AU M² (pour détecter les prix aberrants) =====
PRICE_PER_SQM_MIN = 40   # En dessous, probablement une nuitée ou une erreur
PRICE_PER_SQM_MAX = 2000 # Au-dessus, probablement une erreur


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


def is_sale_announcement(titre: str, prix: Optional[float] = None) -> bool:
    """
    Vérifie si une annonce est une vente (et non une location).
    Retourne True si c'est une vente (à exclure).
    """
    if not titre:
        return False
    
    titre_lower = titre.lower()
    
    # Vérifier les mots-clés de vente dans le titre
    for keyword in SALE_KEYWORDS:
        if keyword in titre_lower:
            logger.debug(f"Exclusion (mot-clé vente): {titre[:50]}")
            return True
    
    # Vérifier les prix aberrants (trop élevés = vente)
    if prix is not None:
        if prix > PRICE_MAX:
            logger.debug(f"Exclusion (prix trop élevé): {prix} DH - {titre[:50]}")
            return True
    
    return False


def is_night_rental(titre: str, prix: Optional[float] = None, surface: Optional[float] = None) -> bool:
    """
    Vérifie si une annonce est une location à la nuitée (et non mensuelle).
    Retourne True si c'est une location à la nuitée (à exclure).
    """
    if not titre:
        return False
    
    titre_lower = titre.lower()
    
    # Vérifier les mots-clés de nuitée dans le titre
    for keyword in NIGHT_KEYWORDS:
        if keyword in titre_lower:
            logger.debug(f"Exclusion (mot-clé nuitée): {titre[:50]}")
            return True
    
    # Vérifier le prix au m² (si trop bas → probablement une nuitée)
    if prix is not None and surface is not None and surface > 0:
        price_per_sqm = prix / surface
        if price_per_sqm < PRICE_PER_SQM_MIN:
            logger.debug(f"Exclusion (prix/m² trop bas: {price_per_sqm:.1f} DH/m²): {titre[:50]}")
            return True
        if price_per_sqm > PRICE_PER_SQM_MAX:
            logger.debug(f"Exclusion (prix/m² trop élevé: {price_per_sqm:.1f} DH/m²): {titre[:50]}")
            return True
    
    return False


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
    
    prix = parse_price(price_text)
    surface = parse_int(details.get("m²", ""))
    
    # Vérifier si c'est une vente (à exclure)
    if is_sale_announcement(title, prix):
        return None
    
    # Vérifier si c'est une location à la nuitée (à exclure)
    if is_night_rental(title, prix, surface):
        return None
    
    # Vérifier le prix minimum
    if prix is not None and prix < PRICE_MIN:
        logger.debug(f"Exclusion (prix trop bas): {prix} DH - {title[:50]}")
        return None

    return Annonce(
        source="sarouty",
        listing_id=listing_id,
        titre=title,
        prix_dh=prix,
        quartier=quartier,
        surface_m2=surface,
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
    excluded_count = 0
    
    for card in cards:
        annonce = parse_card(card)
        if annonce:
            results.append(annonce)
        else:
            excluded_count += 1
    
    if excluded_count > 0:
        logger.debug(f"{excluded_count} annonces exclues (ventes/nuitées/erreurs) sur cette page")

    return results


def get_current_page_number(page: Page) -> int:
    """Récupère le numéro de page actuel depuis le bouton actif de pagination."""
    try:
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


def scrape_all() -> list[Annonce]:
    """Scrape toutes les pages en cliquant sur la pagination."""
    all_results: list[Annonce] = []
    total_excluded = 0

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
            logger.info("%d annonces de location trouvées sur la page %d", len(results), current_page)

            if not results and current_page > 1:
                logger.info("Plus d'annonces de location trouvées, arrêt.")
                break

            # Nettoyage supplémentaire des annonces
            cleaned_results = []
            for annonce in results:
                cleaned = clean_annonce(annonce)
                if cleaned:
                    cleaned_results.append(cleaned)
                else:
                    total_excluded += 1
            
            all_results.extend(cleaned_results)
            logger.info("Après nettoyage: %d annonces valides", len(cleaned_results))

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

    logger.info(f"Total des annonces exclues (ventes/nuitées/erreurs): {total_excluded}")
    return all_results


def save_to_csv(annonces: list[Annonce], path: Path = OUTPUT_CSV) -> None:
    if not annonces:
        logger.warning("Aucune annonce à sauvegarder.")
        return
    
    # Supprimer les doublons (basé sur listing_id)
    seen = set()
    unique_annonces = []
    duplicates = 0
    
    for a in annonces:
        key = a.listing_id or a.titre
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
    
    logger.info("%d annonces de location sauvegardées dans %s", len(unique_annonces), path)


def print_statistics(annonces: list[Annonce]) -> None:
    """Affiche des statistiques sur les annonces scrappées."""
    if not annonces:
        return
    
    prices = [a.prix_dh for a in annonces if a.prix_dh is not None]
    surfaces = [a.surface_m2 for a in annonces if a.surface_m2 is not None]
    
    logger.info("=== STATISTIQUES DES LOCATIONS ===")
    logger.info(f"Total annonces: {len(annonces)}")
    
    if prices:
        logger.info(f"Prix moyen: {sum(prices)/len(prices):.0f} DH")
        logger.info(f"Prix min: {min(prices)} DH")
        logger.info(f"Prix max: {max(prices)} DH")
    
    if surfaces:
        logger.info(f"Surface moyenne: {sum(surfaces)/len(surfaces):.1f} m²")
    
    # Top quartiers
    quartiers = {}
    for a in annonces:
        if a.quartier:
            quartiers[a.quartier] = quartiers.get(a.quartier, 0) + 1
    
    if quartiers:
        top_quartiers = sorted(quartiers.items(), key=lambda x: x[1], reverse=True)[:10]
        logger.info("Top 10 quartiers:")
        for q, count in top_quartiers:
            logger.info(f"  {q}: {count} annonces")
    
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
    logger.info("=== Lancement du scraper Sarouty.ma (LOCATIONS UNIQUEMENT) ===")
    logger.info("URL de base : %s", BASE_URL)
    logger.info("Pages max : %d | Délai : %.1fs", MAX_PAGES, DELAY_SECONDS)
    logger.info(f"Filtres:")
    logger.info(f"  - Prix entre {PRICE_MIN} et {PRICE_MAX} DH")
    logger.info(f"  - Prix/m² entre {PRICE_PER_SQM_MIN} et {PRICE_PER_SQM_MAX} DH/m²")
    logger.info(f"  - Exclusion des mots-clés de vente (français + arabe)")
    logger.info(f"  - Exclusion des mots-clés de nuitée")
    logger.info(f"  - Exclusion des surfaces aberrantes (10-2000 m²)")

    all_annonces = scrape_all()

    # Sauvegarde finale (les doublons sont gérés dans save_to_csv)
    save_to_csv(all_annonces)

    # Afficher des statistiques
    print_statistics(all_annonces)

    # Afficher quelques exemples
    if all_annonces:
        logger.info("--- Exemples de locations ---")
        for a in all_annonces[:5]:
            logger.info("  %s | %s DH | %s | %s m²", 
                       a.titre[:40], a.prix_dh, a.quartier, a.surface_m2)