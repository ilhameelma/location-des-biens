import { Link } from "react-router-dom";
import { Mail } from "lucide-react";
import {
  FacebookIcon,
  InstagramIcon,
  TikTokIcon,
  YouTubeIcon,
} from "../icons/SocialIcons";
import logo from "../../assets/logo_immo1.png";

// Adresse affichée dans le footer de toutes les pages — un seul endroit à
// modifier si elle doit changer.
export const CONTACT_EMAIL = "immovision260@gmail.com";

// Liens des sections de la landing page. Préfixés par "/" pour fonctionner
// depuis n'importe quelle page (pas seulement "/") : le navigateur navigue
// vers la page d'accueil puis défile jusqu'à l'ancre correspondante. Depuis
// la page d'accueil elle-même, "/#services" se comporte comme "#services"
// (même chemin, juste l'ancre change).
const NAV_LINKS = [
  { href: "/#services", label: "Services" },
  { href: "/#catalogue", label: "Catalogue" },
  { href: "/#actualites", label: "Actualités" },
  { href: "/#apropos", label: "À propos" },
  { href: "/#contact", label: "Contact" },
];

// Liens vers les réseaux sociaux officiels d'ImmoVision.
const SOCIAL_LINKS = [
  {
    label: "Facebook",
    href: "https://www.facebook.com/profile.php?id=61593057337517",
    Icon: FacebookIcon,
  },
  {
    label: "Instagram",
    href: "https://www.instagram.com/immovision2026/",
    Icon: InstagramIcon,
  },
  {
    label: "YouTube",
    href: "https://www.youtube.com/@immovision-r5i",
    Icon: YouTubeIcon,
  },
  {
    label: "TikTok",
    href: "https://www.tiktok.com/@immovision26",
    Icon: TikTokIcon,
  },
];

/**
 * Footer riche partagé par TOUTES les pages de la plateforme (publiques et
 * connectées) : logo, navigation vers les sections de la landing page,
 * liens légaux (CGU / Politique Qualité), réseaux sociaux, copyright,
 * contact et mention loi 09-08. Identique visuellement à celui de la
 * landing page — un seul endroit à modifier pour que le changement se
 * répercute partout (DashboardLayout, LoginPage, PublierPage, pages
 * légales, landing page...).
 */
export default function SiteFooter() {
  return (
    <footer className="border-t border-[var(--color-line)] bg-[var(--color-ink)] py-12 text-[#cfcac2]">
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <Link
            to="/"
            className="flex items-center gap-2.5"
            aria-label="Retour à l'accueil"
          >
            <img src={logo} alt="ImmoVision" className="h-9 w-auto" />
            <span className="font-display text-lg text-white">
              ImmoVision
            </span>
          </Link>

          <nav className="flex flex-wrap gap-6 text-sm">
            {NAV_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="transition-colors hover:text-white"
              >
                {l.label}
              </a>
            ))}

            <Link
              to="/login"
              className="transition-colors hover:text-white"
            >
              Connexion
            </Link>
          </nav>
        </div>

        <div className="mt-8 flex flex-col gap-6 border-t border-white/10 pt-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-4 text-xs">
              <Link
                to="/conditions-generales-utilisation"
                className="transition-colors hover:text-white"
              >
                Conditions générales d'utilisation
              </Link>

              <span className="text-white/20">·</span>

              <Link
                to="/politique-qualite"
                className="transition-colors hover:text-white"
              >
                Politique Qualité
              </Link>
            </div>

            <div className="flex items-center gap-3">
              {SOCIAL_LINKS.map(({ label, href, Icon }) => (
                <a
                  key={label}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={label}
                  className="flex h-8 w-8 items-center justify-center rounded-full border border-white/15 text-[#cfcac2] transition-colors hover:border-white/40 hover:text-white"
                >
                  <Icon width={15} height={15} />
                </a>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2 border-t border-white/10 pt-6 text-xs sm:flex-row sm:items-center sm:justify-between">
            <span>
              © {new Date().getFullYear()} ImmoVision L'intelligence au service
              de l'immobilier.
            </span>

            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="flex items-center gap-1.5 transition-colors hover:text-white"
            >
              <Mail size={13} />
              {CONTACT_EMAIL}
            </a>

            <span>
              Données personnelles traitées conformément à la loi 09-08.
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}