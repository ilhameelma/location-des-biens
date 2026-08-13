--
-- PostgreSQL database dump
--

\restrict Sf2ZFN1yDeJPAGV53RFzL84mG9GACdbVwW5T2r6IqW5SQY1IJ5hrCgkR39HsULD

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: dw; Type: SCHEMA; Schema: -; Owner: smartrent
--

CREATE SCHEMA dw;


ALTER SCHEMA dw OWNER TO smartrent;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dim_date; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.dim_date (
    date_id date NOT NULL,
    annee smallint NOT NULL,
    trimestre smallint NOT NULL,
    mois smallint NOT NULL,
    nom_mois character varying(20) NOT NULL,
    jour smallint NOT NULL,
    jour_semaine character varying(20) NOT NULL
);


ALTER TABLE dw.dim_date OWNER TO smartrent;

--
-- Name: dim_utilisateur; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.dim_utilisateur (
    utilisateur_id uuid NOT NULL,
    nom character varying(100),
    prenom character varying(100),
    role character varying(20)
);


ALTER TABLE dw.dim_utilisateur OWNER TO smartrent;

--
-- Name: dim_ville; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.dim_ville (
    ville_id integer NOT NULL,
    ville character varying(100) NOT NULL
);


ALTER TABLE dw.dim_ville OWNER TO smartrent;

--
-- Name: dim_ville_ville_id_seq; Type: SEQUENCE; Schema: dw; Owner: smartrent
--

CREATE SEQUENCE dw.dim_ville_ville_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE dw.dim_ville_ville_id_seq OWNER TO smartrent;

--
-- Name: dim_ville_ville_id_seq; Type: SEQUENCE OWNED BY; Schema: dw; Owner: smartrent
--

ALTER SEQUENCE dw.dim_ville_ville_id_seq OWNED BY dw.dim_ville.ville_id;


--
-- Name: fait_avis; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.fait_avis (
    avis_id uuid NOT NULL,
    bien_id uuid,
    client_id uuid,
    proprietaire_id uuid,
    note smallint,
    date_id date,
    date_creation timestamp without time zone
);


ALTER TABLE dw.fait_avis OWNER TO smartrent;

--
-- Name: fait_bien; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.fait_bien (
    bien_id uuid NOT NULL,
    proprietaire_id uuid,
    ville_id integer,
    type_bien character varying(30),
    prix numeric(12,2),
    statut character varying(20),
    date_id date,
    date_publication timestamp without time zone
);


ALTER TABLE dw.fait_bien OWNER TO smartrent;

--
-- Name: fait_contrat; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.fait_contrat (
    contrat_id uuid NOT NULL,
    bien_id uuid,
    proprietaire_id uuid,
    client_id uuid,
    ville_id integer,
    montant_loyer numeric(12,2),
    statut character varying(20),
    date_debut date,
    date_fin date,
    date_id date,
    date_signature timestamp without time zone
);


ALTER TABLE dw.fait_contrat OWNER TO smartrent;

--
-- Name: fait_paiement; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.fait_paiement (
    paiement_id uuid NOT NULL,
    contrat_id uuid,
    bien_id uuid,
    proprietaire_id uuid,
    client_id uuid,
    ville_id integer,
    montant numeric(12,2),
    methode character varying(30),
    statut character varying(20),
    date_id date,
    date_paiement timestamp without time zone
);


ALTER TABLE dw.fait_paiement OWNER TO smartrent;

--
-- Name: fait_performance_bien; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.fait_performance_bien (
    bien_id uuid NOT NULL,
    proprietaire_id uuid,
    ville_id integer,
    type_bien character varying(30),
    prix numeric(12,2),
    statut character varying(20),
    nb_reservations integer,
    nb_reservations_confirmees integer,
    nb_contrats integer,
    revenu_loyer_total numeric(14,2),
    nb_paiements_reussis integer,
    revenu_paiements_total numeric(14,2),
    nb_avis integer,
    note_moyenne numeric(3,2)
);


ALTER TABLE dw.fait_performance_bien OWNER TO smartrent;

--
-- Name: fait_reclamation; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.fait_reclamation (
    reclamation_id uuid NOT NULL,
    utilisateur_id uuid,
    bien_id uuid,
    contrat_id uuid,
    type_reclamation character varying(50),
    statut character varying(20),
    date_id date,
    date_creation timestamp without time zone
);


ALTER TABLE dw.fait_reclamation OWNER TO smartrent;

--
-- Name: fait_reservation; Type: TABLE; Schema: dw; Owner: smartrent
--

CREATE TABLE dw.fait_reservation (
    reservation_id uuid NOT NULL,
    bien_id uuid,
    client_id uuid,
    proprietaire_id uuid,
    ville_id integer,
    statut character varying(20),
    date_debut date,
    date_fin date,
    date_id date,
    date_creation timestamp without time zone
);


ALTER TABLE dw.fait_reservation OWNER TO smartrent;

--
-- Name: v_activite_mensuelle; Type: VIEW; Schema: dw; Owner: smartrent
--

CREATE VIEW dw.v_activite_mensuelle AS
 SELECT annee,
    mois,
    nom_mois,
    ( SELECT count(*) AS count
           FROM (dw.fait_bien b
             JOIN dw.dim_date db ON ((db.date_id = b.date_id)))
          WHERE ((db.annee = d.annee) AND (db.mois = d.mois))) AS nb_biens_publies,
    ( SELECT count(*) AS count
           FROM (dw.fait_reservation r
             JOIN dw.dim_date dr ON ((dr.date_id = r.date_id)))
          WHERE ((dr.annee = d.annee) AND (dr.mois = d.mois))) AS nb_reservations,
    ( SELECT count(*) AS count
           FROM (dw.fait_contrat c
             JOIN dw.dim_date dc ON ((dc.date_id = c.date_id)))
          WHERE ((dc.annee = d.annee) AND (dc.mois = d.mois))) AS nb_contrats_signes,
    ( SELECT COALESCE(sum(p.montant), (0)::numeric) AS "coalesce"
           FROM (dw.fait_paiement p
             JOIN dw.dim_date dp ON ((dp.date_id = p.date_id)))
          WHERE ((dp.annee = d.annee) AND (dp.mois = d.mois) AND ((p.statut)::text = 'reussi'::text))) AS revenu_total
   FROM dw.dim_date d
  GROUP BY annee, mois, nom_mois
  ORDER BY annee, mois;


ALTER VIEW dw.v_activite_mensuelle OWNER TO smartrent;

--
-- Name: v_note_moyenne_par_ville; Type: VIEW; Schema: dw; Owner: smartrent
--

CREATE VIEW dw.v_note_moyenne_par_ville AS
 SELECT v.ville,
    count(*) AS nb_avis,
    round(avg(a.note), 2) AS note_moyenne
   FROM ((dw.fait_avis a
     JOIN dw.fait_bien b ON ((b.bien_id = a.bien_id)))
     JOIN dw.dim_ville v ON ((v.ville_id = b.ville_id)))
  GROUP BY v.ville
  ORDER BY (round(avg(a.note), 2)) DESC NULLS LAST;


ALTER VIEW dw.v_note_moyenne_par_ville OWNER TO smartrent;

--
-- Name: v_revenu_par_proprietaire; Type: VIEW; Schema: dw; Owner: smartrent
--

CREATE VIEW dw.v_revenu_par_proprietaire AS
 SELECT u.utilisateur_id,
    u.nom,
    u.prenom,
    count(DISTINCT f.bien_id) AS nb_biens,
    COALESCE(sum(f.revenu_paiements_total), (0)::numeric) AS revenu_total,
    COALESCE(sum(f.nb_avis), (0)::bigint) AS nb_avis_recus,
    round(avg(f.note_moyenne), 2) AS note_moyenne
   FROM (dw.fait_performance_bien f
     JOIN dw.dim_utilisateur u ON ((u.utilisateur_id = f.proprietaire_id)))
  GROUP BY u.utilisateur_id, u.nom, u.prenom
  ORDER BY COALESCE(sum(f.revenu_paiements_total), (0)::numeric) DESC;


ALTER VIEW dw.v_revenu_par_proprietaire OWNER TO smartrent;

--
-- Name: v_revenus_par_ville; Type: VIEW; Schema: dw; Owner: smartrent
--

CREATE VIEW dw.v_revenus_par_ville AS
 SELECT v.ville,
    d.annee,
    d.mois,
    d.nom_mois,
    sum(f.montant) AS revenu_total,
    count(*) AS nb_paiements
   FROM ((dw.fait_paiement f
     JOIN dw.dim_ville v ON ((v.ville_id = f.ville_id)))
     JOIN dw.dim_date d ON ((d.date_id = f.date_id)))
  WHERE ((f.statut)::text = 'reussi'::text)
  GROUP BY v.ville, d.annee, d.mois, d.nom_mois
  ORDER BY d.annee, d.mois, (sum(f.montant)) DESC;


ALTER VIEW dw.v_revenus_par_ville OWNER TO smartrent;

--
-- Name: v_taux_confirmation_par_ville; Type: VIEW; Schema: dw; Owner: smartrent
--

CREATE VIEW dw.v_taux_confirmation_par_ville AS
 SELECT v.ville,
    count(*) AS nb_reservations,
    count(*) FILTER (WHERE ((f.statut)::text = 'confirmee'::text)) AS nb_confirmees,
    round(((100.0 * (count(*) FILTER (WHERE ((f.statut)::text = 'confirmee'::text)))::numeric) / (NULLIF(count(*), 0))::numeric), 1) AS taux_confirmation_pct
   FROM (dw.fait_reservation f
     JOIN dw.dim_ville v ON ((v.ville_id = f.ville_id)))
  GROUP BY v.ville
  ORDER BY (round(((100.0 * (count(*) FILTER (WHERE ((f.statut)::text = 'confirmee'::text)))::numeric) / (NULLIF(count(*), 0))::numeric), 1)) DESC NULLS LAST;


ALTER VIEW dw.v_taux_confirmation_par_ville OWNER TO smartrent;

--
-- Name: v_top_biens_par_revenu; Type: VIEW; Schema: dw; Owner: smartrent
--

CREATE VIEW dw.v_top_biens_par_revenu AS
 SELECT b.bien_id,
    b.type_bien,
    v.ville,
    b.prix AS prix_annonce,
    COALESCE(sum(p.montant), (0)::numeric) AS revenu_total
   FROM ((dw.fait_bien b
     JOIN dw.dim_ville v ON ((v.ville_id = b.ville_id)))
     LEFT JOIN dw.fait_paiement p ON (((p.bien_id = b.bien_id) AND ((p.statut)::text = 'reussi'::text))))
  GROUP BY b.bien_id, b.type_bien, v.ville, b.prix
  ORDER BY COALESCE(sum(p.montant), (0)::numeric) DESC;


ALTER VIEW dw.v_top_biens_par_revenu OWNER TO smartrent;

--
-- Name: actualite; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.actualite (
    id uuid NOT NULL,
    auteur_id uuid NOT NULL,
    titre character varying(200) NOT NULL,
    contenu text NOT NULL,
    image_url text,
    publie boolean NOT NULL,
    date_creation timestamp without time zone NOT NULL,
    date_maj timestamp without time zone NOT NULL
);


ALTER TABLE public.actualite OWNER TO smartrent;

--
-- Name: avis; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.avis (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    client_id uuid NOT NULL,
    proprietaire_id uuid NOT NULL,
    bien_id uuid NOT NULL,
    note smallint NOT NULL,
    commentaire text,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT avis_note_check CHECK (((note >= 1) AND (note <= 5)))
);


ALTER TABLE public.avis OWNER TO smartrent;

--
-- Name: bien; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.bien (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    proprietaire_id uuid NOT NULL,
    titre character varying(200) NOT NULL,
    description text,
    type_bien character varying(30) NOT NULL,
    adresse character varying(255) NOT NULL,
    ville character varying(100) NOT NULL,
    latitude double precision,
    longitude double precision,
    superficie numeric(10,2),
    prix numeric(12,2) NOT NULL,
    nb_pieces integer,
    statut character varying(20) DEFAULT 'disponible'::character varying NOT NULL,
    date_publication timestamp without time zone DEFAULT now() NOT NULL,
    date_maj timestamp without time zone DEFAULT now() NOT NULL,
    type_transaction character varying(10) DEFAULT 'location'::character varying NOT NULL,
    projet_id uuid,
    mandant_nom character varying(150),
    mandant_telephone character varying(20),
    proximite_data jsonb,
    proximite_calculee_le timestamp without time zone,
    equipements jsonb DEFAULT '[]'::jsonb NOT NULL,
    CONSTRAINT bien_statut_check CHECK (((statut)::text = ANY ((ARRAY['disponible'::character varying, 'loue'::character varying, 'vendu'::character varying, 'en_attente'::character varying, 'suspendu'::character varying])::text[]))),
    CONSTRAINT bien_type_bien_check CHECK (((type_bien)::text = ANY ((ARRAY['maison'::character varying, 'appartement'::character varying, 'magasin'::character varying, 'garage'::character varying, 'bureau'::character varying, 'terrain'::character varying, 'villa'::character varying])::text[]))),
    CONSTRAINT bien_type_transaction_check CHECK (((type_transaction)::text = ANY ((ARRAY['location'::character varying, 'vente'::character varying])::text[])))
);


ALTER TABLE public.bien OWNER TO smartrent;

--
-- Name: contrat; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.contrat (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    reservation_id uuid,
    bien_id uuid NOT NULL,
    proprietaire_id uuid NOT NULL,
    client_id uuid NOT NULL,
    date_signature timestamp without time zone,
    date_debut date NOT NULL,
    date_fin date,
    montant_loyer numeric(12,2) NOT NULL,
    fichier_url character varying(500),
    statut character varying(20) DEFAULT 'actif'::character varying NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    date_limite_paiement timestamp without time zone,
    date_limite_annulation timestamp without time zone,
    CONSTRAINT contrat_statut_check CHECK (((statut)::text = ANY ((ARRAY['actif'::character varying, 'termine'::character varying, 'resilie'::character varying])::text[])))
);


ALTER TABLE public.contrat OWNER TO smartrent;

--
-- Name: conversation; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.conversation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bien_id uuid,
    client_id uuid NOT NULL,
    proprietaire_id uuid NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.conversation OWNER TO smartrent;

