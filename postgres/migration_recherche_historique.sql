-- ============================================================
-- Migration : ajout de la table "recherche_historique"
-- (historique de recherche du client)
-- À exécuter sur une base déjà initialisée (sinon déjà couvert par
-- smartrent_schema.sql pour une installation neuve).
--
-- PowerShell :
--   Get-Content .\postgres\migration_recherche_historique.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

CREATE TABLE IF NOT EXISTS recherche_historique (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    label               VARCHAR(255) NOT NULL,
    criteres            JSONB NOT NULL,
    date_recherche      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_recherche_historique_client ON recherche_historique(client_id);
CREATE INDEX IF NOT EXISTS idx_recherche_historique_client_date ON recherche_historique(client_id, date_recherche DESC);
