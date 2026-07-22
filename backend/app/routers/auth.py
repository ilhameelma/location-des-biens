from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
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
        # Un propriétaire doit être vérifié par un admin avant de publier (cf. cahier des charges) ;
        # un client/admin est actif immédiatement.
        statut_verification=("en_attente" if payload.role == "proprietaire" else "verifie"),
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