--
-- Name: favori; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.favori (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    utilisateur_id uuid NOT NULL,
    bien_id uuid NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.favori OWNER TO smartrent;

--
-- Name: message; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.message (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    conversation_id uuid NOT NULL,
    expediteur_id uuid NOT NULL,
    contenu text,
    lu boolean DEFAULT false NOT NULL,
    date_envoi timestamp without time zone DEFAULT now() NOT NULL,
    piece_jointe_url text,
    piece_jointe_nom text,
    piece_jointe_type text,
    CONSTRAINT message_piece_jointe_type_check CHECK ((piece_jointe_type = ANY (ARRAY['image'::text, 'pdf'::text])))
);


ALTER TABLE public.message OWNER TO smartrent;

--
-- Name: notification; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.notification (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    utilisateur_id uuid NOT NULL,
    type_notification character varying(50) NOT NULL,
    contenu text NOT NULL,
    lu boolean DEFAULT false NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.notification OWNER TO smartrent;

--
-- Name: paiement; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.paiement (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    contrat_id uuid NOT NULL,
    montant numeric(12,2) NOT NULL,
    methode character varying(30) NOT NULL,
    reference_transaction character varying(100),
    statut character varying(20) DEFAULT 'en_attente'::character varying NOT NULL,
    date_paiement timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT paiement_statut_check CHECK (((statut)::text = ANY ((ARRAY['en_attente'::character varying, 'reussi'::character varying, 'echoue'::character varying, 'rembourse'::character varying])::text[])))
);


ALTER TABLE public.paiement OWNER TO smartrent;

--
-- Name: photo_bien; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.photo_bien (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bien_id uuid NOT NULL,
    url character varying(500) NOT NULL,
    ordre integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.photo_bien OWNER TO smartrent;

--
-- Name: projet_immobilier; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.projet_immobilier (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    promoteur_id uuid NOT NULL,
    nom character varying(200) NOT NULL,
    description text,
    type_bien character varying(30) NOT NULL,
    ville character varying(100) NOT NULL,
    adresse character varying(255) NOT NULL,
    latitude double precision,
    longitude double precision,
    statut character varying(20) DEFAULT 'en_construction'::character varying NOT NULL,
    date_livraison_prevue date,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    date_maj timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT projet_immobilier_statut_check CHECK (((statut)::text = ANY ((ARRAY['en_construction'::character varying, 'livre'::character varying, 'termine'::character varying])::text[]))),
    CONSTRAINT projet_immobilier_type_bien_check CHECK (((type_bien)::text = ANY ((ARRAY['maison'::character varying, 'appartement'::character varying, 'magasin'::character varying, 'garage'::character varying, 'bureau'::character varying, 'terrain'::character varying, 'villa'::character varying])::text[])))
);


ALTER TABLE public.projet_immobilier OWNER TO smartrent;

--
-- Name: recherche_historique; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.recherche_historique (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    client_id uuid NOT NULL,
    label character varying(255) NOT NULL,
    criteres jsonb NOT NULL,
    date_recherche timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.recherche_historique OWNER TO smartrent;

--
-- Name: reclamation; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.reclamation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    utilisateur_id uuid NOT NULL,
    bien_id uuid,
    contrat_id uuid,
    type_reclamation character varying(50) NOT NULL,
    description text NOT NULL,
    statut character varying(20) DEFAULT 'ouverte'::character varying NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT reclamation_statut_check CHECK (((statut)::text = ANY ((ARRAY['ouverte'::character varying, 'en_cours'::character varying, 'resolue'::character varying, 'rejetee'::character varying])::text[])))
);


ALTER TABLE public.reclamation OWNER TO smartrent;

--
-- Name: reservation; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.reservation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bien_id uuid NOT NULL,
    client_id uuid NOT NULL,
    date_debut date NOT NULL,
    date_fin date,
    statut character varying(20) DEFAULT 'en_attente'::character varying NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT reservation_statut_check CHECK (((statut)::text = ANY ((ARRAY['en_attente'::character varying, 'confirmee'::character varying, 'refusee'::character varying, 'annulee'::character varying])::text[])))
);


ALTER TABLE public.reservation OWNER TO smartrent;

--
-- Name: utilisateur; Type: TABLE; Schema: public; Owner: smartrent
--

CREATE TABLE public.utilisateur (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    nom character varying(100) NOT NULL,
    prenom character varying(100) NOT NULL,
    email character varying(150) NOT NULL,
    mot_de_passe_hash character varying(255) NOT NULL,
    telephone character varying(20),
    role character varying(20) NOT NULL,
    statut_verification character varying(20) DEFAULT 'en_attente'::character varying NOT NULL,
    date_creation timestamp without time zone DEFAULT now() NOT NULL,
    date_maj timestamp without time zone DEFAULT now() NOT NULL,
    raison_sociale character varying(150),
    numero_rc character varying(50),
    numero_carte_pro character varying(50),
    email_verifie boolean DEFAULT false NOT NULL,
    email_verification_token character varying(255),
    email_verification_expire timestamp without time zone,
    CONSTRAINT utilisateur_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'proprietaire'::character varying, 'client'::character varying, 'agence'::character varying, 'promoteur'::character varying, 'conciergerie'::character varying])::text[]))),
    CONSTRAINT utilisateur_statut_verification_check CHECK (((statut_verification)::text = ANY ((ARRAY['en_attente'::character varying, 'verifie'::character varying, 'rejete'::character varying])::text[])))
);


ALTER TABLE public.utilisateur OWNER TO smartrent;

--
-- Name: dim_ville ville_id; Type: DEFAULT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.dim_ville ALTER COLUMN ville_id SET DEFAULT nextval('dw.dim_ville_ville_id_seq'::regclass);


--
-- Data for Name: dim_date; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.dim_date (date_id, annee, trimestre, mois, nom_mois, jour, jour_semaine) FROM stdin;
2026-08-01	2026	3	8	Ao??t	1	Samedi
2026-07-29	2026	3	7	Juillet	29	Mercredi
2026-08-06	2026	3	8	Ao??t	6	Jeudi
2026-08-07	2026	3	8	Ao??t	7	Vendredi
2026-08-05	2026	3	8	Ao??t	5	Mercredi
2026-07-26	2026	3	7	Juillet	26	Dimanche
2026-07-25	2026	3	7	Juillet	25	Samedi
2026-08-03	2026	3	8	Ao??t	3	Lundi
2026-07-28	2026	3	7	Juillet	28	Mardi
2026-07-30	2026	3	7	Juillet	30	Jeudi
2026-08-02	2026	3	8	Ao??t	2	Dimanche
2026-07-27	2026	3	7	Juillet	27	Lundi
2026-08-04	2026	3	8	Ao??t	4	Mardi
\.


--
-- Data for Name: dim_utilisateur; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.dim_utilisateur (utilisateur_id, nom, prenom, role) FROM stdin;
9361c869-620e-4160-95ca-a938c5271c8b	nwisr	soumya	agence
ca34e8b2-6727-499e-9832-117d62a3baa2	elma	ilha	client
\.


--
-- Data for Name: dim_ville; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.dim_ville (ville_id, ville) FROM stdin;
1	Agadir
2	Casa
3	Casablanca
4	Fes
5	Meknes
6	Nador
7	RTYY
8	Rabat
9	agadir
10	gfhuhh
11	hhh
12	huhhu
13	t
14	test
15	test3
16	thh
17	tyy
\.


--
-- Data for Name: fait_avis; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.fait_avis (avis_id, bien_id, client_id, proprietaire_id, note, date_id, date_creation) FROM stdin;
6f79fafc-88ad-488d-9b56-4cbf6e6152a3	25168926-7096-4245-be95-7cbc9f6b1404	8216d907-2261-4154-ba11-5e4016de7d47	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	4	2026-08-06	2026-08-06 21:02:12.209763
\.


--
-- Data for Name: fait_bien; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.fait_bien (bien_id, proprietaire_id, ville_id, type_bien, prix, statut, date_id, date_publication) FROM stdin;
0d4347ab-c31e-4c05-8416-a709275a3427	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	6	maison	1234553.00	disponible	2026-08-04	2026-08-04 09:24:27.317958
25168926-7096-4245-be95-7cbc9f6b1404	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	4	appartement	10000.00	disponible	2026-08-04	2026-08-04 09:22:06.482392
2a1d7ff8-0647-47a0-a03f-7da13b38cfeb	ed5f8114-b388-498f-a130-db345f3fdbe3	1	appartement	10000.00	disponible	2026-08-03	2026-08-03 22:18:04.932784
2b5915fc-f749-4de0-84a1-a3b9fc0a101e	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	14	appartement	1234.00	disponible	2026-08-02	2026-08-02 17:41:57.984337
336a3e1c-9805-43cb-83a9-bd5a73e79526	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	8	appartement	12345.00	disponible	2026-08-02	2026-08-02 17:15:11.510228
3f5b8f33-84c2-470f-9730-ff524e23aca3	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	15	appartement	1234.00	disponible	2026-07-28	2026-07-28 13:40:58.226198
51e8bf26-8fc8-4dcf-b6ab-0588f837c676	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	1	appartement	999999.00	disponible	2026-08-03	2026-08-03 10:50:53.344051
54794b94-6d3c-4719-85f6-6a3f9a80af0f	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	14	appartement	1234.00	disponible	2026-08-02	2026-08-02 16:04:56.696609
59f2772c-7920-4476-8954-45dbb3c8f83a	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	8	villa	12345.00	disponible	2026-08-02	2026-08-02 17:26:19.313419
5fbc5ca1-6154-46e7-98ae-c34158e71554	8d3fa2c5-6fae-4280-8e25-ea7487930de4	5	appartement	9998.00	disponible	2026-08-03	2026-08-03 22:21:39.191568
62e0cd4a-be63-4254-bd9b-304f1066917e	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	4	bureau	12334.00	disponible	2026-08-04	2026-08-04 09:06:59.056503
70f0b5ea-6cc0-43c1-96f5-f0b45622db93	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	8	appartement	10000.00	disponible	2026-07-30	2026-07-30 11:06:10.774203
724ab875-34bc-41e9-8872-ad27d8eb17ca	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	2	appartement	1227.00	disponible	2026-08-02	2026-08-02 11:43:59.001929
813c7de2-0bec-4461-af61-b71b5212d315	8d3fa2c5-6fae-4280-8e25-ea7487930de4	5	appartement	9999.00	disponible	2026-08-03	2026-08-03 22:22:20.652357
81fe4ac5-8b61-434f-a675-ca5835740a2b	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	3	villa	19000.00	disponible	2026-07-29	2026-07-29 09:47:27.059761
994b48c4-bdb9-4b57-a2fd-2d8dbe1a1f96	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	3	appartement	11.63	disponible	2026-08-06	2026-08-06 11:20:12.563396
b843ccfc-fa17-4d97-96cd-f23f52c8277c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	8	appartement	10000.00	disponible	2026-07-28	2026-07-28 20:29:40.05458
b8953417-e72b-4604-9254-f7c680782222	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	10	appartement	12344.00	disponible	2026-08-01	2026-08-01 11:21:53.563498
c9d32aca-fd6b-4de0-a9ea-d401e743c6e3	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	11	appartement	121677.00	disponible	2026-08-07	2026-08-07 23:37:58.861873
e4dd3a88-1619-4bf6-a22c-594d119c48f0	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	7	appartement	3445655.00	disponible	2026-08-02	2026-08-02 12:02:44.631295
ecc32d54-0f30-4643-aec2-a2f85417414e	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	8	appartement	1234.00	disponible	2026-08-02	2026-08-02 10:40:59.569028
\.


--
-- Data for Name: fait_contrat; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.fait_contrat (contrat_id, bien_id, proprietaire_id, client_id, ville_id, montant_loyer, statut, date_debut, date_fin, date_id, date_signature) FROM stdin;
132ff516-badb-4613-af44-b7897b2a3f1d	0ab3bb77-895c-4119-ba5a-5a1586ee5627	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	8216d907-2261-4154-ba11-5e4016de7d47	16	123.00	actif	2026-08-05	\N	2026-08-05	2026-08-05 10:14:12.011795
5fdfbb7a-2195-49eb-8c99-b73de63f81b4	997c7479-f435-46ef-a8f0-1ea9ca5e3819	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	06de101d-9f5d-4d70-898f-92206c46718c	13	23.00	actif	2026-08-03	\N	2026-08-03	2026-08-03 11:35:43.409927
77b073ca-cb41-44b0-8f47-4cbc1b4367dc	c49bc394-abc9-4b5d-b3aa-7a86e52bdce1	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	06de101d-9f5d-4d70-898f-92206c46718c	14	3478.00	actif	2026-07-26	\N	2026-07-26	2026-07-26 11:13:03.1263
8addca31-5cfc-4da6-9b4c-d10f2c6abf25	5103e84e-9aa2-493d-940d-f01590fb4134	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	06de101d-9f5d-4d70-898f-92206c46718c	9	5678.00	actif	2026-07-26	\N	2026-07-26	2026-07-26 18:09:20.958801
90fbe9af-6adb-461c-87fa-4d4e0ca8fe24	273c6a23-fe44-44a6-ae9c-fe328715aa80	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	06de101d-9f5d-4d70-898f-92206c46718c	8	8000.00	actif	2026-07-25	\N	2026-07-25	2026-07-25 22:29:46.579236
a79c2cb1-2332-481b-9b97-e5f9bf4be491	a77fc7d3-5d56-4f51-8089-070373ed0f0f	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	06de101d-9f5d-4d70-898f-92206c46718c	12	123.00	actif	2026-07-25	\N	2026-07-26	2026-07-26 10:45:28.668692
b50adcf7-7068-4d05-8a19-7cee890c29e3	ebe53541-aea6-4a49-9be3-58eb42f23757	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	06de101d-9f5d-4d70-898f-92206c46718c	9	5678.00	actif	2026-07-26	\N	2026-07-26	2026-07-26 11:06:06.999433
d4a4aa95-61fb-4917-9664-126c3a25a144	25168926-7096-4245-be95-7cbc9f6b1404	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	8216d907-2261-4154-ba11-5e4016de7d47	4	10000.00	actif	2026-08-07	2026-12-09	2026-08-07	2026-08-07 09:05:52.093031
dfcc3b41-cf8d-46e0-ba55-2589c6a067af	3f5b8f33-84c2-470f-9730-ff524e23aca3	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	8216d907-2261-4154-ba11-5e4016de7d47	15	1234.00	actif	2026-08-06	\N	2026-08-06	2026-08-06 09:23:23.213813
\.


