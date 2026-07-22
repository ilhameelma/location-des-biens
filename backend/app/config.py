from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de données — pointe vers le service "postgres" du docker-compose.yml (Phase 1)
    database_url: str = "postgresql://smartrent:smartrent_pwd@localhost:5432/smartrent_db"

    # JWT (étape 5 — Authentification et sécurité)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h

    # CORS — origine du front-end React (Vite)
    frontend_origin: str = "http://localhost:5173"

    # MinIO (étape 7 — Stockage des images), branché plus tard
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "smartrent_admin"
    minio_secret_key: str = "smartrent_minio_pwd"
    minio_bucket: str = "smartrent-photos"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
