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

    # MinIO (étape 7 — Stockage des images)
    # minio_endpoint : utilisé par le back-end pour PARLER à MinIO.
    #   - en local (back-end hors Docker) : "localhost:9000"
    #   - une fois le back-end conteneurisé (Phase 5) : "minio:9000" (nom du service Docker)
    # minio_public_endpoint : utilisé pour CONSTRUIRE les URLs publiques des
    #   photos, chargées directement par le navigateur du client -> doit donc
    #   toujours pointer vers une adresse accessible depuis le poste utilisateur.
    minio_endpoint: str = "localhost:9000"
    minio_public_endpoint: str = "localhost:9000"
    minio_secure: bool = False
    minio_access_key: str = "smartrent_admin"
    minio_secret_key: str = "smartrent_minio_pwd"
    minio_bucket: str = "smartrent-photos"

    # ============================================================
    # Étape 9 — Notifications
    # ============================================================
    # SMTP : envoi d'emails réels. Si smtp_host est vide, l'envoi d'email
    # est silencieusement désactivé (log un avertissement) — la notification
    # in-app + temps réel fonctionne quand même, seul l'email est sauté.
    # Exemple avec un compte Gmail : smtp_host=smtp.gmail.com, smtp_port=587,
    # smtp_user=<adresse>, smtp_password=<mot de passe d'application>.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "SmartRent <no-reply@smartrent.local>"
    smtp_use_tls: bool = True

    # Firebase Cloud Messaging (push mobile/navigateur) : nécessite un flux
    # d'enregistrement de token d'appareil côté client (app mobile ou
    # service worker web) qui n'existe pas encore dans ce projet.
    # Comme pour Kubernetes (étape 21), présenté comme perspective d'évolution :
    # le point d'intégration (fcm_server_key) est prêt, l'envoi réel est un stub.
    fcm_server_key: str = ""

    # ============================================================
    # Étape 10 — Collecte des données (Kafka)
    # ============================================================
    # kafka_bootstrap_servers : utilisé par le back-end (hors Docker en local)
    # pour PARLER au broker Kafka du docker-compose.yml (Phase 1).
    #   - en local (back-end hors Docker) : "localhost:9092"
    #   - une fois le back-end conteneurisé (Phase 5) : "kafka:9092"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "smartrent-backend"

    # ============================================================
    # Phase 4 — Intelligence artificielle (étape 16)
    # ============================================================
    # ml_service_url : URL du micro-service FastAPI exposant les 3 modèles
    # (estimation, recommandation, fraude).
    #   - en local (les deux hors Docker) : "http://localhost:8001"
    #   - une fois conteneurisés (Phase 5) : "http://ml_service:8001"
    ml_service_url: str = "http://localhost:8001"
    ml_service_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
