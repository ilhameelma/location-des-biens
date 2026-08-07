-- ============================================================
-- Migration : processus de paiement après confirmation d'une réservation
-- ============================================================
-- À la confirmation d'une réservation, le contrat généré automatiquement
-- reçoit désormais une date limite de paiement (24h par défaut,
-- `delai_paiement_heures` dans backend/app/config.py). Passé ce délai
-- sans paiement réussi, la réservation est annulée automatiquement par
-- une tâche d'arrière-plan (backend/app/paiement_expiration.py) : contrat
-- résilié, réservation annulée, bien remis disponible.
--
-- À exécuter une seule fois sur une base existante :
--   Get-Content .\postgres\migration_paiement_delai.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

ALTER TABLE contrat ADD COLUMN IF NOT EXISTS date_limite_paiement TIMESTAMP;

-- Les contrats déjà existants (créés avant cette migration) restent à
-- NULL : ils ne sont jamais annulés automatiquement (comportement
-- volontairement conservateur — seules les nouvelles confirmations de
-- réservation, à partir du déploiement de cette mise à jour, sont
-- concernées par le délai de paiement).