--
-- Data for Name: fait_paiement; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.fait_paiement (paiement_id, contrat_id, bien_id, proprietaire_id, client_id, ville_id, montant, methode, statut, date_id, date_paiement) FROM stdin;
8b848598-8688-4d0d-acd4-7d233729ff0e	d4a4aa95-61fb-4917-9664-126c3a25a144	25168926-7096-4245-be95-7cbc9f6b1404	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	8216d907-2261-4154-ba11-5e4016de7d47	4	10000.00	carte_bancaire	reussi	2026-08-07	2026-08-07 09:05:52.099626
\.


--
-- Data for Name: fait_performance_bien; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.fait_performance_bien (bien_id, proprietaire_id, ville_id, type_bien, prix, statut, nb_reservations, nb_reservations_confirmees, nb_contrats, revenu_loyer_total, nb_paiements_reussis, revenu_paiements_total, nb_avis, note_moyenne) FROM stdin;
\.


--
-- Data for Name: fait_reclamation; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.fait_reclamation (reclamation_id, utilisateur_id, bien_id, contrat_id, type_reclamation, statut, date_id, date_creation) FROM stdin;
\.


--
-- Data for Name: fait_reservation; Type: TABLE DATA; Schema: dw; Owner: smartrent
--

COPY dw.fait_reservation (reservation_id, bien_id, client_id, proprietaire_id, ville_id, statut, date_debut, date_fin, date_id, date_creation) FROM stdin;
03c6e37e-96b1-486a-80e8-583fcac29a24	ccaa4863-764a-4121-b821-1fe6be4acdbc	8216d907-2261-4154-ba11-5e4016de7d47	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	17	en_attente	2026-08-06	\N	2026-08-06	2026-08-06 09:20:16.77145
175310ae-fb82-4d77-8bcd-cb3626424012	5103e84e-9aa2-493d-940d-f01590fb4134	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	9	refusee	2026-07-26	\N	2026-07-26	2026-07-26 11:22:42.491031
244b2fbf-9767-49a2-a769-4b7348c49453	3f5b8f33-84c2-470f-9730-ff524e23aca3	8216d907-2261-4154-ba11-5e4016de7d47	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	15	en_attente	2026-08-06	\N	2026-08-06	2026-08-06 09:21:13.530511
2742dd62-47a2-4d02-8485-59dd9ee3ee6b	c49bc394-abc9-4b5d-b3aa-7a86e52bdce1	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	14	refusee	2026-07-26	\N	2026-07-26	2026-07-26 10:24:29.974571
2adecada-98b2-4331-8bed-b93e397d84da	0ab3bb77-895c-4119-ba5a-5a1586ee5627	8216d907-2261-4154-ba11-5e4016de7d47	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	16	annulee	2026-08-05	\N	2026-08-05	2026-08-05 10:13:26.926923
3b71dbb2-3478-4fc7-aaa1-90f8b3c65ff1	3f5b8f33-84c2-470f-9730-ff524e23aca3	8216d907-2261-4154-ba11-5e4016de7d47	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	15	annulee	2026-08-06	\N	2026-08-06	2026-08-06 09:22:55.560638
3b8fb77d-25c6-4035-9faa-2b84354f48c6	0412744c-9325-4468-b5ff-c2167079180f	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	9	refusee	2026-07-27	\N	2026-07-27	2026-07-27 10:43:45.083468
427c1431-bebd-4e39-802f-fdd0870793e7	5103e84e-9aa2-493d-940d-f01590fb4134	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	9	confirmee	2026-07-26	\N	2026-07-26	2026-07-26 17:50:59.251651
5e0f7624-d940-4ce5-baff-a82a1982a548	5103e84e-9aa2-493d-940d-f01590fb4134	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	9	refusee	2026-07-26	\N	2026-07-26	2026-07-26 10:14:03.259662
6e9f0a9b-773d-45b7-bdc2-06be34d538f7	a77fc7d3-5d56-4f51-8089-070373ed0f0f	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	12	refusee	2026-07-25	\N	2026-07-25	2026-07-25 22:18:37.421426
7d037c55-2dfd-4c27-9fe9-0141c08f2ef4	c49bc394-abc9-4b5d-b3aa-7a86e52bdce1	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	14	confirmee	2026-07-26	\N	2026-07-26	2026-07-26 10:42:33.667026
87ad661b-fc59-48e0-857e-cd7d19df0ec2	ebe53541-aea6-4a49-9be3-58eb42f23757	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	9	confirmee	2026-07-26	\N	2026-07-26	2026-07-26 10:14:08.520291
93632f95-b09d-4098-86c9-d7535a1da091	997c7479-f435-46ef-a8f0-1ea9ca5e3819	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	13	confirmee	2026-08-03	\N	2026-08-03	2026-08-03 11:35:05.713415
b05a54db-57d5-4fc0-8de2-8b1cab2e6f02	273c6a23-fe44-44a6-ae9c-fe328715aa80	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	8	confirmee	2026-07-25	\N	2026-07-25	2026-07-25 22:10:26.381172
b7e3fd12-05f7-4a9f-b1fa-ee9d7828516c	25168926-7096-4245-be95-7cbc9f6b1404	8216d907-2261-4154-ba11-5e4016de7d47	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	4	en_attente	2026-08-06	\N	2026-08-06	2026-08-06 21:01:34.250074
bbf072ca-7947-4b33-9ebd-274bc8f50e24	b843ccfc-fa17-4d97-96cd-f23f52c8277c	8216d907-2261-4154-ba11-5e4016de7d47	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	8	en_attente	2026-08-06	\N	2026-08-06	2026-08-06 09:29:11.883435
be94248d-a927-4905-b3c7-e4d673346cdb	997c7479-f435-46ef-a8f0-1ea9ca5e3819	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	13	refusee	2026-07-26	\N	2026-07-26	2026-07-26 11:22:38.681369
c1399dc1-9459-4345-b457-2baa2f61799f	997c7479-f435-46ef-a8f0-1ea9ca5e3819	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	13	refusee	2026-07-26	\N	2026-07-26	2026-07-26 18:29:13.728259
cbedf0db-a25c-40fb-9ed3-ae38f8afd6ad	a77fc7d3-5d56-4f51-8089-070373ed0f0f	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	12	refusee	2026-07-26	\N	2026-07-26	2026-07-26 10:45:08.931256
d1e35684-edeb-4081-81f8-42bf5980915e	5103e84e-9aa2-493d-940d-f01590fb4134	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	9	refusee	2026-07-26	\N	2026-07-26	2026-07-26 10:07:31.764183
e763447d-99cf-4c9a-8767-a915e86a845c	a77fc7d3-5d56-4f51-8089-070373ed0f0f	06de101d-9f5d-4d70-898f-92206c46718c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	12	confirmee	2026-07-25	\N	2026-07-25	2026-07-25 22:26:00.414125
ebbacc8c-c574-4359-b559-0e9258fa3d22	25168926-7096-4245-be95-7cbc9f6b1404	8216d907-2261-4154-ba11-5e4016de7d47	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	4	confirmee	2026-08-07	2026-12-09	2026-08-07	2026-08-07 09:05:52.077082
\.


--
-- Data for Name: actualite; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.actualite (id, auteur_id, titre, contenu, image_url, publie, date_creation, date_maj) FROM stdin;
96ca02b4-a9f7-486d-bdf0-2e964f2646fa	4b799642-6c05-4d33-891d-283e833b049f	Comment d??finir ses crit??res de recherche immobili??re avant de consulter les annonces au Maroc ?	Consulter des annonces immobili??res sans avoir d??fini ses crit??res revient souvent ?? avancer dans un labyrinthe sans carte. Les biens d??filent, les photographies s??duisent, les prix se m??langent et les priorit??s initiales deviennent progressivement floues.\n\nAu Maroc, l???offre immobili??re peut varier consid??rablement d???une ville ?? l???autre, mais ??galement d???un quartier ?? l???autre. Un appartement situ?? ?? Casablanca ne r??pond pas aux m??mes logiques de prix, de mobilit?? ou de rendement qu???un bien ?? Marrakech, Rabat, Tanger ou Agadir. M??me au sein d???une seule agglom??ration, quelques kilom??tres peuvent transformer la qualit?? de vie, la dur??e des trajets et la valeur du logement.\n\nAvant d???ouvrir un portail immobilier ou de contacter une agence, il est donc indispensable de formaliser son projet. Cette pr??paration permet de gagner du temps, de filtrer les annonces plus efficacement et d?????viter de visiter des biens incompatibles avec ses besoins.\n\nD??finir ses crit??res ne signifie pas rechercher un logement parfait. Il s???agit plut??t d???identifier ce qui est r??ellement n??cessaire, ce qui reste n??gociable et ce qui doit ??tre exclu d??s le d??part.	http://localhost:9000/smartrent-photos/actualites/96ca02b4-a9f7-486d-bdf0-2e964f2646fa/f3c2462596ac41d080bfd2f107abee86.png	t	2026-08-07 09:52:24.180726	2026-08-07 09:52:24.230383
\.


--
-- Data for Name: avis; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.avis (id, client_id, proprietaire_id, bien_id, note, commentaire, date_creation) FROM stdin;
6f79fafc-88ad-488d-9b56-4cbf6e6152a3	8216d907-2261-4154-ba11-5e4016de7d47	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	25168926-7096-4245-be95-7cbc9f6b1404	4	hi	2026-08-06 21:02:12.209763
\.


