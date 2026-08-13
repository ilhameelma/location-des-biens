import IdentitesCards from "../../components/publish/IdentitesCards";

/**
 * "Publier une annonce" pour un CLIENT déjà connecté (route /client/publier,
 * protégée, affichée à l'intérieur de son propre espace via
 * ProtectedRoute > DashboardLayout — sidebar "ESPACE CLIENT", cloche de
 * notifications, etc. restent visibles).
 *
 * Contrairement à la page publique (pages/PublierPage.tsx, pour un visiteur
 * non connecté), on reste ici dans le dashboard du client : il ne quitte
 * jamais visuellement sa session en cliquant "Publier une annonce" dans le
 * header. Un compte professionnel reste toutefois un compte séparé — cliquer
 * une carte mène à l'inscription (email différent), sans déconnecter la
 * session client en cours.
 */
export default function ClientPublierPage() {
  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">
        Publier une annonce
      </h1>
      <p className="mt-4 max-w-2xl text-sm text-[var(--color-ink-2)]">
        Votre compte client permet de rechercher et réserver des biens, pas
        d'en publier. Pour publier une annonce, créez un compte professionnel
        séparé en choisissant le profil qui vous correspond ci-dessous.
      </p>

      <div className="mt-8">
        <IdentitesCards afficherLienClient={false} />
      </div>
    </div>
  );
}
