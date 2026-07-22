// Client API centralisé pour consommer le back-end FastAPI (étape 4 du cahier des charges).
// Le token JWT (étape 5 — Auth) est injecté automatiquement dans chaque requête.

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

const TOKEN_KEY = "smartrent_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

interface RequestOptions extends RequestInit {
  auth?: boolean; // ajoute le header Authorization si true (défaut: true)
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
    throw new Error(body.detail ?? `Erreur API (${res.status})`);
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
// GET/POST /conversations/{id}/messages
// GET    /notifications/me               -> NotificationOut[]
