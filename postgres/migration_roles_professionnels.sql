-- ============================================================
-- Migration : nouveaux rôles professionnels
--   - Agence immobilière (agence)
--   - Promoteur immobilier (promoteur) — publie des lots au sein d'un projet
--   - Courtier / Samsar (courtier) — publie des biens au nom d'un tiers
--
-- À exécuter sur une base DÉJÀ initialisée (ne recrée rien depuis zéro) :
--   Get-Content .\postgres\migration_roles_professionnels.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
-- ============================================================

-- 1) Élargir la contrainte CHECK sur utilisateur.role
ALTER TABLE utilisateur DROP CONSTRAINT IF EXISTS utilisateur_role_check;
ALTER TABLE utilisateur
    ADD CONSTRAINT utilisateur_role_check
    CHECK (role IN ('admin', 'proprietaire', 'client', 'agence', 'promoteur', 'courtier'));

-- 2) Champs professionnels sur utilisateur
ALTER TABLE utilisateur ADD COLUMN IF NOT EXISTS raison_sociale   VARCHAR(150);
ALTER TABLE utilisateur ADD COLUMN IF NOT EXISTS numero_rc        VARCHAR(50);
ALTER TABLE utilisateur ADD COLUMN IF NOT EXISTS numero_carte_pro VARCHAR(50);

-- 3) Table projet_immobilier (promoteur)
CREATE TABLE IF NOT EXISTS projet_immobilier (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promoteur_id            UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    nom                     VARCHAR(200) NOT NULL,
    description             TEXT,
    type_bien               VARCHAR(30) NOT NULL
                            CHECK (type_bien IN ('maison', 'appartement', 'magasin', 'garage', 'bureau', 'terrain', 'villa')),
    ville                   VARCHAR(100) NOT NULL,
    adresse                 VARCHAR(255) NOT NULL,
    latitude                DOUBLE PRECISION,
    longitude               DOUBLE PRECISION,
    statut                  VARCHAR(20) NOT NULL DEFAULT 'en_construction'
                            CHECK (statut IN ('en_construction', 'livre', 'termine')),
    date_livraison_prevue   DATE,
    date_creation           TIMESTAMP NOT NULL DEFAULT now(),
    date_maj                TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_projet_promoteur ON projet_immobilier(promoteur_id);
CREATE INDEX IF NOT EXISTS idx_projet_ville ON projet_immobilier(ville);

-- 4) Champs sur bien : rattachement à un projet (promoteur) + mandant (courtier/agence)
ALTER TABLE bien ADD COLUMN IF NOT EXISTS projet_id UUID REFERENCES projet_immobilier(id) ON DELETE SET NULL;
ALTER TABLE bien ADD COLUMN IF NOT EXISTS mandant_nom       VARCHAR(150);
ALTER TABLE bien ADD COLUMN IF NOT EXISTS mandant_telephone VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_bien_projet ON bien(projet_id);

-- Vérification :
--   \d utilisateur
--   \d bien
--   \d projet_immobilier
