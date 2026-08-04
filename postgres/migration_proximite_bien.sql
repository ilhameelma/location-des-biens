-- ============================================================
-- Migration : stockage des proximités (POI Overpass/OSM) avec l'annonce
-- ============================================================
-- Jusqu'ici, les commodités à proximité (hôtels, jardins, écoles, centres
-- commerciaux) étaient recalculées à la volée via Overpass à CHAQUE
-- affichage de la fiche du bien (cache mémoire de 6h seulement, perdu au
-- redémarrage du back-end) — d'où la lenteur ressentie.
--
-- Cette migration ajoute deux colonnes pour stocker durablement le résultat
-- avec l'annonce elle-même : calculé une fois à la publication (en tâche
-- d'arrière-plan), puis simplement relu à chaque consultation.
--
-- À exécuter une seule fois sur une base existante :
--   Get-Content .\postgres\migration_proximite_bien.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

ALTER TABLE bien ADD COLUMN IF NOT EXISTS proximite_data JSONB;
ALTER TABLE bien ADD COLUMN IF NOT EXISTS proximite_calculee_le TIMESTAMP;

-- Pas d'index nécessaire : ces colonnes ne sont jamais utilisées comme
-- critère de filtre/recherche, seulement lues par id de bien.

-- Pense ensuite à lancer le script de rattrapage pour les annonces déjà
-- publiées avant cette migration (elles n'ont pas encore de proximité
-- stockée et continueront de recalculer à la volée tant qu'il n'a pas
-- tourné) :
--   cd backend
--   venv\Scripts\activate
--   python scripts/calculer_proximites_existants.py
