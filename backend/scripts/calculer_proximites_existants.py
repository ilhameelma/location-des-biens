"""
Complément étape 17 — Proximités stockées avec l'annonce

Script one-shot pour calculer et stocker les proximités (POI Overpass) de
tous les biens déjà présents en base au moment où cette fonctionnalité est
mise en place — sans ça, seuls les biens créés/modifiés APRÈS cette mise à
jour auraient des proximités stockées (le calcul se déclenche au fil de
l'eau depuis app/routers/biens.py), et les biens plus anciens continueraient
à recalculer à la volée (lent) à chaque affichage de leur fiche.

Ne traite que les biens :
  - avec des coordonnées GPS (latitude/longitude non nulles) ;
  - sans proximité stockée (`proximite_data IS NULL`) — relancer le script
    ne repasse donc pas sur les biens déjà traités. Pour forcer un recalcul
    complet (ex. après un ajustement du rayon par défaut), utiliser --force.

Une petite pause entre chaque bien évite de solliciter trop vite les
miroirs Overpass (instances publiques, partagées, rate-limitées) sur un
gros volume de biens.

Utilisation :

    cd backend
    venv\\Scripts\\activate
    python scripts/calculer_proximites_existants.py
    python scripts/calculer_proximites_existants.py --force
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app import models
from app.poi_client import calculer_et_stocker_proximite

PAUSE_ENTRE_BIENS_SECONDES = 1.5


def main():
    force = "--force" in sys.argv

    db = SessionLocal()
    try:
        query = db.query(models.Bien.id).filter(
            models.Bien.latitude.isnot(None),
            models.Bien.longitude.isnot(None),
        )
        if not force:
            query = query.filter(models.Bien.proximite_data.is_(None))
        ids = [str(row.id) for row in query.all()]
    finally:
        db.close()

    if not ids:
        print(
            "[smartrent] Aucun bien à traiter (tous ont déjà des proximités "
            "stockées — utilisez --force pour tout recalculer)."
        )
        return

    print(f"[smartrent] {len(ids)} bien(s) à traiter...")
    reussis = 0
    for i, bien_id in enumerate(ids, start=1):
        calculer_et_stocker_proximite(bien_id)

        # Vérifie si le calcul a effectivement abouti (Overpass peut être
        # temporairement indisponible pour un bien donné, sans que le
        # script ne s'arrête pour autant).
        db = SessionLocal()
        try:
            bien = db.get(models.Bien, bien_id)
            if bien and bien.proximite_data:
                reussis += 1
        finally:
            db.close()

        print(f"  [{i}/{len(ids)}] {bien_id} traité")
        if i < len(ids):
            time.sleep(PAUSE_ENTRE_BIENS_SECONDES)

    echecs = len(ids) - reussis
    print(f"[smartrent] Terminé. {reussis} bien(s) mis à jour, {echecs} échec(s) (Overpass injoignable — relancer le script plus tard pour les rattraper).")


if __name__ == "__main__":
    main()
