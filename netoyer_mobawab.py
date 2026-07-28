"""
Nettoyage du dataset Mubawab (mubawab_locations.csv)
======================================================
Corrige, sans re-scraper :
1. Retire les cartes "Immobilier neuf" / projets promotionnels (prix de VENTE,
   pas de loyer) — repérables via l'URL qui contient "/fr/p/" au lieu de "/fr/a/"
2. Déduplique les annonces (même URL vue plusieurs fois entre pages)
3. Remplit surface_m2 / pieces / chambres / salles_de_bain / meuble via regex
   de secours sur le titre + la description, quand la colonne est vide
4. Normalise les espaces/retours à la ligne dans le titre

USAGE
-----
python clean_mubawab.py mubawab_locations.csv mubawab_locations_clean.csv
"""

import csv
import re
import sys

SURFACE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\xb2", re.I)
CHAMBRES_RE = re.compile(r"(\d+)\s*chambres?\b", re.I)
PIECES_RE = re.compile(r"(\d+)\s*pi[eè]ces?\b", re.I)
SDB_RE = re.compile(r"(\d+)\s*(?:salles?\s+de\s+bains?|sdb)\b", re.I)
NON_MEUBLE_RE = re.compile(r"non[\s-]meubl", re.I)
MEUBLE_RE = re.compile(r"meubl[eé]", re.I)


def clean_number(match) -> str:
    return match.group(1).replace(",", ".") if match else ""


def guess_meuble(text: str) -> str:
    if NON_MEUBLE_RE.search(text):
        return "False"
    if MEUBLE_RE.search(text):
        return "True"
    return ""  # inconnu — laissé vide plutôt que deviné à tort


def clean_row(row: dict) -> dict:
    text = f"{row.get('titre', '')} {row.get('description', '')}"

    if not row.get("surface_m2"):
        row["surface_m2"] = clean_number(SURFACE_RE.search(text))
    if not row.get("chambres"):
        row["chambres"] = clean_number(CHAMBRES_RE.search(text))
    if not row.get("pieces"):
        row["pieces"] = clean_number(PIECES_RE.search(text))
    if not row.get("salles_de_bain"):
        row["salles_de_bain"] = clean_number(SDB_RE.search(text))
    if not row.get("meuble") or row.get("meuble") == "False":
        guessed = guess_meuble(text)
        if guessed:
            row["meuble"] = guessed

    row["titre"] = re.sub(r"\s+", " ", row.get("titre", "")).strip()
    return row


def main(input_path: str, output_path: str) -> None:
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_in = len(rows)

    # 1. Retirer les projets promotionnels (URL "/fr/p/" au lieu de "/fr/a/")
    rows = [r for r in rows if "/fr/a/" in r.get("url", "")]
    after_promo_filter = len(rows)

    # 2. Dédupliquer par URL (identifiant unique de l'annonce)
    seen = set()
    deduped = []
    for r in rows:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            deduped.append(r)
    rows = deduped
    after_dedup = len(rows)

    # 3. Extraction de secours + nettoyage titre
    rows = [clean_row(r) for r in rows]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Lignes de départ         : {total_in}")
    print(f"Après retrait des promos : {after_promo_filter} (-{total_in - after_promo_filter})")
    print(f"Après dédoublonnage      : {after_dedup} (-{after_promo_filter - after_dedup})")
    print(f"Fichier nettoyé écrit    : {output_path}")

    # Stats de complétude après extraction de secours
    for field in ("surface_m2", "pieces", "chambres", "salles_de_bain", "meuble"):
        filled = sum(1 for r in rows if r.get(field))
        print(f"  {field:16s}: {filled}/{len(rows)} renseigné ({100*filled//len(rows) if rows else 0}%)")


if __name__ == "__main__":
    input_path = sys.argv[1] if len(sys.argv) > 1 else "mubawab_locations.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "mubawab_locations_clean.csv"
    main(input_path, output_path)