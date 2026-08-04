// Types alignés EXACTEMENT sur les réponses JSON du back-end FastAPI
// (voir backend/app/schemas.py — lui-même aligné sur postgres/smartrent_schema.sql)

// Rôles "annonceurs" professionnels ajoutés en plus de proprietaire :
//   agence     = agence immobilière
//   promoteur  = promoteur immobilier (publie des lots au sein d'un projet)
//   courtier   = courtier / "samsar" (publie au nom d'un propriétaire tiers)
export type Role = "admin" | "proprietaire" | "client" | "agence" | "promoteur" | "courtier";
export type StatutVerification = "en_attente" | "verifie" | "rejete";

export interface Utilisateur {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  telephone?: string | null;
  role: Role;
  statut_verification: StatutVerification;
  email_verifie: boolean;
  raison_sociale?: string | null;
  numero_rc?: string | null;
  numero_carte_pro?: string | null;
  date_creation: string;
}

export type TypeBien =
  | "maison"
  | "appartement"
  | "magasin"
  | "garage"
  | "bureau"
  | "terrain"
  | "villa";

export type StatutBien = "disponible" | "loue" | "vendu" | "en_attente" | "suspendu";
export type TypeTransaction = "location" | "vente";

export interface PhotoBien {
  id: string;
  url: string;
  ordre: number;
}

export interface Bien {
  id: string;
  proprietaire_id: string;
  titre: string;
  description?: string | null;
  type_bien: TypeBien;
  type_transaction: TypeTransaction;
  adresse: string;
  ville: string;
  superficie?: number | null;
  prix: number;
  nb_pieces?: number | null;
  statut: StatutBien;
  latitude?: number | null;
  longitude?: number | null;
  // Promoteur uniquement : lot rattaché à un projet (voir ProjetImmobilier).
  projet_id?: string | null;
  // Courtier (obligatoire) / agence (optionnel) : propriétaire réel du bien.
  mandant_nom?: string | null;
  mandant_telephone?: string | null;
  photos: PhotoBien[];
  proprietaire_nom?: string | null;
  proprietaire_prenom?: string | null;
  proprietaire_role?: Role | null;
  proprietaire_raison_sociale?: string | null;
}

// Fiche profil publique d'un propriétaire (GET /utilisateurs/{id}/profil-public)
export interface ProprietairePublic {
  id: string;
  nom: string;
  prenom: string;
  role: Role;
  raison_sociale?: string | null;
  date_creation: string;
  nb_biens_actifs: number;
  note_moyenne: number | null;
  nb_avis: number;
}

// ---------- Projet immobilier (promoteur) ----------
export type StatutProjet = "en_construction" | "livre" | "termine";

export interface ProjetImmobilier {
  id: string;
  promoteur_id: string;
  nom: string;
  description?: string | null;
  type_bien: TypeBien;
  ville: string;
  adresse: string;
  latitude?: number | null;
  longitude?: number | null;
  statut: StatutProjet;
  date_livraison_prevue?: string | null;
  date_creation: string;
  nb_lots: number;
  nb_lots_disponibles: number;
  prix_min?: number | null;
  prix_max?: number | null;
  promoteur_nom?: string | null;
  promoteur_prenom?: string | null;
  promoteur_raison_sociale?: string | null;
}

// Complément étape 17 — points d'intérêt à proximité (Overpass/OSM)
export type CategoriePoi = "hotel" | "jardin" | "ecole" | "commerce";

export interface Poi {
  nom: string;
  distance_km: number;
  lat: number;
  lon: number;
}

export interface ProximiteBien {
  disponible: boolean;
  categories: Partial<Record<CategoriePoi, Poi[]>>;
}

export type StatutReservation = "en_attente" | "confirmee" | "refusee" | "annulee";

export interface Reservation {
  id: string;
  bien_id: string;
  client_id: string;
  date_debut: string;
  date_fin?: string | null;
  statut: StatutReservation;
}

