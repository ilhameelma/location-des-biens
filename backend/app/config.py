from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de données — pointe vers le service "postgres" du docker-compose.yml (Phase 1)
    database_url: str = "postgresql://smartrent:smartrent_pwd@localhost:5432/smartrent_db"

    # JWT (étape 5 — Authentification et sécurité)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h
    # JWT (étape 5 — Authentification et sécurité)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h

    # Cookie httpOnly portant le token JWT (remplace le localStorage côté
    # frontend — inaccessible en JavaScript, donc protégé contre le vol par
    # XSS). cookie_secure doit être True dès que le site est servi en HTTPS
    # (VM avec Let's Encrypt) et peut rester False en HTTP local (mkcert ou
    # localhost simple) — un cookie "Secure" est refusé par le navigateur
    # sur une connexion non chiffrée.
    auth_cookie_name: str = "smartrent_token"
    cookie_secure: bool = False  # -> True en prod HTTPS (backend/.env)
    cookie_samesite: str = "lax"  # "lax" suffit en same-origin (via Nginx)
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

    # ============================================================
    # Vérification d'email à l'inscription (code OTP à 6 chiffres)
    # ============================================================
    # Durée de validité du code envoyé par email — volontairement courte
    # (contrairement à l'ancien lien à 24h) car un code à 6 chiffres est
    # plus simple à intercepter/deviner par force brute s'il traîne longtemps.
    email_verification_code_expire_minutes: int = 15
    # Conservé pour un usage futur éventuel (ex. lien "mot de passe oublié") ;
    # n'est plus utilisé pour la vérification d'email désormais basée sur un
    # code saisi directement dans l'application plutôt qu'un lien cliqué.
    frontend_url: str = "http://localhost:5173"

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

    # ============================================================
    # Étape 18 — Recherche avancée (Elasticsearch)
    # ============================================================
    # elasticsearch_url : utilisé par le back-end (hors Docker en local)
    # pour PARLER au service Elasticsearch du docker-compose.yml.
    #   - en local (back-end hors Docker) : "http://localhost:9200"
    #   - une fois le back-end conteneurisé (Phase 5) : "http://elasticsearch:9200"
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "smartrent_biens"

    # ============================================================
    # Complément étape 17 — Points d'intérêt à proximité (Overpass/OSM)
    # ============================================================
    # Instances publiques Overpass, gratuites et sans clé — même écosystème
    # OpenStreetMap que Leaflet (carte) et Nominatim (LocationPicker),
    # déjà utilisés à l'étape 17.
    #
    # Plusieurs miroirs sont essayés dans l'ordre : l'instance historique
    # overpass-api.de renvoie régulièrement des erreurs 406 Not Acceptable
    # depuis qu'elle filtre le trafic jugé "automatisé" (mesure anti-scraping
    # côté serveur, problème documenté côté communauté OSM — rien à corriger
    # côté requête). overpass.kumi.systems est utilisé en premier car il
    # règle la grande majorité de ces cas ; overpass-api.de et
    # overpass.private.coffee restent en repli.
    overpass_urls: list[str] = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]
    overpass_timeout_seconds: float = 15.0
    poi_rayon_km_defaut: float = 1.5
    # Durée de validité des proximités stockées avec l'annonce (bien.proximite_data)
    # avant recalcul — les commerces/écoles/hôtels autour d'une adresse ne
    # changent pas d'un jour à l'autre, une fenêtre large évite de resolliciter
    # Overpass inutilement.
    proximite_ttl_jours: int = 30

    # ============================================================
    # Filigrane sur les photos de biens (protection contre la réutilisation
    # des photos sur d'autres plateformes, comme le fait Avito)
    # ============================================================
    watermark_enabled: bool = True
    watermark_text: str = "ImmoVision.ma"

    # ============================================================
    # Processus de paiement après confirmation d'une réservation
    # ============================================================
    # Délai laissé au client pour payer une fois sa réservation confirmée
    # (contrat généré automatiquement, voir routers/reservations.py) avant
    # annulation automatique de la réservation — voir app/paiement_expiration.py.
    delai_paiement_heures: int = 24
    # Intervalle entre deux passages de la vérification des paiements en
    # attente (tâche d'arrière-plan lancée au démarrage, voir app/main.py).
    verification_paiements_intervalle_secondes: int = 15 * 60  # 15 min

    # ============================================================
    # Réservation instantanée avec paiement immédiat (carte/virement)
    # ============================================================
    # Fenêtre pendant laquelle le client peut annuler gratuitement une
    # réservation payée au moment de la réservation (avant validation du
    # propriétaire), avec remboursement automatique — comme Booking.
    # Voir POST /reservations/instantanee et POST /reservations/{id}/annuler
    # dans routers/reservations.py.
    delai_annulation_heures: int = 24

    # ============================================================
    # Formulaire de contact public (landing page)
    # ============================================================
    # Adresse qui reçoit les messages envoyés depuis le formulaire "Contact"
    # de la landing page (POST /api/contact) — réutilise la config SMTP
    # ci-dessus pour l'envoi réel.
    contact_email: str = "immovision260@gmail.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
