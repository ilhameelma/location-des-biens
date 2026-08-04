-- ============================================================
-- Migration : vérification de l'email à l'inscription
-- À exécuter sur une base déjà initialisée :
--   Get-Content .\postgres\migration_email_verification.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

ALTER TABLE utilisateur
    ADD COLUMN IF NOT EXISTS email_verifie BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255),
    ADD COLUMN IF NOT EXISTS email_verification_expire TIMESTAMP;

-- Comptes déjà existants avant cette migration : on les considère vérifiés
-- (sinon tous les comptes déjà créés seraient bloqués à la prochaine connexion).
-- Seules les NOUVELLES inscriptions, à partir de maintenant, devront confirmer
-- leur email.
UPDATE utilisateur SET email_verifie = true WHERE email_verifie = false;

CREATE INDEX IF NOT EXISTS idx_utilisateur_email_verification_token
    ON utilisateur(email_verification_token);
