import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.Utilisateur:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou expirés",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = db.get(models.Utilisateur, uuid.UUID(user_id))
    if user is None:
        raise credentials_error
    return user


def require_role(*roles: str):
    """Dépendance factory : restreint un endpoint à un ou plusieurs rôles (admin/proprietaire/client)."""

    def checker(user: models.Utilisateur = Depends(get_current_user)) -> models.Utilisateur:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce rôle",
            )
        return user

    return checker