--
-- Data for Name: bien; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.bien (id, proprietaire_id, titre, description, type_bien, adresse, ville, latitude, longitude, superficie, prix, nb_pieces, statut, date_publication, date_maj, type_transaction, projet_id, mandant_nom, mandant_telephone, proximite_data, proximite_calculee_le, equipements) FROM stdin;
cfa9c2df-b5b3-4a4f-af65-2adff7f09c14	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	testt	\N	appartement	test	test	\N	\N	124.00	1237.00	4	loue	2026-07-23 09:03:17.054908	2026-07-23 18:27:35.579472	location	\N	\N	\N	\N	\N	[]
5fbc5ca1-6154-46e7-98ae-c34158e71554	8d3fa2c5-6fae-4280-8e25-ea7487930de4	Appartement 3 eme etage	test	appartement	Meknes 	Meknes	32.84036602561056	-5.686039955315796	98.00	9998.00	\N	disponible	2026-08-03 22:21:39.191568	2026-08-07 23:29:32.594583	location	24a5692f-7d79-4aa6-9902-869f97b089b0	\N	\N	{"categories": {"ecole": [], "hotel": [], "jardin": [], "commerce": []}, "disponible": true}	2026-08-07 23:29:32.593145	[]
0412744c-9325-4468-b5ff-c2167079180f	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	t	\N	appartement	 rtyhh	agadir	\N	\N	345.00	1234.00	4	disponible	2026-07-25 11:16:35.121938	2026-07-25 11:16:35.121938	location	\N	\N	\N	\N	\N	[]
273c6a23-fe44-44a6-ae9c-fe328715aa80	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	apparetement a louer	\N	appartement	Rabat	Rabat	\N	\N	456.00	8000.00	3	loue	2026-07-24 18:58:57.106339	2026-07-25 22:29:46.564663	location	\N	\N	\N	\N	\N	[]
813c7de2-0bec-4461-af61-b71b5212d315	8d3fa2c5-6fae-4280-8e25-ea7487930de4	appartement test	test	appartement	Meknes 	Meknes	32.84036602561056	-5.686039955315796	100.00	9999.00	\N	disponible	2026-08-03 22:22:20.652357	2026-08-07 23:29:34.137385	location	24a5692f-7d79-4aa6-9902-869f97b089b0	\N	\N	{"categories": {"ecole": [], "hotel": [], "jardin": [], "commerce": []}, "disponible": true}	2026-08-07 23:29:34.136441	[]
b843ccfc-fa17-4d97-96cd-f23f52c8277c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	Appartement moderne ?? louer ??? Agdal, Rabat	Magnifique appartement lumineux situ?? au c??ur du quartier Agdal ?? Rabat, ?? proximit?? des commerces, restaurants, caf??s, ??coles et transports en commun. Il comprend un grand salon, deux chambres spacieuses, une cuisine enti??rement ??quip??e, deux salles de bain modernes et un balcon offrant une belle vue sur le quartier. La r??sidence est s??curis??e 24h/24 avec ascenseur et parking priv??.	appartement	Avenue de France, Agdal, Rabat	Rabat	\N	\N	95.00	10000.00	3	disponible	2026-07-28 20:29:40.05458	2026-07-28 20:29:40.05458	location	\N	\N	\N	\N	\N	[]
b8953417-e72b-4604-9254-f7c680782222	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	huhhjj	ggu	appartement	hbjjjjk	gfhuhh	\N	\N	\N	12344.00	\N	disponible	2026-08-01 11:21:53.563498	2026-08-01 11:21:53.563498	vente	\N	\N	\N	\N	\N	[]
e4dd3a88-1619-4bf6-a22c-594d119c48f0	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	reclam3	\N	appartement	jjjjj	RTYY	\N	\N	234.00	3445655.00	\N	disponible	2026-08-02 12:02:44.631295	2026-08-02 12:02:44.631295	vente	\N	\N	\N	\N	\N	[]
2b5915fc-f749-4de0-84a1-a3b9fc0a101e	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	test entourage 4	test	appartement	test	test	33.598177765730846	-7.6253700256347665	120.00	1234.00	6	disponible	2026-08-02 17:41:57.984337	2026-08-04 09:13:32.56951	location	\N	\N	\N	{"categories": {"ecole": [{"lat": 33.5994664, "lon": -7.6306385, "nom": "??????????????? ????????????????????? ?????????????????? ?????????????? ???????????????????? ????????????", "distance_km": 0.51}, {"lat": 33.6000419, "lon": -7.6319168, "nom": "Amina bent ouahab", "distance_km": 0.64}, {"lat": 33.5977896, "lon": -7.6327744, "nom": "Groupe Scolaire El Farabi II", "distance_km": 0.69}, {"lat": 33.5970748, "lon": -7.6327837, "nom": "Coll??ge Omar El Khayam", "distance_km": 0.7}, {"lat": 33.5924531, "lon": -7.6287112, "nom": "??cole Jeanne d'Arc", "distance_km": 0.71}], "hotel": [{"lat": 33.5952857, "lon": -7.6252246, "nom": "Hotel Windsor", "distance_km": 0.32}, {"lat": 33.5951283, "lon": -7.6246635, "nom": "Windsor", "distance_km": 0.35}, {"lat": 33.5991958, "lon": -7.6208392, "nom": "Mehdi House", "distance_km": 0.43}, {"lat": 33.5947874, "lon": -7.628718, "nom": "Barcel?? Hotels & Resorts", "distance_km": 0.49}, {"lat": 33.5932591, "lon": -7.6233917, "nom": "Hotel Les Almohades", "distance_km": 0.58}], "jardin": [{"lat": 33.5961282, "lon": -7.6239915, "nom": "?????????? ?????????? ????????????", "distance_km": 0.26}, {"lat": 33.595683, "lon": -7.622538, "nom": "Parc de l'Hypercentre", "distance_km": 0.38}, {"lat": 33.5986745, "lon": -7.631681, "nom": "Jardin Bordeaux", "distance_km": 0.59}, {"lat": 33.6023142, "lon": -7.6357926, "nom": "Parc le Lac", "distance_km": 1.07}, {"lat": 33.5882716, "lon": -7.624064, "nom": "Parc de la Ligue Arabe ?????????? ?????????????? ??????????????", "distance_km": 1.11}], "commerce": [{"lat": 33.5917373, "lon": -7.6270098, "nom": "Centre commercial Sorour", "distance_km": 0.73}, {"lat": 33.6012122, "lon": -7.6340939, "nom": "Dussy", "distance_km": 0.88}, {"lat": 33.5975901, "lon": -7.6157256, "nom": "Mazda", "distance_km": 0.9}, {"lat": 33.5958961, "lon": -7.6142839, "nom": "Centre Allal Ben Abdellah", "distance_km": 1.06}, {"lat": 33.6069866, "lon": -7.6206415, "nom": "Marina Shopping Center", "distance_km": 1.07}]}, "disponible": true}	2026-08-04 09:13:32.566997	[]
62e0cd4a-be63-4254-bd9b-304f1066917e	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	testproximites	test proximites	bureau	Fes	Fes	34.0631192	-4.9737999	50.00	12334.00	2	disponible	2026-08-04 09:06:59.056503	2026-08-04 09:16:34.956215	vente	\N	\N	\N	{"categories": {"ecole": [{"lat": 34.062892, "lon": -4.974572, "nom": "?????????? ?????? ???????????? ?????????????? (?????????? ??????????)", "distance_km": 0.08}, {"lat": 34.063688, "lon": -4.977373, "nom": "?????????? ??????????????", "distance_km": 0.34}, {"lat": 34.059415, "lon": -4.969828, "nom": "??cole Ben Ghazi", "distance_km": 0.55}, {"lat": 34.0631246, "lon": -4.9797455, "nom": "Shems'y ??cole des m??tiers d'arts", "distance_km": 0.55}, {"lat": 34.0677009, "lon": -4.9768355, "nom": "?????????? ?????????? ??????????????", "distance_km": 0.58}], "hotel": [{"lat": 34.063122, "lon": -4.9750446, "nom": "Riad Abadi", "distance_km": 0.11}, {"lat": 34.0640972, "lon": -4.9728407, "nom": "dar seffarine", "distance_km": 0.14}, {"lat": 34.0626425, "lon": -4.9754468, "nom": "Dar Bensouda", "distance_km": 0.16}, {"lat": 34.0617457, "lon": -4.9742668, "nom": "Riad Ouliya", "distance_km": 0.16}, {"lat": 34.0616571, "lon": -4.9744447, "nom": "Riad Laayoun", "distance_km": 0.17}], "jardin": [{"lat": 34.0609437, "lon": -4.9793896, "nom": "Dar Pacha Tazi", "distance_km": 0.57}, {"lat": 34.0706084, "lon": -4.9737998, "nom": "Oued Zhoun Garden", "distance_km": 0.83}, {"lat": 34.063457, "lon": -4.9853418, "nom": "Place Bab Mahrouk", "distance_km": 1.06}, {"lat": 34.0592882, "lon": -4.9846065, "nom": "Dar El-Beida Royal Palace", "distance_km": 1.08}, {"lat": 34.0585551, "lon": -4.9878437, "nom": "Jnan Sbil ???????? ????????????", "distance_km": 1.39}], "commerce": [{"lat": 34.0681079, "lon": -4.9861031, "nom": "Laiterie El Borje", "distance_km": 1.26}, {"lat": 34.0683084, "lon": -4.986206, "nom": "Cremerie Istanbul", "distance_km": 1.28}, {"lat": 34.0676913, "lon": -4.9873226, "nom": "Cremerie", "distance_km": 1.35}]}, "disponible": true}	2026-08-04 09:16:34.952129	[]
724ab875-34bc-41e9-8872-ad27d8eb17ca	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	testreclama2	GGHJH	appartement	ffhghjh	Casa	28.57487404744697	-3.2080078125000004	1234.00	1227.00	\N	disponible	2026-08-02 11:43:59.001929	2026-08-04 09:32:15.802074	vente	\N	\N	\N	{"categories": {"ecole": [], "hotel": [], "jardin": [], "commerce": []}, "disponible": true}	2026-08-04 09:32:15.801241	[]
2a1d7ff8-0647-47a0-a03f-7da13b38cfeb	ed5f8114-b388-498f-a130-db345f3fdbe3	test courtier	test courtier	appartement	Agadir	Agadir	28.926439238621036	-9.554573114194183	123.00	10000.00	4	disponible	2026-08-03 22:18:04.932784	2026-08-04 09:33:40.3609	location	\N	\N	\N	{"categories": {"ecole": [], "hotel": [], "jardin": [], "commerce": []}, "disponible": true}	2026-08-04 09:33:40.359919	[]
3f5b8f33-84c2-470f-9730-ff524e23aca3	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	test3	\N	appartement	test3	test3	\N	\N	345.00	1234.00	2	disponible	2026-07-28 13:40:58.226198	2026-08-07 09:29:50.183613	location	\N	\N	\N	\N	\N	[]
336a3e1c-9805-43cb-83a9-bd5a73e79526	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	test entourage	TEST	appartement	Rabat Hay Riad	Rabat	33.950444477350366	-6.88671112060547	100.00	12345.00	3	disponible	2026-08-02 17:15:11.510228	2026-08-07 23:29:08.031912	vente	\N	\N	\N	{"categories": {"ecole": [{"lat": 33.9574536, "lon": -6.8805559, "nom": "Ecole des Hautes Etudes Commerciales", "distance_km": 0.96}, {"lat": 33.9393162, "lon": -6.8860138, "nom": "IBN ELBACHIR", "distance_km": 1.24}], "hotel": [{"lat": 33.9424611, "lon": -6.8885922, "nom": "Cozy Haven Appartements", "distance_km": 0.9}], "jardin": [{"lat": 33.9517141, "lon": -6.8842574, "nom": "parc de jeu prestigia", "distance_km": 0.27}], "commerce": [{"lat": 33.9531872, "lon": -6.8805872, "nom": "Marjane Market", "distance_km": 0.64}]}, "disponible": true}	2026-08-07 23:29:08.023611	[]
51e8bf26-8fc8-4dcf-b6ab-0588f837c676	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	testlogo	testlogo	appartement	Agadir	Agadir	30.418218402096528	-9.583099102148358	100.00	999999.00	4	disponible	2026-08-03 10:50:53.344051	2026-08-04 09:13:52.426206	vente	\N	\N	\N	{"categories": {"ecole": [{"lat": 30.4198832, "lon": -9.586569, "nom": "ISTA", "distance_km": 0.38}, {"lat": 30.4172442, "lon": -9.5881276, "nom": "Ecole FATIMA AL FIHRYA", "distance_km": 0.49}, {"lat": 30.4158776, "lon": -9.5755937, "nom": "???????????? ??????????", "distance_km": 0.77}, {"lat": 30.4158387, "lon": -9.5752054, "nom": "???????? ???????????? ???????????? ???????????????? ????????????", "distance_km": 0.8}, {"lat": 30.423795, "lon": -9.5892325, "nom": "Ecole ATTAQADDOUM", "distance_km": 0.85}], "hotel": [{"lat": 30.4171173, "lon": -9.588974, "nom": "Riad Les Chtis d'Agadir", "distance_km": 0.58}, {"lat": 30.4222655, "lon": -9.5899952, "nom": "Agadirinou House", "distance_km": 0.8}, {"lat": 30.4103149, "lon": -9.5829455, "nom": "Senator Agadir Hotel", "distance_km": 0.88}, {"lat": 30.4182796, "lon": -9.5941731, "nom": "Residence Isni", "distance_km": 1.06}, {"lat": 30.4117063, "lon": -9.5915616, "nom": "Hotel Solman", "distance_km": 1.09}], "jardin": [{"lat": 30.4229944, "lon": -9.5855277, "nom": "Jardin Ihchahch", "distance_km": 0.58}, {"lat": 30.4202426, "lon": -9.5888312, "nom": "Jardin Talborjt", "distance_km": 0.59}, {"lat": 30.4129796, "lon": -9.5865804, "nom": "Jardin Lalla Meriem", "distance_km": 0.67}, {"lat": 30.4191834, "lon": -9.5927482, "nom": "Jardin Ibn Za??doun", "distance_km": 0.93}, {"lat": 30.4248676, "lon": -9.5952078, "nom": "F.O.S.E Agadir Club de l'Enseignant", "distance_km": 1.38}], "commerce": []}, "disponible": true}	2026-08-04 09:13:52.425118	[]
59f2772c-7920-4476-8954-45dbb3c8f83a	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	test entourage 2	test	villa	Rabat Hay Riad	Rabat	33.9640224	-6.8825842	300.00	12345.00	7	disponible	2026-08-02 17:26:19.313419	2026-08-04 09:19:21.540975	vente	\N	\N	\N	{"categories": {"ecole": [{"lat": 33.9652869, "lon": -6.8817595, "nom": "?????? ???????????? ??????????????", "distance_km": 0.16}, {"lat": 33.9667628, "lon": -6.88094, "nom": "???????????? ?????????????? ???????????? ??????????????????", "distance_km": 0.34}, {"lat": 33.9681023, "lon": -6.8778243, "nom": "?????????? ??????????????", "distance_km": 0.63}, {"lat": 33.9574536, "lon": -6.8805559, "nom": "Ecole des Hautes Etudes Commerciales", "distance_km": 0.75}, {"lat": 33.9690008, "lon": -6.8767504, "nom": "?????????????? ?????????????? ???????????? ???????????? ???????????? ??????????????", "distance_km": 0.77}], "hotel": [{"lat": 33.9697533, "lon": -6.8914096, "nom": "?????????? ??????????????????", "distance_km": 1.03}, {"lat": 33.975078, "lon": -6.882833, "nom": "Maison wlad benhaddouch", "distance_km": 1.23}], "jardin": [{"lat": 33.9727804, "lon": -6.882048, "nom": "?????????? ??????????????", "distance_km": 0.98}, {"lat": 33.9741336, "lon": -6.8911134, "nom": "?????? ????????????", "distance_km": 1.37}, {"lat": 33.9517141, "lon": -6.8842574, "nom": "parc de jeu prestigia", "distance_km": 1.38}], "commerce": [{"lat": 33.9531872, "lon": -6.8805872, "nom": "Marjane Market", "distance_km": 1.22}]}, "disponible": true}	2026-08-04 09:19:21.539975	[]
0d4347ab-c31e-4c05-8416-a709275a3427	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	testaproximits3	test	maison	Nador	Nador	35.1754779	-2.921135	100.00	1234553.00	4	disponible	2026-08-04 09:24:27.317958	2026-08-04 09:24:55.171633	vente	\N	\N	\N	{"categories": {"ecole": [{"lat": 35.1714601, "lon": -2.9233167, "nom": "Lyc??e Abdelkrim el Khatabi ???????????????? ?????????????????? ?????? ???????????? ??????????????", "distance_km": 0.49}, {"lat": 35.1779408, "lon": -2.9267562, "nom": "Lyc??e Qualifiant Ibn Rochd ???????????????? ?????????????????? ?????? ??????", "distance_km": 0.58}, {"lat": 35.1805876, "lon": -2.9235648, "nom": "??cole Primaire Martchika ?????????????? ???????????????????? ??????????????", "distance_km": 0.61}, {"lat": 35.1701863, "lon": -2.923716, "nom": "??cole Primaire Hassan II ?????????????? ???????????????????? ?????????? ????????????", "distance_km": 0.63}, {"lat": 35.1767067, "lon": -2.928335, "nom": "Institut Descartes d'Informatique ???????? ???????????? ??????????????????????", "distance_km": 0.67}], "hotel": [{"lat": 35.1741386, "lon": -2.9212711, "nom": "Hotel Al Khattabi ???????? ??????????????", "distance_km": 0.15}, {"lat": 35.174646, "lon": -2.919868, "nom": "Corniche Hotel", "distance_km": 0.15}, {"lat": 35.1740761, "lon": -2.9214681, "nom": "Hotel Nador ???????? ??????????????", "distance_km": 0.16}, {"lat": 35.1739696, "lon": -2.9205141, "nom": "Hotel Alhabib ???????? ????????????", "distance_km": 0.18}, {"lat": 35.1735738, "lon": -2.9215789, "nom": "Al Hilal ????????????", "distance_km": 0.22}], "jardin": [], "commerce": [{"lat": 35.1719465, "lon": -2.9354205, "nom": "Souk Oulad Mimoun", "distance_km": 1.36}, {"lat": 35.1708963, "lon": -2.936142, "nom": "Souk Oulad Mimoun", "distance_km": 1.46}]}, "disponible": true}	2026-08-04 09:24:55.170633	[]
54794b94-6d3c-4719-85f6-6a3f9a80af0f	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	testreclma4	NNN	appartement	test	test	29.420460341013133	-0.3515625	123.00	1234.00	3456	disponible	2026-08-02 16:04:56.696609	2026-08-04 09:32:37.140134	location	\N	\N	\N	{"categories": {"ecole": [], "hotel": [], "jardin": [], "commerce": []}, "disponible": true}	2026-08-04 09:32:37.139116	[]
81fe4ac5-8b61-434f-a675-ca5835740a2b	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	Villa familiale avec piscine ?? louer ??? Bouskoura, Casablanca	Situ??e dans une r??sidence s??curis??e ?? Bouskoura, cette villa moderne offre un cadre de vie calme et confortable. Elle comprend deux grands salons, cinq chambres spacieuses, une cuisine enti??rement ??quip??e, quatre salles de bain, un jardin paysager et une piscine priv??e. La r??sidence est proche des ??coles internationales, des commerces et des principaux axes routiers.	villa	R??sidence Les Jardins de Bouskoura	Casablanca	33.456443	-7.650666	300.00	19000.00	7	disponible	2026-07-29 09:47:27.059761	2026-08-06 09:14:29.597793	location	\N	\N	\N	{"categories": {"ecole": [{"lat": 33.4651848, "lon": -7.642313, "nom": "???????????? ?????? ???????? ????????????????", "distance_km": 1.24}], "hotel": [], "jardin": [], "commerce": []}, "disponible": true}	2026-08-06 09:14:29.596205	[]
70f0b5ea-6cc0-43c1-96f5-f0b45622db93	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	Appartement a vendre	huhhibnnkkllllkknnnbbbbbbbbb	appartement	Rabat Akdal	Rabat	33.9582551	-6.8712989	100.00	10000.00	\N	disponible	2026-07-30 11:06:10.774203	2026-08-06 09:15:38.932464	vente	\N	\N	\N	{"categories": {"ecole": [{"lat": 33.9610647, "lon": -6.8700316, "nom": "OFPPT", "distance_km": 0.33}, {"lat": 33.9616758, "lon": -6.8703527, "nom": "EIR", "distance_km": 0.39}, {"lat": 33.9583797, "lon": -6.8647222, "nom": "College Ibn Tofail", "distance_km": 0.61}, {"lat": 33.9574536, "lon": -6.8805559, "nom": "Ecole des Hautes Etudes Commerciales", "distance_km": 0.86}, {"lat": 33.966039, "lon": -6.8658688, "nom": "Centre Socio Educatif de Hay Ryad", "distance_km": 1.0}], "hotel": [{"lat": 33.956175, "lon": -6.8583089, "nom": "Athuya", "distance_km": 1.22}, {"lat": 33.9570245, "lon": -6.8570718, "nom": "Al Yabrouh", "distance_km": 1.32}, {"lat": 33.9566384, "lon": -6.8565576, "nom": "Al laymoune", "distance_km": 1.37}], "jardin": [{"lat": 33.9575433, "lon": -6.8573578, "nom": "jardin de la residence", "distance_km": 1.29}, {"lat": 33.9517141, "lon": -6.8842574, "nom": "parc de jeu prestigia", "distance_km": 1.4}, {"lat": 33.9534545, "lon": -6.8573031, "nom": "terrain vide", "distance_km": 1.4}], "commerce": [{"lat": 33.9531872, "lon": -6.8805872, "nom": "Marjane Market", "distance_km": 1.03}]}, "disponible": true}	2026-08-06 09:15:38.930442	[]
994b48c4-bdb9-4b57-a2fd-2d8dbe1a1f96	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	test equipement	test equipement	appartement	Casablanca	Casablanca	33.5832502	-7.6573822	100.00	11.63	14	disponible	2026-08-06 11:20:12.563396	2026-08-06 11:20:39.084918	location	\N	\N	\N	{"categories": {"ecole": [{"lat": 33.5815185, "lon": -7.6588138, "nom": "??cole La Cit?? Ghandi", "distance_km": 0.23}, {"lat": 33.5813161, "lon": -7.6582667, "nom": "Groupe Scolaire Mala??ka", "distance_km": 0.23}, {"lat": 33.5816878, "lon": -7.6515299, "nom": "Lyc??e Ziriab ???????????????? ?????????????????? ??????????", "distance_km": 0.57}, {"lat": 33.5791745, "lon": -7.653736, "nom": "Groupe Scolaire Romandie", "distance_km": 0.57}, {"lat": 33.5827076, "lon": -7.6509597, "nom": "Groupe Scolaire Tazi ???????????? ?????????? ????????????", "distance_km": 0.6}], "hotel": [{"lat": 33.5886569, "lon": -7.6477704, "nom": "Le Casablanca", "distance_km": 1.07}, {"lat": 33.5853855, "lon": -7.6442143, "nom": "Adagio", "distance_km": 1.24}], "jardin": [{"lat": 33.5914271, "lon": -7.6535687, "nom": "Jardin Val d'Anfa", "distance_km": 0.98}, {"lat": 33.5894107, "lon": -7.6456376, "nom": "Parc du V??lodrome ?????????? ????????????????????", "distance_km": 1.29}], "commerce": [{"lat": 33.5744135, "lon": -7.6503349, "nom": "Ghandi Mall", "distance_km": 1.18}, {"lat": 33.5900932, "lon": -7.6442751, "nom": "??????????????? ??????????????", "distance_km": 1.43}]}, "disponible": true}	2026-08-06 11:20:39.083919	["meuble", "climatisation", "lave_linge", "ascenseur", "jardin", "interphone_digicode", "espace_travail", "wifi", "parking", "television", "balcon_terrasse", "cuisine_equipee"]
25168926-7096-4245-be95-7cbc9f6b1404	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	testaproximite2	tes	appartement	Fes	Fes	34.0631192	-4.9737999	123.00	10000.00	4	loue	2026-08-04 09:22:06.482392	2026-08-07 09:05:52.06279	location	\N	\N	\N	{"categories": {"ecole": [{"lat": 34.062892, "lon": -4.974572, "nom": "?????????? ?????? ???????????? ?????????????? (?????????? ??????????)", "distance_km": 0.08}, {"lat": 34.063688, "lon": -4.977373, "nom": "?????????? ??????????????", "distance_km": 0.34}, {"lat": 34.059415, "lon": -4.969828, "nom": "??cole Ben Ghazi", "distance_km": 0.55}, {"lat": 34.0631246, "lon": -4.9797455, "nom": "Shems'y ??cole des m??tiers d'arts", "distance_km": 0.55}, {"lat": 34.0677009, "lon": -4.9768355, "nom": "?????????? ?????????? ??????????????", "distance_km": 0.58}], "hotel": [{"lat": 34.063122, "lon": -4.9750446, "nom": "Riad Abadi", "distance_km": 0.11}, {"lat": 34.0640972, "lon": -4.9728407, "nom": "dar seffarine", "distance_km": 0.14}, {"lat": 34.0626425, "lon": -4.9754468, "nom": "Dar Bensouda", "distance_km": 0.16}, {"lat": 34.0617457, "lon": -4.9742668, "nom": "Riad Ouliya", "distance_km": 0.16}, {"lat": 34.0616571, "lon": -4.9744447, "nom": "Riad Laayoun", "distance_km": 0.17}], "jardin": [{"lat": 34.0609437, "lon": -4.9793896, "nom": "Dar Pacha Tazi", "distance_km": 0.57}, {"lat": 34.0706084, "lon": -4.9737998, "nom": "Oued Zhoun Garden", "distance_km": 0.83}, {"lat": 34.063457, "lon": -4.9853418, "nom": "Place Bab Mahrouk", "distance_km": 1.06}, {"lat": 34.0592882, "lon": -4.9846065, "nom": "Dar El-Beida Royal Palace", "distance_km": 1.08}, {"lat": 34.0585551, "lon": -4.9878437, "nom": "Jnan Sbil ???????? ????????????", "distance_km": 1.39}], "commerce": [{"lat": 34.0681079, "lon": -4.9861031, "nom": "Laiterie El Borje", "distance_km": 1.26}, {"lat": 34.0683084, "lon": -4.986206, "nom": "Cremerie Istanbul", "distance_km": 1.28}, {"lat": 34.0676913, "lon": -4.9873226, "nom": "Cremerie", "distance_km": 1.35}]}, "disponible": true}	2026-08-04 09:22:07.036966	[]
c9d32aca-fd6b-4de0-a9ea-d401e743c6e3	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	testdocker	TEST	appartement	hghgh	hhh	33.44003646532446	-7.505947251986897	100.00	121677.00	6	disponible	2026-08-07 23:37:58.861873	2026-08-07 23:38:15.993532	location	\N	\N	\N	{"categories": {"ecole": [], "hotel": [], "jardin": [], "commerce": []}, "disponible": true}	2026-08-07 23:38:15.990289	["meuble", "climatisation"]
\.


