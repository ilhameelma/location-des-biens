import uuid
from datetime import datetime, date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field

Role = Literal["admin", "proprietaire", "client"]
StatutVerification = Literal["en_attente", "verifie", "rejete"]
TypeBien = Literal["maison", "appartement", "magasin", "garage", "bureau", "terrain"]
StatutBien = Literal["disponible", "loue", "en_attente", "suspendu"]
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
    adresse: str
    ville: str
    superficie: Optional[float] = None
    prix: float
    nb_pieces: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class BienUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    prix: Optional[float] = None
    statut: Optional[StatutBien] = None


class BienOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    proprietaire_id: uuid.UUID
    titre: str
    description: Optional[str] = None
    type_bien: TypeBien
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


class ReclamationStatutUpdate(BaseModel):
    statut: StatutReclamation


# ---------- Messagerie ----------
class MessageCreate(BaseModel):
    contenu: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    conversation_id: uuid.UUID
    expediteur_id: uuid.UUID
    contenu: str
    date_envoi: datetime
    lu: bool


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    bien_id: Optional[uuid.UUID] = None
    client_id: uuid.UUID
    proprietaire_id: uuid.UUID


# ---------- Notification ----------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type_notification: str
    contenu: str
    lu: bool
    date_creation: datetime
