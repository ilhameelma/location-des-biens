import uuid
from datetime import datetime, date

from sqlalchemy import String, Numeric, Boolean, ForeignKey, DateTime, Date, Text, Integer, SmallInteger, Double, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    # admin | client | proprietaire | agence | promoteur | conciergerie
    role: Mapped[str] = mapped_column(String(20))
    statut_verification: Mapped[str] = mapped_column(String(20), default="en_attente")  # en_attente|verifie|rejete
    # Vérification de l'email à l'inscription (indépendante de statut_verification
    # ci-dessus, qui est la vérification "métier" du profil par un admin).
    # email_verification_token stocke désormais un code OTP à 6 chiffres (et non
    # plus un jeton de lien) — nom de colonne conservé tel quel pour éviter une
    # migration SQL, seule la sémantique/génération a changé (voir security.py).
    email_verifie: Mapped[bool] = mapped_column(default=False)
    email_verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email_verification_expire: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Champs professionnels (NULL pour client/admin/proprietaire particulier)
    raison_sociale: Mapped[str | None] = mapped_column(String(150), nullable=True)
    numero_rc: Mapped[str | None] = mapped_column(String(50), nullable=True)
    numero_carte_pro: Mapped[str | None] = mapped_column(String(50), nullable=True)
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
    # Sépare les annonces à louer des annonces à vendre.
    type_transaction: Mapped[str] = mapped_column(String(10), default="location", index=True)  # location|vente
    adresse: Mapped[str] = mapped_column(String(255))
    ville: Mapped[str] = mapped_column(String(100), index=True)
    latitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    superficie: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    prix: Mapped[float] = mapped_column(Numeric(12, 2))
    nb_pieces: Mapped[int | None] = mapped_column(Integer, nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="disponible", index=True)
    # Promoteur uniquement : lot rattaché à un projet immobilier (voir ProjetImmobilier).
    # NULL pour les autres rôles annonceurs (proprietaire/agence/conciergerie).
    projet_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projet_immobilier.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Conciergerie (obligatoire) / agence (optionnel) : identité du propriétaire
    # réel pour le compte duquel l'annonce est publiée ("sous mandat").
    mandant_nom: Mapped[str | None] = mapped_column(String(150), nullable=True)
    mandant_telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_publication: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_maj: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Complément étape 17 — proximités (POI) calculées à la publication et
    # stockées avec l'annonce, pour éviter de resolliciter Overpass (lent,
    # ~1-5s) à chaque affichage de la fiche. `proximite_data` a exactement
    # la forme renvoyée par poi_client.get_proximite() / ProximiteOut.
    # NULL tant que le calcul en arrière-plan n'a pas encore abouti (juste
    # après publication) ou pour les biens créés avant cette fonctionnalité.
    proximite_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    proximite_calculee_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Équipements/commodités proposés par le bien (façon Airbnb — voir
    # frontend/src/lib/equipements.ts pour le catalogue de codes valides,
    # propre à chaque type_bien). Liste de codes texte, ex. ["wifi", "meuble"].
    equipements: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    proprietaire: Mapped["Utilisateur"] = relationship(back_populates="biens")
    photos: Mapped[list["PhotoBien"]] = relationship(back_populates="bien", cascade="all, delete-orphan")

    # Champs pratiques exposés dans BienOut (fiche bien, résultats de
    # recherche) pour afficher "Publié par X" sans requête supplémentaire
    # côté front-end — nécessitent que la relation `proprietaire` soit
    # chargée (voir joinedload(Bien.proprietaire) dans routers/biens.py).
    @property
    def proprietaire_nom(self) -> str | None:
        return self.proprietaire.nom if self.proprietaire else None

    @property
    def proprietaire_prenom(self) -> str | None:
        return self.proprietaire.prenom if self.proprietaire else None

    @property
    def proprietaire_role(self) -> str | None:
        return self.proprietaire.role if self.proprietaire else None

    @property
    def proprietaire_raison_sociale(self) -> str | None:
        return self.proprietaire.raison_sociale if self.proprietaire else None


class ProjetImmobilier(Base):
    """Projet immobilier neuf publié par un promoteur (rôle `promoteur`).

    Un projet regroupe plusieurs lots — les biens dont `bien.projet_id`
    pointe vers ce projet (ex. "Résidence Al Manar", 24 appartements)."""

    __tablename__ = "projet_immobilier"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    promoteur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    nom: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_bien: Mapped[str] = mapped_column(String(30))
    ville: Mapped[str] = mapped_column(String(100), index=True)
    adresse: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Double, nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="en_construction")  # en_construction|livre|termine
    date_livraison_prevue: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_maj: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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

    # Processus de paiement : une réservation confirmée génère un contrat
    # (voir routers/reservations.py) dont le paiement est suivi. Relation
    # 1-1 côté réservation, purement pratique pour exposer directement dans
    # ReservationOut (voir schemas.py) l'état du paiement sans que le
    # front-end n'ait à recouper deux appels API séparés.
    contrat: Mapped["Contrat | None"] = relationship(back_populates="reservation", uselist=False)

    @property
    def contrat_id(self) -> uuid.UUID | None:
        return self.contrat.id if self.contrat else None

    @property
    def date_limite_paiement(self) -> datetime | None:
        return self.contrat.date_limite_paiement if self.contrat else None

    @property
    def paiement_effectue(self) -> bool | None:
        """None si la réservation n'a pas (encore) de contrat associé
        (pas confirmée) ; sinon True/False selon qu'un paiement `reussi`
        existe déjà pour ce contrat."""
        if not self.contrat:
            return None
        return any(p.statut == "reussi" for p in self.contrat.paiements)

    @property
    def montant_a_payer(self) -> float | None:
        return float(self.contrat.montant_loyer) if self.contrat else None

    # ------------------------------------------------------------
    # Réservation instantanée avec paiement immédiat (carte/virement) —
    # complément à la logique "payer après confirmation" ci-dessus.
    # Quand la réservation est créée + payée en une seule fois (voir
    # POST /reservations/instantanee), le client dispose d'une fenêtre de
    # `settings.delai_annulation_heures` (24h par défaut) pour annuler et
    # être remboursé sans justification, comme sur Booking.
    # ------------------------------------------------------------
    @property
    def date_limite_annulation(self) -> datetime | None:
        return self.contrat.date_limite_annulation if self.contrat else None

    @property
    def peut_annuler(self) -> bool:
        """True si le client peut encore annuler gratuitement cette
        réservation (contrat actif, dans la fenêtre des 24h)."""
        if not self.contrat or self.contrat.statut != "actif":
            return False
        if self.statut != "confirmee":
            return False
        if not self.contrat.date_limite_annulation:
            return False
        return datetime.utcnow() < self.contrat.date_limite_annulation


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
    # Processus de paiement : fixée à la confirmation de la réservation
    # (date_creation + settings.delai_paiement_heures, 24h par défaut) —
    # voir routers/reservations.py. NULL pour les contrats créés avant
    # cette fonctionnalité, ou non issus d'une réservation (le cas
    # échéant) : jamais annulés automatiquement.
    date_limite_paiement: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Réservation instantanée (paiement carte/virement au moment de la
    # réservation, avant toute validation du propriétaire) : fenêtre
    # d'annulation gratuite avec remboursement, façon Booking. NULL pour
    # les contrats issus de l'ancien flux "payer après confirmation"
    # (date_limite_paiement) — les deux mécanismes sont mutuellement
    # exclusifs sur un même contrat.
    date_limite_annulation: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reservation: Mapped["Reservation | None"] = relationship(back_populates="contrat")
    paiements: Mapped[list["Paiement"]] = relationship(back_populates="contrat")


class Paiement(Base):
    __tablename__ = "paiement"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    contrat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contrat.id"))
    montant: Mapped[float] = mapped_column(Numeric(12, 2))
    methode: Mapped[str] = mapped_column(String(30))
    reference_transaction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="en_attente")  # en_attente|reussi|echoue|rembourse
    date_paiement: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contrat: Mapped["Contrat"] = relationship(back_populates="paiements")


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


