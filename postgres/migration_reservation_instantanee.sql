-- ============================================================
-- Migration : réservation instantanée avec paiement immédiat
-- (carte bancaire / virement), avant validation du propriétaire
-- ============================================================
-- Le client peut désormais réserver ET payer en une seule étape depuis
-- « Réserver » (comme Booking). La réservation est créée directement au
-- statut "confirmee" et le contrat associé est généré immédiatement, avec
-- une fenêtre d'annulation gratuite (24h par défaut,
-- `delai_annulation_heures` dans backend/app/config.py) pendant laquelle
-- le client peut annuler et être remboursé sans justification
-- (POST /reservations/{id}/annuler dans backend/app/routers/reservations.py).
--
-- Ce mécanisme est distinct de l'ancien `date_limite_paiement` (payer
-- après confirmation du propriétaire, toujours utilisé pour les
-- réservations qui suivent le flux "demande classique" via
-- POST /reservations) : les deux colonnes sont mutuellement exclusives
-- sur un même contrat.
--
-- À exécuter une seule fois sur une base existante :
--   Get-Content .\postgres\migration_reservation_instantanee.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

ALTER TABLE contrat ADD COLUMN IF NOT EXISTS date_limite_annulation TIMESTAMP;

-- Les contrats déjà existants (créés avant cette migration) restent à
-- NULL : comportement conservateur, ils ne deviennent pas rétroactivement
-- annulables gratuitement par ce nouveau mécanisme.
