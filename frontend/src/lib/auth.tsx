import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import type { Role, Utilisateur } from "../types";
import { api } from "./api";

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
  raison_sociale?: string;
  numero_rc?: string;
  numero_carte_pro?: string;
}

interface ProfileUpdatePayload {
  nom?: string;
  prenom?: string;
  email?: string;
  telephone?: string;
  raison_sociale?: string;
  numero_rc?: string;
  numero_carte_pro?: string;
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
  verifyEmail: (email: string, code: string) => Promise<void>;
  logout: () => void;
  updateProfile: (payload: ProfileUpdatePayload) => Promise<Utilisateur>;
  changePassword: (motDePasseActuel: string, nouveauMotDePasse: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Utilisateur | null>(null);
  const [loading, setLoading] = useState(true);

  // Au chargement de l'app : le token vit désormais dans un cookie httpOnly
  // (invisible en JavaScript), donc on ne peut plus savoir à l'avance s'il
  // existe. On tente simplement /auth/me : ça réussit si le cookie est
  // présent et valide, ça échoue silencieusement sinon (visiteur non connecté).
  useEffect(() => {
    api
      .get<Utilisateur>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    // Le backend pose le cookie httpOnly via Set-Cookie sur la réponse ;
    // rien à stocker manuellement côté client.
    const res = await api.post<TokenResponse>("/auth/login", { email, password });
    setUser(res.user);
    return res.user;
  };

  const register = async (payload: RegisterPayload) => {
    // L'inscription ne renvoie plus de token ni de connexion automatique :
    // le compte doit d'abord être confirmé via le code reçu par email.
    return api.post<RegisterResponse>("/auth/register", payload);
  };

  const resendVerification = async (email: string) => {
    await api.post<void>("/auth/resend-verification", { email });
  };

  const verifyEmail = async (email: string, code: string) => {
    await api.post<Utilisateur>("/auth/verify-email", { email, code });
  };

  const logout = () => {
    // Demande au backend d'effacer le cookie httpOnly (le JS ne peut pas le
    // lire ni le supprimer lui-même). Best-effort : même si l'appel réseau
    // échoue, on nettoie l'état local pour ne pas laisser l'UI incohérente.
    api.post<void>("/auth/logout").catch(() => {});
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