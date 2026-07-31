"""
Étape 18 — Recherche avancée (Elasticsearch)

Script one-shot pour indexer dans Elasticsearch tous les biens déjà présents
dans PostgreSQL au moment où l'étape 18 est mise en place — sans ça, seuls
les biens créés/modifiés APRÈS cette mise à jour seraient indexés (l'index
se construit au fil de l'eau depuis app/routers/biens.py), et les biens plus
anciens resteraient invisibles à la recherche avancée.

À relancer aussi après tout `docker-compose down -v` (l'index Elasticsearch
n'est pas persistant si le volume est supprimé) ou en cas de doute sur la
cohérence de l'index.

Utilisation :

    cd backend
    venv\\Scripts\\activate
    python scripts/reindex_elasticsearch.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elasticsearch.helpers import bulk

from app.database import SessionLocal
from app import models
from app.es_client import _get_client, _bien_to_document, ensure_index
from app.config import settings


def main():
    ensure_index()
    client = _get_client()
    if client is None:
        print(
            "[smartrent] Elasticsearch indisponible — vérifiez que "
            "`docker-compose up -d` a bien démarré le service `elasticsearch` "
            "et que ELASTICSEARCH_URL pointe dessus."
        )
        sys.exit(1)

    db = SessionLocal()
    try:
        biens = db.query(models.Bien).all()
        actions = [
            {
                "_op_type": "index",
                "_index": settings.elasticsearch_index,
                "_id": str(bien.id),
                "_source": _bien_to_document(bien),
            }
            for bien in biens
        ]
        if not actions:
            print("[smartrent] Aucun bien en base à indexer.")
            return

        success, errors = bulk(client, actions, stats_only=False, raise_on_error=False)
        print(f"[smartrent] Terminé. {success} bien(s) indexé(s), {len(errors)} erreur(s).")
        for err in errors[:5]:
            print(f"  - {err}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
