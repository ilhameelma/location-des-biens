// Types alignés EXACTEMENT sur les réponses JSON du back-end FastAPI
// (voir backend/app/schemas.py — lui-même aligné sur postgres/smartrent_schema.sql)

export type Role = "admin" | "proprietaire" | "client";
export type StatutVerification = "en_attente" | "verifie" | "rejete";

export interface Utilisateur {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  telephone?: string | null;
  role: Role;
  statut_verification: StatutVerification;
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

export type StatutBien = "disponible" | "loue" | "en_attente" | "suspendu";

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
  adresse: string;
  ville: string;
  superficie?: number | null;
  prix: number;
  nb_pieces?: number | null;
  statut: StatutBien;
  latitude?: number | null;
  longitude?: number | null;
  photos: PhotoBien[];
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
  contenu: string;
  date_envoi: string;
  lu: boolean;
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

