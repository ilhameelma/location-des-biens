import { useState, type ReactNode } from "react";
import { NavLink, Link } from "react-router-dom";
import {
  Building2,
  LayoutGrid,
  Search,
  FileSignature,
  Wallet,
  MessageSquare,
  Star,
  ShieldAlert,
  Users,
  BarChart3,
  LogOut,
  Home,
  UserCircle,
  Heart,
  HardHat,
  FolderKanban,
  Newspaper,
  Menu,
  X,
} from "lucide-react";
import { useAuth } from "../../lib/auth";
import { useFavorisCount } from "../../lib/useFavorisCount";
import type { Role } from "../../types";
import NotificationBell from "./NotificationBell";
import SiteFooter from "./SiteFooter";
import PublierAnnonceButton from "../publish/PublierAnnonceButton";
import logo from "../../assets/logo_immo1.png";

interface NavItem {
  to: string;
  label: string;
  icon: typeof Home;
}

const NAV_BY_ROLE: Record<Role, NavItem[]> = {
  client: [
    { to: "/client", label: "Rechercher", icon: Search },
    { to: "/client/favoris", label: "Annonces enregistrées", icon: Heart },
    { to: "/client/reservations", label: "Réservations", icon: FileSignature },
    { to: "/client/paiements", label: "Paiements", icon: Wallet },
    { to: "/client/messages", label: "Messagerie", icon: MessageSquare },
    { to: "/client/avis", label: "Mes avis", icon: Star },
    { to: "/client/reclamations", label: "Réclamations", icon: ShieldAlert },
  ],

  proprietaire: [
    { to: "/proprietaire", label: "Mes biens", icon: LayoutGrid },
    { to: "/proprietaire/demandes", label: "Demandes", icon: FileSignature },
    { to: "/proprietaire/paiements", label: "Paiements", icon: Wallet },
    { to: "/proprietaire/messages", label: "Messagerie", icon: MessageSquare },
    { to: "/proprietaire/avis", label: "Avis clients", icon: Star },
  ],

  agence: [
    { to: "/agence", label: "Mes biens", icon: LayoutGrid },
    { to: "/agence/demandes", label: "Demandes", icon: FileSignature },
    { to: "/agence/paiements", label: "Paiements", icon: Wallet },
    { to: "/agence/messages", label: "Messagerie", icon: MessageSquare },
    { to: "/agence/avis", label: "Avis clients", icon: Star },
    { to: "/agence/blog", label: "Blog", icon: Newspaper },
  ],

  promoteur: [
    { to: "/promoteur", label: "Mes biens (lots)", icon: HardHat },
    { to: "/promoteur/projets", label: "Mes projets", icon: FolderKanban },
    { to: "/promoteur/demandes", label: "Demandes", icon: FileSignature },
    { to: "/promoteur/paiements", label: "Paiements", icon: Wallet },
    { to: "/promoteur/messages", label: "Messagerie", icon: MessageSquare },
    { to: "/promoteur/avis", label: "Avis clients", icon: Star },
  ],

  conciergerie: [
    { to: "/conciergerie", label: "Mes biens", icon: LayoutGrid },
    { to: "/conciergerie/demandes", label: "Demandes", icon: FileSignature },
    { to: "/conciergerie/paiements", label: "Paiements", icon: Wallet },
    { to: "/conciergerie/messages", label: "Messagerie", icon: MessageSquare },
    { to: "/conciergerie/avis", label: "Avis clients", icon: Star },
  ],

  admin: [
    { to: "/admin", label: "Vue d'ensemble", icon: BarChart3 },
    { to: "/admin/utilisateurs", label: "Utilisateurs", icon: Users },
    { to: "/admin/biens", label: "Annonces", icon: Building2 },
    { to: "/admin/reclamations", label: "Réclamations", icon: ShieldAlert },
    { to: "/admin/actualites", label: "Blog", icon: Newspaper },
  ],
};

