from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db
from ..deps import ROLES_ANNONCEURS, get_current_user
from ..notifications_service import send_email
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_email_verification_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _envoyer_email_verification(user: models.Utilisateur) -> None:
    """Génère un nouveau token de vérification, l'enregistre sur l'utilisateur
    (à committer par l'appelant) et envoie l'email contenant le lien.
    L'envoi est best-effort (voir notifications_service.send_email) : un échec
    SMTP n'empêche pas l'inscription de se terminer, mais l'utilisateur ne
    pourra se connecter qu'après avoir demandé un renvoi (/auth/resend-verification)."""
    token = generate_email_verification_token()
    user.email_verification_token = token
    user.email_verification_expire = datetime.utcnow() + timedelta(
        hours=settings.email_verification_expire_heures
    )

    lien = f"{settings.frontend_url}/verify-email?token={token}"
    corps = (
        f"Bonjour {user.prenom},\n\n"
        "Merci de vous être inscrit(e) sur SmartRent. Pour activer votre compte, "
        f"veuillez confirmer votre adresse email en cliquant sur le lien suivant "
        f"(valable {settings.email_verification_expire_heures} heures) :\n\n"
        f"{lien}\n\n"
        "Si vous n'êtes pas à l'origine de cette inscription, ignorez simplement cet email.\n\n"
        "— L'équipe SmartRent"
    )
    send_email(user.email, "SmartRent — Confirmez votre adresse email", corps)


@router.post("/register", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.Utilisateur).filter(models.Utilisateur.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email")

    user = models.Utilisateur(
        nom=payload.nom,
        prenom=payload.prenom,
        email=payload.email,
        telephone=payload.telephone,
        mot_de_passe_hash=hash_password(payload.password),
        role=payload.role,
        raison_sociale=payload.raison_sociale,
        numero_rc=payload.numero_rc,
        numero_carte_pro=payload.numero_carte_pro,
        # Un propriétaire ou un professionnel (agence/promoteur/courtier) doit
        # être vérifié par un admin avant de publier (cf. cahier des charges) ;
        # un client/admin est actif immédiatement — ceci reste indépendant de
        # la vérification d'email ci-dessous, requise pour tous les rôles.
        statut_verification=("en_attente" if payload.role in ROLES_ANNONCEURS else "verifie"),
        email_verifie=False,
    )
    _envoyer_email_verification(user)

    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.RegisterResponse(
        message="Compte créé. Vérifiez votre boîte email pour confirmer votre adresse avant de vous connecter.",
        email=user.email,
    )


@router.get("/verify-email", response_model=schemas.UtilisateurOut)
def verify_email(token: str, db: Session = Depends(get_db)):
    user = (
        db.query(models.Utilisateur)
        .filter(models.Utilisateur.email_verification_token == token)
        .first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Lien de vérification invalide ou déjà utilisé")

    if user.email_verification_expire and user.email_verification_expire < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Ce lien de vérification a expiré. Demandez-en un nouveau.",
        )

    user.email_verifie = True
    # Le token est à usage unique : on l'efface une fois utilisé.
    user.email_verification_token = None
    user.email_verification_expire = None
    db.commit()
    db.refresh(user)
    return user


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
def resend_verification(payload: schemas.ResendVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(models.Utilisateur).filter(models.Utilisateur.email == payload.email).first()
    # Réponse identique que le compte existe ou non / soit déjà vérifié ou non,
    # pour ne pas laisser deviner quels emails sont inscrits sur la plateforme.
    if user and not user.email_verifie:
        _envoyer_email_verification(user)
        db.commit()
    return None


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Utilisateur).filter(models.Utilisateur.email == payload.email).first()
    if not user or not verify_password(payload.password, user.mot_de_passe_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    if not user.email_verifie:
        raise HTTPException(
            status_code=403,
            detail="Adresse email non confirmée. Vérifiez votre boîte de réception (ou vos spams) "
            "et cliquez sur le lien de confirmation avant de vous connecter.",
        )

    token = create_access_token(subject=str(user.id), role=user.role)
    return schemas.TokenResponse(access_token=token, role=user.role, user=user)


@router.get("/me", response_model=schemas.UtilisateurOut)
def me(current_user: models.Utilisateur = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UtilisateurOut)
def update_me(
    payload: schemas.UtilisateurUpdate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """Page « Mon compte » : le membre connecté modifie ses propres informations
    (nom, prénom, téléphone, email). Seuls les champs envoyés sont mis à jour."""
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"] != current_user.email:
        existing = (
            db.query(models.Utilisateur)
            .filter(models.Utilisateur.email == data["email"])
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé par un autre compte")

    email_a_change = "email" in data and data["email"] != current_user.email

    for field, value in data.items():
        setattr(current_user, field, value)

    if email_a_change:
        # La nouvelle adresse doit être reconfirmée avant de pouvoir resservir
        # à se connecter — même logique qu'à l'inscription.
        current_user.email_verifie = False
        _envoyer_email_verification(current_user)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/mot-de-passe", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.Utilisateur = Depends(get_current_user),
):
    """Page « Mon compte » : changement de mot de passe, exige l'ancien mot de passe."""
    if not verify_password(payload.mot_de_passe_actuel, current_user.mot_de_passe_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    current_user.mot_de_passe_hash = hash_password(payload.nouveau_mot_de_passe)
    db.commit()
    return None
