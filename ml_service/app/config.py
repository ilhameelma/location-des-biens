from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Dossier contenant les 3 artefacts .joblib (modele_estimation_loyer,
    # modele_fraude, recommender_artifacts). En local hors Docker : ./models
    # relatif au dossier d'exécution ; en Docker (Phase 5) : /app/models
    models_dir: str = "models"

    # Origine(s) autorisées à appeler ce service — en pratique uniquement le
    # back-end principal, jamais directement le front-end
    allowed_origin: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
