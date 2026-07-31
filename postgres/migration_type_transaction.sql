-- ============================================================
-- Migration : ajout de la distinction Location / Vente
-- ============================================================
-- À exécuter UNE SEULE FOIS sur une base déjà initialisée
-- (si tu repars de zéro avec `docker-compose down -v` puis `up -d`,
-- ce n'est PAS nécessaire : smartrent_schema.sql contient déjà
-- ces colonnes/contraintes).
--
-- Utilisation (PowerShell) :
--   Get-Content .\postgres\migration_type_transaction.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

-- 1. Nouvelle colonne type_transaction (défaut 'location' pour ne pas casser
--    les annonces existantes, qui étaient toutes implicitement des locations)
ALTER TABLE bien
    ADD COLUMN IF NOT EXISTS type_transaction VARCHAR(10) NOT NULL DEFAULT 'location';

ALTER TABLE bien
    DROP CONSTRAINT IF EXISTS bien_type_transaction_check;
ALTER TABLE bien
    ADD CONSTRAINT bien_type_transaction_check CHECK (type_transaction IN ('location', 'vente'));

CREATE INDEX IF NOT EXISTS idx_bien_type_transaction ON bien(type_transaction);

-- 2. Élargit le statut du bien pour permettre 'vendu' (en plus de 'loue')
ALTER TABLE bien
    DROP CONSTRAINT IF EXISTS bien_statut_check;
ALTER TABLE bien
    ADD CONSTRAINT bien_statut_check CHECK (statut IN ('disponible', 'loue', 'vendu', 'en_attente', 'suspendu'));

-- 3. Corrige le CHECK type_bien qui excluait 'villa' (déjà utilisé par
--    l'application) — sans cette correction, publier une annonce de type
--    "villa" échoue avec une violation de contrainte.
ALTER TABLE bien
    DROP CONSTRAINT IF EXISTS bien_type_bien_check;
ALTER TABLE bien
    ADD CONSTRAINT bien_type_bien_check
    CHECK (type_bien IN ('maison', 'appartement', 'magasin', 'garage', 'bureau', 'terrain', 'villa'));

-- Vérification :
--   \d bien
-- doit montrer la colonne type_transaction et les 2 nouvelles contraintes.
