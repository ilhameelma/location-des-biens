"""
Étape 7 — Stockage des images (MinIO)

Centralise l'accès à MinIO pour l'upload/suppression des photos de biens.
Le bucket est créé automatiquement au démarrage (s'il n'existe pas déjà)
et une politique de lecture publique lui est appliquée, afin que les URLs
des photos soient directement affichables côté front-end (comme le serait
une URL S3/Cloudinary publique), sans passer par le back-end.
"""
import json
import logging

from minio import Minio
from minio.error import S3Error

from .config import settings

logger = logging.getLogger(__name__)

# ============================================================
# Client MinIO
# ============================================================
# minio_endpoint est de la forme "host:port" (ex: "localhost:9000"),
# sans schéma http(s) — c'est ce qu'attend le SDK MinIO.
_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def _public_read_policy(bucket: str) -> str:
    """Politique IAM autorisant la lecture publique (GetObject) sur le bucket."""
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
    )


def ensure_bucket() -> None:
    """
    Crée le bucket MinIO s'il n'existe pas et applique une politique de
    lecture publique. À appeler au démarrage de l'application (main.py).
    """
    try:
        if not _client.bucket_exists(settings.minio_bucket):
            _client.make_bucket(settings.minio_bucket)
            logger.info("Bucket MinIO '%s' créé.", settings.minio_bucket)

        _client.set_bucket_policy(
            settings.minio_bucket, _public_read_policy(settings.minio_bucket)
        )
    except S3Error as exc:
        # On ne bloque pas le démarrage de l'API si MinIO n'est pas encore
        # disponible (ex: conteneur en cours de démarrage) ; l'upload
        # échouera avec une erreur explicite le cas échéant.
        logger.warning("Impossible d'initialiser le bucket MinIO : %s", exc)


def upload_photo(object_name: str, content: bytes, content_type: str | None) -> str:
    """
    Upload un fichier binaire vers MinIO et retourne son URL publique.

    object_name : chemin/clé de l'objet dans le bucket (ex: "biens/<uuid>/xxx.jpg")
    """
    from io import BytesIO

    _client.put_object(
        settings.minio_bucket,
        object_name,
        data=BytesIO(content),
        length=len(content),
        content_type=content_type or "application/octet-stream",
    )
    return build_public_url(object_name)


def delete_photo(object_name: str) -> None:
    """Supprime un objet du bucket MinIO (ne lève pas d'erreur si absent)."""
    try:
        _client.remove_object(settings.minio_bucket, object_name)
    except S3Error as exc:
        logger.warning("Suppression MinIO échouée pour '%s' : %s", object_name, exc)


def build_public_url(object_name: str) -> str:
    """Construit l'URL publique d'un objet du bucket."""
    scheme = "https" if settings.minio_secure else "http"
    return f"{scheme}://{settings.minio_public_endpoint}/{settings.minio_bucket}/{object_name}"


def object_name_from_url(url: str) -> str | None:
    """
    Retrouve le nom d'objet MinIO ("biens/<uuid>/xxx.jpg") à partir d'une
    URL publique stockée en base. Retourne None si l'URL ne correspond pas
    au pattern attendu (ex: anciennes photos stockées localement).
    """
    marker = f"/{settings.minio_bucket}/"
    if marker not in url:
        return None
    return url.split(marker, 1)[1]
