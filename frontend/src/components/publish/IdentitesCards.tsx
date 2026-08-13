import { Link } from "react-router-dom";
import { ArrowRight, Home, Building2, HardHat, Handshake } from "lucide-react";
import photoProprietaire from "../../assets/home1.png";
import photoAgence from "../../assets/home2.png";
import photoPromoteur from "../../assets/home3.png";
import photoConciergerie from "../../assets/home4.png";
import type { Role } from "../../types";

const PROFILS: {
  role: Role;
  label: string;
  photo: string;
  icon: typeof Home;
  description: string;
}[] = [
  {
    role: "proprietaire",
    label: "Propriétaire",
    photo: photoProprietaire,
    icon: Home,
    description:
      "Vous possédez un bien (appartement, maison, magasin...) et souhaitez le mettre en location ou en vente.",
  },
  {
    role: "agence",
    label: "Agence immobilière",
    photo: photoAgence,
    icon: Building2,
    description:
      "Vous représentez une agence et gérez un portefeuille de biens pour le compte de plusieurs mandants.",
  },
  {
    role: "promoteur",
    label: "Promoteur immobilier",
    photo: photoPromoteur,
    icon: HardHat,
    description:
      "Vous êtes promoteur et souhaitez présenter vos projets neufs, lot par lot, aux futurs acquéreurs.",
  },
  {
    role: "conciergerie",
    label: "Conciergerie",
    photo: photoConciergerie,
    icon: Handshake,
    description:
      "Vous gérez des biens pour le compte de propriétaires (location courte ou longue durée) et publiez en leur nom.",
  },
];

/**
 * Grille des 4 profils professionnels, réutilisée par :
 * - PublierPage.tsx (page publique /publier, visiteur non connecté)
 * - client/PublierPage.tsx (page /client/publier, client déjà connecté —
 *   affichée à l'intérieur de son propre espace via DashboardLayout, pour
 *   qu'il ne perde jamais le fil de sa session en cliquant "Publier une
 *   annonce")
 *
 * Chaque carte renvoie vers l'inscription avec le rôle déjà présélectionné.
 * Un compte professionnel est un compte séparé (email différent) du compte
 * client déjà connecté — l'inscription se fait normalement, sans jamais
 * déconnecter la session client en cours tant que l'inscription n'est pas
 * finalisée.
 */
export default function IdentitesCards({
  afficherLienClient = true,
}: {
  afficherLienClient?: boolean;
}) {
  return (
    <>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {PROFILS.map((p) => (
          <Link
            key={p.role}
            to={`/login?mode=register&role=${p.role}`}
            className="group flex flex-col overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] transition-shadow hover:shadow-lg"
          >
            <div className="relative h-40 w-full overflow-hidden">
              <img
                src={p.photo}
                alt={p.label}
                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
            </div>
            <div className="flex flex-1 flex-col p-5">
              <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-[var(--color-brass-bg)] px-3 py-1 text-xs font-medium text-[var(--color-brass-deep)]">
                <p.icon size={13} />
                {p.label}
              </span>
              <p className="mt-3 flex-1 text-sm leading-relaxed text-[var(--color-ink-2)]">
                {p.description}
              </p>
              <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--color-brass-deep)] transition-colors group-hover:text-[var(--color-brass)]">
                S'inscrire
                <ArrowRight size={15} className="transition-transform group-hover:translate-x-1" />
              </span>
            </div>
          </Link>
        ))}
      </div>

      {afficherLienClient && (
        <p className="mt-10 text-center text-xs text-[var(--color-ink-3)]">
          Vous cherchez simplement un bien à louer ou à acheter ?{" "}
          <Link to="/login?mode=register" className="font-medium text-[var(--color-brass-deep)] hover:underline">
            Créez un compte client
          </Link>
          .
        </p>
      )}
    </>
  );
}