--
-- Data for Name: contrat; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.contrat (id, reservation_id, bien_id, proprietaire_id, client_id, date_signature, date_debut, date_fin, montant_loyer, fichier_url, statut, date_creation, date_limite_paiement, date_limite_annulation) FROM stdin;
d4a4aa95-61fb-4917-9664-126c3a25a144	ebbacc8c-c574-4359-b559-0e9258fa3d22	25168926-7096-4245-be95-7cbc9f6b1404	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	8216d907-2261-4154-ba11-5e4016de7d47	2026-08-07 09:05:52.088309	2026-08-07	2026-12-09	10000.00	\N	actif	2026-08-07 09:05:52.093031	\N	2026-08-08 09:05:52.088309
dfcc3b41-cf8d-46e0-ba55-2589c6a067af	3b71dbb2-3478-4fc7-aaa1-90f8b3c65ff1	3f5b8f33-84c2-470f-9730-ff524e23aca3	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	8216d907-2261-4154-ba11-5e4016de7d47	\N	2026-08-06	\N	1234.00	\N	resilie	2026-08-06 09:23:23.213813	2026-08-07 09:23:23.201544	\N
\.


--
-- Data for Name: conversation; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.conversation (id, bien_id, client_id, proprietaire_id, date_creation) FROM stdin;
a97c4feb-1ece-4cf1-ac76-c9424d557385	0412744c-9325-4468-b5ff-c2167079180f	8216d907-2261-4154-ba11-5e4016de7d47	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	2026-08-06 09:13:11.387616
d85cd277-0446-4a09-b876-fb6188c869c2	25168926-7096-4245-be95-7cbc9f6b1404	8216d907-2261-4154-ba11-5e4016de7d47	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	2026-08-06 21:01:53.384494
\.


--
-- Data for Name: favori; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.favori (id, utilisateur_id, bien_id, date_creation) FROM stdin;
201716ac-dc12-4d6d-ae3b-2646a82dc8e9	8216d907-2261-4154-ba11-5e4016de7d47	81fe4ac5-8b61-434f-a675-ca5835740a2b	2026-08-06 09:13:52.981686
\.


--
-- Data for Name: message; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.message (id, conversation_id, expediteur_id, contenu, lu, date_envoi, piece_jointe_url, piece_jointe_nom, piece_jointe_type) FROM stdin;
052f6725-436c-4c0e-8083-9f6c8ded6d74	d85cd277-0446-4a09-b876-fb6188c869c2	8216d907-2261-4154-ba11-5e4016de7d47	hi	f	2026-08-06 21:01:57.068627	\N	\N	\N
\.


