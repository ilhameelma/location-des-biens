import uuid
from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field, model_validator

# Rôles "annonceurs" professionnels (agence/promoteur/conciergerie), en plus du
# propriétaire particulier — voir ROLES_ANNONCEURS dans deps.py pour le
# groupe utilisé côté contrôle d'accès.
Role = Literal["admin", "proprietaire", "client", "agence", "promoteur", "conciergerie"]
StatutVerification = Literal["en_attente", "verifie", "rejete"]
TypeBien = Literal["maison", "appartement", "magasin", "garage", "bureau", "terrain", "villa"]
TypeTransaction = Literal["location", "vente"]
StatutBien = Literal["disponible", "loue", "vendu", "en_attente", "suspendu"]
StatutReservation = Literal["en_attente", "confirmee", "refusee", "annulee"]
StatutContrat = Literal["actif", "termine", "resilie"]
StatutPaiement = Literal["en_attente", "reussi", "echoue", "rembourse"]
StatutReclamation = Literal["ouverte", "en_cours", "resolue", "rejetee"]
StatutProjet = Literal["en_construction", "livre", "termine"]

# Rôles pour qui la raison sociale (nom de société) est obligatoire à l'inscription.
_ROLES_RAISON_SOCIALE_OBLIGATOIRE = ("agence", "promoteur")


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    user: "UtilisateurOut"


