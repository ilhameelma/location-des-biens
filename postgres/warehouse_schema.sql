-- ============================================================
-- SmartRent Platform — Étape 14 : Data warehouse
-- ============================================================
-- Schéma dédié "dw" dans la même base PostgreSQL que la base
-- transactionnelle (smartrent_db), pour ne pas ajouter de nouveau
-- moteur (ClickHouse) à l'infrastructure. Alimenté par le job Spark
-- data/spark/jobs/load_to_warehouse.py, qui relit la couche bronze
-- (étape 12) et écrit ici en JDBC.
--
-- Modèle en étoile : 2 dimensions (date, ville) + 4 tables de faits,
-- une par type d'événement métier Kafka (étape 10). Vues d'agrégation
-- prêtes pour Power BI (étape 15) en bas de fichier.
--
-- Stratégie de rechargement : "full reload" (TRUNCATE + INSERT) à
-- chaque exécution du DAG. Possible car la couche bronze (data lake)
-- est la source de vérité rejouable dans son intégralité — pas besoin
-- d'un mécanisme d'upsert incrémental pour un volume de PFE.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- ------------------------------------------------------------
-- Dimensions
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_id      DATE PRIMARY KEY,
    annee        SMALLINT NOT NULL,
    trimestre    SMALLINT NOT NULL,
    mois         SMALLINT NOT NULL,
    nom_mois     VARCHAR(20) NOT NULL,
    jour         SMALLINT NOT NULL,
    jour_semaine VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_ville (
    ville_id SERIAL PRIMARY KEY,
    ville    VARCHAR(100) UNIQUE NOT NULL
);

