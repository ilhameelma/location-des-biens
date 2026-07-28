"""
Nettoyage du dataset Sarouty (sarouty_locations.csv)
======================================================
La pagination par URL (?page=N) ne fonctionnait pas — chaque "page" a en
fait rechargé les mêmes ~25 annonces de la page 1. Ce script déduplique
par listing_id pour ne garder que les annonces réellement distinctes.

Pour obtenir plus de données réelles, utilise la version corrigée de
scraper_sarouty_playwright.py (pagination par clic) plutôt que de relancer
ce nettoyage seul.

USAGE
-----
python clean_sarouty.py sarouty_locations.csv sarouty_locations_clean.csv
"""

import csv
import sys


def main(input_path: str, output_path: str) -> None:
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_in = len(rows)

    seen = set()
    deduped = []
    for r in rows:
        lid = r.get("listing_id", "")
        if lid and lid not in seen:
            seen.add(lid)
            deduped.append(r)
    rows = deduped

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Lignes de départ      : {total_in}")
    print(f"Annonces uniques      : {len(rows)}")
    print(f"Fichier nettoyé écrit : {output_path}")
    print()
    print("⚠️ Ce nombre d'annonces uniques est probablement proche du total")
    print("   réellement disponible sur UNE SEULE page de résultats (~25-30).")
    print("   Utilise le scraper corrigé (pagination par clic) pour aller")
    print("   chercher les pages suivantes.")


if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else "sarouty_locations.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "sarouty_locations_clean.csv"
    main(input_path, output_path)