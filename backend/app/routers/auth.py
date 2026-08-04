from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import ROLES_ANNONCEURS, get_current_user
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UtilisateurOut, status_code=status.HTTP_201_CREATED)
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
        # un client/admin est actif immédiatement.
        statut_verification=("en_attente" if payload.role in ROLES_ANNONCEURS else "verifie"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.Utilisateur).filter(models.Utilisateur.email == payload.email).first()
    if not user or not verify_password(payload.password, user.mot_de_passe_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

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

    for field, value in data.items():
        setattr(current_user, field, value)

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
