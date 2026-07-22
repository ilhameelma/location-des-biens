-- ============================================================
-- SmartRent Platform — Schéma de base de données PostgreSQL
-- Étape 2 : Conception de la base de données
-- ============================================================

-- Extension pour UUID (optionnel, sinon utiliser SERIAL)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Table : utilisateur
-- ============================================================
CREATE TABLE utilisateur (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom                 VARCHAR(100) NOT NULL,
    prenom              VARCHAR(100) NOT NULL,
    email               VARCHAR(150) UNIQUE NOT NULL,
    mot_de_passe_hash   VARCHAR(255) NOT NULL,
    telephone           VARCHAR(20),
    role                VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'proprietaire', 'client')),
    statut_verification VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                        CHECK (statut_verification IN ('en_attente', 'verifie', 'rejete')),
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now()
);

-- ============================================================
-- Table : bien
-- ============================================================
CREATE TABLE bien (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proprietaire_id     UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    titre               VARCHAR(200) NOT NULL,
    description         TEXT,
    type_bien           VARCHAR(30) NOT NULL
                        CHECK (type_bien IN ('maison', 'appartement', 'magasin', 'garage', 'bureau', 'terrain')),
    adresse             VARCHAR(255) NOT NULL,
    ville               VARCHAR(100) NOT NULL,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    superficie          NUMERIC(10,2),
    prix                NUMERIC(12,2) NOT NULL,
    nb_pieces           INTEGER,
    statut              VARCHAR(20) NOT NULL DEFAULT 'disponible'
                        CHECK (statut IN ('disponible', 'loue', 'en_attente', 'suspendu')),
    date_publication    TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_bien_proprietaire ON bien(proprietaire_id);
CREATE INDEX idx_bien_ville ON bien(ville);
CREATE INDEX idx_bien_type ON bien(type_bien);

-- ============================================================
-- Table : photo_bien
-- ============================================================
CREATE TABLE photo_bien (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bien_id             UUID NOT NULL REFERENCES bien(id) ON DELETE CASCADE,
    url                 VARCHAR(500) NOT NULL,  -- URL MinIO/S3
    ordre               INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_photo_bien ON photo_bien(bien_id);

-- ============================================================
-- Table : reservation
-- ============================================================
CREATE TABLE reservation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bien_id             UUID NOT NULL REFERENCES bien(id) ON DELETE CASCADE,
    client_id           UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    date_debut          DATE NOT NULL,
    date_fin            DATE,
    statut              VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                        CHECK (statut IN ('en_attente', 'confirmee', 'refusee', 'annulee')),
    date_creation       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_reservation_bien ON reservation(bien_id);
CREATE INDEX idx_reservation_client ON reservation(client_id);

-- ============================================================
-- Table : contrat
-- ============================================================
CREATE TABLE contrat (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reservation_id      UUID UNIQUE REFERENCES reservation(id) ON DELETE SET NULL,
    bien_id             UUID NOT NULL REFERENCES bien(id) ON DELETE CASCADE,
    proprietaire_id     UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    client_id           UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    date_signature      TIMESTAMP,
    date_debut          DATE NOT NULL,
    date_fin            DATE,
    montant_loyer       NUMERIC(12,2) NOT NULL,
    fichier_url         VARCHAR(500),  -- contrat signé stocké sur MinIO/S3
    statut              VARCHAR(20) NOT NULL DEFAULT 'actif'
                        CHECK (statut IN ('actif', 'termine', 'resilie')),
    date_creation       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_contrat_bien ON contrat(bien_id);
CREATE INDEX idx_contrat_client ON contrat(client_id);

-- ============================================================
-- Table : paiement
-- ============================================================
CREATE TABLE paiement (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contrat_id            UUID NOT NULL REFERENCES contrat(id) ON DELETE CASCADE,
    montant               NUMERIC(12,2) NOT NULL,
    methode               VARCHAR(30) NOT NULL,
    reference_transaction VARCHAR(100),
    statut                VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                          CHECK (statut IN ('en_attente', 'reussi', 'echoue', 'rembourse')),
    date_paiement         TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_paiement_contrat ON paiement(contrat_id);

-- ============================================================
-- Table : avis
-- ============================================================
CREATE TABLE avis (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    proprietaire_id     UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    bien_id             UUID NOT NULL REFERENCES bien(id) ON DELETE CASCADE,
    note                SMALLINT NOT NULL CHECK (note BETWEEN 1 AND 5),
    commentaire         TEXT,
    date_creation       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_avis_proprietaire ON avis(proprietaire_id);
CREATE INDEX idx_avis_bien ON avis(bien_id);

-- ============================================================
-- Table : reclamation
-- ============================================================
CREATE TABLE reclamation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id      UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    bien_id             UUID REFERENCES bien(id) ON DELETE SET NULL,
    contrat_id          UUID REFERENCES contrat(id) ON DELETE SET NULL,
    type_reclamation    VARCHAR(50) NOT NULL,
    description         TEXT NOT NULL,
    statut              VARCHAR(20) NOT NULL DEFAULT 'ouverte'
                        CHECK (statut IN ('ouverte', 'en_cours', 'resolue', 'rejetee')),
    date_creation       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_reclamation_utilisateur ON reclamation(utilisateur_id);

-- ============================================================
-- Table : conversation
-- ============================================================
CREATE TABLE conversation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bien_id             UUID REFERENCES bien(id) ON DELETE SET NULL,
    client_id           UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    proprietaire_id     UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    date_creation       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_conversation_client ON conversation(client_id);
CREATE INDEX idx_conversation_proprietaire ON conversation(proprietaire_id);

-- ============================================================
-- Table : message
-- ============================================================
CREATE TABLE message (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    expediteur_id       UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    contenu             TEXT NOT NULL,
    lu                  BOOLEAN NOT NULL DEFAULT FALSE,
    date_envoi          TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_message_conversation ON message(conversation_id);

-- ============================================================
-- Table : notification
-- ============================================================
CREATE TABLE notification (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id      UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    type_notification   VARCHAR(50) NOT NULL,
    contenu             TEXT NOT NULL,
    lu                  BOOLEAN NOT NULL DEFAULT FALSE,
    date_creation       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_notification_utilisateur ON notification(utilisateur_id);

-- ============================================================
-- Fin du script
-- ============================================================