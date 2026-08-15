import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import PublierAnnonceButton from "../publish/PublierAnnonceButton";
import logo from "../../assets/logo_immo1.png";

const NAV_LINKS = [
  { href: "#services", label: "Services" },
  { href: "#catalogue", label: "Catalogue" },
  { href: "#actualites", label: "Actualités" },
  { href: "#apropos", label: "À propos" },
  { href: "#contact", label: "Contact" },
  { href: "faq", label: "FAQ" },
];

/**
 * Header public partagé — utilisé par LandingPage.tsx ET PublierPage.tsx
 * (et potentiellement toute autre page publique), pour garantir que la
 * navigation reste EXACTEMENT la même en passant de l'une à l'autre, plutôt
 * que d'avoir une mini-page avec un header réduit.
 *
 * Les liens d'ancrage (#services, #catalogue...) renvoient vers ces
 * sections sur la landing page via "/#..." (et non un simple <a href="#...">
 * qui ne fonctionnerait que si on est déjà sur la landing page) — voir le
 * useEffect de défilement automatique vers le hash dans LandingPage.tsx.
 */
export default function SiteHeader() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--color-line)] bg-[var(--color-paper)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-1.5">
        <Link to="/" className="flex items-center gap-2.5" aria-label="Retour à l'accueil">
          <img src={logo} alt="ImmoVision" className="h-28 w-auto" />
          <span className="font-display text-xl font-semibold text-[var(--color-ink)]">
            
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              to={`/${l.href}`}
              className="text-sm font-medium text-[var(--color-ink-2)] transition-colors hover:text-[var(--color-brass-deep)]"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <PublierAnnonceButton variant="outline" />
          <Link
            to="/login"
            className="rounded-md border border-[var(--color-line)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] transition-colors hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]"
          >
            Connexion
          </Link>
          <Link
            to="/login?mode=register"
            className="rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
          >
            Inscription
          </Link>
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <PublierAnnonceButton variant="icon" />
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Ouvrir le menu"
            aria-expanded={menuOpen}
            className="text-[var(--color-ink)]"
          >
            {menuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="border-t border-[var(--color-line)] bg-[var(--color-paper)] px-6 py-4 md:hidden">
          <nav className="flex flex-col gap-3">
            {NAV_LINKS.map((l) => (
              <Link
                key={l.href}
                to={`/${l.href}`}
                onClick={() => setMenuOpen(false)}
                className="text-sm font-medium text-[var(--color-ink-2)]"
              >
                {l.label}
              </Link>
            ))}
            <div className="mt-2 flex gap-3">
              <Link
                to="/login"
                className="flex-1 rounded-md border border-[var(--color-line)] px-4 py-2 text-center text-sm font-medium text-[var(--color-ink)]"
              >
                Connexion
              </Link>
              <Link
                to="/login?mode=register"
                className="flex-1 rounded-md bg-[var(--color-brass)] px-4 py-2 text-center text-sm font-medium text-white"
              >
                Inscription
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
