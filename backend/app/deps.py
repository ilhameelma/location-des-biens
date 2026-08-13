import uuid

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .database import get_db
from .security import decode_access_token

ROLES_ANNONCEURS = ("proprietaire", "agence", "promoteur", "conciergerie")

# Conservé pour Swagger /docs (bouton "Authorize") et les tests Postman
# (étape 19) qui envoient un header Authorization classique — mais en usage
# normal depuis le frontend, c'est le cookie httpOnly qui fait foi (voir
# _resolve_token ci-dessous), jamais accessible en JavaScript côté navigateur.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def _resolve_token(
    header_token: str | None,
    cookie_token: str | None,
) -> str | None:
    """Priorité au cookie httpOnly (flux navigateur normal) ; le header
    Authorization reste utilisable en repli (Swagger, Postman, scripts)."""
    return cookie_token or header_token


def get_current_user(
    header_token: str | None = Depends(oauth2_scheme),
    cookie_token: str | None = Cookie(default=None, alias="smartrent_token"),
    db: Session = Depends(get_db),
) -> models.Utilisateur:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou expirés",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = _resolve_token(header_token, cookie_token)
    if token is None:
        raise credentials_error

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


def get_optional_user(
    header_token: str | None = Depends(oauth2_scheme_optional),
    cookie_token: str | None = Cookie(default=None, alias="smartrent_token"),
    db: Session = Depends(get_db),
) -> models.Utilisateur | None:
    token = _resolve_token(header_token, cookie_token)
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return db.get(models.Utilisateur, uuid.UUID(user_id))


def require_role(*roles: str):
    def checker(user: models.Utilisateur = Depends(get_current_user)) -> models.Utilisateur:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce rôle",
            )
        return user

    return checker