--
-- Data for Name: notification; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.notification (id, utilisateur_id, type_notification, contenu, lu, date_creation) FROM stdin;
8fec3d9d-91d9-45d1-9f94-561c38fa45bd	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? testt ?? de la part de ilhame elma.	t	2026-07-23 18:25:22.345
bc9824ab-21ca-499b-b2eb-847a2ab9058c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? kkk ?? de la part de ilhame elma.	t	2026-07-24 18:43:39.988022
38caef54-7e79-48db-ad55-ae2902a8c674	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? hhihji ?? de la part de ilhame elma.	t	2026-07-24 19:42:16.411183
62fd3d31-3cbf-48b7-9900-05eff1b57b17	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? kjj ?? de la part de ilhame elma.	t	2026-07-25 10:40:03.269709
51b86e37-37e5-4f32-88f2-82b82a2b9121	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? JH ?? de la part de ilhame elma.	t	2026-07-25 11:08:25.230608
fe5e64c8-a01e-4dbb-89b0-63d42e90f17c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? KJ ?? de la part de ilhame elma.	f	2026-07-25 20:22:45.588403
ccb0c1a2-d849-4c13-843f-64648dc27b22	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? t ?? de la part de ilhame elma.	f	2026-07-25 20:49:54.906332
a3f9c4df-ea3b-4154-8a7b-b17f56811fc1	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? hhihji ?? de la part de ilhame elma.	f	2026-07-25 21:11:11.482461
6dddf6a4-48c6-4a5f-95cc-f3ba6b181df8	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? KJ ?? de la part de ilhame elma.	f	2026-07-25 21:40:37.051557
8331eaa5-7d35-4a4c-81bb-bce037f1bdc5	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? hhihji ?? de la part de ilhame elma.	f	2026-07-25 21:40:49.404977
babb3517-2721-4e52-ba9a-9c870e622f54	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? kkk ?? de la part de ilhame elma.	f	2026-07-25 21:58:00.831927
0189090e-1977-46c8-a425-b1e46855c194	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? apparetement a louer ?? de la part de ilhame elma.	f	2026-07-25 22:10:26.407231
7ebe74a5-094e-4cd2-9297-4defcefefdae	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? hhihji ?? de la part de ilhame elma.	f	2026-07-25 22:18:37.435662
3f5effd9-a23e-40d7-be65-0cfe1bc5a1c1	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? hhihji ?? de la part de ilhame elma.	f	2026-07-25 22:26:00.429236
800ab355-4bb4-4b2f-a8ce-7c6d169397bf	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test1 ?? de la part de ilhame elma.	f	2026-07-26 10:07:32.040978
52c8afb5-3647-46c2-b348-72a3f90c6e09	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test1 ?? de la part de ilhame elma.	f	2026-07-26 10:14:03.304797
3e5c5dde-372f-4694-8d0b-be76e3a30b80	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test1 ?? de la part de ilhame elma.	f	2026-07-26 10:14:08.586633
9c04cf48-1b85-4a42-b5cd-657c034ffe3c	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test ?? de la part de ilhame elma.	f	2026-07-26 10:24:30.079713
789c5437-836b-4bd1-a23f-43698ed83164	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test ?? de la part de ilhame elma.	f	2026-07-26 10:42:33.803409
e2e81f90-b63a-4d18-bf95-7f71b9089c90	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? hhihji ?? de la part de ilhame elma.	f	2026-07-26 10:45:08.973312
b9aa9087-4b10-4d2c-9d1a-e03c902d8ce0	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? t ?? de la part de ilhame elma.	f	2026-07-26 11:22:38.789697
dc032fca-86e8-4ace-8a6e-5369dc9d0662	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test1 ?? de la part de ilhame elma.	f	2026-07-26 11:22:42.573612
1d80221e-031d-43bd-892b-b5cb7d8f0cd7	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test1 ?? de la part de ilhame elma.	f	2026-07-26 17:50:59.464275
e6388fb3-c451-40d8-aee3-6da1bef01b81	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? t ?? de la part de ilhame elma.	f	2026-07-26 18:29:13.755003
5443036a-eba1-4a2d-8e1d-e0bd5c09cee4	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? t ?? de la part de ilhame elma.	f	2026-07-27 10:43:45.258334
f2a8c727-2ecd-4ef3-a4af-756ab9c12113	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? t ??.	f	2026-07-31 11:24:13.084982
9d419629-0d68-41cb-9f36-2e428527be62	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? test reclamation ??.	f	2026-08-02 10:45:04.657742
45babb4c-b83f-4fd6-874a-7054cac155ee	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? test reclamation ?? : ?? lannance est  faux ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-02 10:45:04.69957
5e41dffd-57fe-4015-b18c-8ba25eef4951	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? testreclama2 ??.	f	2026-08-02 11:45:08.775282
56741cf7-4195-4586-a475-cfb9ba242b0a	4b799642-6c05-4d33-891d-283e833b049f	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? testreclama2 ??.	f	2026-08-02 11:45:08.799018
6caa78ba-b733-4c42-96f2-e2b09f44350d	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? testreclama2 ?? : ?? LE PRIX INCONVENABLE ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-02 11:45:08.828897
65b327e5-c233-4e9b-9e78-1ad6169aeb38	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? testreclama2 ??.	f	2026-08-02 11:52:58.622714
e554aa47-2a2a-4eb7-af4e-9302d876b6d5	4b799642-6c05-4d33-891d-283e833b049f	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? testreclama2 ??.	f	2026-08-02 11:52:59.302842
defaecf3-96c9-4daa-b714-6c190ca09696	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? testreclama2 ?? : ?? la annce  n'est pas claire ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-02 11:52:59.937624
171c44e4-3f99-4ad7-a288-2d798079b98b	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? reclam3 ??.	f	2026-08-02 12:03:42.45708
9881b18d-ec95-4298-afe5-1db440f0a1e6	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? reclam3 ?? : ?? PRIX PROBLEM ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-02 12:03:45.611248
4315a969-9d8c-4a49-b75f-18d1ab452aae	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? reclam3 ??.	f	2026-08-02 12:06:31.714304
639dab8f-ffa5-4b8a-83e8-d1f9a3af86ba	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? reclam3 ?? : ?? ANNACE INCOMPLETE ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-02 12:06:33.774166
291b6bd5-c9ae-4b24-917c-a0e7fbb8d623	4b799642-6c05-4d33-891d-283e833b049f	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? reclam3 ??.	t	2026-08-02 12:06:32.718383
f2ecebdf-c871-42ba-a150-f3b5567b78ce	4b799642-6c05-4d33-891d-283e833b049f	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? reclam3 ??.	t	2026-08-02 12:03:43.728671
33f0cd8a-1379-449b-9981-c9993eaacb1f	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? testreclma4 ??.	f	2026-08-02 16:05:55.503808
021c0619-429b-44fe-be21-db0fd965e59c	4b799642-6c05-4d33-891d-283e833b049f	reclamation	Nouvelle r??clamation de ilhame elmat (Annonce trompeuse) concernant ?? testreclma4 ??.	f	2026-08-02 16:05:55.516692
418bc4e3-c8ff-4907-a57b-5bd42f2029ff	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? testreclma4 ?? : ?? annance n'est pas corecte ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-02 16:05:55.528857
df516b23-6a1d-4862-b4d6-f04feed76725	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? testreclma4 ??.	f	2026-08-02 16:08:18.783644
0c28a532-78a4-4738-a912-295f99bf83b6	4b799642-6c05-4d33-891d-283e833b049f	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? testreclma4 ??.	f	2026-08-02 16:08:20.162896
c4e7606b-5c71-4a81-90e7-647081be4678	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? testreclma4 ?? : ?? annace n'est pas claire ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-02 16:08:21.533549
b4d435ab-b285-4dd8-afbb-f03361e07351	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? t ?? de la part de ilhame elmat.	f	2026-08-03 11:35:05.862392
68a86370-44d5-4642-a764-9406024eb9a4	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? t ?? de la part de elma karima.	f	2026-08-05 10:13:27.126989
a5d2e3cd-b367-4c6d-9c6c-f4172bb4ece2	8216d907-2261-4154-ba11-5e4016de7d47	reservation	Votre r??servation pour ?? t ?? a ??t?? confirm??e. Vous disposez de 24h pour effectuer le paiement depuis votre espace ?? Mes r??servations ??, sans quoi elle sera annul??e automatiquement.	f	2026-08-05 10:14:12.255463
fd1a7b81-6312-4bfc-ac00-c8801af84b1f	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? kkk ?? de la part de elma karima.	f	2026-08-06 09:20:16.969884
f59c1785-a11a-4757-8adb-585455104daa	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test3 ?? de la part de elma karima.	f	2026-08-06 09:21:13.56535
3fa92e3f-c500-4e16-9590-0bf69e43fb59	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? test3 ?? de la part de elma karima.	f	2026-08-06 09:22:55.6194
37b16b50-3288-4dff-8cb6-3cfc130640d3	8216d907-2261-4154-ba11-5e4016de7d47	reservation	Votre r??servation pour ?? test3 ?? a ??t?? confirm??e. Vous disposez de 24h pour effectuer le paiement depuis votre espace ?? Mes r??servations ??, sans quoi elle sera annul??e automatiquement.	f	2026-08-06 09:23:23.359154
fb85009e-aaf7-46a9-a7d6-c877b13fd4a8	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	Nouvelle demande de r??servation pour ?? Appartement moderne ?? louer ??? Agdal, Rabat ?? de la part de elma karima.	f	2026-08-06 09:29:11.90726
cbf5c1fb-d103-4775-ab06-1dba1bbbf30c	8216d907-2261-4154-ba11-5e4016de7d47	reservation	Votre r??servation pour ?? t ?? a ??t?? annul??e automatiquement : le paiement n'a pas ??t?? effectu?? dans le d??lai de 24h apr??s confirmation.	f	2026-08-06 10:16:36.890976
83e73aa7-363e-4a03-858d-86773d1f319f	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	La r??servation de ?? t ?? a ??t?? annul??e automatiquement : le client n'a pas effectu?? le paiement dans le d??lai imparti. Le bien est de nouveau disponible ?? la r??servation.	f	2026-08-06 10:16:36.915228
c1f43b3e-2e91-49ec-8791-e8936c9bccc5	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	reservation	Nouvelle demande de r??servation pour ?? testaproximite2 ?? de la part de elma karima.	f	2026-08-06 21:01:34.473571
d3dac57b-6b3d-44d1-bc8e-c9a546f99c7f	1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? testaproximite2 ??.	f	2026-08-06 21:10:46.135566
71a9e91c-7a41-4b14-9557-14fec2db9fab	4b799642-6c05-4d33-891d-283e833b049f	reclamation	Nouvelle r??clamation de elma karima (Annonce trompeuse) concernant ?? testaproximite2 ??.	f	2026-08-06 21:10:47.719325
6be054c5-c646-493c-915d-a089f52a1f21	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	avertissement	?????? Un client a d??pos?? une r??clamation vous concernant (Annonce trompeuse) au sujet de l'annonce ?? testaproximite2 ?? : ?? prix nest pas corcte ??. Notre ??quipe va l'examiner ; vous serez tenu inform?? de son traitement.	f	2026-08-06 21:10:49.172474
6262b83c-df1b-40b9-a6f8-81860afb6df1	83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	reservation	R??servation pay??e et confirm??e pour ?? testaproximite2 ?? par elma karima (10000.00 MAD, carte bancaire).	f	2026-08-07 09:05:52.784001
cb460b8e-5742-4b0a-aae8-b6f6678e43b9	8216d907-2261-4154-ba11-5e4016de7d47	paiement	Paiement de 10000.00 MAD confirm?? pour ?? testaproximite2 ??. R??servation confirm??e. Vous pouvez encore l'annuler gratuitement pendant 24h depuis ?? Mes r??servations ??.	f	2026-08-07 09:05:54.232555
c8f11e5f-ce21-4dc3-94e7-691f1197960c	8216d907-2261-4154-ba11-5e4016de7d47	reservation	Votre r??servation pour ?? test3 ?? a ??t?? annul??e automatiquement : le paiement n'a pas ??t?? effectu?? dans le d??lai de 24h apr??s confirmation.	f	2026-08-07 09:29:50.215895
2acace95-c26d-4475-9972-b1eb9395a68e	e8dfdd21-1f8b-4148-8ef3-44a8d09da176	reservation	La r??servation de ?? test3 ?? a ??t?? annul??e automatiquement : le client n'a pas effectu?? le paiement dans le d??lai imparti. Le bien est de nouveau disponible ?? la r??servation.	f	2026-08-07 09:29:51.486992
\.


--
-- Data for Name: paiement; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.paiement (id, contrat_id, montant, methode, reference_transaction, statut, date_paiement) FROM stdin;
8b848598-8688-4d0d-acd4-7d233729ff0e	d4a4aa95-61fb-4917-9664-126c3a25a144	10000.00	carte_bancaire	**** 7654	reussi	2026-08-07 09:05:52.099626
\.


--
-- Data for Name: photo_bien; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.photo_bien (id, bien_id, url, ordre) FROM stdin;
a721fcde-703e-4a31-b49a-e42e44046696	cfa9c2df-b5b3-4a4f-af65-2adff7f09c14	http://localhost:9000/smartrent-photos/biens/cfa9c2df-b5b3-4a4f-af65-2adff7f09c14/081886ee0fd3492b85f3ebfe84b6c9f1.jfif	0
d9d73f50-ef06-4c4f-ac6e-ffe0dc71e7af	273c6a23-fe44-44a6-ae9c-fe328715aa80	http://localhost:9000/smartrent-photos/biens/273c6a23-fe44-44a6-ae9c-fe328715aa80/a0b75f2c433f49fc81454df909ae0742.jfif	0
714ecec1-79eb-44dc-82c9-c20d8cfffc7f	0412744c-9325-4468-b5ff-c2167079180f	http://localhost:9000/smartrent-photos/biens/0412744c-9325-4468-b5ff-c2167079180f/94f223b53ac74d148d7e1d2d6722900a.jfif	0
3988f9ac-df5f-4348-8227-8fc6c7711065	3f5b8f33-84c2-470f-9730-ff524e23aca3	http://localhost:9000/smartrent-photos/biens/3f5b8f33-84c2-470f-9730-ff524e23aca3/d3237a26cb31446983ff0387a64e29ea.jfif	0
b05682ab-cade-4cdc-8480-a7ca06cabba7	3f5b8f33-84c2-470f-9730-ff524e23aca3	http://localhost:9000/smartrent-photos/biens/3f5b8f33-84c2-470f-9730-ff524e23aca3/bcb1777c43904120883a65a13c4b07e0.png	1
20574be3-0b3b-4566-bdaf-cb92d68de156	3f5b8f33-84c2-470f-9730-ff524e23aca3	http://localhost:9000/smartrent-photos/biens/3f5b8f33-84c2-470f-9730-ff524e23aca3/9ff33b464ee04fbaa7e1c61494ba6293.png	2
150f0b52-03e2-432f-8b5a-97ff7d49a87a	b843ccfc-fa17-4d97-96cd-f23f52c8277c	http://localhost:9000/smartrent-photos/biens/b843ccfc-fa17-4d97-96cd-f23f52c8277c/2b4c32a4a65a4a02881fec4b4a30ee74.jfif	0
37ef9f96-7f0d-4a1a-870d-58530bf58ce5	b843ccfc-fa17-4d97-96cd-f23f52c8277c	http://localhost:9000/smartrent-photos/biens/b843ccfc-fa17-4d97-96cd-f23f52c8277c/52c57cb75d234827a879e9cd6281e2e4.png	1
16153d5f-9f47-47a6-afc0-e67453b5c44d	81fe4ac5-8b61-434f-a675-ca5835740a2b	http://localhost:9000/smartrent-photos/biens/81fe4ac5-8b61-434f-a675-ca5835740a2b/743682d4df2e4ef38e1d2179fbbe88dc.jfif	0
4bddb268-a0ad-4e40-af84-d807bcdd0af9	81fe4ac5-8b61-434f-a675-ca5835740a2b	http://localhost:9000/smartrent-photos/biens/81fe4ac5-8b61-434f-a675-ca5835740a2b/65c9e11190b2462fbb031c53450cc9e6.jfif	1
04f2ed19-c5e5-4210-82aa-a523a5b9dfc1	70f0b5ea-6cc0-43c1-96f5-f0b45622db93	http://localhost:9000/smartrent-photos/biens/70f0b5ea-6cc0-43c1-96f5-f0b45622db93/79f2e8d7ce2b4d19bbae450b064eeb88.jfif	0
e3415312-573e-44e6-b6c5-35c39d61a809	70f0b5ea-6cc0-43c1-96f5-f0b45622db93	http://localhost:9000/smartrent-photos/biens/70f0b5ea-6cc0-43c1-96f5-f0b45622db93/237c8479c66641618908eb3cd47de78b.jfif	1
3f79abc9-3c1c-452c-a2d4-03bc05cd03fb	70f0b5ea-6cc0-43c1-96f5-f0b45622db93	http://localhost:9000/smartrent-photos/biens/70f0b5ea-6cc0-43c1-96f5-f0b45622db93/573320d400a6479f8e99a339acd5ee2b.jfif	2
97e23104-e042-4c00-ae73-f865403d3743	b8953417-e72b-4604-9254-f7c680782222	http://localhost:9000/smartrent-photos/biens/b8953417-e72b-4604-9254-f7c680782222/a29f8abb00a34aa1b4e79bcd1ed4040f.jfif	0
8131cfb0-a3ca-4621-aa52-bc2b917fd080	724ab875-34bc-41e9-8872-ad27d8eb17ca	http://localhost:9000/smartrent-photos/biens/724ab875-34bc-41e9-8872-ad27d8eb17ca/af4d24ac6a27432c84abb3140556f0a0.jfif	0
4379f00e-04bc-4ba7-b4ac-3ec6c36e9aac	e4dd3a88-1619-4bf6-a22c-594d119c48f0	http://localhost:9000/smartrent-photos/biens/e4dd3a88-1619-4bf6-a22c-594d119c48f0/84ac18fe3a664f448892f71294024dec.jfif	0
a1e7e046-8491-4d04-9087-2f805dd0ef62	54794b94-6d3c-4719-85f6-6a3f9a80af0f	http://localhost:9000/smartrent-photos/biens/54794b94-6d3c-4719-85f6-6a3f9a80af0f/c3699c278a6f47a493b462ac840a0510.jfif	0
44cdf65f-de1d-4171-bba0-4f647cd08f26	336a3e1c-9805-43cb-83a9-bd5a73e79526	http://localhost:9000/smartrent-photos/biens/336a3e1c-9805-43cb-83a9-bd5a73e79526/174da82454fc4a83bebb40ed5e191945.jfif	0
9d1e4cd4-03e5-4da0-a60d-713a8d97632d	59f2772c-7920-4476-8954-45dbb3c8f83a	http://localhost:9000/smartrent-photos/biens/59f2772c-7920-4476-8954-45dbb3c8f83a/89d97b7aa01d40c1a63a439fc6c14661.jfif	0
a7b9eb92-bbb9-4891-a9bb-a1c9e880369c	59f2772c-7920-4476-8954-45dbb3c8f83a	http://localhost:9000/smartrent-photos/biens/59f2772c-7920-4476-8954-45dbb3c8f83a/3880a8fb0f0b40a9954499a7a74a9d9a.jfif	1
63266027-324d-425e-ab7d-7f918dc67235	2b5915fc-f749-4de0-84a1-a3b9fc0a101e	http://localhost:9000/smartrent-photos/biens/2b5915fc-f749-4de0-84a1-a3b9fc0a101e/a451bcbf9000469bbae1a65fd2dfaa9b.jfif	0
5121df89-2b95-4a78-9abd-6429ab87f37a	51e8bf26-8fc8-4dcf-b6ab-0588f837c676	http://localhost:9000/smartrent-photos/biens/51e8bf26-8fc8-4dcf-b6ab-0588f837c676/b85daf3a25424b88892c7feb330e120a.jpg	0
81551200-e41d-46a8-be09-5f6bd7b935b5	2a1d7ff8-0647-47a0-a03f-7da13b38cfeb	http://localhost:9000/smartrent-photos/biens/2a1d7ff8-0647-47a0-a03f-7da13b38cfeb/62594e6b7f1b46aab37fbbf47ee4bdbe.jpg	0
04d8d098-d8ff-4f23-8668-b04b912c10f1	2a1d7ff8-0647-47a0-a03f-7da13b38cfeb	http://localhost:9000/smartrent-photos/biens/2a1d7ff8-0647-47a0-a03f-7da13b38cfeb/8f05ae87800040d9b5d322dda695d510.jpg	1
6463b369-eccd-4a05-9ee4-02057cf7a364	5fbc5ca1-6154-46e7-98ae-c34158e71554	http://localhost:9000/smartrent-photos/biens/5fbc5ca1-6154-46e7-98ae-c34158e71554/9dc1402479e84bbeabb76104245567a1.jpg	0
ecb52237-9f46-447d-bedf-2bfd64c3f38a	5fbc5ca1-6154-46e7-98ae-c34158e71554	http://localhost:9000/smartrent-photos/biens/5fbc5ca1-6154-46e7-98ae-c34158e71554/269a4ca11bec4ddebd87221a63345b88.jpg	1
e1c046c6-e616-456c-bcee-d067dc8e7b27	813c7de2-0bec-4461-af61-b71b5212d315	http://localhost:9000/smartrent-photos/biens/813c7de2-0bec-4461-af61-b71b5212d315/a04b3a1d60e84fafa25c72af1d630149.jpg	0
cd5679ad-a6fe-4067-8827-b29d93b06c2b	62e0cd4a-be63-4254-bd9b-304f1066917e	http://localhost:9000/smartrent-photos/biens/62e0cd4a-be63-4254-bd9b-304f1066917e/8842a992042545ea964a83bf625bf61a.jpg	0
676aeaf9-1eca-47b7-b6de-45f71ccce779	62e0cd4a-be63-4254-bd9b-304f1066917e	http://localhost:9000/smartrent-photos/biens/62e0cd4a-be63-4254-bd9b-304f1066917e/994ffc58684d4c2788188b9b1cfc8f62.jpg	1
a40bd40b-b6ef-42f5-ac18-35c363ef13a2	25168926-7096-4245-be95-7cbc9f6b1404	http://localhost:9000/smartrent-photos/biens/25168926-7096-4245-be95-7cbc9f6b1404/8682a5e255404e51917da3e7a8bdbf9a.jpg	0
036342e4-2de5-4c56-b910-d2f36917c716	25168926-7096-4245-be95-7cbc9f6b1404	http://localhost:9000/smartrent-photos/biens/25168926-7096-4245-be95-7cbc9f6b1404/5ed643aae4dc426782fc044228455b88.jpg	1
f9125b34-82fb-413d-9773-7f28155c9cb6	0d4347ab-c31e-4c05-8416-a709275a3427	http://localhost:9000/smartrent-photos/biens/0d4347ab-c31e-4c05-8416-a709275a3427/499294e002194ad782adfd4543a078ad.jpg	0
1d48a1c2-0075-4d48-bc99-f3f033fa98c9	994b48c4-bdb9-4b57-a2fd-2d8dbe1a1f96	http://localhost:9000/smartrent-photos/biens/994b48c4-bdb9-4b57-a2fd-2d8dbe1a1f96/72d1d8dbb07149d29b6d12aaea0460db.jpg	0
\.


