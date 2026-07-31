-- ============================================================
-- Migration : ajout de la table "favori" (annonces enregistrées)
-- À exécuter sur une base déjà initialisée (sinon déjà couvert par
-- smartrent_schema.sql pour une installation neuve).
--
-- PowerShell :
--   Get-Content .\postgres\migration_favoris.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

CREATE TABLE IF NOT EXISTS favori (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id      UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    bien_id             UUID NOT NULL REFERENCES bien(id) ON DELETE CASCADE,
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_favori_utilisateur_bien UNIQUE (utilisateur_id, bien_id)
);

CREATE INDEX IF NOT EXISTS idx_favori_utilisateur ON favori(utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_favori_bien ON favori(bien_id);
