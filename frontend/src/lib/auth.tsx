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

interface ProfileUpdatePayload {
  nom?: string;
  prenom?: string;
  email?: string;
  telephone?: string;
}

interface RegisterResponse {
  message: string;
  email: string;
}

interface AuthContextValue {
  user: Utilisateur | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<Utilisateur>;
  register: (payload: RegisterPayload) => Promise<RegisterResponse>;
  resendVerification: (email: string) => Promise<void>;
  verifyEmail: (token: string) => Promise<void>;
  logout: () => void;
  updateProfile: (payload: ProfileUpdatePayload) => Promise<Utilisateur>;
  changePassword: (motDePasseActuel: string, nouveauMotDePasse: string) => Promise<void>;
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
    // L'inscription ne renvoie plus de token ni de connexion automatique :
    // le compte doit d'abord être confirmé via le lien reçu par email.
    return api.post<RegisterResponse>("/auth/register", payload, { auth: false });
  };

  const resendVerification = async (email: string) => {
    await api.post<void>("/auth/resend-verification", { email }, { auth: false });
  };

  const verifyEmail = async (token: string) => {
    await api.get<Utilisateur>(`/auth/verify-email?token=${encodeURIComponent(token)}`);
  };

  const logout = () => {
    tokenStore.clear();
    setUser(null);
  };

  // Page « Mon compte » : met à jour nom/prénom/email/téléphone côté back-end
  // (PATCH /auth/me) puis synchronise l'utilisateur en mémoire/contexte.
  const updateProfile = async (payload: ProfileUpdatePayload) => {
    const updated = await api.patch<Utilisateur>("/auth/me", payload);
    setUser(updated);
    return updated;
  };

  // Page « Mon compte » : changement de mot de passe (exige l'ancien).
  const changePassword = async (motDePasseActuel: string, nouveauMotDePasse: string) => {
    await api.patch<void>("/auth/me/mot-de-passe", {
      mot_de_passe_actuel: motDePasseActuel,
      nouveau_mot_de_passe: nouveauMotDePasse,
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        resendVerification,
        verifyEmail,
        logout,
        updateProfile,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé dans AuthProvider");
  return ctx;
}
