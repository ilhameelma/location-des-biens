import SiteFooter from "../components/layout/SiteFooter";
import SiteHeader from "../components/layout/SiteHeader";
import IdentitesCards from "../components/publish/IdentitesCards";

/**
 * Page publique dédiée à la publication d'une annonce (visiteur non
 * connecté). Un client déjà connecté qui clique "Publier une annonce" est
 * envoyé sur la variante /client/publier (pages/client/PublierPage.tsx),
 * qui affiche le même contenu (IdentitesCards) mais à l'intérieur de son
 * propre espace (sidebar + header du dashboard), pour qu'il ne perde jamais
 * le fil de sa session.
 *
 * Utilise SiteHeader.tsx (le même header que LandingPage.tsx) plutôt qu'un
 * header réduit : la navigation reste identique en passant de l'accueil à
 * cette page.
 */
export default function PublierPage() {
  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      <SiteHeader />

      <main className="mx-auto max-w-5xl px-6 py-16">
        <div className="text-center">
          <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
            Publier une annonce
          </span>
          <h1 className="mt-4 font-display text-3xl text-[var(--color-ink)] sm:text-4xl">
            Vous êtes... ?
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-sm text-[var(--color-ink-2)]">
            Choisissez le profil qui vous correspond — votre inscription s'ouvrira
            directement avec ce profil, en une seule étape.
          </p>
        </div>

        <div className="mt-12">
          <IdentitesCards />
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
