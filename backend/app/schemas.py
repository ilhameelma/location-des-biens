import uuid
from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field

Role = Literal["admin", "proprietaire", "client"]
StatutVerification = Literal["en_attente", "verifie", "rejete"]
TypeBien = Literal["maison", "appartement", "magasin", "garage", "bureau", "terrain", "villa"]
TypeTransaction = Literal["location", "vente"]
StatutBien = Literal["disponible", "loue", "vendu", "en_attente", "suspendu"]
StatutReservation = Literal["en_attente", "confirmee", "refusee", "annulee"]
StatutContrat = Literal["actif", "termine", "resilie"]
StatutPaiement = Literal["en_attente", "reussi", "echoue", "rembourse"]
StatutReclamation = Literal["ouverte", "en_cours", "resolue", "rejetee"]


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
    date_creation: datetime


class UtilisateurUpdate(BaseModel):
    """Page « Mon compte » : mise à jour du profil (tous les champs optionnels,
    seuls ceux envoyés par le front-end sont modifiés)."""
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(default=None, max_length=20)


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
    photos: list[PhotoBienOut] = []


# ---------- Reservation ----------
class ReservationCreate(BaseModel):
    bien_id: uuid.UUID
    date_debut: date
    date_fin: Optional[date] = None


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bien_id: uuid.UUID
    client_id: uuid.UUID
    date_debut: date
    date_fin: Optional[date] = None
    statut: StatutReservation


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