class Favori(Base):
    """Annonces enregistrées ("mises de côté") par un client."""

    __tablename__ = "favori"
    __table_args__ = (
        UniqueConstraint("utilisateur_id", "bien_id", name="uq_favori_utilisateur_bien"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    utilisateur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    bien_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bien.id", ondelete="CASCADE"))
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RechercheHistorique(Base):
    """Historique des recherches effectuées par un client sur la page de
    recherche (critères + libellé lisible), pour lui permettre de relancer
    une recherche récente en un clic."""

    __tablename__ = "recherche_historique"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(255))
    criteres: Mapped[dict] = mapped_column(JSONB)
    date_recherche: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    # Optionnel désormais : un message peut être uniquement une pièce jointe
    # (photo/PDF), sans texte d'accompagnement.
    contenu: Mapped[str | None] = mapped_column(Text, nullable=True)
    lu: Mapped[bool] = mapped_column(Boolean, default=False)
    date_envoi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Pièce jointe (photo ou PDF) — stockée dans MinIO comme les photos de
    # biens (étape 7), sous la clé "messages/<conversation_id>/<uuid>.<ext>".
    piece_jointe_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    piece_jointe_nom: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "image" ou "pdf" — sert au front-end à décider comment afficher la pièce
    # jointe (aperçu image vs carte fichier avec lien "Ouvrir").
    piece_jointe_type: Mapped[str | None] = mapped_column(Text, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    utilisateur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    type_notification: Mapped[str] = mapped_column(String(50))
    contenu: Mapped[str] = mapped_column(Text)
    lu: Mapped[bool] = mapped_column(Boolean, default=False)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Actualite(Base):
    """Articles du blog ImmoVision — publiés par un admin (contenu éditorial
    officiel) ou par une agence (visibilité/crédibilité pour l'agence),
    affichés sur la page d'accueil publique (aperçu) et sur /blog (liste +
    fiche par slug).

    Anciennement "actualités" simple texte ; upgradé en vrai blog : slug
    (URL SEO), extrait (résumé/meta description), catégorie, contenu HTML
    riche (sanitizé côté serveur avant stockage, voir routers/actualites.py).
    """

    __tablename__ = "actualite"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    auteur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateur.id"))
    titre: Mapped[str] = mapped_column(String(200))
    # URL propre (ex. "nouvelle-fonctionnalite-recherche"), unique, générée
    # à la création à partir du titre — voir _slugify()/_unique_slug() dans
    # routers/actualites.py. Nullable pour compatibilité avec les lignes
    # créées avant cette évolution (rétro-remplies à la volée si NULL).
    slug: Mapped[str | None] = mapped_column(String(220), nullable=True)
    # Résumé court affiché sur les cartes/aperçus et utilisé comme meta
    # description SEO ; optionnel (dérivé du contenu si absent, côté front).
    extrait: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # actualite | marche_immobilier | conseils_locataires |
    # conseils_proprietaires | guide_juridique | vie_pratique
    categorie: Mapped[str] = mapped_column(String(50), default="actualite")
    # Contenu riche (éditeur type CMS côté front) — stocké en HTML déjà
    # sanitizé (nh3) avant écriture, jamais de HTML brut non filtré en base.
    contenu_html: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Permet de dépublier un article sans le supprimer (retiré de la landing
    # page/blog mais conservé côté gestion) — même logique que `statut` sur
    # `bien`.
    publie: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_maj: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
