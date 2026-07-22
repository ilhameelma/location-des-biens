import uuid
from datetime import datetime, date

from sqlalchemy import String, Numeric, Boolean, ForeignKey, DateTime, Date, Text, Integer, SmallInteger, Double
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255))
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20))  # admin | proprietaire | client
    statut_verification: Mapped[str] = mapped_column(String(20), default="en_attente")  # en_attente|verifie|rejete
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_maj: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    biens: Mapped[list["Bien"]] = relationship(back_populates="proprietaire")


class Bien(Base):
    __tablename__ = "bien"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    proprietaire_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    titre: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_bien: Mapped[str] = mapped_column(String(30))  # maison|appartement|magasin|garage|bureau|terrain
    adresse: Mapped[str] = mapped_column(String(255))
    ville: Mapped[str] = mapped_column(String(100), index=True)
    latitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    superficie: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    prix: Mapped[float] = mapped_column(Numeric(12, 2))
    nb_pieces: Mapped[int | None] = mapped_column(Integer, nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="disponible", index=True)
    date_publication: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_maj: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    proprietaire: Mapped["Utilisateur"] = relationship(back_populates="biens")
    photos: Mapped[list["PhotoBien"]] = relationship(back_populates="bien", cascade="all, delete-orphan")


class PhotoBien(Base):
    __tablename__ = "photo_bien"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    bien_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bien.id"))
    url: Mapped[str] = mapped_column(String(500))
    ordre: Mapped[int] = mapped_column(Integer, default=0)

    bien: Mapped["Bien"] = relationship(back_populates="photos")


class Reservation(Base):
    __tablename__ = "reservation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    bien_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bien.id"))
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    date_debut: Mapped[date] = mapped_column(Date)
    date_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="en_attente")  # en_attente|confirmee|refusee|annulee
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Contrat(Base):
    __tablename__ = "contrat"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    reservation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reservation.id"), unique=True, nullable=True
    )
    bien_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bien.id"))
    proprietaire_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    date_signature: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_debut: Mapped[date] = mapped_column(Date)
    date_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    montant_loyer: Mapped[float] = mapped_column(Numeric(12, 2))
    fichier_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="actif")  # actif|termine|resilie
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Paiement(Base):
    __tablename__ = "paiement"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    contrat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contrat.id"))
    montant: Mapped[float] = mapped_column(Numeric(12, 2))
    methode: Mapped[str] = mapped_column(String(30))
    reference_transaction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="en_attente")  # en_attente|reussi|echoue|rembourse
    date_paiement: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Avis(Base):
    __tablename__ = "avis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    proprietaire_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    bien_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bien.id"))
    note: Mapped[int] = mapped_column(SmallInteger)  # 1-5
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Reclamation(Base):
    __tablename__ = "reclamation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    utilisateur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    bien_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bien.id"), nullable=True)
    contrat_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("contrat.id"), nullable=True)
    type_reclamation: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    statut: Mapped[str] = mapped_column(String(20), default="ouverte")  # ouverte|en_cours|resolue|rejetee
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    bien_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("bien.id"), nullable=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    proprietaire_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversation.id"))
    expediteur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    contenu: Mapped[str] = mapped_column(Text)
    lu: Mapped[bool] = mapped_column(Boolean, default=False)
    date_envoi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    utilisateur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    type_notification: Mapped[str] = mapped_column(String(50))
    contenu: Mapped[str] = mapped_column(Text)
    lu: Mapped[bool] = mapped_column(Boolean, default=False)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
