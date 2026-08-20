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
    --   conciergerie = conciergerie (publie/gère des biens au nom d'un propriétaire tiers, mandant_nom obligatoire)
    role                VARCHAR(20) NOT NULL
                        CHECK (role IN ('admin', 'proprietaire', 'client', 'agence', 'promoteur', 'conciergerie')),
    statut_verification VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                        CHECK (statut_verification IN ('en_attente', 'verifie', 'rejete')),
    -- Vérification de l'email à l'inscription : un compte nouvellement créé
    -- ne peut pas se connecter tant que le lien reçu par email n'a pas été
    -- cliqué. Indépendant de statut_verification ci-dessus, qui concerne la
    -- vérification "métier" du profil professionnel par un admin.
    email_verifie                BOOLEAN NOT NULL DEFAULT false,
    email_verification_token     VARCHAR(255),
    email_verification_expire    TIMESTAMP,
    -- Champs professionnels (NULL pour client/admin/proprietaire particulier) :
    raison_sociale      VARCHAR(150),  -- nom de la société — obligatoire pour agence/promoteur
    numero_rc           VARCHAR(50),   -- registre de commerce / agrément promoteur
    numero_carte_pro    VARCHAR(50),   -- carte professionnelle conciergerie (optionnel — souvent informelle)
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_utilisateur_email_verification_token ON utilisateur(email_verification_token);

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
    -- les 3 autres rôles annonceurs (proprietaire/agence/conciergerie).
    projet_id           UUID REFERENCES projet_immobilier(id) ON DELETE SET NULL,
    -- Conciergerie (obligatoire) / agence (optionnel) : identité du propriétaire
    -- réel pour le compte duquel l'annonce est publiée ("sous mandat").
    mandant_nom         VARCHAR(150),
    mandant_telephone   VARCHAR(20),
    date_publication    TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now(),
    -- Complément étape 17 : proximités (POI Overpass/OSM) calculées à la
    -- publication et stockées ici, pour ne plus jamais recalculer à la
    -- volée (lent) à chaque affichage de la fiche. NULL = pas encore
    -- calculées (bien tout juste créé, calcul en arrière-plan en cours).
    proximite_data        JSONB,
    proximite_calculee_le TIMESTAMP,
    -- Complément "équipements" (façon Airbnb) : liste de codes texte parmi
    -- le catalogue défini côté front-end (frontend/src/lib/equipements.ts),
    -- propre à chaque type_bien (résidentiel / bureau / magasin / garage /
    -- terrain). Stocké en JSONB plutôt qu'une table à part : simple liste,
    -- jamais interrogée par elle-même (pas de filtre de recherche dessus
    -- pour l'instant), donc pas besoin de normaliser.
    equipements           JSONB NOT NULL DEFAULT '[]'::jsonb
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
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    -- Processus de paiement : fixée à la confirmation de la réservation
    -- (date_creation + délai configurable, 24h par défaut). Passé ce délai
    -- sans paiement réussi, la réservation est annulée automatiquement
    -- (backend/app/paiement_expiration.py). NULL = pas de délai (contrat
    -- créé avant cette fonctionnalité).
    date_limite_paiement TIMESTAMP,
    -- Réservation instantanée avec paiement immédiat (carte/virement, avant
    -- validation du propriétaire) : fenêtre d'annulation gratuite avec
    -- remboursement (date_signature + délai configurable, 24h par défaut).
    -- Mutuellement exclusif avec date_limite_paiement sur un même contrat
    -- (backend/app/routers/reservations.py).
    date_limite_annulation TIMESTAMP
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
-- ============================================================
-- Table : actualite (actualités publiées par un admin, affichées
-- sur la page d'accueil publique)
-- ============================================================
-- Articles du blog ImmoVision (admin ou agence) : titre, slug (URL SEO),
-- extrait (résumé/meta description), catégorie, contenu riche sanitizé.
CREATE TABLE actualite (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auteur_id           UUID NOT NULL REFERENCES utilisateur(id),
    titre               VARCHAR(200) NOT NULL,
    slug                VARCHAR(220),
    extrait             VARCHAR(300),
    categorie           VARCHAR(50) NOT NULL DEFAULT 'actualite'
                        CHECK (categorie IN ('actualite', 'marche_immobilier', 'conseils_locataires',
                                              'conseils_proprietaires', 'guide_juridique', 'vie_pratique')),
    contenu_html        TEXT NOT NULL,
    image_url           TEXT,
    publie              BOOLEAN NOT NULL DEFAULT true,
    date_creation       TIMESTAMP NOT NULL DEFAULT now(),
    date_maj            TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_actualite_publie_date ON actualite(publie, date_creation DESC);
CREATE UNIQUE INDEX idx_actualite_slug ON actualite(slug) WHERE slug IS NOT NULL;
CREATE INDEX idx_actualite_categorie ON actualite(categorie, publie, date_creation DESC);

-- Fin du script
-- ============================================================