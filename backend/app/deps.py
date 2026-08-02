import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# auto_error=False : ne lève jamais d'exception si l'en-tête Authorization est
# absent — utilisé par les endpoints réellement publics (ex. GET /biens) qui
# doivent rester accessibles à un visiteur non connecté (landing page...),
# tout en restant capables d'identifier l'utilisateur s'il est bien connecté.
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


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


def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)
) -> models.Utilisateur | None:
    """
    Variante de get_current_user pour les endpoints publics : renvoie
    l'utilisateur connecté s'il y a un token valide, sinon None — sans jamais
    lever d'erreur 401. Un token invalide/expiré est traité comme "pas de
    token" plutôt que comme une erreur, pour ne pas casser un endpoint public
    à cause d'un vieux token périmé traînant côté client.
    """
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
    """Dépendance factory : restreint un endpoint à un ou plusieurs rôles (admin/proprietaire/client)."""

    def checker(user: models.Utilisateur = Depends(get_current_user)) -> models.Utilisateur:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce rôle",
            )
        return user

    return checker
