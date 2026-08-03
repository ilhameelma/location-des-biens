import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_role
from ..notifications_service import notify

router = APIRouter(prefix="/reclamations", tags=["reclamations"])

# Au-delà de ce nombre de réclamations reçues (toutes confondues) sur une
# même annonce, les admins reçoivent une alerte dédiée les invitant à
# vérifier l'annonce et, le cas échéant, à la supprimer.
SEUIL_RECLAMATIONS_ANNONCE = 20

# Libellés lisibles pour le contenu des notifications — mêmes valeurs que
# TYPE_OPTIONS côté front-end (frontend/src/pages/client/ReclamationsPage.tsx).
TYPE_LABELS = {
    "annonce_trompeuse": "Annonce trompeuse",
    "prix_incorrect": "Prix incorrect / non respecté",
    "bien_indisponible": "Bien déjà indisponible",
    "comportement_proprietaire": "Comportement du propriétaire",
    "autre": "Autre",
}


def _enrich(db: Session, reclamations: list[models.Reclamation]) -> list[schemas.ReclamationOut]:
    """Complète chaque réclamation avec :
    - le bien concerné (titre exact de l'annonce, si renseigné) ;
    - l'identité du client à l'origine de la réclamation (le plaignant) ;
    - l'identité du propriétaire du bien visé (déduite de bien.proprietaire_id).
    Tout est résolu via des requêtes groupées (pas de N+1) — utilisé à la fois
    par « Mes réclamations » (client) et par la modération admin.
    """
    if not reclamations:
        return []

    bien_ids = {r.bien_id for r in reclamations if r.bien_id is not None}
    biens = (
        {b.id: b for b in db.query(models.Bien).filter(models.Bien.id.in_(bien_ids))}
        if bien_ids
        else {}
    )

    # Utilisateurs à résoudre : les plaignants (utilisateur_id) + les
    # propriétaires des biens concernés (bien.proprietaire_id).
    user_ids = {r.utilisateur_id for r in reclamations}
    user_ids |= {b.proprietaire_id for b in biens.values()}
    utilisateurs = (
        {u.id: u for u in db.query(models.Utilisateur).filter(models.Utilisateur.id.in_(user_ids))}
        if user_ids
        else {}
    )

    # Nombre total de réclamations par annonce — calculé en une seule requête
    # groupée (pas de N+1), utilisé côté admin pour repérer les annonces à
    # risque (cf. SEUIL_RECLAMATIONS_ANNONCE).
    counts_par_bien: dict[uuid.UUID, int] = {}
    if bien_ids:
        rows = (
            db.query(models.Reclamation.bien_id, func.count(models.Reclamation.id))
            .filter(models.Reclamation.bien_id.in_(bien_ids))
            .group_by(models.Reclamation.bien_id)
            .all()
        )
        counts_par_bien = {bien_id: count for bien_id, count in rows}

    result = []
    for r in reclamations:
        bien = biens.get(r.bien_id) if r.bien_id else None
        client = utilisateurs.get(r.utilisateur_id)
        proprietaire = utilisateurs.get(bien.proprietaire_id) if bien else None
        result.append(
            schemas.ReclamationOut(
                id=r.id,
                utilisateur_id=r.utilisateur_id,
                bien_id=r.bien_id,
                contrat_id=r.contrat_id,
                type_reclamation=r.type_reclamation,
                description=r.description,
                statut=r.statut,
                date_creation=r.date_creation,
                bien_titre=bien.titre if bien else None,
                client_nom=client.nom if client else None,
                client_prenom=client.prenom if client else None,
                client_email=client.email if client else None,
                client_telephone=client.telephone if client else None,
                proprietaire_id=proprietaire.id if proprietaire else None,
                proprietaire_nom=proprietaire.nom if proprietaire else None,
                proprietaire_prenom=proprietaire.prenom if proprietaire else None,
                proprietaire_email=proprietaire.email if proprietaire else None,
                proprietaire_telephone=proprietaire.telephone if proprietaire else None,
                bien_reclamations_count=counts_par_bien.get(r.bien_id) if r.bien_id else None,
            )
        )
    return result


