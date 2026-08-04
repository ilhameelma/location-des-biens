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
    -- Rôles "annonceurs" professionnels ajoutés en plus de proprietaire :
    --   agence     = agence immobilière (portefeuille de biens, éventuellement pour le compte de tiers)
    --   promoteur  = promoteur immobilier (publie des lots au sein d'un projet immobilier neuf)
    --   courtier   = courtier / "samsar" (publie des biens au nom d'un propriétaire tiers, mandant_nom obligatoire)
    role                VARCHAR(20) NOT NULL
                        CHECK (role IN ('admin', 'proprietaire', 'client', 'agence', 'promoteur', 'courtier')),
    statut_verification VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                        CHECK (statut_verification IN ('en_attente', 'verifie', 'rejete')),
    -- Champs professionnels (NULL pour client/admin/proprietaire particulier) :
    raison_sociale      VARCHAR(150),  -- nom de la société — obligatoire pour agence/promoteur
    numero_rc           VARCHAR(50),   -- registre de commerce / agrément promoteur
    numero_carte_pro    VARCHAR(50),   -- carte professionnelle courtier (optionnel — "samsar" souvent informel)
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now()
);

-- ============================================================
-- Table : projet_immobilier (promoteur uniquement)
-- Un projet regroupe plusieurs lots (biens neufs) publiés par un même
-- promoteur — ex. "Résidence Al Manar" à Tanger, 24 lots.
-- ============================================================
CREATE TABLE projet_immobilier (
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

CREATE INDEX idx_projet_promoteur ON projet_immobilier(promoteur_id);
CREATE INDEX idx_projet_ville ON projet_immobilier(ville);

-- ============================================================
-- Table : bien
-- ============================================================
CREATE TABLE bien (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proprietaire_id     UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    titre               VARCHAR(200) NOT NULL,
    description         TEXT,
    type_bien           VARCHAR(30) NOT NULL
                        CHECK (type_bien IN ('maison', 'appartement', 'magasin', 'garage', 'bureau', 'terrain', 'villa')),
    -- Sépare les annonces à louer des annonces à vendre.
    type_transaction    VARCHAR(10) NOT NULL DEFAULT 'location'
                        CHECK (type_transaction IN ('location', 'vente')),
    adresse             VARCHAR(255) NOT NULL,
    ville               VARCHAR(100) NOT NULL,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    superficie          NUMERIC(10,2),
    prix                NUMERIC(12,2) NOT NULL,
    nb_pieces           INTEGER,
    statut              VARCHAR(20) NOT NULL DEFAULT 'disponible'
                        CHECK (statut IN ('disponible', 'loue', 'vendu', 'en_attente', 'suspendu')),
    -- Promoteur uniquement : lot rattaché à un projet immobilier. NULL pour
    -- les 3 autres rôles annonceurs (proprietaire/agence/courtier).
    projet_id           UUID REFERENCES projet_immobilier(id) ON DELETE SET NULL,
    -- Courtier (obligatoire) / agence (optionnel) : identité du propriétaire
    -- réel pour le compte duquel l'annonce est publiée ("sous mandat").
    mandant_nom         VARCHAR(150),
    mandant_telephone   VARCHAR(20),
    date_publication    TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_bien_proprietaire ON bien(proprietaire_id);
CREATE INDEX idx_bien_ville ON bien(ville);
CREATE INDEX idx_bien_type ON bien(type_bien);
CREATE INDEX idx_bien_type_transaction ON bien(type_transaction);
CREATE INDEX idx_bien_projet ON bien(projet_id);

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
-- Table : favori (annonces enregistrées par un client)
-- ============================================================
CREATE TABLE favori (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    utilisateur_id      UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    bien_id             UUID NOT NULL REFERENCES bien(id) ON DELETE CASCADE,
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_favori_utilisateur_bien UNIQUE (utilisateur_id, bien_id)
);

CREATE INDEX idx_favori_utilisateur ON favori(utilisateur_id);
CREATE INDEX idx_favori_bien ON favori(bien_id);

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
    contenu             TEXT,
    piece_jointe_url    TEXT,
    piece_jointe_nom    TEXT,
    piece_jointe_type   TEXT CHECK (piece_jointe_type IN ('image', 'pdf')),
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
-- Table : recherche_historique (historique de recherche du client)
-- ============================================================
CREATE TABLE recherche_historique (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           UUID NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
    label               VARCHAR(255) NOT NULL,
    criteres            JSONB NOT NULL,
    date_recherche      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_recherche_historique_client ON recherche_historique(client_id);
CREATE INDEX idx_recherche_historique_client_date ON recherche_historique(client_id, date_recherche DESC);

-- ============================================================
-- Fin du script
-- ============================================================