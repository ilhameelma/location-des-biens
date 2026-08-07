-- ============================================================
-- Migration : équipements d'une annonce (façon Airbnb)
-- ============================================================
-- Ajoute la liste des équipements/commodités proposés par un bien
-- ("Ce que propose ce logement" côté fiche détaillée). Stockée en JSONB
-- comme une simple liste de codes texte (ex. ["wifi", "meuble", "ascenseur"]),
-- le catalogue des codes valides étant défini côté front-end
-- (frontend/src/lib/equipements.ts) et propre à chaque type_bien
-- (résidentiel / bureau / magasin / garage / terrain).
--
-- À exécuter une seule fois sur une base existante :
--   Get-Content .\postgres\migration_equipements_bien.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

ALTER TABLE bien ADD COLUMN IF NOT EXISTS equipements JSONB NOT NULL DEFAULT '[]'::jsonb;

-- Pas d'index nécessaire : pas de filtre de recherche sur ce champ pour
-- l'instant (affichage uniquement sur la fiche détaillée du bien).