@router.post("", response_model=schemas.ReclamationOut, status_code=201)
def create_reclamation(
    payload: schemas.ReclamationCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    reclamation = models.Reclamation(**payload.model_dump(), utilisateur_id=current_user.id)
    db.add(reclamation)
    db.commit()
    db.refresh(reclamation)

    enriched = _enrich(db, [reclamation])[0]

    # Notification automatique de tous les administrateurs (in-app temps réel
    # + email best-effort si l'admin est hors ligne — même mécanisme que pour
    # les réservations/paiements, voir notifications_service.notify()).
    contenu = (
        f"Nouvelle réclamation de {current_user.prenom} {current_user.nom} "
        f"({TYPE_LABELS.get(reclamation.type_reclamation, reclamation.type_reclamation)})"
    )
    if enriched.bien_titre:
        contenu += f" concernant « {enriched.bien_titre} »"
    contenu += "."

    admins = db.query(models.Utilisateur).filter(models.Utilisateur.role == "admin").all()
    for admin in admins:
        notify(
            db,
            admin.id,
            "reclamation",
            contenu,
            email_subject="SmartRent — Nouvelle réclamation à traiter",
        )

    # Avertissement au propriétaire visé par la réclamation : notification
    # in-app (badge "warning", voir NotificationBell.tsx) + email envoyé
    # systématiquement (force_email=True), qu'il soit connecté ou non — un
    # signalement client doit toujours laisser une trace dans sa boîte mail,
    # pas seulement un badge qu'il pourrait manquer.
    if enriched.proprietaire_id:
        type_label = TYPE_LABELS.get(reclamation.type_reclamation, reclamation.type_reclamation)
        avertissement = (
            f"⚠️ Un client a déposé une réclamation vous concernant "
            f"({type_label})"
        )
        if enriched.bien_titre:
            avertissement += f" au sujet de l'annonce « {enriched.bien_titre} »"
        avertissement += (
            f" : « {reclamation.description} ». "
            "Notre équipe va l'examiner ; vous serez tenu informé de son traitement."
        )
        notify(
            db,
            enriched.proprietaire_id,
            "avertissement",
            avertissement,
            email_subject="SmartRent — Réclamation d'un client vous concernant",
            force_email=True,
        )

    # Alerte dédiée aux admins si cette annonce vient de dépasser le seuil de
    # réclamations (déclenchée une seule fois, au moment précis où le seuil
    # est franchi, pour ne pas spammer les admins à chaque réclamation
    # suivante sur la même annonce).
    if enriched.bien_reclamations_count == SEUIL_RECLAMATIONS_ANNONCE + 1:
        alerte = (
            f"🚨 L'annonce « {enriched.bien_titre or 'sans titre'} » a dépassé "
            f"{SEUIL_RECLAMATIONS_ANNONCE} réclamations ({enriched.bien_reclamations_count} au total). "
            "Une vérification manuelle est recommandée — envisagez de suspendre ou de supprimer cette annonce."
        )
        for admin in admins:
            notify(
                db,
                admin.id,
                "alerte_annonce",
                alerte,
                email_subject="SmartRent — Annonce à risque : seuil de réclamations dépassé",
                force_email=True,
            )

    return enriched


@router.get("/me", response_model=list[schemas.ReclamationOut])
def my_reclamations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """Page « Mes réclamations » (client, mais accessible à tout utilisateur
    connecté) : les réclamations que j'ai déposées, les plus récentes d'abord."""
    reclamations = (
        db.query(models.Reclamation)
        .filter(models.Reclamation.utilisateur_id == current_user.id)
        .order_by(models.Reclamation.date_creation.desc())
        .all()
    )
    return _enrich(db, reclamations)


@router.get("", response_model=list[schemas.ReclamationOut])
def list_reclamations(
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    reclamations = db.query(models.Reclamation).order_by(models.Reclamation.date_creation.desc()).all()
    return _enrich(db, reclamations)


@router.patch("/{reclamation_id}/statut", response_model=schemas.ReclamationOut)
def update_statut(
    reclamation_id: uuid.UUID,
    payload: schemas.ReclamationStatutUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(require_role("admin")),
):
    reclamation = db.get(models.Reclamation, reclamation_id)
    if not reclamation:
        raise HTTPException(status_code=404, detail="Réclamation introuvable")
    reclamation.statut = payload.statut
    db.commit()
    db.refresh(reclamation)
    return _enrich(db, [reclamation])[0]
