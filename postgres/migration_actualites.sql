-- ============================================================
-- Migration : ajout de la table "actualite"
-- Actualités publiées par un administrateur, affichées sur la page
-- d'accueil publique (landing page).
-- À exécuter sur une base déjà initialisée (sinon déjà couvert par
-- smartrent_schema.sql pour une installation neuve).
--
-- PowerShell :
--   Get-Content .\postgres\migration_actualites.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

CREATE TABLE IF NOT EXISTS actualite (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auteur_id           UUID NOT NULL REFERENCES utilisateur(id),
    titre               VARCHAR(200) NOT NULL,
    contenu             TEXT NOT NULL,
    image_url           TEXT,
    publie              BOOLEAN NOT NULL DEFAULT true,
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_actualite_publie_date ON actualite(publie, date_creation DESC);
