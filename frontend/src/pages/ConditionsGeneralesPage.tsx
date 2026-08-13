import SiteFooter from "../components/layout/SiteFooter";
import SiteHeader from "../components/layout/SiteHeader";

/**
 * Page publique — Conditions générales d'utilisation.
 * Contenu générique/placeholder, à faire relire et compléter (mentions
 * légales exactes de la structure éditrice, RC, etc.) avant mise en
 * production réelle — voir aussi PolitiqueQualitePage.tsx (même patron).
 */
export default function ConditionsGeneralesPage() {
  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      <SiteHeader />

      <main className="mx-auto max-w-3xl px-6 py-16">
        <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
          Informations légales
        </span>
        <h1 className="mt-4 font-display text-3xl text-[var(--color-ink)] sm:text-4xl">
          Conditions générales d'utilisation
        </h1>
        <p className="mt-2 text-xs text-[var(--color-ink-3)]">Dernière mise à jour : {new Date().getFullYear()}</p>

        <div className="mt-8 space-y-6 text-sm leading-relaxed text-[var(--color-ink-2)]">
          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">1. Objet</h2>
            <p>
              Les présentes conditions générales d'utilisation (CGU) régissent l'accès et
              l'utilisation de la plateforme ImmoVision, service de mise en relation entre
              propriétaires et locataires/acheteurs de biens immobiliers au Maroc. En créant
              un compte ou en utilisant la plateforme, l'utilisateur accepte sans réserve les
              présentes conditions.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">2. Comptes utilisateurs</h2>
            <p>
              ImmoVision distingue trois types de comptes : client, propriétaire (particulier,
              agence, promoteur ou conciergerie) et administrateur. Les comptes propriétaires
              professionnels font l'objet d'une vérification avant de pouvoir publier une
              annonce. Chaque utilisateur est responsable de la confidentialité de ses
              identifiants et de l'exactitude des informations qu'il communique.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">3. Annonces et transactions</h2>
            <p>
              Les propriétaires sont seuls responsables du contenu, de l'exactitude et de la
              légalité des annonces publiées. ImmoVision met à disposition des outils de
              réservation, de contrat, de paiement et de messagerie, mais n'est pas partie aux
              transactions conclues entre utilisateurs et n'intervient qu'en tant
              qu'intermédiaire technique.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">4. Usage interdit</h2>
            <p>
              Il est interdit de publier des annonces frauduleuses, d'usurper l'identité
              d'autrui, ou de détourner la plateforme à des fins autres que la mise en relation
              immobilière. Tout manquement peut entraîner la suspension ou la suppression du
              compte concerné, sans préjudice d'éventuelles poursuites.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">5. Données personnelles</h2>
            <p>
              Les données personnelles collectées sont traitées conformément à la loi 09-08
              relative à la protection des personnes physiques à l'égard du traitement des
              données à caractère personnel. Voir la Politique Qualité pour le détail des
              engagements pris par la plateforme.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">6. Évolution des CGU</h2>
            <p>
              ImmoVision se réserve le droit de modifier les présentes conditions à tout
              moment. Les utilisateurs seront informés de toute modification substantielle par
              les moyens de communication habituels de la plateforme.
            </p>
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
