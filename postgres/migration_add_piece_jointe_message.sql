-- ============================================================
-- Migration ponctuelle : pièces jointes (photo/PDF) dans la messagerie
-- ============================================================
-- `contenu` devient optionnel (un message peut être uniquement une pièce
-- jointe, sans texte), et 3 colonnes sont ajoutées pour stocker l'URL
-- MinIO, le nom d'origine et le type ("image" ou "pdf") de la pièce jointe.
--
-- À exécuter une seule fois sur une base déjà initialisée avec l'ancien
-- smartrent_schema.sql :
--
--   Get-Content .\postgres\migration_add_piece_jointe_message.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
--
-- (smartrent_schema.sql a aussi été mis à jour pour les futures
-- installations fraîches — cette migration reste nécessaire pour ta base
-- actuelle.)

ALTER TABLE message ALTER COLUMN contenu DROP NOT NULL;

ALTER TABLE message ADD COLUMN IF NOT EXISTS piece_jointe_url TEXT;
ALTER TABLE message ADD COLUMN IF NOT EXISTS piece_jointe_nom TEXT;
ALTER TABLE message ADD COLUMN IF NOT EXISTS piece_jointe_type TEXT
    CHECK (piece_jointe_type IN ('image', 'pdf'));
