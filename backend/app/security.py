import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from .config import settings
import hashlib
import secrets
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_otp_code() -> str:
    """Code de vérification à 6 chiffres, généré de façon cryptographiquement
    sûre (secrets.randbelow), pour la confirmation d'email par OTP saisi par
    l'utilisateur — à usage unique et à courte durée de vie (voir routers/auth.py).
    zfill(6) conserve les zéros en tête (ex. "004821")."""
    return str(secrets.randbelow(1_000_000)).zfill(6)

# security.py — ajouter


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

def verify_otp(code: str, hashed: str) -> bool:
    return secrets.compare_digest(hash_otp(code), hashed)
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
