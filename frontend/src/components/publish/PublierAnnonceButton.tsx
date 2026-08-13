import { useNavigate } from "react-router-dom";
import { Megaphone } from "lucide-react";
import { useAuth } from "../../lib/auth";
import type { Role } from "../../types";

/**
 * Bouton "Publier une annonce" réutilisé sur les pages publiques (landing,
 * actualités) et, pour les clients connectés uniquement, dans le dashboard
 * (voir DashboardLayout.tsx — masqué pour les rôles professionnels, qui ont
 * déjà "Mes biens" dans leur menu latéral, pour éviter un doublon).
 *
 * Comportement :
 * - Visiteur non connecté → renvoie vers la page publique /publier
 *   (PublierPage.tsx).
 * - Connecté en tant que client → renvoie vers /client/publier
 *   (pages/client/PublierPage.tsx), le même contenu mais affiché À
 *   L'INTÉRIEUR de son propre espace (sidebar "ESPACE CLIENT" + header du
 *   dashboard restent visibles) — il ne quitte jamais sa session en
 *   apparence.
 *   Les deux versions listent les 4 profils professionnels ; chaque carte
 *   mène ensuite vers l'inscription avec le rôle déjà présélectionné
 *   (/login?mode=register&role=...).
 * - Connecté avec un rôle professionnel (proprietaire/agence/conciergerie)
 *   → va directement vers son espace "Mes biens".
 * - Connecté en tant que promoteur → va vers "Mes projets" (un lot se
 *   publie uniquement depuis un projet pour ce rôle).
 * - Connecté en tant qu'admin → composant masqué (un admin ne publie pas).
 */

const CHEMIN_PUBLICATION: Partial<Record<Role, string>> = {
  proprietaire: "/proprietaire",
  agence: "/agence",
  conciergerie: "/conciergerie",
  promoteur: "/promoteur/projets",
};

type Variant = "solid" | "outline" | "icon";

export default function PublierAnnonceButton({
  variant = "solid",
  className = "",
}: {
  variant?: Variant;
  className?: string;
}) {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Un administrateur ne publie jamais d'annonce.
  if (user?.role === "admin") return null;

  const handleClick = () => {
    if (!user) {
      navigate("/publier");
      return;
    }
    if (user.role === "client") {
      navigate("/client/publier");
      return;
    }
    navigate(CHEMIN_PUBLICATION[user.role] ?? "/");
  };

  const baseClasses =
    variant === "solid"
      ? "inline-flex items-center gap-2 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
      : variant === "outline"
      ? "inline-flex items-center gap-2 rounded-md border border-[var(--color-line)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] transition-colors hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]"
      : "inline-flex items-center justify-center rounded-lg p-2 text-[var(--color-ink)] transition-colors hover:bg-[var(--color-paper-2)]";

  return (
    <button
      type="button"
      onClick={handleClick}
      title="Publier une annonce"
      aria-label="Publier une annonce"
      className={`${baseClasses} ${className}`}
    >
      <Megaphone size={variant === "icon" ? 20 : 16} />
      {variant !== "icon" && "Publier une annonce"}
    </button>
  );
}