const ROLE_LABEL: Record<Role, string> = {
  client: "ESPACE CLIENT",
  proprietaire: "ESPACE PROPRIÉTAIRE",
  agence: "ESPACE AGENCE",
  promoteur: "ESPACE PROMOTEUR",
  conciergerie: "ESPACE CONCIERGERIE",
  admin: "ADMINISTRATION",
};

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  const { user, logout } = useAuth();
  const favorisCount = useFavorisCount();
  const [menuOpen, setMenuOpen] = useState(false);

  if (!user) return null;

  const items = NAV_BY_ROLE[user.role];

  const sidebarContent = (
    <>
      <div>
        {/* Logo */}
        <div className="mb-8 flex items-center justify-between gap-3 px-2">
          <Link to="/" className="flex items-center gap-3" aria-label="Retour à l'accueil">
            <img src={logo} alt="ImmoVision" className="h-14 w-auto lg:h-28" />
            <span className="font-display text-xl font-semibold text-[var(--color-ink)] lg:text-2xl">
              
            </span>
          </Link>
          {/* Bouton de fermeture du tiroir — visible uniquement en dessous de lg */}
          <button
            type="button"
            onClick={() => setMenuOpen(false)}
            className="rounded-lg p-1.5 text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)] lg:hidden"
            aria-label="Fermer le menu"
          >
            <X size={20} />
          </button>
        </div>

        {/* Role */}
        <div className="mb-4 px-2 font-mono text-[11px] uppercase tracking-widest text-[var(--color-ink-3)]">
          {ROLE_LABEL[user.role]}
        </div>

        {/* Menu */}
        <nav className="space-y-1">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === `/${user.role}`}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-all duration-200 ${
                  isActive
                    ? "bg-[var(--color-brass-bg)] text-[var(--color-brass)] shadow-sm"
                    : "text-[var(--color-ink)] hover:bg-[var(--color-paper-2)] hover:text-[var(--color-brass)]"
                }`
              }
            >
              <span className="flex items-center gap-3">
                <item.icon size={18} />
                {item.label}
              </span>

              {item.to === "/client/favoris" && favorisCount > 0 && (
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--color-brass)] px-1.5 text-[10px] font-semibold text-white">
                  {favorisCount > 99 ? "99+" : favorisCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Bas Sidebar */}
      <div className="space-y-1">
        <NavLink
          to="/compte"
          onClick={() => setMenuOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200 ${
              isActive
                ? "bg-[var(--color-brass-bg)] text-[var(--color-brass)]"
                : "text-[var(--color-ink)] hover:bg-[var(--color-paper-2)] hover:text-[var(--color-brass)]"
            }`
          }
        >
          <UserCircle size={18} />
          Mon compte
        </NavLink>

        <button
          onClick={() => {
            // Rechargement complet vers "/" plutôt qu'une navigation
            // React Router : on évite ainsi toute course possible avec
            // la redirection de ProtectedRoute (qui renvoie vers /login
            // dès que `user` devient null) — ici la page recharge
            // entièrement, donc React repart de zéro directement sur "/".
            logout();
            window.location.href = "/";
          }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-[var(--color-ink-2)] transition-all duration-200 hover:bg-[var(--color-rust-bg)] hover:text-[var(--color-rust)]"
        >
          <LogOut size={18} />
          Déconnexion
        </button>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-paper)] lg:flex-row">
      {/* ================= SIDEBAR — fixe à partir de lg, tiroir en dessous ================= */}

      {/* Fond semi-transparent derrière le tiroir mobile/tablette */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col justify-between overflow-y-auto border-r border-[var(--color-line)] bg-[var(--color-card)] px-4 py-6 transition-transform duration-200 ease-out lg:sticky lg:top-0 lg:z-auto lg:h-screen lg:w-64 lg:max-w-none lg:translate-x-0 ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {sidebarContent}
      </aside>

      {/* ================= CONTENU ================= */}

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Barre supérieure mobile/tablette : hamburger + logo, remplace le
            header desktop en dessous de lg (la sidebar n'est plus visible) */}
        <div className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-card)] px-4 py-3 lg:hidden">
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            className="rounded-lg p-2 text-[var(--color-ink)] hover:bg-[var(--color-paper-2)]"
            aria-label="Ouvrir le menu"
          >
            <Menu size={22} />
          </button>
          <Link to="/" className="flex items-center gap-2" aria-label="Retour à l'accueil">
            <img src={logo} alt="ImmoVision" className="h-9 w-auto" />
            <span className="font-display text-lg font-semibold text-[var(--color-ink)]">
              ImmoVision
            </span>
          </Link>
          <div className="flex items-center gap-1">
            {user.role === "client" && <PublierAnnonceButton variant="icon" />}
            <NotificationBell />
          </div>
        </div>

        <header className="hidden items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-card)] px-8 py-4 lg:flex">
          <div />

          <div className="flex items-center gap-4">
            {user.role === "client" && <PublierAnnonceButton variant="outline" />}
            <NotificationBell />

            <NavLink
              to="/compte"
              className="flex items-center gap-2 rounded-lg px-2 py-1 transition hover:bg-[var(--color-paper-2)]"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-paper-2)] font-display text-[var(--color-ink)]">
                {user.prenom[0]}
                {user.nom[0]}
              </div>

              <span className="text-sm text-[var(--color-ink-2)]">
                {user.prenom} {user.nom}
              </span>
            </NavLink>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">{children}</main>

        <SiteFooter />
      </div>
    </div>
  );
}