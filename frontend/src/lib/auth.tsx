import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import type { Role, Utilisateur } from "../types";
import { api, tokenStore } from "./api";

interface TokenResponse {
  access_token: string;
  token_type: string;
  role: Role;
  user: Utilisateur;
}

interface RegisterPayload {
  nom: string;
  prenom: string;
  email: string;
  password: string;
  telephone?: string;
  role: Role;
}

interface AuthContextValue {
  user: Utilisateur | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<Utilisateur>;
  register: (payload: RegisterPayload) => Promise<Utilisateur>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Utilisateur | null>(null);
  const [loading, setLoading] = useState(true);

  // Au chargement de l'app, si un token existe déjà (session précédente), on le valide
  // via /auth/me pour restaurer la session sans redemander l'email/mot de passe.
  useEffect(() => {
    const token = tokenStore.get();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get<Utilisateur>("/auth/me")
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post<TokenResponse>(
      "/auth/login",
      { email, password },
      { auth: false }
    );
    tokenStore.set(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const register = async (payload: RegisterPayload) => {
    await api.post<Utilisateur>("/auth/register", payload, { auth: false });
    // L'inscription ne renvoie pas de token : on enchaîne avec un login.
    return login(payload.email, payload.password);
  };

  const logout = () => {
    tokenStore.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé dans AuthProvider");
  return ctx;
}
