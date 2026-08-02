// Client API centralisé pour consommer le back-end FastAPI (étape 4 du cahier des charges).
// Le token JWT (étape 5 — Auth) est injecté automatiquement dans chaque requête.

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

const TOKEN_KEY = "smartrent_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

// Construit l'URL WebSocket correspondant à un chemin API donné, en réutilisant
// le même host/port que l'API REST (http -> ws, https -> wss).
// Le token JWT est transmis en query param : un navigateur ne peut pas ajouter
// de header Authorization à une connexion WebSocket.
export function wsUrl(path: string): string {
  const token = tokenStore.get();
  const httpUrl = new URL(`${API_BASE_URL}${path}`);
  httpUrl.protocol = httpUrl.protocol === "https:" ? "wss:" : "ws:";
  if (token) httpUrl.searchParams.set("token", token);
  return httpUrl.toString();
}

interface RequestOptions extends RequestInit {
  auth?: boolean; // ajoute le header Authorization si true (défaut: true)
}

// Met en forme le champ `detail` renvoyé par FastAPI, qui peut être :
// - une chaîne simple (HTTPException classique) → utilisée telle quelle
// - un tableau d'erreurs de validation Pydantic (422) → chaque élément a la
//   forme { loc: [...], msg: "...", type: "..." } → on les joint en texte lisible
// - autre chose d'inattendu → repli sur un message générique plutôt que
//   d'afficher "[object Object]" côté UI
export function formatErrorDetail(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const loc = Array.isArray((item as { loc?: unknown[] }).loc)
            ? (item as { loc: unknown[] }).loc.filter((l) => l !== "body").join(".")
            : null;
          const msg = String((item as { msg: unknown }).msg);
          return loc ? `${loc} : ${msg}` : msg;
        }
        return null;
      })
      .filter((m): m is string => Boolean(m));
    if (messages.length > 0) return messages.join(" — ");
  }
  return `Erreur API (${status})`;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const token = auth ? tokenStore.get() : null;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(formatErrorDetail(body.detail, res.status));
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  put: <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
    request<T>(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  patch: <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
    request<T>(path, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// --- Endpoints réels côté FastAPI (backend/app/routers) ---
// POST   /auth/register, /auth/login   -> TokenResponse / UtilisateurOut
// GET    /auth/me                       -> UtilisateurOut
// GET    /biens?ville=&type_bien=&prix_max=  -> BienOut[]
// POST   /biens                          -> BienOut (proprietaire)
// GET    /biens/me/annonces              -> BienOut[] (proprietaire)
// PATCH  /biens/{id}                     -> BienOut
// POST   /reservations                   -> ReservationOut (client)
// GET    /reservations/me | /recues      -> ReservationOut[]
// PATCH  /reservations/{id}/statut       -> ReservationOut
// GET    /contrats/me                    -> ContratOut[]
// GET    /paiements/me                   -> PaiementOut[]
// POST   /paiements                      -> PaiementOut (client)
// POST   /avis                           -> AvisOut (client)
// POST   /reclamations, GET /reclamations (admin)
// GET/POST /conversations                -> ConversationOut[] / ConversationOut (POST: client)
// GET/POST /conversations/{id}/messages   -> MessageOut[] / MessageOut
// WS       /conversations/ws/{id}?token=  -> canal temps réel (étape 8)
// GET    /notifications/me               -> NotificationOut[]