class RegisterRequest(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    password: str = Field(min_length=8)
    telephone: Optional[str] = None
    role: Role
    # Champs professionnels — raison_sociale obligatoire pour agence/promoteur
    # (voir validateur ci-dessous), numero_carte_pro optionnel pour conciergerie
    # (pas toujours de carte professionnelle officielle).
    raison_sociale: Optional[str] = None
    numero_rc: Optional[str] = None
    numero_carte_pro: Optional[str] = None

    @model_validator(mode="after")
    def _valider_champs_professionnels(self):
        # Le rôle "admin" ne doit jamais pouvoir être créé via l'inscription
        # publique (front-end ou appel direct à l'API) — seuls les comptes
        # admin déjà existants en base peuvent se connecter.
        if self.role == "admin":
            raise ValueError("Le rôle Administrateur ne peut pas être choisi à l'inscription.")

        if self.role in _ROLES_RAISON_SOCIALE_OBLIGATOIRE and not (
            self.raison_sociale and self.raison_sociale.strip()
        ):
            raise ValueError(
                "La raison sociale est obligatoire pour un compte Agence immobilière "
                "ou Promoteur immobilier."
            )
        return self


# ---------- Utilisateur ----------
class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nom: str
    prenom: str
    email: EmailStr
    telephone: Optional[str] = None
    role: Role
    statut_verification: StatutVerification
    email_verifie: bool
    raison_sociale: Optional[str] = None
    numero_rc: Optional[str] = None
    numero_carte_pro: Optional[str] = None
    date_creation: datetime


class RegisterResponse(BaseModel):
    """Réponse de POST /auth/register : pas de token — le compte doit d'abord
    être confirmé par email avant de pouvoir se connecter."""
    message: str
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    """Saisie du code OTP reçu par email (6 chiffres) pour confirmer un compte."""
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UtilisateurUpdate(BaseModel):
    """Page « Mon compte » : mise à jour du profil (tous les champs optionnels,
    seuls ceux envoyés par le front-end sont modifiés)."""
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(default=None, max_length=20)
    raison_sociale: Optional[str] = Field(default=None, max_length=150)
    numero_rc: Optional[str] = Field(default=None, max_length=50)
    numero_carte_pro: Optional[str] = Field(default=None, max_length=50)


class ChangePasswordRequest(BaseModel):
    mot_de_passe_actuel: str
    nouveau_mot_de_passe: str = Field(min_length=8)


# ---------- Bien ----------
class PhotoBienOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    url: str
    ordre: int


class BienCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    type_bien: TypeBien
    type_transaction: TypeTransaction = "location"
    adresse: str
    ville: str
    superficie: Optional[float] = None
    prix: float
    nb_pieces: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Promoteur uniquement : lot rattaché à un projet (voir routers/projets.py) —
    # requis pour ce rôle, refusé pour les autres (contrôlé côté router).
    projet_id: Optional[uuid.UUID] = None
    # Conciergerie (obligatoire) / agence (optionnel) : propriétaire réel du bien.
    mandant_nom: Optional[str] = None
    mandant_telephone: Optional[str] = None
    # Équipements/commodités (façon Airbnb) — liste de codes libres, propres
    # au catalogue défini côté front (frontend/src/lib/equipements.ts),
    # différent selon type_bien (résidentiel/bureau/magasin/garage/terrain).
    equipements: list[str] = Field(default_factory=list)


class BienUpdate(BaseModel):
    """Tous les champs sont optionnels : seuls ceux envoyés par le front-end
    sont modifiés (voir `payload.model_dump(exclude_unset=True)` dans le
    router). Permet une édition complète de l'annonce par son propriétaire,
    pas seulement le prix/statut/position."""
    titre: Optional[str] = None
    description: Optional[str] = None
    type_bien: Optional[TypeBien] = None
    type_transaction: Optional[TypeTransaction] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    superficie: Optional[float] = None
    prix: Optional[float] = None
    nb_pieces: Optional[int] = None
    statut: Optional[StatutBien] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    mandant_nom: Optional[str] = None
    mandant_telephone: Optional[str] = None
    equipements: Optional[list[str]] = None


class BienOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    proprietaire_id: uuid.UUID
    titre: str
    description: Optional[str] = None
    type_bien: TypeBien
    type_transaction: TypeTransaction
    adresse: str
    ville: str
    superficie: Optional[float] = None
    prix: float
    nb_pieces: Optional[int] = None
    statut: StatutBien
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    projet_id: Optional[uuid.UUID] = None
    mandant_nom: Optional[str] = None
    mandant_telephone: Optional[str] = None
    equipements: list[str] = []
    photos: list[PhotoBienOut] = []
    # Pratique pour l'affichage ("Publié par ...") sans requête supplémentaire.
    proprietaire_nom: Optional[str] = None
    proprietaire_prenom: Optional[str] = None
    proprietaire_role: Optional[Role] = None
    proprietaire_raison_sociale: Optional[str] = None


# ---------- Fiche profil publique d'un propriétaire ----------
class ProprietairePublicOut(BaseModel):
    """Consultable par tout visiteur (ex. lien "Voir le profil" depuis une
    fiche bien) — expose uniquement des informations non sensibles (pas
    d'email, pas de téléphone). Utilisé pour les 4 rôles annonceurs
    (proprietaire/agence/promoteur/conciergerie)."""
    id: uuid.UUID
    nom: str
    prenom: str
    role: Role
    raison_sociale: Optional[str] = None
    date_creation: datetime
    nb_biens_actifs: int
    note_moyenne: Optional[float] = None
    nb_avis: int


# ---------- Projet immobilier (promoteur) ----------
class ProjetCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    type_bien: TypeBien
    ville: str
    adresse: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    date_livraison_prevue: Optional[date] = None


class ProjetUpdate(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    type_bien: Optional[TypeBien] = None
    ville: Optional[str] = None
    adresse: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    date_livraison_prevue: Optional[date] = None
    statut: Optional[StatutProjet] = None


class ProjetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    promoteur_id: uuid.UUID
    nom: str
    description: Optional[str] = None
    type_bien: TypeBien
    ville: str
    adresse: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    statut: StatutProjet
    date_livraison_prevue: Optional[date] = None
    date_creation: datetime
    # Enrichissements calculés côté routeur (voir routers/projets.py._enrich)
    nb_lots: int = 0
    nb_lots_disponibles: int = 0
    prix_min: Optional[float] = None
    prix_max: Optional[float] = None
    promoteur_nom: Optional[str] = None
    promoteur_prenom: Optional[str] = None
    promoteur_raison_sociale: Optional[str] = None


# ---------- Proximité (complément étape 17 — points d'intérêt OSM/Overpass) ----------
class PoiOut(BaseModel):
    nom: str
    distance_km: float
    lat: float
    lon: float


class ProximiteOut(BaseModel):
    disponible: bool
    categories: dict[str, list[PoiOut]]


# ---------- Reservation ----------
class ReservationCreate(BaseModel):
    bien_id: uuid.UUID
    date_debut: date
    date_fin: Optional[date] = None


MethodePaiementInstantane = Literal["carte_bancaire", "virement"]


class ReservationInstantaneeCreate(BaseModel):
    """Réservation + paiement en une seule étape (carte ou virement),
    avant toute validation du propriétaire — voir
    POST /reservations/instantanee. Réservé aux annonces en location
    (type_transaction="location") ; une offre d'achat continue de passer
    par ReservationCreate (POST /reservations), sans paiement immédiat."""

    bien_id: uuid.UUID
    date_debut: date
    date_fin: Optional[date] = None
    methode_paiement: MethodePaiementInstantane
    # Référence simulée (jamais de vraies coordonnées bancaires côté
    # back-end) : ex. "**** 4242" pour une carte, ou une référence de
    # virement saisie/générée côté front.
    reference_transaction: Optional[str] = None


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bien_id: uuid.UUID
    client_id: uuid.UUID
    date_debut: date
    date_fin: Optional[date] = None
    statut: StatutReservation
    # Processus de paiement (rempli uniquement une fois la réservation
    # confirmée, voir Reservation.contrat_id et propriétés associées dans
    # app/models.py) : permet au front-end d'afficher directement "Payer
    # maintenant" + le compte à rebours sans appel API supplémentaire.
    contrat_id: Optional[uuid.UUID] = None
    date_limite_paiement: Optional[datetime] = None
    paiement_effectue: Optional[bool] = None
    montant_a_payer: Optional[float] = None
    # Réservation instantanée avec paiement immédiat : fenêtre d'annulation
    # gratuite (24h par défaut, voir settings.delai_annulation_heures).
    date_limite_annulation: Optional[datetime] = None
    peut_annuler: bool = False


class ReservationStatutUpdate(BaseModel):
    statut: StatutReservation


# ---------- Contrat ----------
class ContratOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    reservation_id: Optional[uuid.UUID] = None
    bien_id: uuid.UUID
    proprietaire_id: uuid.UUID
    client_id: uuid.UUID
    date_signature: Optional[datetime] = None
    date_debut: date
    date_fin: Optional[date] = None
    montant_loyer: float
    fichier_url: Optional[str] = None
    statut: StatutContrat
    date_limite_paiement: Optional[datetime] = None
    date_limite_annulation: Optional[datetime] = None


# ---------- Paiement ----------
class PaiementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contrat_id: uuid.UUID
    montant: float
    methode: str
    reference_transaction: Optional[str] = None
    statut: StatutPaiement
    date_paiement: datetime


class PaiementCreate(BaseModel):
    contrat_id: uuid.UUID
    montant: float
    methode: str
    reference_transaction: Optional[str] = None


# ---------- Avis ----------
class AvisCreate(BaseModel):
    proprietaire_id: uuid.UUID
    bien_id: uuid.UUID
    note: int = Field(ge=1, le=5)
    commentaire: Optional[str] = None


class AvisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    client_id: uuid.UUID
    proprietaire_id: uuid.UUID
    bien_id: uuid.UUID
    note: int
    commentaire: Optional[str] = None
    date_creation: datetime
    # Champs enrichis (jointure faite côté routeur) — utiles pour l'affichage
    # côté propriétaire ("avis reçus") sans requête supplémentaire par avis.
    client_nom: Optional[str] = None
    client_prenom: Optional[str] = None
    bien_titre: Optional[str] = None


# ---------- Reclamation ----------
class ReclamationCreate(BaseModel):
    bien_id: Optional[uuid.UUID] = None
    contrat_id: Optional[uuid.UUID] = None
    type_reclamation: str
    description: str


class ReclamationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    utilisateur_id: uuid.UUID
    bien_id: Optional[uuid.UUID] = None
    contrat_id: Optional[uuid.UUID] = None
    type_reclamation: str
    description: str
    statut: StatutReclamation
    date_creation: datetime
    bien_titre: Optional[str] = None
    # Identité du client à l'origine de la réclamation (le "plaignant")
    client_nom: Optional[str] = None
    client_prenom: Optional[str] = None
    client_email: Optional[str] = None
    client_telephone: Optional[str] = None
    # Identité du propriétaire du bien concerné (déduite via bien.proprietaire_id)
    proprietaire_id: Optional[uuid.UUID] = None
    proprietaire_nom: Optional[str] = None
    proprietaire_prenom: Optional[str] = None
    proprietaire_email: Optional[str] = None
    proprietaire_telephone: Optional[str] = None
    # Nombre total de réclamations reçues par l'annonce concernée (toutes
    # réclamations confondues, tous statuts) — utilisé côté admin pour
    # repérer les annonces à risque. None si la réclamation n'est pas liée
    # à un bien.
    bien_reclamations_count: Optional[int] = None


class ReclamationStatutUpdate(BaseModel):
    statut: StatutReclamation


# ---------- Favoris (annonces enregistrées) ----------
class FavoriCreate(BaseModel):
    bien_id: uuid.UUID


class FavoriOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bien_id: uuid.UUID
    date_creation: datetime


# ---------- Historique de recherche ----------
class RechercheCreate(BaseModel):
    label: str
    criteres: dict


class RechercheOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    label: str
    criteres: dict
    date_recherche: datetime


# ---------- Messagerie ----------
class MessageCreate(BaseModel):
    contenu: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    conversation_id: uuid.UUID
    expediteur_id: uuid.UUID
    contenu: Optional[str] = None
    date_envoi: datetime
    lu: bool
    piece_jointe_url: Optional[str] = None
    piece_jointe_nom: Optional[str] = None
    piece_jointe_type: Optional[Literal["image", "pdf"]] = None


class ConversationCreate(BaseModel):
    """Créée par le client pour démarrer (ou récupérer) une conversation avec un propriétaire."""
    proprietaire_id: uuid.UUID
    bien_id: Optional[uuid.UUID] = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bien_id: Optional[uuid.UUID] = None
    bien_titre: Optional[str] = None
    client_id: uuid.UUID
    proprietaire_id: uuid.UUID
    # Nom/prénom de l'AUTRE interlocuteur, du point de vue de l'utilisateur connecté
    # (calculés côté back-end pour éviter à chaque écran client de refaire cette logique).
    autre_nom: str
    autre_prenom: str
    dernier_message: Optional[str] = None
    date_dernier_message: Optional[datetime] = None
    non_lus: int = 0


# ---------- Notification ----------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type_notification: str
    contenu: str
    lu: bool
    date_creation: datetime


# ---------- Actualité (publiées par un admin, affichées sur la landing page) ----------
class ActualiteCreate(BaseModel):
    titre: str = Field(min_length=1, max_length=200)
    contenu: str = Field(min_length=1)


class ActualiteUpdate(BaseModel):
    titre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contenu: Optional[str] = Field(default=None, min_length=1)
    publie: Optional[bool] = None


class ActualiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    auteur_id: uuid.UUID
    titre: str
    contenu: str
    image_url: Optional[str] = None
    publie: bool
    date_creation: datetime
    date_maj: datetime
    auteur_nom: Optional[str] = None
    auteur_prenom: Optional[str] = None
