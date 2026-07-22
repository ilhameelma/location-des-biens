# SmartRent Backend — FastAPI

API REST du back-end SmartRent (étape 4 du cahier des charges), connectée au schéma
PostgreSQL produit en Phase 1 (`postgres/smartrent_schema.sql`).

## Installation

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Modifie `.env` si besoin (notamment `DATABASE_URL` si ton PostgreSQL Docker n'utilise pas
les identifiants par défaut du `docker-compose.yml` de la Phase 1).

## Lancer le serveur

```bash
uvicorn app.main:app --reload --port 8000
```

- API : http://localhost:8000/api
- Documentation interactive (Swagger) : http://localhost:8000/docs
- Vérification de santé : http://localhost:8000/api/health

⚠️ Le serveur PostgreSQL (`docker-compose up -d`, cf. README principal) doit être démarré
avant de lancer le back-end.

## Structure

```
backend/
├── app/
│   ├── main.py          # point d'entrée, assemble les routers, CORS
│   ├── config.py        # variables d'environnement (Pydantic Settings)
│   ├── database.py       # connexion SQLAlchemy / session
│   ├── models.py         # 11 entités ORM (utilisateur, bien, reservation...)
│   ├── schemas.py        # schémas Pydantic (entrée/sortie API)
│   ├── security.py       # hachage BCrypt + JWT
│   ├── deps.py            # dépendances FastAPI (utilisateur courant, rôles)
│   └── routers/
│       ├── auth.py            # /api/auth (register, login, me)
│       ├── utilisateurs.py    # /api/utilisateurs (admin)
│       ├── biens.py           # /api/biens (annonces, recherche)
│       ├── reservations.py    # /api/reservations
│       ├── contrats.py        # /api/contrats
│       ├── paiements.py       # /api/paiements
│       ├── avis.py            # /api/avis
│       ├── reclamations.py    # /api/reclamations
│       ├── messagerie.py      # /api/conversations
│       └── notifications.py   # /api/notifications
└── requirements.txt
```

## Endpoints principaux

| Méthode | Route | Rôle requis | Description |
|---|---|---|---|
| POST | `/api/auth/register` | public | Créer un compte |
| POST | `/api/auth/login` | public | Se connecter, obtenir un JWT |
| GET | `/api/auth/me` | connecté | Profil de l'utilisateur courant |
| GET | `/api/biens` | public | Recherche multicritères (ville, type_bien, prix_max) |
| POST | `/api/biens` | proprietaire | Publier une annonce (statut initial : en_attente) |
| GET | `/api/biens/me/annonces` | proprietaire | Mes annonces |
| PATCH | `/api/biens/{id}` | proprietaire/admin | Modifier / changer le statut d'un bien |
| POST | `/api/reservations` | client | Réserver un bien |
| GET | `/api/reservations/recues` | proprietaire | Demandes reçues |
| PATCH | `/api/reservations/{id}/statut` | proprietaire | Confirmer/refuser — génère automatiquement le contrat si `confirmee` |
| GET | `/api/contrats/me` | connecté | Mes contrats |
| PATCH | `/api/contrats/{id}/resilier` | connecté | Résilier un contrat (libère le bien) |
| GET | `/api/paiements/me` | connecté | Historique de paiements |
| POST | `/api/paiements` | client | Enregistrer un paiement sur un contrat |
| POST | `/api/avis` | client | Noter un propriétaire pour un bien |
| POST | `/api/reclamations` | connecté | Signaler un problème |
| GET | `/api/reclamations` | admin | Modération |
| GET/POST | `/api/conversations/{id}/messages` | connecté | Messagerie (REST) |
| GET | `/api/notifications/me` | connecté | Mes notifications |
| GET | `/api/utilisateurs` | admin | Liste des comptes |
| PATCH | `/api/utilisateurs/{id}/verifier` | admin | Vérifier un propriétaire |
| PATCH | `/api/utilisateurs/{id}/rejeter` | admin | Rejeter un compte |

## Connecter le front-end

Dans `frontend/.env`, pointe `VITE_API_URL` vers `http://localhost:8000/api`.

Le front consomme déjà ce contrat via `src/lib/api.ts` — il reste à remplacer, dans
`src/lib/auth.tsx`, la connexion « démo » par un vrai appel :

```ts
const { access_token, user } = await api.post("/auth/login", { email, password }, { auth: false });
login(user, access_token);
```

## Prochaines étapes (Phase 2)

- **Étape 7 — Stockage des images** : brancher MinIO pour l'upload des photos de biens
  et documents (actuellement `photo_bien.url` attend une URL déjà hébergée).
- **Étape 8 — Messagerie temps réel** : ajouter un endpoint WebSocket (`/ws/conversations/{id}`)
  qui diffuse les nouveaux messages aux deux interlocuteurs connectés, en parallèle des
  routes REST existantes.
- **Étape 9 — Notifications** : déclencher la création de `Notification` (et l'envoi SMTP /
  Firebase Cloud Messaging) à chaque événement métier (nouvelle demande, paiement reçu...).

## Notes

- Les mots de passe sont hachés avec BCrypt (jamais stockés en clair).
- Le token JWT est valable 24h par défaut (`JWT_EXPIRE_MINUTES`).
- Un compte `proprietaire` est créé avec `statut_verification="en_attente"` : il doit être
  validé par un admin via `PATCH /api/utilisateurs/{id}/verifier` avant de pouvoir publier
  (cohérent avec le rôle « Administrateur » décrit dans le cahier des charges). Un `client`
  ou `admin` est actif immédiatement (`verifie`).
- Un bien nouvellement publié a le statut `en_attente` ; il doit être passé à `disponible`
  (par le propriétaire ou un admin, via `PATCH /api/biens/{id}`) pour apparaître dans la
  recherche publique.
- Quand un propriétaire confirme une réservation (`PATCH /api/reservations/{id}/statut`
  avec `statut=confirmee`), le contrat correspondant est **généré automatiquement**
  (`montant_loyer` = prix du bien, dates reprises de la réservation) et le bien passe à
  `loue`.
- **Ce back-end est maintenant aligné exactement sur `postgres/smartrent_schema.sql`**
  (noms de colonnes et valeurs de statut identiques). Si ce script SQL évolue, il faut
  répercuter les changements dans `app/models.py` et `app/schemas.py`.
