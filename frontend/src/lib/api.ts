// Client API centralisé pour consommer le back-end FastAPI (étape 4 du cahier des charges).
// L'authentification passe désormais par un cookie httpOnly (posé par
// /auth/login) transmis automatiquement par le navigateur à chaque requête
// (credentials: "include") — plus de token manipulé en JavaScript, donc plus
// de risque de vol par XSS via localStorage.

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

// Construit l'URL WebSocket correspondant à un chemin API donné, en réutilisant
// le même host/port que l'API REST (http -> ws, https -> wss). Le cookie
// httpOnly est envoyé automatiquement par le navigateur au handshake
// WebSocket (même origine, via Nginx) — aucun token à ajouter en query param.
export function wsUrl(path: string): string {
  const httpUrl = new URL(`${API_BASE_URL}${path}`);
  httpUrl.protocol = httpUrl.protocol === "https:" ? "wss:" : "ws:";
  return httpUrl.toString();
}

interface RequestOptions extends RequestInit {
  auth?: boolean; // conservé pour compat d'API, sans effet désormais (le cookie part toujours)
}

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
  const { headers, ...rest } = options;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    credentials: "include", // envoie/reçoit le cookie httpOnly sur chaque requête
    headers: {
      "Content-Type": "application/json",
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