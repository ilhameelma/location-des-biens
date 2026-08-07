import { Mail } from "lucide-react";

// Adresse affichée dans le footer de toutes les pages — un seul endroit à
// modifier si elle doit changer.
export const CONTACT_EMAIL = "immovision260@gmail.com";

/**
 * Footer compact réutilisé sur les pages qui n'ont pas déjà leur propre
 * footer "riche" (voir LandingPage.tsx, qui garde le sien mais affiche
 * aussi CONTACT_EMAIL). Utilisé dans DashboardLayout (toutes les pages
 * connectées) et LoginPage (formulaire + panneau de saisie du code OTP).
 *
 * `variant="dark"` : pour les pages à fond sombre (ex. LoginPage, sur
 * bg-[var(--color-ink)]) — texte clair au lieu du gris foncé par défaut,
 * sinon illisible.
 */
export default function Footer({ variant = "light" }: { variant?: "light" | "dark" }) {
  const estSombre = variant === "dark";

  return (
    <footer
      className={`px-6 py-4 text-xs ${
        estSombre
          ? "text-[#cfcac2]"
          : "border-t border-[var(--color-line)] text-[var(--color-ink-3)]"
      }`}
    >
      <div className="flex flex-col items-center justify-between gap-2 sm:flex-row">
        <span>© {new Date().getFullYear()} ImmoVision — L'intelligence au service de l'immobilier.</span>
        <a
          href={`mailto:${CONTACT_EMAIL}`}
          className={`flex items-center gap-1.5 transition-colors ${
            estSombre ? "hover:text-white" : "hover:text-[var(--color-brass)]"
          }`}
        >
          <Mail size={13} />
          {CONTACT_EMAIL}
        </a>
      </div>
    </footer>
  );
}