--
-- Data for Name: projet_immobilier; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.projet_immobilier (id, promoteur_id, nom, description, type_bien, ville, adresse, latitude, longitude, statut, date_livraison_prevue, date_creation, date_maj) FROM stdin;
24a5692f-7d79-4aa6-9902-869f97b089b0	8d3fa2c5-6fae-4280-8e25-ea7487930de4	Residenance soukaina	test promoteur	appartement	Meknes	Meknes 	32.84036602561056	-5.686039955315796	en_construction	\N	2026-08-03 22:20:21.438173	2026-08-03 22:20:21.438173
\.


--
-- Data for Name: recherche_historique; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.recherche_historique (id, client_id, label, criteres, date_recherche) FROM stdin;
cbf3f649-3d3b-4abf-9545-6cc53857534e	8216d907-2261-4154-ba11-5e4016de7d47	Location ?? ?? test ??	{"q": "test", "tri": "pertinence", "type_bien": "tous", "type_transaction": "location"}	2026-08-06 09:15:30.81471
\.


--
-- Data for Name: reclamation; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.reclamation (id, utilisateur_id, bien_id, contrat_id, type_reclamation, description, statut, date_creation) FROM stdin;
b88f84a6-c9eb-42d1-9fe3-da8e3d748395	8216d907-2261-4154-ba11-5e4016de7d47	724ab875-34bc-41e9-8872-ad27d8eb17ca	\N	annonce_trompeuse	la annce  n'est pas claire	resolue	2026-08-02 11:52:57.822999
fbe60d2f-e95c-459a-af52-90b39f072a2d	8216d907-2261-4154-ba11-5e4016de7d47	e4dd3a88-1619-4bf6-a22c-594d119c48f0	\N	annonce_trompeuse	ANNACE INCOMPLETE	ouverte	2026-08-02 12:06:30.709167
85c2a961-cf87-4919-9e74-e4962191fd99	8216d907-2261-4154-ba11-5e4016de7d47	54794b94-6d3c-4719-85f6-6a3f9a80af0f	\N	annonce_trompeuse	annace n'est pas claire	ouverte	2026-08-02 16:08:16.758611
d7d1d83e-c828-4959-af30-a6e136688427	8216d907-2261-4154-ba11-5e4016de7d47	25168926-7096-4245-be95-7cbc9f6b1404	\N	annonce_trompeuse	prix nest pas corcte	ouverte	2026-08-06 21:10:44.825543
\.


--
-- Data for Name: reservation; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.reservation (id, bien_id, client_id, date_debut, date_fin, statut, date_creation) FROM stdin;
244b2fbf-9767-49a2-a769-4b7348c49453	3f5b8f33-84c2-470f-9730-ff524e23aca3	8216d907-2261-4154-ba11-5e4016de7d47	2026-08-06	\N	en_attente	2026-08-06 09:21:13.530511
bbf072ca-7947-4b33-9ebd-274bc8f50e24	b843ccfc-fa17-4d97-96cd-f23f52c8277c	8216d907-2261-4154-ba11-5e4016de7d47	2026-08-06	\N	en_attente	2026-08-06 09:29:11.883435
b7e3fd12-05f7-4a9f-b1fa-ee9d7828516c	25168926-7096-4245-be95-7cbc9f6b1404	8216d907-2261-4154-ba11-5e4016de7d47	2026-08-06	\N	en_attente	2026-08-06 21:01:34.250074
ebbacc8c-c574-4359-b559-0e9258fa3d22	25168926-7096-4245-be95-7cbc9f6b1404	8216d907-2261-4154-ba11-5e4016de7d47	2026-08-07	2026-12-09	confirmee	2026-08-07 09:05:52.077082
3b71dbb2-3478-4fc7-aaa1-90f8b3c65ff1	3f5b8f33-84c2-470f-9730-ff524e23aca3	8216d907-2261-4154-ba11-5e4016de7d47	2026-08-06	\N	annulee	2026-08-06 09:22:55.560638
\.


--
-- Data for Name: utilisateur; Type: TABLE DATA; Schema: public; Owner: smartrent
--

COPY public.utilisateur (id, nom, prenom, email, mot_de_passe_hash, telephone, role, statut_verification, date_creation, date_maj, raison_sociale, numero_rc, numero_carte_pro, email_verifie, email_verification_token, email_verification_expire) FROM stdin;
1f7b8d7a-9ac1-41a5-ae63-e9db52b455da	admin	admin1	admin@gmail.com	$2b$12$l74WQB/fLAOwjcvKpqGjHe71RQlX.tScKPio04NQZzkTSq1eJpKIS	0789654312	admin	verifie	2026-07-23 10:03:03.080542	2026-07-23 10:03:03.080542	\N	\N	\N	t	\N	\N
e8dfdd21-1f8b-4148-8ef3-44a8d09da176	elma	ily	ily123@gmail.com	$2b$12$4X45i8gmln8B/lsEsyLKRO0oIeM.hfsiRoADW.gxexDwKg/0cbFzm	06788907654	proprietaire	verifie	2026-07-22 11:33:27.836184	2026-07-23 10:03:31.081297	\N	\N	\N	t	\N	\N
8216d907-2261-4154-ba11-5e4016de7d47	karima	elma	karima@gmail.com	$2b$12$jnvfVcpiSrNOcdMp8J4mp.okL.q8JG/l0SDjiF1TehtiBMlEeDkru	0898765432	client	verifie	2026-07-28 19:39:13.077962	2026-07-28 19:39:13.077962	\N	\N	\N	t	\N	\N
4b799642-6c05-4d33-891d-283e833b049f	vision	immo	immovision260@gmail.com	$2b$12$UJXhLC2oPb9hHaGq8y1Kd.6mauEm61pXW1APWR6eogm1j7CV3Rc3S	0678543212	admin	verifie	2026-08-02 11:36:40.462858	2026-08-02 11:36:40.462858	\N	\N	\N	t	\N	\N
83cd0abc-3c0c-4a48-996e-62f0bb8adcdd	sali	salima	ilhameelma@gmail.com	$2b$12$u3oQt9TJ3X8lWfsM61gBuegxMjJp8zNSxuPSv.gdfFZyeEHOnncQG	0789654312	proprietaire	verifie	2026-08-02 10:39:54.606875	2026-08-02 11:37:33.078647	\N	\N	\N	t	\N	\N
8d3fa2c5-6fae-4280-8e25-ea7487930de4	chahd	rizlane	rizlane@gmail.com	$2b$12$UBCJRj8s6mBfZ/T0eW49AuCTz6lC3NU2pYsBrpIElHFUO/Zb7bhkC		promoteur	en_attente	2026-08-03 22:05:41.921762	2026-08-03 22:05:41.921762	rizlane immobilier		\N	t	\N	\N
ed5f8114-b388-498f-a130-db345f3fdbe3	elma	firdous	firdous@gmail.com	$2b$12$XYEhqt4Law8TY/3zsBqaHeTDQaqh7C.ox8BnO4Pn/uHXRZtT1vRGK	0789654312	conciergerie	verifie	2026-08-03 22:00:23.292485	2026-08-04 20:21:38.023166				t	\N	\N
9361c869-620e-4160-95ca-a938c5271c8b	nwisr	soumya	ilyelma315@gmail.com	$2b$12$wIQJffKi4sE9dA4dj779Ne6ac7d7YtY6XjnMOjAPRO888CZksTVDi		agence	en_attente	2026-08-08 08:41:33.059297	2026-08-08 08:41:56.50675	soumya immobilier		\N	t	\N	\N
b71aecd7-f03e-4acc-a1f5-e38ed6cc2305	snhaji	khadija	khadija@gmail.com	$2b$12$H/EyPr8q4b5/vlZ7kqIP7.BV7.mNoojZo84VwdXCComgD7zD/7.lS		client	verifie	2026-08-04 10:31:15.865453	2026-08-09 16:05:29.644244	\N	\N	\N	f	673050	2026-08-09 16:20:27.748928
ca34e8b2-6727-499e-9832-117d62a3baa2	elma	ilha	ilhamelmattichi12@gmail.com	$2b$12$tZiF8UJuZfpLJew3YMt26eTWRATJ7M08jDW9zED80z.y5KnZLcNUe		client	verifie	2026-08-09 16:07:23.55313	2026-08-09 16:07:48.929488	\N	\N	\N	t	\N	\N
\.


--
-- Name: dim_ville_ville_id_seq; Type: SEQUENCE SET; Schema: dw; Owner: smartrent
--

SELECT pg_catalog.setval('dw.dim_ville_ville_id_seq', 1, false);


--
-- Name: dim_date dim_date_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (date_id);


--
-- Name: dim_utilisateur dim_utilisateur_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.dim_utilisateur
    ADD CONSTRAINT dim_utilisateur_pkey PRIMARY KEY (utilisateur_id);


--
-- Name: dim_ville dim_ville_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.dim_ville
    ADD CONSTRAINT dim_ville_pkey PRIMARY KEY (ville_id);


--
-- Name: dim_ville dim_ville_ville_key; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.dim_ville
    ADD CONSTRAINT dim_ville_ville_key UNIQUE (ville);


--
-- Name: fait_avis fait_avis_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_avis
    ADD CONSTRAINT fait_avis_pkey PRIMARY KEY (avis_id);


--
-- Name: fait_bien fait_bien_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_bien
    ADD CONSTRAINT fait_bien_pkey PRIMARY KEY (bien_id);


