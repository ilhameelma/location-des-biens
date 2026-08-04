-- ============================================================
-- Migration : renommage du rôle "courtier" -> "conciergerie"
-- À exécuter sur une base déjà initialisée :
--   Get-Content .\postgres\migration_renommage_conciergerie.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
--
-- Sur une base toute neuve, smartrent_schema.sql mis à jour suffit (le rôle
-- "conciergerie" y est déjà déclaré directement) — cette migration ne sert
-- qu'à faire migrer les comptes déjà créés avec l'ancienne valeur "courtier".
-- ============================================================

-- 1. Retirer temporairement la contrainte CHECK existante, qui n'autorise
--    pas encore la valeur 'conciergerie'.
ALTER TABLE utilisateur DROP CONSTRAINT IF EXISTS utilisateur_role_check;

-- 2. Faire basculer tous les comptes existants portant l'ancien rôle.
UPDATE utilisateur SET role = 'conciergerie' WHERE role = 'courtier';

-- 3. Recréer la contrainte CHECK avec la nouvelle valeur (et sans l'ancienne,
--    pour empêcher toute nouvelle insertion avec 'courtier').
ALTER TABLE utilisateur
    ADD CONSTRAINT utilisateur_role_check
    CHECK (role IN ('admin', 'proprietaire', 'client', 'agence', 'promoteur', 'conciergerie'));

-- Remarque : si votre installation a nommé la contrainte différemment,
-- retrouvez son nom réel avec :
--   \d utilisateur
-- (ou la requête ci-dessous) avant de relancer cette migration :
--   SELECT conname FROM pg_constraint
--   WHERE conrelid = 'utilisateur'::regclass AND contype = 'c';
