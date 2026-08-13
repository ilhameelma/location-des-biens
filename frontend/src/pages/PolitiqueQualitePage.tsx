import SiteFooter from "../components/layout/SiteFooter";
import SiteHeader from "../components/layout/SiteHeader";

/**
 * Page publique — Politique Qualité.
 * Contenu générique/placeholder décrivant les engagements de la plateforme
 * (vérification des annonces/propriétaires, sécurité des paiements et des
 * données, modération) — à faire relire et compléter avant mise en
 * production réelle, voir aussi ConditionsGeneralesPage.tsx (même patron).
 */
export default function PolitiqueQualitePage() {
  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      <SiteHeader />

      <main className="mx-auto max-w-3xl px-6 py-16">
        <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
          Nos engagements
        </span>
        <h1 className="mt-4 font-display text-3xl text-[var(--color-ink)] sm:text-4xl">
          Politique Qualité
        </h1>
        <p className="mt-2 text-xs text-[var(--color-ink-3)]">Dernière mise à jour : {new Date().getFullYear()}</p>

        <div className="mt-8 space-y-6 text-sm leading-relaxed text-[var(--color-ink-2)]">
          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">Vérification des propriétaires</h2>
            <p>
              Tout compte propriétaire professionnel (agence, promoteur, conciergerie) est
              examiné par notre équipe avant de pouvoir publier une annonce. Un compte
              propriétaire particulier peut être vérifié à tout moment sur demande.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">Détection des annonces frauduleuses</h2>
            <p>
              Chaque annonce peut être passée au crible de notre module de détection de fraude
              (analyse de l'écart entre le prix affiché et une estimation automatique du
              marché), en complément de la modération humaine assurée par nos administrateurs.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">Sécurité des paiements</h2>
            <p>
              Les paiements effectués sur la plateforme sont suivis de bout en bout et associés
              à un contrat généré automatiquement à la confirmation d'une réservation, pour
              garantir la traçabilité de chaque transaction.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">Protection des données</h2>
            <p>
              Les données personnelles des utilisateurs sont traitées conformément à la loi
              09-08. Les mots de passe sont chiffrés, et les échanges (messagerie, notifications)
              transitent via des connexions sécurisées.
            </p>
          </section>

          <section>
            <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">Réclamations et litiges</h2>
            <p>
              Toute réclamation déposée depuis la plateforme est transmise sans délai à notre
              équipe ainsi qu'au propriétaire concerné, afin d'assurer un traitement rapide et
              transparent des litiges signalés.
            </p>
          </section>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