--
-- Name: fait_contrat fait_contrat_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_contrat
    ADD CONSTRAINT fait_contrat_pkey PRIMARY KEY (contrat_id);


--
-- Name: fait_paiement fait_paiement_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_paiement
    ADD CONSTRAINT fait_paiement_pkey PRIMARY KEY (paiement_id);


--
-- Name: fait_performance_bien fait_performance_bien_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_performance_bien
    ADD CONSTRAINT fait_performance_bien_pkey PRIMARY KEY (bien_id);


--
-- Name: fait_reclamation fait_reclamation_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_reclamation
    ADD CONSTRAINT fait_reclamation_pkey PRIMARY KEY (reclamation_id);


--
-- Name: fait_reservation fait_reservation_pkey; Type: CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_reservation
    ADD CONSTRAINT fait_reservation_pkey PRIMARY KEY (reservation_id);


--
-- Name: actualite actualite_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.actualite
    ADD CONSTRAINT actualite_pkey PRIMARY KEY (id);


--
-- Name: avis avis_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.avis
    ADD CONSTRAINT avis_pkey PRIMARY KEY (id);


--
-- Name: bien bien_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.bien
    ADD CONSTRAINT bien_pkey PRIMARY KEY (id);


--
-- Name: contrat contrat_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.contrat
    ADD CONSTRAINT contrat_pkey PRIMARY KEY (id);


--
-- Name: contrat contrat_reservation_id_key; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.contrat
    ADD CONSTRAINT contrat_reservation_id_key UNIQUE (reservation_id);


--
-- Name: conversation conversation_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.conversation
    ADD CONSTRAINT conversation_pkey PRIMARY KEY (id);


--
-- Name: favori favori_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.favori
    ADD CONSTRAINT favori_pkey PRIMARY KEY (id);


--
-- Name: message message_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_pkey PRIMARY KEY (id);


--
-- Name: notification notification_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_pkey PRIMARY KEY (id);


--
-- Name: paiement paiement_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.paiement
    ADD CONSTRAINT paiement_pkey PRIMARY KEY (id);


--
-- Name: photo_bien photo_bien_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.photo_bien
    ADD CONSTRAINT photo_bien_pkey PRIMARY KEY (id);


--
-- Name: projet_immobilier projet_immobilier_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.projet_immobilier
    ADD CONSTRAINT projet_immobilier_pkey PRIMARY KEY (id);


--
-- Name: recherche_historique recherche_historique_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.recherche_historique
    ADD CONSTRAINT recherche_historique_pkey PRIMARY KEY (id);


--
-- Name: reclamation reclamation_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.reclamation
    ADD CONSTRAINT reclamation_pkey PRIMARY KEY (id);


--
-- Name: reservation reservation_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_pkey PRIMARY KEY (id);


--
-- Name: favori uq_favori_utilisateur_bien; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.favori
    ADD CONSTRAINT uq_favori_utilisateur_bien UNIQUE (utilisateur_id, bien_id);


--
-- Name: utilisateur utilisateur_email_key; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.utilisateur
    ADD CONSTRAINT utilisateur_email_key UNIQUE (email);


--
-- Name: utilisateur utilisateur_pkey; Type: CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.utilisateur
    ADD CONSTRAINT utilisateur_pkey PRIMARY KEY (id);


--
-- Name: idx_fait_avis_bien; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_avis_bien ON dw.fait_avis USING btree (bien_id);


--
-- Name: idx_fait_bien_ville; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_bien_ville ON dw.fait_bien USING btree (ville_id);


--
-- Name: idx_fait_contrat_ville; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_contrat_ville ON dw.fait_contrat USING btree (ville_id);


--
-- Name: idx_fait_paiement_date; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_paiement_date ON dw.fait_paiement USING btree (date_id);


--
-- Name: idx_fait_paiement_ville; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_paiement_ville ON dw.fait_paiement USING btree (ville_id);


--
-- Name: idx_fait_perf_bien_ville; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_perf_bien_ville ON dw.fait_performance_bien USING btree (ville_id);


--
-- Name: idx_fait_reclamation_bien; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_reclamation_bien ON dw.fait_reclamation USING btree (bien_id);


--
-- Name: idx_fait_reservation_ville; Type: INDEX; Schema: dw; Owner: smartrent
--

CREATE INDEX idx_fait_reservation_ville ON dw.fait_reservation USING btree (ville_id);


--
-- Name: idx_actualite_publie_date; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_actualite_publie_date ON public.actualite USING btree (publie, date_creation DESC);


--
-- Name: idx_avis_bien; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_avis_bien ON public.avis USING btree (bien_id);


--
-- Name: idx_avis_proprietaire; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_avis_proprietaire ON public.avis USING btree (proprietaire_id);


--
-- Name: idx_bien_projet; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_bien_projet ON public.bien USING btree (projet_id);


--
-- Name: idx_bien_proprietaire; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_bien_proprietaire ON public.bien USING btree (proprietaire_id);


--
-- Name: idx_bien_type; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_bien_type ON public.bien USING btree (type_bien);


--
-- Name: idx_bien_type_transaction; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_bien_type_transaction ON public.bien USING btree (type_transaction);


--
-- Name: idx_bien_ville; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_bien_ville ON public.bien USING btree (ville);


--
-- Name: idx_contrat_bien; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_contrat_bien ON public.contrat USING btree (bien_id);


--
-- Name: idx_contrat_client; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_contrat_client ON public.contrat USING btree (client_id);


--
-- Name: idx_conversation_client; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_conversation_client ON public.conversation USING btree (client_id);


--
-- Name: idx_conversation_proprietaire; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_conversation_proprietaire ON public.conversation USING btree (proprietaire_id);


--
-- Name: idx_favori_bien; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_favori_bien ON public.favori USING btree (bien_id);


--
-- Name: idx_favori_utilisateur; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_favori_utilisateur ON public.favori USING btree (utilisateur_id);


--
-- Name: idx_message_conversation; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_message_conversation ON public.message USING btree (conversation_id);


--
-- Name: idx_notification_utilisateur; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_notification_utilisateur ON public.notification USING btree (utilisateur_id);


--
-- Name: idx_paiement_contrat; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_paiement_contrat ON public.paiement USING btree (contrat_id);


--
-- Name: idx_photo_bien; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_photo_bien ON public.photo_bien USING btree (bien_id);


--
-- Name: idx_projet_promoteur; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_projet_promoteur ON public.projet_immobilier USING btree (promoteur_id);


--
-- Name: idx_projet_ville; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_projet_ville ON public.projet_immobilier USING btree (ville);


--
-- Name: idx_recherche_historique_client; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_recherche_historique_client ON public.recherche_historique USING btree (client_id);


--
-- Name: idx_recherche_historique_client_date; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_recherche_historique_client_date ON public.recherche_historique USING btree (client_id, date_recherche DESC);


--
-- Name: idx_reclamation_utilisateur; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_reclamation_utilisateur ON public.reclamation USING btree (utilisateur_id);


--
-- Name: idx_reservation_bien; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_reservation_bien ON public.reservation USING btree (bien_id);


--
-- Name: idx_reservation_client; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_reservation_client ON public.reservation USING btree (client_id);


--
-- Name: idx_utilisateur_email_verification_token; Type: INDEX; Schema: public; Owner: smartrent
--

CREATE INDEX idx_utilisateur_email_verification_token ON public.utilisateur USING btree (email_verification_token);


--
-- Name: fait_avis fait_avis_date_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_avis
    ADD CONSTRAINT fait_avis_date_id_fkey FOREIGN KEY (date_id) REFERENCES dw.dim_date(date_id);


--
-- Name: fait_bien fait_bien_date_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_bien
    ADD CONSTRAINT fait_bien_date_id_fkey FOREIGN KEY (date_id) REFERENCES dw.dim_date(date_id);


--
-- Name: fait_bien fait_bien_ville_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_bien
    ADD CONSTRAINT fait_bien_ville_id_fkey FOREIGN KEY (ville_id) REFERENCES dw.dim_ville(ville_id);


--
-- Name: fait_contrat fait_contrat_date_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_contrat
    ADD CONSTRAINT fait_contrat_date_id_fkey FOREIGN KEY (date_id) REFERENCES dw.dim_date(date_id);


--
-- Name: fait_contrat fait_contrat_ville_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_contrat
    ADD CONSTRAINT fait_contrat_ville_id_fkey FOREIGN KEY (ville_id) REFERENCES dw.dim_ville(ville_id);


--
-- Name: fait_paiement fait_paiement_date_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_paiement
    ADD CONSTRAINT fait_paiement_date_id_fkey FOREIGN KEY (date_id) REFERENCES dw.dim_date(date_id);


--
-- Name: fait_paiement fait_paiement_ville_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_paiement
    ADD CONSTRAINT fait_paiement_ville_id_fkey FOREIGN KEY (ville_id) REFERENCES dw.dim_ville(ville_id);


--
-- Name: fait_performance_bien fait_performance_bien_ville_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_performance_bien
    ADD CONSTRAINT fait_performance_bien_ville_id_fkey FOREIGN KEY (ville_id) REFERENCES dw.dim_ville(ville_id);


--
-- Name: fait_reclamation fait_reclamation_date_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_reclamation
    ADD CONSTRAINT fait_reclamation_date_id_fkey FOREIGN KEY (date_id) REFERENCES dw.dim_date(date_id);


--
-- Name: fait_reservation fait_reservation_date_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_reservation
    ADD CONSTRAINT fait_reservation_date_id_fkey FOREIGN KEY (date_id) REFERENCES dw.dim_date(date_id);


--
-- Name: fait_reservation fait_reservation_ville_id_fkey; Type: FK CONSTRAINT; Schema: dw; Owner: smartrent
--

ALTER TABLE ONLY dw.fait_reservation
    ADD CONSTRAINT fait_reservation_ville_id_fkey FOREIGN KEY (ville_id) REFERENCES dw.dim_ville(ville_id);


--
-- Name: actualite actualite_auteur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.actualite
    ADD CONSTRAINT actualite_auteur_id_fkey FOREIGN KEY (auteur_id) REFERENCES public.utilisateur(id);


--
-- Name: avis avis_bien_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.avis
    ADD CONSTRAINT avis_bien_id_fkey FOREIGN KEY (bien_id) REFERENCES public.bien(id) ON DELETE CASCADE;


--
-- Name: avis avis_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.avis
    ADD CONSTRAINT avis_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: avis avis_proprietaire_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.avis
    ADD CONSTRAINT avis_proprietaire_id_fkey FOREIGN KEY (proprietaire_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: bien bien_projet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.bien
    ADD CONSTRAINT bien_projet_id_fkey FOREIGN KEY (projet_id) REFERENCES public.projet_immobilier(id) ON DELETE SET NULL;


--
-- Name: bien bien_proprietaire_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.bien
    ADD CONSTRAINT bien_proprietaire_id_fkey FOREIGN KEY (proprietaire_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: contrat contrat_bien_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.contrat
    ADD CONSTRAINT contrat_bien_id_fkey FOREIGN KEY (bien_id) REFERENCES public.bien(id) ON DELETE CASCADE;


--
-- Name: contrat contrat_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.contrat
    ADD CONSTRAINT contrat_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: contrat contrat_proprietaire_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.contrat
    ADD CONSTRAINT contrat_proprietaire_id_fkey FOREIGN KEY (proprietaire_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: contrat contrat_reservation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.contrat
    ADD CONSTRAINT contrat_reservation_id_fkey FOREIGN KEY (reservation_id) REFERENCES public.reservation(id) ON DELETE SET NULL;


--
-- Name: conversation conversation_bien_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.conversation
    ADD CONSTRAINT conversation_bien_id_fkey FOREIGN KEY (bien_id) REFERENCES public.bien(id) ON DELETE SET NULL;


--
-- Name: conversation conversation_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.conversation
    ADD CONSTRAINT conversation_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: conversation conversation_proprietaire_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.conversation
    ADD CONSTRAINT conversation_proprietaire_id_fkey FOREIGN KEY (proprietaire_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: favori favori_bien_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.favori
    ADD CONSTRAINT favori_bien_id_fkey FOREIGN KEY (bien_id) REFERENCES public.bien(id) ON DELETE CASCADE;


--
-- Name: favori favori_utilisateur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.favori
    ADD CONSTRAINT favori_utilisateur_id_fkey FOREIGN KEY (utilisateur_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: message message_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversation(id) ON DELETE CASCADE;


--
-- Name: message message_expediteur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_expediteur_id_fkey FOREIGN KEY (expediteur_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: notification notification_utilisateur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_utilisateur_id_fkey FOREIGN KEY (utilisateur_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: paiement paiement_contrat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.paiement
    ADD CONSTRAINT paiement_contrat_id_fkey FOREIGN KEY (contrat_id) REFERENCES public.contrat(id) ON DELETE CASCADE;


--
-- Name: photo_bien photo_bien_bien_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.photo_bien
    ADD CONSTRAINT photo_bien_bien_id_fkey FOREIGN KEY (bien_id) REFERENCES public.bien(id) ON DELETE CASCADE;


--
-- Name: projet_immobilier projet_immobilier_promoteur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.projet_immobilier
    ADD CONSTRAINT projet_immobilier_promoteur_id_fkey FOREIGN KEY (promoteur_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: recherche_historique recherche_historique_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.recherche_historique
    ADD CONSTRAINT recherche_historique_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: reclamation reclamation_bien_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.reclamation
    ADD CONSTRAINT reclamation_bien_id_fkey FOREIGN KEY (bien_id) REFERENCES public.bien(id) ON DELETE SET NULL;


--
-- Name: reclamation reclamation_contrat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.reclamation
    ADD CONSTRAINT reclamation_contrat_id_fkey FOREIGN KEY (contrat_id) REFERENCES public.contrat(id) ON DELETE SET NULL;


--
-- Name: reclamation reclamation_utilisateur_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.reclamation
    ADD CONSTRAINT reclamation_utilisateur_id_fkey FOREIGN KEY (utilisateur_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- Name: reservation reservation_bien_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_bien_id_fkey FOREIGN KEY (bien_id) REFERENCES public.bien(id) ON DELETE CASCADE;


--
-- Name: reservation reservation_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: smartrent
--

ALTER TABLE ONLY public.reservation
    ADD CONSTRAINT reservation_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict Sf2ZFN1yDeJPAGV53RFzL84mG9GACdbVwW5T2r6IqW5SQY1IJ5hrCgkR39HsULD