-- ------------------------------------------------------------
-- Faits — un enregistrement par événement métier capté par Kafka.
-- Limitation documentée : chaque table de faits reflète l'état de
-- l'entité AU MOMENT où l'événement a été publié (snapshot), pas son
-- état courant en base transactionnelle — sauf fait_reservation, qui
-- combine "reservation.creee" et le dernier "reservation.statut_maj"
-- reçu pour obtenir le statut final.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dw.fait_bien (
    bien_id          UUID PRIMARY KEY,
    proprietaire_id  UUID,
    ville_id         INTEGER REFERENCES dw.dim_ville(ville_id),
    type_bien        VARCHAR(30),
    prix             NUMERIC(12, 2),
    statut           VARCHAR(20),
    date_id          DATE REFERENCES dw.dim_date(date_id),
    date_publication TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dw.fait_reservation (
    reservation_id   UUID PRIMARY KEY,
    bien_id          UUID,
    client_id        UUID,
    proprietaire_id  UUID,
    ville_id         INTEGER REFERENCES dw.dim_ville(ville_id),
    statut           VARCHAR(20),
    date_debut       DATE,
    date_fin         DATE,
    date_id          DATE REFERENCES dw.dim_date(date_id),
    date_creation    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dw.fait_contrat (
    contrat_id       UUID PRIMARY KEY,
    bien_id          UUID,
    proprietaire_id  UUID,
    client_id        UUID,
    ville_id         INTEGER REFERENCES dw.dim_ville(ville_id),
    montant_loyer    NUMERIC(12, 2),
    statut           VARCHAR(20),
    date_debut       DATE,
    date_fin         DATE,
    date_id          DATE REFERENCES dw.dim_date(date_id),
    date_signature   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dw.fait_paiement (
    paiement_id      UUID PRIMARY KEY,
    contrat_id       UUID,
    bien_id          UUID,
    proprietaire_id  UUID,
    client_id        UUID,
    ville_id         INTEGER REFERENCES dw.dim_ville(ville_id),
    montant          NUMERIC(12, 2),
    methode          VARCHAR(30),
    statut           VARCHAR(20),
    date_id          DATE REFERENCES dw.dim_date(date_id),
    date_paiement    TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fait_bien_ville        ON dw.fait_bien(ville_id);
CREATE INDEX IF NOT EXISTS idx_fait_reservation_ville  ON dw.fait_reservation(ville_id);
CREATE INDEX IF NOT EXISTS idx_fait_contrat_ville      ON dw.fait_contrat(ville_id);
CREATE INDEX IF NOT EXISTS idx_fait_paiement_ville     ON dw.fait_paiement(ville_id);
CREATE INDEX IF NOT EXISTS idx_fait_paiement_date      ON dw.fait_paiement(date_id);

-- ------------------------------------------------------------
-- Vues d'agrégation — consommées directement par Power BI (étape 15)
-- ------------------------------------------------------------

-- Revenus (paiements réussis) par ville et par mois
CREATE OR REPLACE VIEW dw.v_revenus_par_ville AS
SELECT
    v.ville,
    d.annee,
    d.mois,
    d.nom_mois,
    SUM(f.montant)   AS revenu_total,
    COUNT(*)         AS nb_paiements
FROM dw.fait_paiement f
JOIN dw.dim_ville v ON v.ville_id = f.ville_id
JOIN dw.dim_date  d ON d.date_id  = f.date_id
WHERE f.statut = 'reussi'
GROUP BY v.ville, d.annee, d.mois, d.nom_mois
ORDER BY d.annee, d.mois, revenu_total DESC;

-- Taux de confirmation des réservations par ville
-- (proxy simple du "taux d'occupation" mentionné au cahier des charges,
-- calculable à partir des seuls événements captés par Kafka)
CREATE OR REPLACE VIEW dw.v_taux_confirmation_par_ville AS
SELECT
    v.ville,
    COUNT(*)                                                     AS nb_reservations,
    COUNT(*) FILTER (WHERE f.statut = 'confirmee')               AS nb_confirmees,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE f.statut = 'confirmee')
        / NULLIF(COUNT(*), 0), 1
    )                                                             AS taux_confirmation_pct
FROM dw.fait_reservation f
JOIN dw.dim_ville v ON v.ville_id = f.ville_id
GROUP BY v.ville
ORDER BY taux_confirmation_pct DESC NULLS LAST;

-- Activité mensuelle globale (biens publiés, réservations, contrats, revenus)
CREATE OR REPLACE VIEW dw.v_activite_mensuelle AS
SELECT
    d.annee,
    d.mois,
    d.nom_mois,
    (SELECT COUNT(*) FROM dw.fait_bien b
        JOIN dw.dim_date db ON db.date_id = b.date_id
        WHERE db.annee = d.annee AND db.mois = d.mois)            AS nb_biens_publies,
    (SELECT COUNT(*) FROM dw.fait_reservation r
        JOIN dw.dim_date dr ON dr.date_id = r.date_id
        WHERE dr.annee = d.annee AND dr.mois = d.mois)            AS nb_reservations,
    (SELECT COUNT(*) FROM dw.fait_contrat c
        JOIN dw.dim_date dc ON dc.date_id = c.date_id
        WHERE dc.annee = d.annee AND dc.mois = d.mois)            AS nb_contrats_signes,
    (SELECT COALESCE(SUM(p.montant), 0) FROM dw.fait_paiement p
        JOIN dw.dim_date dp ON dp.date_id = p.date_id
        WHERE dp.annee = d.annee AND dp.mois = d.mois AND p.statut = 'reussi') AS revenu_total
FROM dw.dim_date d
GROUP BY d.annee, d.mois, d.nom_mois
ORDER BY d.annee, d.mois;

-- Top biens par revenu généré (contrats + paiements réussis)
CREATE OR REPLACE VIEW dw.v_top_biens_par_revenu AS
SELECT
    b.bien_id,
    b.type_bien,
    v.ville,
    b.prix AS prix_annonce,
    COALESCE(SUM(p.montant), 0) AS revenu_total
FROM dw.fait_bien b
JOIN dw.dim_ville v ON v.ville_id = b.ville_id
LEFT JOIN dw.fait_paiement p ON p.bien_id = b.bien_id AND p.statut = 'reussi'
GROUP BY b.bien_id, b.type_bien, v.ville, b.prix
ORDER BY revenu_total DESC;
