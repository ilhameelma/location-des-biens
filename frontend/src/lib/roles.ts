import type { Role } from "../types";

/** Rôles pouvant publier/gérer des annonces (biens) — utilisé pour router
 * vers le même type de tableau de bord et pour les contrôles d'accès
 * front-end (le back-end revalide toujours indépendamment). */
export const ROLES_ANNONCEURS: Role[] = ["proprietaire", "agence", "promoteur", "conciergerie"];

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Administrateur",
  client: "Client",
  proprietaire: "Propriétaire",
  agence: "Agence immobilière",
  promoteur: "Promoteur immobilier",
  conciergerie: "Conciergerie",
};

/** Emoji utilisé comme icône légère dans les badges/cartes — cohérent avec
 * le reste de l'app qui utilise déjà lucide-react pour les icônes vectorielles
 * mais des badges emoji ponctuels pour les libellés de rôle. */
export const ROLE_EMOJI: Record<Role, string> = {
  admin: "🛡️",
  client: "🔑",
  proprietaire: "🏠",
  agence: "🏢",
  promoteur: "🏗️",
  conciergerie: "🤝",
};

export function isRoleAnnonceur(role: Role | null | undefined): boolean {
  return !!role && (ROLES_ANNONCEURS as string[]).includes(role);
}

/** Libellé court affiché dans "Publié par ..." sur une fiche bien. */
export function labelAnnonceur(role: Role | null | undefined): string {
  if (!role) return "ce propriétaire";
  return ROLE_LABELS[role] ?? "ce propriétaire";
}