export type StatutContrat = "actif" | "termine" | "resilie";

export interface Contrat {
  id: string;
  reservation_id?: string | null;
  bien_id: string;
  proprietaire_id: string;
  client_id: string;
  date_signature?: string | null;
  date_debut: string;
  date_fin?: string | null;
  montant_loyer: number;
  fichier_url?: string | null;
  statut: StatutContrat;
}

export type StatutPaiement = "en_attente" | "reussi" | "echoue" | "rembourse";

export interface Paiement {
  id: string;
  contrat_id: string;
  montant: number;
  methode: string;
  reference_transaction?: string | null;
  statut: StatutPaiement;
  date_paiement: string;
}

export interface Avis {
  id: string;
  client_id: string;
  proprietaire_id: string;
  bien_id: string;
  note: number;
  commentaire?: string | null;
  date_creation: string;
  client_nom?: string | null;
  client_prenom?: string | null;
  bien_titre?: string | null;
}

export type StatutReclamation = "ouverte" | "en_cours" | "resolue" | "rejetee";

export interface Reclamation {
  id: string;
  utilisateur_id: string;
  bien_id?: string | null;
  contrat_id?: string | null;
  type_reclamation: string;
  description: string;
  statut: StatutReclamation;
  date_creation: string;
  bien_titre?: string | null;
  client_nom?: string | null;
  client_prenom?: string | null;
  client_email?: string | null;
  client_telephone?: string | null;
  proprietaire_id?: string | null;
  proprietaire_nom?: string | null;
  proprietaire_prenom?: string | null;
  proprietaire_email?: string | null;
  proprietaire_telephone?: string | null;
  // Nombre total de réclamations reçues par l'annonce concernée (bien_id),
  // toutes réclamations confondues. null/undefined si bien_id est absent.
  bien_reclamations_count?: number | null;
}

export interface Favori {
  id: string;
  bien_id: string;
  date_creation: string;
}

// Historique de recherche (page de recherche client)
export interface CriteresRecherche {
  type_transaction: TypeTransaction;
  ville?: string;
  type_bien?: TypeBien | "tous";
  q?: string;
  prix_min?: string;
  prix_max?: string;
  superficie_min?: string;
  tri?: "pertinence" | "prix_asc" | "prix_desc" | "recent";
}

export interface RechercheHistorique {
  id: string;
  label: string;
  criteres: CriteresRecherche;
  date_recherche: string;
}

export interface Conversation {
  id: string;
  bien_id?: string | null;
  bien_titre?: string | null;
  client_id: string;
  proprietaire_id: string;
  autre_nom: string;
  autre_prenom: string;
  dernier_message?: string | null;
  date_dernier_message?: string | null;
  non_lus: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  expediteur_id: string;
  contenu?: string | null;
  date_envoi: string;
  lu: boolean;
  piece_jointe_url?: string | null;
  piece_jointe_nom?: string | null;
  piece_jointe_type?: "image" | "pdf" | null;
}

export interface Notification {
  id: string;
  type_notification: string;
  contenu: string;
  lu: boolean;
  date_creation: string;
}

// ---------- Intelligence artificielle (étape 16) ----------

export interface EstimationResponse {
  prix_estime_dh: number;
  fourchette_basse_dh: number;
  fourchette_haute_dh: number;
  marge_erreur_dh: number;
}

export interface FraudeResponse {
  est_suspect: boolean;
  prix_attendu_dh: number;
  ecart_prix_pct: number;
  raison: string;
  anomaly_score: number;
}

export interface RecommandationItem {
  id?: string | null;
  titre?: string | null;
  ville: string;
  quartier?: string | null;
  prix_dh: number;
  superficie_m2?: number | null;
  score_similarite: number;
}

export interface RecommandationResponse {
  source_catalogue: "reel" | "bootstrap_externe";
  resultats: RecommandationItem[];
}

