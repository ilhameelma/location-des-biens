import { type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Building2, LayoutGrid, Search, FileSignature, Wallet, MessageSquare,
  Star, ShieldAlert, Users, BarChart3, LogOut, Home, UserCircle,
} from "lucide-react";
import { useAuth } from "../../lib/auth";
import type { Role } from "../../types";
import NotificationBell from "./NotificationBell";

interface NavItem {
  to: string;
  label: string;
  icon: typeof Home;
}

const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  client: [
    { to: "/client", label: "Rechercher", icon: Search },
    { to: "/client/reservations", label: "Réservations", icon: FileSignature },
    { to: "/client/paiements", label: "Paiements", icon: Wallet },
    { to: "/client/messages", label: "Messagerie", icon: MessageSquare },
    { to: "/client/avis", label: "Mes avis", icon: Star },
  ],
  proprietaire: [
    { to: "/proprietaire", label: "Mes biens", icon: LayoutGrid },
    { to: "/proprietaire/demandes", label: "Demandes", icon: FileSignature },
    { to: "/proprietaire/paiements", label: "Paiements", icon: Wallet },
    { to: "/proprietaire/messages", label: "Messagerie", icon: MessageSquare },
    { to: "/proprietaire/avis", label: "Avis clients", icon: Star },
  ],
  admin: [
    { to: "/admin", label: "Vue d'ensemble", icon: BarChart3 },
    { to: "/admin/utilisateurs", label: "Utilisateurs", icon: Users },
    { to: "/admin/biens", label: "Annonces", icon: Building2 },
    { to: "/admin/reclamations", label: "Réclamations", icon: ShieldAlert },
  ],
};

const ROLE_LABEL: Record<Role, string> = {
  client: "Espace Client",
  proprietaire: "Espace Propriétaire",
  admin: "Administration",
};

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;
  const items = NAV_BY_ROLE[user.role];

  return (
    <div className="flex min-h-screen bg-[var(--color-paper)]">
      <aside className="flex w-64 flex-col justify-between bg-[var(--color-ink)] px-4 py-6 text-white">
        <div>
          <div className="mb-8 flex items-center gap-2 px-2">
            <Home size={20} className="text-[var(--color-brass)]" />
            <span className="font-display text-lg">SmartRent</span>
          </div>
          <div className="mb-4 px-2 font-mono text-[11px] uppercase tracking-widest text-white/50">
            {ROLE_LABEL[user.role]}
          </div>
          <nav className="space-y-1">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === `/${user.role}`}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? "bg-white/10 text-[var(--color-brass)]"
                      : "text-white/75 hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                <item.icon size={17} />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="space-y-1">
          <NavLink
            to="/compte"
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-white/10 text-[var(--color-brass)]"
                  : "text-white/75 hover:bg-white/5 hover:text-white"
              }`
            }
          >
            <UserCircle size={17} />
            Mon compte
          </NavLink>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-white/60 transition-colors hover:bg-white/5 hover:text-white"
          >
            <LogOut size={17} />
            Déconnexion
          </button>
        </div>
      </aside>

      <div className="flex-1">
        <header className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-card)] px-8 py-4">
          <div />
          <div className="flex items-center gap-4">
            <NotificationBell />
            <NavLink
              to="/compte"
              className="flex items-center gap-2 rounded-md px-2 py-1 text-sm transition-colors hover:bg-[var(--color-paper-2)]"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-paper-2)] font-display text-[var(--color-ink)]">
                {user.prenom[0]}
                {user.nom[0]}
              </div>
              <span className="text-[var(--color-ink-2)]">
                {user.prenom} {user.nom}
              </span>
            </NavLink>
          </div>
        </header>
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
